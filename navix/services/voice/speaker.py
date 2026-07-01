"""
speaker.py — NAVIX Text-to-Speech
Priority: Kokoro (GPU, offline) → Edge TTS (online) → pyttsx3 (last resort)
"""
import threading
import subprocess
import tempfile
import os
import time
import numpy as np
import sounddevice as sd
import soundfile as sf
from loguru import logger
from navix.services.voice.language_config import USER_PROFILE

# ── Kokoro config ──────────────────────────────────────────────────────────────
KOKORO_VOICE   = "af_heart"   # warm, natural female — best for a friendly AI companion
KOKORO_SPEED   = 1.05         # slightly faster than default — natural speaking pace
SAMPLE_RATE_KO = 24000        # Kokoro outputs at 24kHz

# ── Edge TTS fallback config ───────────────────────────────────────────────────
ENGLISH_VOICE  = "en-US-AriaNeural"
TAMIL_VOICE    = "ta-IN-PallaviNeural"
FFPLAY         = "F:\\naveen\\AGI_Start\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin\\ffplay.exe"

_interrupt  = threading.Event()
_speaking   = False
_ko_pipe    = None   # lazy-loaded Kokoro pipeline


def interrupt_speech():
    _interrupt.set()
    logger.info("Speech interrupted")


def is_speaking() -> bool:
    return _speaking


# ── Kokoro pipeline (loaded once, reused) ─────────────────────────────────────
def _get_kokoro():
    global _ko_pipe
    if _ko_pipe is None:
        try:
            from kokoro import KPipeline
            _ko_pipe = KPipeline(lang_code="a")   # 'a' = American English
            logger.info("Kokoro TTS loaded")
        except Exception as e:
            logger.warning(f"Kokoro load failed: {e}")
    return _ko_pipe


# ── Main speak function ────────────────────────────────────────────────────────
def speak(text: str, language: str = None):
    global _speaking
    lang = language or USER_PROFILE.get("preferred_language", "english")

    # Clean text for TTS
    clean = _clean(text)
    if not clean:
        return

    logger.info(f"NAVIX ({lang}): {text}")
    print(f"\n[NAVIX]: {text}\n")

    _interrupt.clear()
    _speaking = True

    # (Removed sd.stop() here as it causes PortAudio segfaults when running concurrently with wake_word sd.rec)

    try:
        if lang != "tamil":
            # Try Kokoro first (offline, GPU)
            success = _speak_kokoro(clean)
            if success:
                return
        # Tamil or Kokoro failed → Edge TTS
        _speak_edge(clean, lang)
    finally:
        # Let audio fully finish and clear the device buffer before mic reopens
        time.sleep(0.3)
        _speaking = False


def _clean(text: str) -> str:
    """Strip markdown/quotes for clean TTS output."""
    import re
    text = text.strip().strip('"').strip("'")
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+\s*', '', text)
    text = text.replace('\n', ' ').strip()
    return text


# ── Tier 1: Kokoro (offline, GPU) ─────────────────────────────────────────────
def _speak_kokoro(text: str) -> bool:
    try:
        import sounddevice as sd
        sd.stop()
        
        pipeline = _get_kokoro()
        for _, _, audio in pipeline(text, voice=KOKORO_VOICE, speed=KOKORO_SPEED):
            if _interrupt.is_set():
                return True
            # use default output device
            sd.play(audio, samplerate=24000)
            sd.wait()
        return True
    except Exception as e:
        logger.warning(f"Kokoro TTS failed: {e}")
        return False

# ── Tier 2: Edge TTS (online, high quality) ───────────────────────────────────
def _speak_edge(text: str, lang: str = "english"):
    voice = TAMIL_VOICE if lang == "tamil" else ENGLISH_VOICE
    try:
        tmp = tempfile.mktemp(suffix=".mp3")
        result = subprocess.run(
            ["edge-tts", "--voice", voice, "--text", text, "--write-media", tmp],
            capture_output=True, timeout=15
        )
        if result.returncode != 0 or not os.path.exists(tmp):
            _speak_pyttsx3(text)
            return

        proc = subprocess.Popen(
            [FFPLAY, "-nodisp", "-autoexit", "-loglevel", "quiet", tmp],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        while proc.poll() is None:
            if _interrupt.is_set():
                proc.terminate()
                break
            time.sleep(0.1)

        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass

    except Exception as e:
        logger.warning(f"Edge TTS failed: {e}")
        _speak_pyttsx3(text)


# ── Tier 3: pyttsx3 (offline, robotic — last resort) ─────────────────────────
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


# ── Async wrapper ──────────────────────────────────────────────────────────────
async def speak_async(text: str, language: str = None):
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, speak, text, language)