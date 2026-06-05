import threading
import subprocess
import tempfile
import os
import time
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

ENGLISH_VOICE = "en-US-AriaNeural"
TAMIL_VOICE = "ta-IN-PallaviNeural"

# Global interrupt flag
_interrupt = threading.Event()
_speaking = False
_speak_thread = None

def interrupt_speech():
    global _interrupt
    _interrupt.set()
    logger.info("Speech interrupted")

def is_speaking() -> bool:
    return _speaking

def speak(text: str, language: str = None):
    global _speaking, _speak_thread, _interrupt
    lang = language or USER_PROFILE.get("preferred_language", "english")
    logger.info(f"NAVIX AI ({lang}): {text}")
    print(f"\n🤖 NAVIX AI: {text}\n")

    _interrupt.clear()
    _speaking = True
    _speak_thread = threading.Thread(
        target=_speak_edge, args=(text, lang), daemon=True
    )
    _speak_thread.start()
    _speak_thread.join()
    _speaking = False

def _speak_edge(text: str, lang: str = "english"):
    global _interrupt
    try:
        voice = TAMIL_VOICE if lang == "tamil" else ENGLISH_VOICE
        clean = text.replace('"', "'").replace('\n', ' ').replace('*', '').strip()
        if not clean:
            return

        tmp = tempfile.mktemp(suffix=".mp3")
        result = subprocess.run([
            "edge-tts", "--voice", voice,
            "--text", clean, "--write-media", tmp
        ], capture_output=True, timeout=15)

        if result.returncode != 0 or not os.path.exists(tmp):
            _speak_pyttsx3(text)
            return

        # play with ffplay — kill process on interrupt
        ffplay = os.path.join(
            "F:\\naveen\\AGI_Start\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin",
            "ffplay.exe"
        )
        proc = subprocess.Popen(
            [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", tmp],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # check for interrupt every 100ms
        while proc.poll() is None:
            if _interrupt.is_set():
                proc.terminate()
                logger.info("Audio playback stopped")
                break
            time.sleep(0.1)

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
            if any(w in v.name.lower() for w in ["female", "zira", "hazel"]):
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
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, speak, text, language)