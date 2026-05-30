import whisper
import sounddevice as sd
import numpy as np
import tempfile
import soundfile as sf
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

# Load whisper model once
_whisper_model = None

def get_whisper_model(size: str = "base"):
    global _whisper_model
    if _whisper_model is None:
        logger.info(f"Loading Whisper model: {size}")
        _whisper_model = whisper.load_model(size)
        logger.info("Whisper model loaded")
    return _whisper_model

def record_audio(duration: int = 5, sample_rate: int = 16000) -> np.ndarray:
    logger.info(f"Recording for {duration} seconds...")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    logger.info("Recording complete")
    return audio.flatten()

def transcribe_audio(audio: np.ndarray, language: str = None) -> str:
    model = get_whisper_model()

    # save to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, 16000)
        tmp_path = f.name

    # detect language or use specified
    lang = language or USER_PROFILE.get("preferred_language", "english")
    whisper_lang = "ta" if lang == "tamil" else "en"

    result = model.transcribe(tmp_path, language=whisper_lang)
    text = result["text"].strip()
    logger.info(f"Transcribed ({lang}): {text}")
    return text

def listen_once(duration: int = 5, language: str = None) -> str:
    audio = record_audio(duration=duration)
    return transcribe_audio(audio, language=language)

def detect_language_from_audio(audio: np.ndarray) -> str:
    model = get_whisper_model()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, 16000)
        tmp_path = f.name
    audio_loaded = whisper.load_audio(tmp_path)
    audio_loaded = whisper.pad_or_trim(audio_loaded)
    mel = whisper.log_mel_spectrogram(audio_loaded).to(model.device)
    _, probs = model.detect_language(mel)
    detected = max(probs, key=probs.get)
    logger.info(f"Detected language: {detected}")
    return detected