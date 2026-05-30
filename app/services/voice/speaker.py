import httpx
import subprocess
import tempfile
import os
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

async def speak_ollama(text: str):
    logger.info(f"Speaking: {text[:50]}")
    print(f"\n🤖 NAVIX AI: {text}\n")

def speak(text: str, language: str = None):
    lang = language or USER_PROFILE.get("preferred_language", "english")
    logger.info(f"NAVIX AI ({lang}): {text}")
    print(f"\n🤖 NAVIX AI: {text}\n")

    try:
        if os.name == "nt":
            subprocess.run([
                "powershell", "-Command",
                f"Add-Type -AssemblyName System.Speech; "
                f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$s.Speak('{text.replace(chr(39), '')}');"
            ], capture_output=True, timeout=30)
    except Exception as e:
        logger.warning(f"TTS failed, text only: {e}")