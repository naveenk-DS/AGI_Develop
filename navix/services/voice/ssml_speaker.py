import subprocess
import tempfile
import os
import threading
import random
from loguru import logger
from navix.services.voice.language_config import USER_PROFILE

ENGLISH_VOICE = "en-US-AriaNeural"
TAMIL_VOICE = "ta-IN-PallaviNeural"

_interrupt = threading.Event()
_speaking = False

def interrupt_speech():
    _interrupt.set()

def is_speaking() -> bool:
    return _speaking

def speak_with_ssml(text: str, language: str = None):
    global _speaking
    lang = language or USER_PROFILE.get("preferred_language", "english")
    voice = TAMIL_VOICE if lang == "tamil" else ENGLISH_VOICE

    logger.info(f"NAVIX: {text}")
    print(f"\n🤖 NAVIX: {text}\n")

    _interrupt.clear()
    _speaking = True

    thread = threading.Thread(
        target=_speak_ssml,
        args=(text, voice),
        daemon=True
    )
    thread.start()
    thread.join()
    _speaking = False

def _build_ssml(text: str, voice: str) -> str:
    import re

    # detect emotion markers
    rate = "medium"
    pitch = "medium"

    text_lower = text.lower()
    if any(w in text_lower for w in ["!", "wow", "amazing", "great", "love"]):
        rate = "fast"
        pitch = "high"
    elif any(w in text_lower for w in ["sorry", "sad", "tough", "difficult"]):
        rate = "slow"
        pitch = "low"
    elif any(w in text_lower for w in ["hmm", "let me think", "wait"]):
        rate = "slow"
        pitch = "medium"

    # add natural pauses after punctuation
    text = text.replace("...", '<break time="600ms"/>')
    text = text.replace(". ", '. <break time="300ms"/>')
    text = text.replace("? ", '? <break time="400ms"/>')
    text = text.replace("! ", '! <break time="300ms"/>')
    text = text.replace(", ", ', <break time="150ms"/>')

    # emphasize key words
    text = re.sub(r'\b(important|remember|listen|wait|stop)\b',
                  r'<emphasis level="strong">\1</emphasis>', text, flags=re.IGNORECASE)

    ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
        xmlns:mstts="http://www.w3.org/2001/mstts"
        xml:lang="en-US">
        <voice name="{voice}">
            <mstts:express-as style="friendly">
                <prosody rate="{rate}" pitch="{pitch}">
                    {text}
                </prosody>
            </mstts:express-as>
        </voice>
    </speak>"""

    return ssml

def _speak_ssml(text: str, voice: str):
    try:
        ssml = _build_ssml(text, voice)
        tmp_ssml = tempfile.mktemp(suffix=".xml")
        tmp_mp3  = tempfile.mktemp(suffix=".mp3")

        with open(tmp_ssml, "w", encoding="utf-8") as f:
            f.write(ssml)

        result = subprocess.run([
            "edge-tts",
            "--voice", voice,
            "--file", tmp_ssml,
            "--write-media", tmp_mp3
        ], capture_output=True, timeout=15)

        if result.returncode != 0 or not os.path.exists(tmp_mp3):
            _speak_plain(text, voice)
            return

        ffplay = "C:\\\\Users\\\\Naveen\\\\AGI_Develop\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin\\ffplay.exe"
        proc = subprocess.Popen(
            [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_mp3],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        while proc.poll() is None:
            if _interrupt.is_set():
                proc.terminate()
                break
            import time
            time.sleep(0.1)

        for f in [tmp_ssml, tmp_mp3]:
            try:
                if os.path.exists(f):
                    os.unlink(f)
            except:
                pass

    except Exception as e:
        logger.warning(f"SSML speak failed: {e}")
        _speak_plain(text, voice)

def _speak_plain(text: str, voice: str):
    try:
        tmp = tempfile.mktemp(suffix=".mp3")
        subprocess.run([
            "edge-tts", "--voice", voice,
            "--text", text[:500],
            "--write-media", tmp
        ], capture_output=True, timeout=15)

        if os.path.exists(tmp):
            ffplay = "C:\\\\Users\\\\Naveen\\\\AGI_Develop\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin\\ffplay.exe"
            proc = subprocess.Popen(
                [ffplay, "-nodisp", "-autoexit", "-loglevel", "quiet", tmp],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            proc.wait()
            os.unlink(tmp)
    except Exception as e:
        logger.warning(f"Plain speak failed: {e}")