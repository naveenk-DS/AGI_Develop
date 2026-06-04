import sounddevice as sd
import numpy as np
import tempfile
import soundfile as sf
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

DEVICE_ID = 1
SAMPLE_RATE = 16000

_model = None

def get_model():
    global _model
    if _model is None:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        logger.info(f"Loading Faster-Whisper on {device}...")
        from faster_whisper import WhisperModel
        _model = WhisperModel(
            "medium",        # upgrade from base to medium — much better accuracy
            device=device,
            compute_type=compute
        )
        logger.info(f"Faster-Whisper loaded on {device}")
    return _model

def record_audio(duration: int = 5) -> np.ndarray:
    logger.info(f"Recording for {duration} seconds...")
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=DEVICE_ID
    )
    sd.wait()
    audio = audio.flatten()
    logger.info("Recording complete")
    return audio  # no amplification needed — mic is already loud

def transcribe_audio(audio: np.ndarray, language: str = None) -> str:
    model = get_model()
    lang = language or USER_PROFILE.get("preferred_language", "english")
    whisper_lang = "ta" if lang == "tamil" else "en"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, SAMPLE_RATE)
        tmp_path = f.name

    segments, info = model.transcribe(
        tmp_path,
        language=whisper_lang,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    text = " ".join([s.text for s in segments]).strip()
    logger.info(f"Transcribed ({lang}): {text}")
    return text

def listen_once(duration: int = 5, language: str = None) -> str:
    audio = record_audio(duration=duration)
    return transcribe_audio(audio, language=language)