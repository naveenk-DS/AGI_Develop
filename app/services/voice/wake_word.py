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

WAKE_WORDS = ["navix", "hey navix", "நவிக்ஸ்", "நவிக்ஸ் AI"]
ENERGY_THRESHOLD = 0.02
SAMPLE_RATE = 16000
CHUNK_DURATION = 1  # seconds per chunk

def add_wake_callback(callback):
    _wake_callbacks.append(callback)

def _check_wake_word(text: str) -> bool:
    text_lower = text.lower().strip()
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
                # record short chunk
                chunk = sd.rec(
                    int(CHUNK_DURATION * SAMPLE_RATE),
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="float32"
                )
                sd.wait()
                audio = chunk.flatten()

                # check energy — only transcribe if sound detected
                energy = _calculate_energy(audio)
                if energy > ENERGY_THRESHOLD:
                    text = transcribe_audio(audio)
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
    logger.info("Wake word listener stopped")