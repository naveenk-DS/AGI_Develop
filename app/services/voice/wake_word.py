from litellm.litellm_core_utils import streaming_chunk_builder_utils
from app.services.voice.listener import DEVICE_ID, CHANNELS
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

_interrupt_callbacks = []

def add_interrupt_callback(callback):
    _interrupt_callbacks.append(callback)

WAKE_WORDS = [
    "navix", "hey navix", "navi", "hey navi",
    "navik", "nabix", "navicks", "navic",
    "activate", "computer", "start", "hey","mofi"
    # add whatever Whisper hears when you say hey navix
]
ENERGY_THRESHOLD = 0.0005   # lowered: catches quieter speech
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.3  # 300ms chunks for hyper-fast mic yielding
WINDOW_DURATION = 1.5 # 1.5s sliding window for transcription

def add_wake_callback(callback):
    _wake_callbacks.append(callback)

def _check_wake_word(text: str) -> bool:
    text_lower = text.lower().strip()
    WAKE_WORDS = [
        # correct
        "naveen", "hey naveen", "hi naveen",
        # whisper mishears
        "navin", "naven", "navine", "nabean",
        "kevin", "navine", "naveen",
        "navi", "navy", "navey",
        "the bean", "nahveen", "navien",
        "hey", "mofi"
        # tamil accent variations
        "நவீன்", "நவீன்",
    ]
    for word in WAKE_WORDS:
        if word in text_lower:
            return True
    return False

def _calculate_energy(audio: np.ndarray) -> float:
    return float(np.sqrt(np.mean(audio**2)))

INTERRUPT_WORDS = [
    "stop", "wait", "pause", "hold on",
    "listen", "hey", "naveen", "quiet"
]

def _check_interrupt(text: str) -> bool:
    text_lower = text.lower().strip()
    return any(w in text_lower for w in INTERRUPT_WORDS)

def start_wake_word_listener():
    global _listening
    _listening = True
    _stop_event.clear()
    logger.info("Wake word listener started — say 'Naveen' to activate")

    from app.services.voice.listener import DEVICE_ID, CHANNELS
    

    def listen_loop():
        while not _stop_event.is_set():
            if _handling.is_set():
                sd.stop()
                time.sleep(0.2)
                continue
            try:
                channels = CHANNELS
            
                chunk = sd.rec(
                    int(CHUNK_DURATION * SAMPLE_RATE),
                    samplerate=SAMPLE_RATE,
                    channels=channels,
                    dtype="float32",
                    device=DEVICE_ID
                )
                sd.wait()
                audio = chunk.mean(axis=1) if channels > 1 else chunk.flatten()
            
                audio_clipped = np.clip(audio, -1.0, 1.0)
                energy = float(np.sqrt(np.mean(audio_clipped**2)))
                
                if energy < 0.001:
                    continue

                text = transcribe_audio(audio)
                if not text or len(text.strip()) < 2:
                    continue

                logger.debug(f"Heard: {text}")

                from app.services.voice.speaker import is_speaking, interrupt_speech
                if is_speaking() and _check_interrupt(text):
                    interrupt_speech()
                    for cb in _interrupt_callbacks:
                        cb(text)
                    continue

                if _check_wake_word(text):
                    logger.info(f"Wake word: {text}")
                    for cb in _wake_callbacks:
                        cb(text)

            except Exception as e:
                logger.error(f"Wake word error: {e}")
                time.sleep(1)

    thread = threading.Thread(target=listen_loop, daemon=True)
    thread.start()
    return thread

def set_handling():
    """Call when entering a voice command session — pauses the wake word listener."""
    _handling.set()
    logger.debug("[wake_word] mic handed to command session")

def clear_handling():
    """Call when exiting a voice command session — resumes the wake word listener."""
    _handling.clear()
    logger.debug("[wake_word] mic returned to wake word listener")

def stop_wake_word_listener():
    global _listening
    _listening = False
    _stop_event.set()
    _handling.clear()
    logger.info("Wake word listener stopped")