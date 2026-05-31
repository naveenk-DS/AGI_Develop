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
                "message": text
            })
            if r.status_code == 200:
                return r.json()["answer"]
            return "Sorry I could not process that"
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return "Sorry there was an error"

async def navix_session():
    global _active
    _active = True

    # greet
    greeting = get_greeting()
    speak(f"{greeting}. What is your plan today?")

    # listen for response
    await asyncio.sleep(0.5)
    plan = listen_once(duration=8)
    if plan:
        speak(f"Got it. I will help you with that.")
        response = await process_command(f"Remember my plan for today: {plan}")
        logger.info(f"Plan stored: {plan}")

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
    speak("NAVIX online. Say Hey NAVIX to activate.")
    add_wake_callback(on_wake_word)
    start_wake_word_listener()
    logger.info("NAVIX ready — listening for wake word")


async def handle_wake_word(text: str):
    from app.services.voice.pin_auth import authenticate, is_authenticated
    from app.services.voice.speaker import speak

    lang_config = SUPPORTED_LANGUAGES[USER_PROFILE["preferred_language"]]

    # check if already authenticated
    if not is_authenticated():
        speak("Please enter your PIN to activate NAVIX")
        success = authenticate()
        if not success:
            speak("Authentication failed. NAVIX locked.")
            return
        speak(lang_config["wake_response"])
    else:
        speak(lang_config["wake_response"])

    await asyncio.sleep(0.3)
    command = listen_once(duration=7)

    if not command:
        speak("I did not hear anything. Please try again.")
        return

    logger.info(f"Command received: {command}")

     # lock command
    if any(w in command.lower() for w in ["lock", "lock navix", "goodbye", "bye navix"]):
        from app.services.voice.pin_auth import lock
        lock()
        speak("NAVIX locked. Say Hey Navix to unlock.")
        return

    # check if browser command
    from app.services.command_parser import execute_browser_command
    browser_result = await execute_browser_command(command)

    if browser_result:
        speak(browser_result)
        return

    # send to AI agent
    response = await process_command(command)
    speak(response)