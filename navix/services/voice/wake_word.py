"""
wake_word.py — NAVIX wake-word detection

Uses soundcard (Windows WASAPI) for microphone access — same as listener.py —
to avoid PortAudio WDM-KS errors on Windows.
"""
import threading
import numpy as np
from loguru import logger
import time

from navix.services.voice.listener import transcribe_audio, SAMPLE_RATE

_listening = False
_wake_callbacks      = []
_interrupt_callbacks = []
_stop_event          = threading.Event()
_handling            = threading.Event()   # set while handling a command

CHUNK_DURATION = 1.5   # seconds — longer window gives Whisper more context


def add_wake_callback(callback):
    _wake_callbacks.append(callback)

def add_interrupt_callback(callback):
    _interrupt_callbacks.append(callback)


def _check_wake_word(text: str) -> bool:
    import re
    text_lower = text.lower().strip()
    patterns = [
        r"\b(hey|hi|hello)?\s*(naveen|navin|navix)\b",
        r"\bநவீன்\b",
    ]
    return any(re.search(pat, text_lower) for pat in patterns)


INTERRUPT_WORDS = ["stop", "wait", "pause", "hold on", "listen", "hey", "naveen", "quiet"]

def _check_interrupt(text: str) -> bool:
    text_lower = text.lower().strip()
    return any(w in text_lower for w in INTERRUPT_WORDS)


def start_wake_word_listener():
    global _listening
    _listening = True
    _stop_event.clear()
    logger.info("Wake word listener started — say 'Naveen' to activate")

    def listen_loop():
        import soundcard as sc
        chunk_size = int(CHUNK_DURATION * SAMPLE_RATE)

        while not _stop_event.is_set():
            if _handling.is_set():
                time.sleep(0.2)
                continue

            try:
                # Get current best mic each loop (handles USB mic plug/unplug)
                from navix.services.voice.listener import _get_mic
                mic = _get_mic()
                if mic is None:
                    logger.warning("No microphone available — retrying in 5s")
                    time.sleep(5)
                    continue

                with mic.recorder(samplerate=SAMPLE_RATE, channels=1, blocksize=chunk_size) as rec:
                    logger.debug("Wake-word mic open")
                    while not _stop_event.is_set() and not _handling.is_set():
                        chunk = rec.record(numframes=chunk_size)   # (N, 1)
                        audio = chunk[:, 0].astype(np.float32)

                        energy = float(np.sqrt(np.mean(audio ** 2)))
                        if energy < 0.005:
                            continue

                        # Never process audio while NAVIX is outputting speech through speakers
                        from navix.services.voice.speaker import is_speaking, interrupt_speech
                        if is_speaking():
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


def set_handling():
    """Pause wake-word listener — mic handed to command session."""
    _handling.set()
    logger.debug("[wake_word] mic handed to command session")

def clear_handling():
    """Resume wake-word listener — mic returned."""
    _handling.clear()
    logger.debug("[wake_word] mic returned to wake word listener")

def stop_wake_word_listener():
    global _listening
    _listening = False
    _stop_event.set()
    _handling.clear()
    logger.info("Wake word listener stopped")