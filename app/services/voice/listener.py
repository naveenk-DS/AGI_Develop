import sounddevice as sd
import numpy as np
import tempfile
import soundfile as sf
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

DEVICE_ID   = 1
SAMPLE_RATE = 16000

_model = None


def get_model():
    global _model
    if _model is None:
        import torch
        device  = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        logger.info(f"Loading Faster-Whisper on {device}...")
        from faster_whisper import WhisperModel
        _model = WhisperModel("medium", device=device, compute_type=compute)
        logger.info(f"Faster-Whisper loaded on {device}")
    return _model


# ── VAD recording ─────────────────────────────────────────────────────────────

def record_until_silence(
    max_duration: int   = 30,
    silence_sec: float  = 1.5,
    threshold: float    = 0.008,
) -> np.ndarray:
    """
    Real-time VAD recording.
    Starts immediately, stops when you've been quiet for silence_sec,
    hard cap at max_duration seconds. Works like ChatGPT voice.
    """
    chunk_size    = int(0.25 * SAMPLE_RATE)          # 250 ms chunks
    max_chunks    = int(max_duration / 0.25)
    need_silence  = int(silence_sec / 0.25)          # chunks of silence to stop

    recorded: list[np.ndarray] = []
    silence_count   = 0
    started_speaking = False

    logger.info("VAD listening — speak now...")
    try:
        with sd.InputStream(
            samplerate  = SAMPLE_RATE,
            channels    = 1,
            dtype       = "float32",
            device      = DEVICE_ID,
            blocksize   = chunk_size,
        ) as stream:
            for _ in range(max_chunks):
                chunk, _ = stream.read(chunk_size)
                audio    = chunk.flatten()
                energy   = float(np.sqrt(np.mean(audio ** 2)))
                recorded.append(audio.copy())

                if energy > threshold:
                    started_speaking = True
                    silence_count    = 0
                elif started_speaking:
                    silence_count += 1
                    if silence_count >= need_silence:
                        logger.info("Silence detected — stopping VAD")
                        break

    except Exception as e:
        logger.error(f"VAD recording error: {e}")

    if not recorded:
        return np.zeros(SAMPLE_RATE, dtype="float32")

    audio = np.concatenate(recorded)
    logger.info(f"VAD captured {len(audio) / SAMPLE_RATE:.1f}s")
    return audio


def transcribe_audio(audio: np.ndarray, language: str = None) -> str:
    model = get_model()
    lang  = language or USER_PROFILE.get("preferred_language", "english")
    whisper_lang = "ta" if lang == "tamil" else "en"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, SAMPLE_RATE)
        tmp_path = f.name

    segments, _ = model.transcribe(
        tmp_path,
        language       = whisper_lang,
        beam_size      = 5,
        vad_filter     = True,
        vad_parameters = dict(min_silence_duration_ms=500),
    )

    text = " ".join([s.text for s in segments]).strip()
    logger.info(f"Transcribed ({lang}): {text}")
    return text


def listen_once(duration: int = None, language: str = None) -> str:
    """
    Listen and transcribe.
    No duration  → VAD mode (stops when you stop speaking). ← DEFAULT
    With duration → fixed-length recording (legacy fallback).
    """
    if duration is not None:
        logger.info(f"Fixed recording {duration}s...")
        audio = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate = SAMPLE_RATE,
            channels   = 1,
            dtype      = "float32",
            device     = DEVICE_ID,
        )
        sd.wait()
        audio = audio.flatten()
    else:
        audio = record_until_silence()

    return transcribe_audio(audio, language=language)