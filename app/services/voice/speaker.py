import threading
import pyttsx3
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

# initialize once
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 170)
        _engine.setProperty("volume", 1.0)
    return _engine

def speak(text: str, language: str = None):
    lang = language or USER_PROFILE.get("preferred_language", "english")
    logger.info(f"NAVIX AI ({lang}): {text}")
    print(f"\n🤖 NAVIX AI: {text}\n")
    thread = threading.Thread(target=_speak, args=(text,), daemon=True)
    thread.start()
    thread.join()

def _speak(text: str):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 170)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        logger.warning(f"TTS error: {e}")

async def speak_async(text: str, language: str = None):
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, speak, text, language)