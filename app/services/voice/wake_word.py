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
    # Primary wake words
    "naveen", "hey naveen",
    "navix", "hey navix", "navix ai", "hey navix ai",
    "navi", "hey navi",
    "ஜார்விஸ்", "நவிக்ஸ்"
]
ENERGY_THRESHOLD = 0.02   # lowered: catches quieter speech
SAMPLE_RATE = 16000
CHUNK_DURATION = 1.5  # seconds per chunk — long enough for "Hey Navix"

def add_wake_callback(callback):
    _wake_callbacks.append(callback)

def _check_wake_word(text: str) -> bool:
    text_lower = text.lower().strip()
    WAKE_WORDS = [
        "jarvis", "hey jarvis",
        "navix", "hey navix", "navix ai",
        "navi", "hey navi",
        "navis", "nabix", "navirus",  # common misrecognitions
        "ஜார்விஸ்", "நவிக்ஸ்"
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
    logger.info("Wake word listener started — say 'Hey NAVIX AI'")

    def listen_loop():
        while not _stop_event.is_set():
            try:
                chunk = sd.rec(
                    int(CHUNK_DURATION * SAMPLE_RATE),
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="float32"
                )
                sd.wait()
                audio = chunk.flatten()

                # always transcribe — no energy gate
                text = transcribe_audio(audio)
                if text and text.strip():
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