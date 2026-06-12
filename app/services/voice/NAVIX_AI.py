import asyncio
import re
import threading
from datetime import datetime
from loguru import logger
from app.services.voice.language_config import USER_PROFILE, SUPPORTED_LANGUAGES
from app.services.voice.speaker import speak, interrupt_speech, is_speaking
from app.services.voice.listener import listen_once
from app.services.voice.wake_word import start_wake_word_listener, add_wake_callback
import httpx

BASE_URL   = "http://127.0.0.1:8001"
SESSION_ID = "navix-main"

async def ask_model(text: str, context: str = "") -> str:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{BASE_URL}/agent/run",
                json={"session_id": SESSION_ID, "message": text}
            )
            if r.status_code == 200:
                return r.json().get("answer", "")
    except Exception as e:
        logger.error(f"Model error: {e}")
    return ""

def get_greeting() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:   return "morning"
    if 12 <= hour < 17:  return "afternoon"
    if 17 <= hour < 21:  return "evening"
    return "night"

async def navix_session():
    from app.services.planner import get_todays_plan, save_daily_plan
    from app.services.reminder import start_reminder_loop
    from navix_tray import set_tray_state

    set_tray_state("sleeping")
    hour     = datetime.now().hour
    period   = get_greeting()
    plan     = await get_todays_plan()

    if plan:
        context = f"Good {period}. User's plan today: {plan}"
    else:
        context = f"Good {period}. No plan set yet."

    # let model generate greeting naturally
    greeting = await ask_model(
        f"Greet Naveen naturally for {period}. If he has a plan say it briefly. Plan: '{plan}'. Keep it 1-2 sentences.",
        context
    )
    if greeting:
        set_tray_state("talking")
        speak(greeting)

    # morning briefing via model
    if 6 <= hour <= 9:
        try:
            from app.services.news_briefing import get_quick_headlines
            headlines = await get_quick_headlines()
            if headlines:
                brief = await ask_model(
                    f"Read these news headlines naturally to Naveen in 2 sentences: {headlines}"
                )
                if brief:
                    set_tray_state("talking")
                    speak(brief)
        except Exception as e:
            logger.warning(f"Briefing error: {e}")

    asyncio.create_task(start_reminder_loop())
    set_tray_state("sleeping")


def on_wake_word(text: str):
    t = threading.Thread(target=_run_conversation, daemon=True)
    t.start()

def _run_conversation():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(handle_wake_word(""))
    finally:
        loop.close()

def start_navix():
    logger.info("Starting NAVIX...")
    add_wake_callback(on_wake_word)
    start_wake_word_listener()
    logger.info("NAVIX ready")


async def handle_wake_word(text: str):
    from app.services.voice.pin_auth import authenticate, is_authenticated
    from navix_tray import set_tray_state

    set_tray_state("listening")

    # PIN
    if not is_authenticated():
        speak_simple("Please enter your PIN")
        success = authenticate()
        if not success:
            speak_simple("Authentication failed.")
            set_tray_state("sleeping")
            return

    # activated — let model say something natural
    activation = await ask_model(
        "Naveen just activated you. Say one short natural response to show you are listening. Max 5 words."
    )
    set_tray_state("talking")
    speak(activation or "Yes?")

    while True:
        set_tray_state("active")
        command = listen_once(duration=30)

        if not command or not command.strip():
            continue

        command_lower = command.lower().strip()
        logger.info(f"Command: {command}")

        # stop
        if any(w in command_lower for w in ["stop", "bye", "goodbye", "exit", "ok bye"]):
            farewell = await ask_model("Naveen said bye. Say a natural short goodbye.")
            set_tray_state("talking")
            speak(farewell or "Bye Naveen!")
            set_tray_state("sleeping")
            break

        # lock
        if any(w in command_lower for w in ["lock", "lock navix"]):
            from app.services.voice.pin_auth import lock
            lock()
            locked_msg = await ask_model("You are being locked. Say a short natural response.")
            set_tray_state("talking")
            speak(locked_msg or "Locked.")
            set_tray_state("sleeping")
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
            confirm = await ask_model(
                f"Confirm reminder set for '{message}' at {hour}:{minute:02d}. One natural sentence."
            )
            set_tray_state("talking")
            speak(confirm or f"Reminder set for {hour}:{minute:02d}")
            continue

        # browser / app / PC commands
        from app.services.command_parser import execute_browser_command
        from app.services.pc_command_parser import execute_pc_command

        pc_result = await execute_pc_command(command)
        if pc_result:
            action_response = await ask_model(
                f"You just did: {pc_result}. Confirm in one natural casual sentence."
            )
            set_tray_state("talking")
            speak(action_response or pc_result)
            continue

        browser_result = await execute_browser_command(command)
        if browser_result:
            action_response = await ask_model(
                f"You just did: {browser_result}. Confirm in one natural casual sentence."
            )
            set_tray_state("talking")
            speak(action_response or browser_result)
            continue

        # everything else — model handles it
        set_tray_state("talking")
        speak_thinking()
        response = await ask_model(command)
        if response:
            speak(response)
        set_tray_state("active")


def speak_simple(text: str):
    speak(text)

def speak_thinking():
    import random
    sounds = ["Hmm...", "Let me think...", "Sure...", "Okay..."]
    speak(random.choice(sounds))