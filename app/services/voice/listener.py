import sounddevice as sd
import numpy as np
import tempfile
import soundfile as sf
from pathlib import Path
from datetime import datetime
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

DEVICE_ID = 6
SAMPLE_RATE = 16000
CHANNELS = 1

# Voice data collection folder
VOICE_DATA_DIR = Path("F:/naveen/AGI_Start/data/voice_samples")
VOICE_DATA_DIR.mkdir(parents=True, exist_ok=True)

_model = None

def get_model():
    global _model
    if _model is None:
        import torch
        logger.info("Loading Whisper large-v3-turbo on CUDA...")
        from faster_whisper import WhisperModel
        _model = WhisperModel(
            "large-v3-turbo",
            device="cuda",
            compute_type="float16"
        )
        logger.info("Whisper large-v3-turbo loaded on CUDA")
    return _model

def record_audio(duration: int = 5) -> np.ndarray:
    logger.info(f"Listening — speak now...")
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        device=DEVICE_ID
    )
    sd.wait()
    audio = audio.flatten()
    max_val = np.max(np.abs(audio))
    if max_val > 0.001:
        audio = audio / max_val * 0.9
    return audio

def save_voice_sample(audio: np.ndarray, transcription: str):
    """Save audio + transcription for future fine-tuning."""
    try:
        # skip if transcription too short or empty
        if not transcription or len(transcription.strip()) < 3:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_path = VOICE_DATA_DIR / f"{timestamp}.wav"
        text_path  = VOICE_DATA_DIR / f"{timestamp}.txt"
        
        sf.write(str(audio_path), audio, SAMPLE_RATE)
        text_path.write_text(transcription.strip(), encoding="utf-8")
        
        logger.debug(f"Voice sample saved: {timestamp}")
    except Exception as e:
        logger.warning(f"Could not save voice sample: {e}")

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
        vad_parameters=dict(min_silence_duration_ms=300)
    )

    text = " ".join([s.text for s in segments]).strip()
    logger.info(f"Transcribed: {text}")

    # ── Auto save in background ──────────────────────────────────────────────
    import threading
    threading.Thread(
        target=save_voice_sample,
        args=(audio.copy(), text),
        daemon=True
    ).start()

    return text

def listen_once(duration: int = 30, language: str = None) -> str:
    audio = record_until_silence(
        min_duration=1,
        max_duration=duration,
        silence_duration=1.2
    )
    if audio is None or len(audio) == 0:
        return ""
    return transcribe_audio(audio, language=language)

def record_until_silence(
    min_duration: int = 1,
    max_duration: int = 30,
    silence_threshold: float = 0.008,
    silence_duration: float = 1.5
) -> np.ndarray:
    chunk_size = int(0.3 * SAMPLE_RATE)
    all_audio = []
    silent_chunks = 0
    speaking_started = False
    total_chunks = 0
    max_chunks = int(max_duration / 0.3)
    silence_chunks_needed = int(silence_duration / 0.3)
    min_chunks = int(min_duration / 0.3)
    max_silent_before_speech = int(8 / 0.3)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        device=DEVICE_ID
    ) as stream:
        while total_chunks < max_chunks:
            chunk, _ = stream.read(chunk_size)
            if CHANNELS > 1:
                chunk = chunk.mean(axis=1)

            all_audio.append(chunk.flatten())
            total_chunks += 1
            energy = float(np.sqrt(np.mean(chunk**2)))

            if energy > silence_threshold:
                speaking_started = True
                silent_chunks = 0
            elif speaking_started:
                silent_chunks += 1
                if silent_chunks >= silence_chunks_needed and total_chunks >= min_chunks:
                    break
            else:
                if total_chunks > max_silent_before_speech:
                    return np.array([])

    if not speaking_started:
        return np.array([])

    audio = np.concatenate(all_audio)
    max_val = np.max(np.abs(audio))
    if max_val > 0.001:
        audio = audio / max_val * 0.9
    return audio

def record_audio(duration: int = 5) -> np.ndarray:
    # keep for compatibility
    return record_until_silence(min_duration=1, max_duration=duration)


def transcribe_audio(audio: np.ndarray, language: str = None) -> str:
    if audio is None or len(audio) == 0:
        logger.debug("Empty audio — skipping transcription")
        return ""

    model = get_model()
    lang  = language or USER_PROFILE.get("preferred_language", "english")
    whisper_lang = "ta" if lang == "tamil" else "en"



    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, SAMPLE_RATE)
        tmp_path = f.name

    segments, _info = model.transcribe(
        tmp_path,
        language=whisper_lang,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            threshold=0.4,   # slightly lower → catches quieter voices
        ),
    )

    text = " ".join([s.text for s in segments]).strip()

    # ignore very short transcriptions — likely noise
    if len(text) < 3:
        return ""

    logger.info(f"Transcribed: {text}")
    return text


def listen_once(duration: int = 30, language: str = None) -> str:
    """
    Record one utterance and transcribe it.
    Waits up to `duration` seconds for speech, then transcribes.
    """
    from app.services.voice.wake_word import set_handling, clear_handling

    set_handling()  # pause wake-word listener, take mic ownership
    try:
        audio = record_until_silence(
            min_duration=1,
            max_duration=duration,
            silence_duration=2.5,
        )
    finally:
        clear_handling() # return mic to wake-word listener

    return transcribe_audio(audio, language=language)