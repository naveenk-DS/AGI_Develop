import threading
import sounddevice as sd
import numpy as np
from loguru import logger
import time

# Simple energy-based wake word detection
# No API key needed — detects loud sound then listens for "jarvis"
from app.services.voice.listener import transcribe_audio

_listening = False
_wake_callbacks = []
_stop_event = threading.Event()
_handling = threading.Event()  # set while a wake-word command is being handled

WAKE_WORDS = [
    "navix", "hey navix", "navi", "hey navi",
    "navik", "nabix", "navicks", "navic",
    "activate", "computer", "start",
    # add whatever Whisper hears when you say hey navix
]
ENERGY_THRESHOLD = 0.02   # lowered: catches quieter speech
SAMPLE_RATE = 16000
CHUNK_DURATION = 1.5  # seconds per chunk — long enough for "Hey Navix"

def add_wake_callback(callback):
    _wake_callbacks.append(callback)

def _check_wake_word(text: str) -> bool:
    text_lower = text.lower().strip()
    WAKE_WORDS = [
        # Original
        "navix", "hey navix", "navi", "hey navi",
        # Your name as wake word
        "naveen", "hey naveen", "hi naveen",
        # Common misrecognitions of Naveen
        "navin", "naven", "navine", "kevin",
        # Tamil
        "நவீன்", "ஜார்விஸ்"
    ]
    for word in WAKE_WORDS:
        if word in text_lower:
            return True
    return False

def _calculate_energy(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(audio**2)))

def start_wake_word_listener():
    global _listening
    _listening = True
    _stop_event.clear()
    logger.info("Wake word listener started — say 'Naveen' to activate")

    def listen_loop():
        while not _stop_event.is_set():
            try:
                chunk = sd.rec(
                    int(CHUNK_DURATION * SAMPLE_RATE),
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="float32",
                    device=1
                )
                sd.wait()
                audio = chunk.flatten()

                # only transcribe if sound is loud enough
                energy = float(np.sqrt(np.mean(audio**2)))
                if energy < 0.001:
                    continue

                text = transcribe_audio(audio)
                if not text or len(text.strip()) < 2:
                    continue

                logger.debug(f"Heard: {text}")

                if _check_wake_word(text):
                    logger.info(f"Wake word detected: {text}")
                    for cb in _wake_callbacks:
                        cb(text)

            except Exception as e:
                logger.error(f"Wake word error: {e}")
                time.sleep(1)
    thread = threading.Thread(target=listen_loop, daemon=True)
    thread.start()
    return thread

def stop_wake_word_listener():
    global _listening
    _listening = False
    _stop_event.set()
    _handling.clear()
    logger.info("Wake word listener stopped")