import threading
import subprocess
import tempfile
import os
import time
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

ENGLISH_VOICE = "en-US-AriaNeural"
TAMIL_VOICE   = "ta-IN-PallaviNeural"

_interrupt = threading.Event()
_speaking  = False

def interrupt_speech():
    _interrupt.set()
    logger.info("Speech interrupted")

def is_speaking() -> bool:
    return _speaking

def speak(text: str, language: str = None):
    global _speaking
    lang  = language or USER_PROFILE.get("preferred_language", "english")
    voice = TAMIL_VOICE if lang == "tamil" else ENGLISH_VOICE

    logger.info(f"NAVIX ({lang}): {text}")
    print(f"\n🤖 NAVIX: {text}\n")

    _interrupt.clear()
    _speaking = True
    t = threading.Thread(target=_speak_edge, args=(text, voice), daemon=True)
    t.start()
    t.join()
    _speaking = False

def _speak_edge(text: str, voice: str):
    try:
        clean = text.replace('"', "'").replace('\n', ' ').replace('*', '').strip()
        if not clean:
            return

        tmp = tempfile.mktemp(suffix=".mp3")
        result = subprocess.run([
            "edge-tts", "--voice", voice,
            "--text", clean,
            "--write-media", tmp
        ], capture_output=True, timeout=15)

        if result.returncode != 0 or not os.path.exists(tmp):
            _speak_pyttsx3(text)
            return

        ffplay = "F:\\naveen\\AGI_Start\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin\\ffplay.exe"
        proc = subprocess.Popen(
            [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", tmp],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        while proc.poll() is None:
            if _interrupt.is_set():
                proc.terminate()
                logger.info("Audio stopped")
                break
            time.sleep(0.1)

        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except:
            pass

    except Exception as e:
        logger.warning(f"Edge TTS failed: {e}")
        _speak_pyttsx3(text)

def _speak_pyttsx3(text: str):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        for v in voices:
            if any(w in v.name.lower() for w in ["zira", "hazel", "female"]):
                engine.setProperty("voice", v.id)
                break
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