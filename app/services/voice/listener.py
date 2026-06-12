import sounddevice as sd
import numpy as np
import tempfile
import soundfile as sf
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

DEVICE_ID = 6
SAMPLE_RATE = 16000
CHANNELS = 1  # device 6 uses 1 channel

_model = None

def get_model():
    global _model
    if _model is None:
        logger.info("Loading Faster-Whisper...")
        import torch
        from faster_whisper import WhisperModel
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        _model = WhisperModel("medium", device=device, compute_type=compute)
        logger.info(f"Faster-Whisper loaded on {device}")
    return _model


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
    max_silent_before_speech = int(8 / 0.3)  # 8 seconds before speech starts

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
                # no speech yet — wait max 8 seconds
                if total_chunks > max_silent_before_speech:
                    return np.array([])  # return empty — no speech detected

    if not speaking_started:
        return np.array([])

    audio = np.concatenate(all_audio)
    max_val = np.max(np.abs(audio))
    if max_val > 0.001:
        audio = audio / max_val * 0.9
    return audio



# def record_audio(duration: int = 5) -> np.ndarray:
#     # keep for compatibility
#     return record_until_silence(min_duration=1, max_duration=duration)


# def transcribe_audio(audio: np.ndarray, language: str = None) -> str:
#     if audio is None or len(audio) == 0:
#         logger.debug("Empty audio — skipping transcription")
#         return ""

#     model = get_model()
#     lang = language or USER_PROFILE.get("preferred_language", "english")
#     whisper_lang = "ta" if lang == "tamil" else "en"

#     # check if audio has enough energy — skip silence
#     energy = float(np.sqrt(np.mean(audio**2)))
#     if energy < 0.005:
#         logger.debug("Too quiet — skipping transcription")
#         return ""

#     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
#         sf.write(f.name, audio, SAMPLE_RATE)
#         tmp_path = f.name

#     segments, info = model.transcribe(
#         tmp_path,
#         language=whisper_lang,
#         beam_size=5,
#         vad_filter=True,
#         vad_parameters=dict(
#             min_silence_duration_ms=500,
#             threshold=0.5            # higher threshold — ignore quiet sounds
#         )
#     )

#     text = " ".join([s.text for s in segments]).strip()

#     # ignore very short transcriptions — likely noise
#     if len(text) < 3:
#         return ""

#     logger.info(f"Transcribed: {text}")
#     return text


def listen_once(duration: int = 30, language: str = None) -> str:
    audio = record_until_silence(
        min_duration=1,
        max_duration=duration,
        silence_duration=1.2
    )
    if audio is None or len(audio) == 0:
        return ""
    return transcribe_audio(audio, language=language)