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

    # ── tray: sleeping while greeting plays ──────────────────────────────────
    set_tray_state("sleeping")

    greeting = get_greeting()
    hour = datetime.now().hour
    existing_plan = await get_todays_plan()

    if existing_plan:
        # ── tray: talking while NAVIX speaks ─────────────────────────────────
        set_tray_state("talking")
        speak(f"{greeting}. Welcome back. Your plan today is: {existing_plan}")
    else:
        set_tray_state("talking")
        speak(f"{greeting}. What is your plan for today?")
        add_chat_message("NAVIX", f"{greeting}. What is your plan for today?")
        # ── tray: active while recording your answer ──────────────────────────
        set_tray_state("listening")
        await asyncio.sleep(0.5)
        plan = listen_once()           # VAD — stops when you stop speaking
        if plan and plan.strip():
            add_chat_message("You", plan)
            await save_daily_plan(plan)
            set_tray_state("talking")
            speak("Got it. I have saved your plan. I will help you stay on track.")
            add_chat_message("NAVIX", "Got it. I have saved your plan. I will help you stay on track.")
        else:
            set_tray_state("talking")
            speak(f"{greeting}. No plan recorded. Say Naveen anytime to start.")
            add_chat_message("NAVIX", f"{greeting}. No plan recorded. Say Naveen anytime to start.")

    # ── auto morning briefing between 6 AM and 9 AM ──────────────────────────
    if 6 <= hour <= 9:
        from app.services.news_briefing import build_morning_briefing
        try:
            briefing = await build_morning_briefing()
            set_tray_state("talking")
            speak(briefing)
            add_chat_message("NAVIX", briefing)
        except Exception as e:
            logger.warning(f"Briefing error: {e}")

    # ── daily insight — once per day between 6 AM and 10 AM ──────────────────
    if 6 <= hour <= 10:
        try:
            from app.services.world_model import generate_daily_insight
            insight = await generate_daily_insight()
            set_tray_state("talking")
            speak(f"Here is your daily insight Naveen. {insight}")
            add_chat_message("NAVIX", f"Here is your daily insight Naveen. {insight}")
        except Exception as e:
            logger.warning(f"Insight error: {e}")

    if 18 <= hour <= 21:
        set_tray_state("talking")
        speak("Good evening. How did your day go? What did you complete today?")
        add_chat_message("NAVIX", "Good evening. How did your day go? What did you complete today?")
        set_tray_state("listening")
        await asyncio.sleep(0.5)
        completed = listen_once()      # VAD
        if completed and completed.strip():
            add_chat_message("You", completed)
            from app.services.planner import save_completed
            await save_completed(completed)
            set_tray_state("talking")
            speak("Great. I have saved your progress for today.")
            add_chat_message("NAVIX", "Great. I have saved your progress for today.")

    asyncio.create_task(start_reminder_loop())

    # ── tray: back to sleeping — waiting for wake word ────────────────────────
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
    from app.services.command_parser import execute_browser_command
    from app.services.pc_command_parser import execute_pc_command

    lang_config = SUPPORTED_LANGUAGES[USER_PROFILE["preferred_language"]]

    # ── WAKE WORD FIRED — tray glows purple ──────────────────────────────────
    set_tray_state("listening")

    if not is_authenticated():
        set_tray_state("talking")
        speak("Please enter your PIN to activate NAVIX")
        set_tray_state("listening")               # ← waiting for PIN input
        success = authenticate()
        if not success:
            set_tray_state("talking")
            speak("Authentication failed. NAVIX locked.")
            set_tray_state("sleeping")            # ← back to sleep on fail
            return
    
    # ── PIN PASSED — tray goes green ─────────────────────────────────────────
    set_tray_state("active")
    set_tray_state("talking")
    speak(lang_config["wake_response"])

    # ── CONVERSATION LOOP ─────────────────────────────────────────────────────
    while True:
        set_tray_state("listening")               # purple: listening
        await asyncio.sleep(0.2)
        command = listen_once()                   # VAD — no fixed duration

        if not command or not command.strip():
            set_tray_state("talking")
            phrase = random.choice(LISTENING_PHRASES)
            speak(phrase)
            add_chat_message("NAVIX", phrase)
            continue

        add_chat_message("You", command)

        command_lower = command.lower().strip()
        logger.info(f"Command received: {command}")

        # stop
        if any(w in command_lower for w in [
            "stop","bye","goodbye","that's all",
            "exit","close navix","ok bye","okay bye"
        ]):
            set_tray_state("talking")
            speak("Okay Naveen. I am always here when you need me. Goodbye.")
            set_tray_state("sleeping")            # ← goodbye → sleep
            break

        # lock
        if any(w in command_lower for w in ["lock","lock navix"]):
            from app.services.voice.pin_auth import lock
            lock()
            set_tray_state("talking")
            speak("NAVIX locked. Say Naveen to unlock anytime.")
            set_tray_state("sleeping")            # ← locked → sleep
            break

        # reminder
        remind_match = re.search(
            r"remind me (?:to )?(.+?) at (\d+)(?::(\d+))?\s*(am|pm)?",
            command_lower
        )
        if remind_match:
            from app.services.reminder import add_reminder
            message = remind_match.group(1)
            hour    = int(remind_match.group(2))
            minute  = int(remind_match.group(3) or 0)
            ampm    = remind_match.group(4)
            if ampm == "pm" and hour < 12:
                hour += 12
            await add_reminder(message, hour, minute)
            reply = f"Done. I will remind you to {message} at {hour}:{minute:02d}. Anything else?"
            set_tray_state("talking")
            speak(reply)
            add_chat_message("NAVIX", reply)
            continue

        # PC control
        pc_result = await execute_pc_command(command)
        if pc_result:
            set_tray_state("talking")
            speak(random.choice(DONE_PHRASES))
            continue

        # world model commands
        if any(w in command_lower for w in ["my goal is", "add goal", "weekly goal"]):
            from app.services.world_model import set_weekly_goal
            goal_match = re.search(r"(?:my goal is|add goal|weekly goal)\s+(.+)", command_lower)
            if goal_match:
                result = await set_weekly_goal(goal_match.group(1))
                set_tray_state("talking")
                speak(f"Got it. {result}")
                continue

        if any(w in command_lower for w in ["i completed", "i finished", "mark done"]):
            from app.services.world_model import complete_goal
            goal_match = re.search(r"(?:i completed|i finished|mark done)\s+(.+)", command_lower)
            if goal_match:
                result = await complete_goal(goal_match.group(1))
                set_tray_state("talking")
                speak(f"Great work Naveen. {result}")
                continue

        if any(w in command_lower for w in ["give me an insight", "what should i focus", "daily insight", "advise me"]):
            from app.services.world_model import generate_daily_insight
            insight = await generate_daily_insight()
            set_tray_state("talking")
            speak(insight)
            continue

        if any(w in command_lower for w in ["i feel", "i am feeling", "my mood"]):
            mood_match = re.search(r"(?:i feel|i am feeling|my mood is)\s+(.+)", command_lower)
            if mood_match:
                from app.services.world_model import record_mood
                mood = mood_match.group(1).strip()
                await record_mood(mood)
                set_tray_state("talking")
                speak(f"Got it Naveen. I have noted that you are feeling {mood}.")
                continue

        # browser / app commands
        browser_result = await execute_browser_command(command)
        if browser_result:
            set_tray_state("talking")
            speak(browser_result)
            speak(random.choice(DONE_PHRASES))
            continue

        # AI agent
        try:
            set_tray_state("active")              # purple: thinking
            response = await process_command(command)
            followup = random.choice(FOLLOWUP_PHRASES)
            set_tray_state("talking")             # teal: speaking
            speak(response)
            add_chat_message("NAVIX", response)
            speak(followup)
        except Exception as e:
            logger.error(f"Agent error: {e}")
            err_msg = "Sorry I could not do that. What else can I help with?"
            set_tray_state("talking")
            speak(err_msg)
            add_chat_message("NAVIX", err_msg)