import asyncio
import re
import random
import threading
from datetime import datetime
from loguru import logger
from app.services.voice.language_config import USER_PROFILE, SUPPORTED_LANGUAGES
from app.services.voice.speaker import speak
from app.services.voice.listener import listen_once
from app.services.voice.wake_word import start_wake_word_listener, add_wake_callback
from navix_tray import set_tray_state, add_chat_message


from app.services.voice.wake_word import add_interrupt_callback
from app.services.voice.speaker import interrupt_speech

_interrupted = threading.Event()

def on_interrupt(text: str):
    _interrupted.set()
    interrupt_speech()

# register once
add_interrupt_callback(on_interrupt)

BASE_URL = "http://127.0.0.1:8001"
SESSION_ID = "navix-main"

LISTENING_PHRASES = ["Mmm?","Yes?","Tell me.","Go ahead.","I'm here.","What's up?"]
FOLLOWUP_PHRASES  = ["What else can I do for you?","Anything else?","What's next?","I'm listening."]
DONE_PHRASES      = ["Done! What else?","Got it. Anything else?","Sure! Need anything more?","Alright! What's next?"]

def get_greeting() -> str:
    hour = datetime.now().hour
    lang = USER_PROFILE["preferred_language"]
    cfg  = SUPPORTED_LANGUAGES[lang]
    if 5 <= hour < 12:  return cfg["greeting_morning"]
    if 12 <= hour < 17: return cfg["greeting_afternoon"]
    if 17 <= hour < 21: return cfg["greeting_evening"]
    return cfg["greeting_night"]

async def process_command(text: str) -> str:
    try:
        from core.graph import get_graph
        from app.services.personal_memory import get_context_for_ai
        personal_context = await get_context_for_ai()
        graph = get_graph()
        state = {
            "messages": [], "user_input": text,
            "emotion": "neutral", "tool": "chat",
            "response": "", "personal_context": personal_context
        }
        result = await graph.ainvoke(state)
        return result["response"]
    except Exception as e:
        logger.error(f"Graph error: {e}")
        return "Sorry, something went wrong"

async def navix_session():
    from app.services.planner import save_daily_plan, get_todays_plan
    from app.services.reminder import start_reminder_loop
    from app.services.voice.personality import greeting
    from core.emotion import detect_emotion

    set_tray_state("sleeping")
    hour = datetime.now().hour
    existing_plan = await get_todays_plan()

    # friendly morning greeting
    greet = get_greeting()
    set_tray_state("talking")

    if existing_plan:
        speak(f"{greet} Welcome back Naveen! Your plan today is {existing_plan}. Let's do this!")
    else:
        speak(f"{greet} What are we doing today Naveen?")
        set_tray_state("active")
        await asyncio.sleep(0.5)
        plan = listen_once(duration=8)
        if plan and plan.strip():
            await save_daily_plan(plan)
            speak(f"Got it! {plan}. Sounds good, I've saved that. Let's get to it!")
        else:
            speak("No worries! Say Naveen anytime you need me.")

    # morning briefing
    if 6 <= hour <= 9:
        try:
            from app.services.news_briefing import build_morning_briefing
            briefing = await build_morning_briefing()
            set_tray_state("talking")
            speak(briefing)
        except Exception as e:
            logger.warning(f"Briefing error: {e}")

    # daily insight
    if 6 <= hour <= 10:
        try:
            from app.services.world_model import generate_daily_insight
            insight = await generate_daily_insight()
            set_tray_state("talking")
            speak(f"Quick insight for today Naveen. {insight}")
        except Exception as e:
            logger.warning(f"Insight error: {e}")

    asyncio.create_task(start_reminder_loop())
    set_tray_state("sleeping")


def on_wake_word(text: str):
    import threading
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(handle_wake_word(text))
        finally:
            loop.close()
    # daemon=True, no join() — lets wake word listener keep running
    threading.Thread(target=run, daemon=True).start()

def start_navix():
    logger.info("Starting NAVIX...")
    set_tray_state("talking")                     # ← speaking startup message
    speak("NAVIX online. Say Naveen to activate.")
    set_tray_state("sleeping")                    # ← back to sleep, waiting
    add_wake_callback(on_wake_word)
    start_wake_word_listener()
    logger.info("NAVIX ready — listening for wake word")


async def handle_wake_word(text: str):
    from app.services.voice.pin_auth import authenticate, is_authenticated
    from app.services.voice.personality import (
        thinking_sound, greeting, follow_up, done,
        confused, resuming, get_action_response, wrap_as_friend
    )
    from app.services.command_parser import execute_browser_command
    from app.services.pc_command_parser import execute_pc_command
    from core.emotion import detect_emotion
    from navix_tray import set_tray_state

    lang_config = SUPPORTED_LANGUAGES[USER_PROFILE["preferred_language"]]

    # wake word — PIN check
    set_tray_state("listening")
    if not is_authenticated():
        speak("Please enter your PIN to activate NAVIX")
        set_tray_state("listening")
        success = authenticate()
        if not success:
            speak("Authentication failed. NAVIX locked.")
            set_tray_state("sleeping")
            return

    # activated
    set_tray_state("active")
    speak(greeting())

    last_topic = ""
    last_response = ""

    while True:
        set_tray_state("active")
        await asyncio.sleep(0.2)
        command = listen_once(duration=6)

        if not command or not command.strip():
            speak(confused())
            continue

        command_lower = command.lower().strip()
        logger.info(f"Command: {command}")

        # stop
        if any(w in command_lower for w in [
            "stop", "bye", "goodbye", "exit", "ok bye", "okay bye", "that's all"
        ]):
            set_tray_state("talking")
            speak("Okay Naveen! Talk later. Take care!")
            set_tray_state("sleeping")
            break

        # lock
        if any(w in command_lower for w in ["lock", "lock navix"]):
            from app.services.voice.pin_auth import lock
            lock()
            set_tray_state("talking")
            speak("Locked! Say Naveen to unlock anytime.")
            set_tray_state("sleeping")
            break

        # resume last topic
        if any(w in command_lower for w in ["continue", "go on", "carry on", "you were saying"]):
            if last_response:
                set_tray_state("talking")
                speak(resuming())
                speak(last_response)
                speak(follow_up())
                continue

        # reminder
        import re
        remind_match = re.search(
            r"remind me (?:to )?(.+?) at (\d+)(?::(\d+))?\s*(am|pm)?",
            command_lower
        )
        if remind_match:
            from app.services.reminder import add_reminder
            message  = remind_match.group(1)
            hour     = int(remind_match.group(2))
            minute   = int(remind_match.group(3) or 0)
            ampm     = remind_match.group(4)
            if ampm == "pm" and hour < 12:
                hour += 12
            await add_reminder(message, hour, minute)
            set_tray_state("talking")
            speak(f"Done! Reminding you to {message} at {hour}:{minute:02d}.")
            continue

        # world model commands
        if any(w in command_lower for w in ["my goal is", "add goal", "weekly goal"]):
            from app.services.world_model import set_weekly_goal
            goal_match = re.search(r"(?:my goal is|add goal|weekly goal)\s+(.+)", command_lower)
            if goal_match:
                result = await set_weekly_goal(goal_match.group(1))
                set_tray_state("talking")
                speak(f"Got it! {result}")
                continue

        if any(w in command_lower for w in ["give me an insight", "advise me", "daily insight"]):
            from app.services.world_model import generate_daily_insight
            set_tray_state("talking")
            speak(thinking_sound())
            insight = await generate_daily_insight()
            speak(insight)
            speak(follow_up())
            continue

        if any(w in command_lower for w in ["i feel", "i am feeling", "my mood"]):
            mood_match = re.search(r"(?:i feel|i am feeling|my mood is)\s+(.+)", command_lower)
            if mood_match:
                from app.services.world_model import record_mood
                mood = mood_match.group(1).strip()
                await record_mood(mood)
                set_tray_state("talking")
                emotion = detect_emotion(mood)
                if emotion == "sadness":
                    speak(f"Aw Naveen... I hear you. You're feeling {mood}. I'm here if you need to talk.")
                elif emotion == "joy":
                    speak(f"That's great Naveen! Love to hear you're feeling {mood}!")
                else:
                    speak(f"Got it, noted that you're feeling {mood}.")
                continue

        # crew commands
        if any(w in command_lower for w in [
            "research", "deep dive", "investigate",
            "advise me on", "should i", "help me decide",
            "plan for", "create a plan", "roadmap"
        ]):
            import asyncio as _asyncio
            set_tray_state("talking")
            speak(f"{thinking_sound()} Let me get my team on that. Give me a moment.")
            set_tray_state("active")

            if any(w in command_lower for w in ["advise", "should i", "decide"]):
                from core.crew_agents import get_advisory_crew as crew_fn
            elif any(w in command_lower for w in ["plan", "roadmap", "steps"]):
                from core.crew_agents import get_planning_crew as crew_fn
            else:
                from core.crew_agents import get_research_crew as crew_fn

            try:
                result = await _asyncio.get_event_loop().run_in_executor(
                    None, crew_fn, command
                )
                emotion = detect_emotion(result)
                friendly = wrap_as_friend(result, emotion)
                set_tray_state("talking")
                speak(friendly)
                last_response = friendly
                speak(follow_up())
            except Exception as e:
                logger.error(f"Crew error: {e}")
                speak("Hmm my team ran into a problem. Let me handle it myself.")
                response = await process_command(command)
                speak(wrap_as_friend(response))
            continue

        # PC control
        pc_result = await execute_pc_command(command)
        if pc_result:
            set_tray_state("talking")
            speak(done())
            continue

        # browser and app
        browser_result = await execute_browser_command(command)
        if browser_result:
            set_tray_state("talking")
            speak(get_action_response(command))
            speak(follow_up())
            continue

        # AI agent — thinking sound first
        try:
            emotion = detect_emotion(command)
            set_tray_state("talking")
            speak(thinking_sound())
            set_tray_state("active")
            response = await process_command(command)
            friendly = wrap_as_friend(response, emotion)
            last_topic = command
            last_response = friendly
            set_tray_state("talking")
            speak(friendly)
            speak(follow_up())
        except Exception as e:
            logger.error(f"Agent error: {e}")
            speak("Hmm something went wrong. What else can I help with?")