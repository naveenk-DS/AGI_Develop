import threading
import asyncio
import os
import subprocess
import tempfile
import random
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

ENGLISH_VOICE = "en-US-AriaNeural"
TAMIL_VOICE = "ta-IN-PallaviNeural"

def speak(text: str, language: str = None):
    lang = language or USER_PROFILE.get("preferred_language", "english")
    logger.info(f"NAVIX AI ({lang}): {text}")
    print(f"\n🤖 NAVIX AI: {text}\n")
    thread = threading.Thread(target=_speak_edge, args=(text, lang), daemon=True)
    thread.start()
    thread.join()

def _speak_edge(text: str, lang: str = "english"):
    try:
        voice = TAMIL_VOICE if lang == "tamil" else ENGLISH_VOICE
        clean = text.replace('"', "'").replace('\n', ' ').replace('*', '').strip()
        if not clean:
            return

        tmp = tempfile.mktemp(suffix=".mp3")

        # generate with edge-tts
        result = subprocess.run([
            "edge-tts",
            "--voice", voice,
            "--text", clean,
            "--write-media", tmp
        ], capture_output=True, timeout=15)

        if result.returncode != 0 or not os.path.exists(tmp):
            _speak_pyttsx3(text)
            return

        # play with ffplay (from ffmpeg)
        subprocess.run([
            "F:\\naveen\\AGI_Start\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin\\ffplay.exe",
            "-nodisp", "-autoexit", "-loglevel", "quiet", tmp
        ], timeout=30)

        if os.path.exists(tmp):
            os.unlink(tmp)

    except Exception as e:
        logger.warning(f"Edge TTS failed: {e}")
        _speak_pyttsx3(text)

def _speak_pyttsx3(text: str):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        female = None
        for v in voices:
            if any(w in v.name.lower() for w in ["female", "zira", "hazel", "aria"]):
                female = v.id
                break
        if female:
            engine.setProperty("voice", female)
        elif len(voices) > 1:
            engine.setProperty("voice", voices[1].id)
        engine.setProperty("rate", 160)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        logger.warning(f"pyttsx3 failed: {e}")

async def speak_async(text: str, language: str = None):
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, speak, text, language)