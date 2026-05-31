import sys
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
    sys.stdout.buffer.write(f"\n🤖 NAVIX AI: {text}\n\n".encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    thread = threading.Thread(target=_speak, args=(text,), daemon=True)
    thread.start()
    thread.join()

def _speak(text: str):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        
        # find female voice
        female_voice = None
        for voice in voices:
            if any(w in voice.name.lower() for w in ["female", "zira", "hazel", "susan", "linda", "woman"]):
                female_voice = voice.id
                break
        
        if female_voice:
            engine.setProperty("voice", female_voice)
        elif len(voices) > 1:
            engine.setProperty("voice", voices[1].id)  # usually female on Windows
            
        engine.setProperty("rate", 160)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        logger.warning(f"TTS error: {e}")


