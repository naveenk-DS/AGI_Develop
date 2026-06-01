import asyncio
from datetime import datetime
from loguru import logger
from app.services.voice.language_config import USER_PROFILE, SUPPORTED_LANGUAGES
from app.services.voice.speaker import speak
from app.services.voice.listener import listen_once
from app.services.voice.wake_word import start_wake_word_listener, add_wake_callback
import httpx

BASE_URL = "http://127.0.0.1:8001"
SESSION_ID = "navix-main"
_active = False

def get_greeting() -> str:
    hour = datetime.now().hour
    lang = USER_PROFILE["preferred_language"]
    lang_config = SUPPORTED_LANGUAGES[lang]

    if 5 <= hour < 12:
        return lang_config["greeting_morning"]
    elif 12 <= hour < 17:
        return lang_config["greeting_afternoon"]
    elif 17 <= hour < 21:
        return lang_config["greeting_evening"]
    else:
        return lang_config["greeting_night"]

async def process_command(text: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{BASE_URL}/agent/run", json={
                "session_id": SESSION_ID,
                "message": text,
                "system": (
                    "You are NAVIX, a friendly personal AI assistant like Google Assistant or Alexa. "
                    "Your user's name is Naveen. "
                    "Keep responses SHORT — 1 to 3 sentences maximum. "
                    "Be natural, warm and conversational. "
                    "Never use bullet points or numbered lists in spoken responses. "
                    "Speak like a helpful friend, not a formal assistant. "
                    "If explaining something, keep it simple and brief."
                )
            })
            if r.status_code == 200:
                return r.json()["answer"]
            return "Sorry, I could not process that"
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return "Sorry, something went wrong"

async def navix_session():
    from app.services.planner import save_daily_plan, get_todays_plan
    from app.services.reminder import start_reminder_loop
    import asyncio

    greeting = get_greeting()
    hour = datetime.now().hour

    # check if plan already exists today
    existing_plan = await get_todays_plan()

    if existing_plan:
        speak(f"{greeting}. Welcome back. Your plan today is: {existing_plan}")
    else:
        speak(f"{greeting}. What is your plan for today?")
        await asyncio.sleep(0.5)
        plan = listen_once(duration=8)
        if plan and plan.strip():
            await save_daily_plan(plan)
            speak(f"Got it. I have saved your plan. I will help you stay on track.")
        else:
            speak(f"{greeting}. No plan recorded. Say Hey Navix anytime to start.")

    # evening check-in
    if 18 <= hour <= 21:
        speak("Good evening. How did your day go? What did you complete today?")
        await asyncio.sleep(0.5)
        completed = listen_once(duration=8)
        if completed and completed.strip():
            from app.services.planner import save_completed
            await save_completed(completed)
            speak("Great. I have saved your progress for today.")

    # start reminder loop in background
    asyncio.create_task(start_reminder_loop())

def on_wake_word(text: str):
    """Called from the wake word listener thread. Run command handler in its own thread."""
    import threading
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(handle_wake_word(text))
        finally:
            loop.close()
    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join()  # wait so _handling flag stays set until done

def start_navix():
    logger.info("Starting NAVIX...")
    speak("NAVIX online. Say Naveen to activate.")
    add_wake_callback(on_wake_word)
    start_wake_word_listener()
    logger.info("NAVIX ready — listening for wake word")


async def handle_wake_word(text: str):
    from app.services.voice.pin_auth import authenticate, is_authenticated
    from app.services.voice.speaker import speak
    from app.services.command_parser import execute_browser_command

    import random

    LISTENING_PHRASES = [
        "Mmm?",
        "Yes?",
        "Tell me.",
        "Go ahead.",
        "I'm here.",
        "What's up?",
    ]

    FOLLOWUP_PHRASES = [
        "What else can I do for you?",
        "Anything else?",
        "What's next?",
        "Need anything else?",
        "I'm listening.",
        "What else?",
    ]

    DONE_PHRASES = [
        "Done! What else?",
        "Got it. Anything else?",
        "Sure! Need anything more?",
        "Alright! What's next?",
    ]

    lang_config = SUPPORTED_LANGUAGES[USER_PROFILE["preferred_language"]]

    # PIN check
    if not is_authenticated():
        speak("Please enter your PIN to activate NAVIX")
        success = authenticate()
        if not success:
            speak("Authentication failed. NAVIX locked.")
            return
        speak(lang_config["wake_response"])
    else:
        speak(lang_config["wake_response"])

    # conversation loop
    while True:
        await asyncio.sleep(0.2)
        command = listen_once(duration=6)

        if not command or not command.strip():
            speak(random.choice(LISTENING_PHRASES))
            continue

        command_lower = command.lower().strip()
        logger.info(f"Command received: {command}")

        # stop conversation
        if any(w in command_lower for w in [
            "stop", "bye", "goodbye", "that's all",
            "exit", "close navix", "thank you stop",
            "ok bye", "okay bye"
        ]):
            speak("Okay Naveen. I am always here when you need me. Goodbye.")
            break

        # lock
        if any(w in command_lower for w in ["lock", "lock navix"]):
            from app.services.voice.pin_auth import lock
            lock()
            speak("NAVIX locked. Say Naveen to unlock anytime.")
            break

        # reminder
        import re
        remind_match = re.search(
            r"remind me (?:to )?(.+?) at (\d+)(?::(\d+))?\s*(am|pm)?",
            command_lower
        )
        if remind_match:
            from app.services.reminder import add_reminder
            message = remind_match.group(1)
            hour = int(remind_match.group(2))
            minute = int(remind_match.group(3) or 0)
            ampm = remind_match.group(4)
            if ampm == "pm" and hour < 12:
                hour += 12
            await add_reminder(message, hour, minute)
            speak(f"Done. I will remind you to {message} at {hour}:{minute:02d}. Anything else?")
            continue

        # browser and app commands
        browser_result = await execute_browser_command(command)
        if browser_result:
            speak(browser_result)
            speak(random.choice(DONE_PHRASES))
            continue

        # AI agent for questions and conversation
        try:
            response = await process_command(command)
            speak(response)
            speak(random.choice(FOLLOWUP_PHRASES))
        except Exception as e:
            logger.error(f"Agent error: {e}")
            speak("Sorry I could not do that. What else can I help with?")