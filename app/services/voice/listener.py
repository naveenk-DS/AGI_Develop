import time
import sounddevice as sd
import numpy as np
import tempfile
import soundfile as sf
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

import sounddevice as sd

DEVICE_ID = sd.default.device[0]
try:
    if DEVICE_ID is not None and DEVICE_ID >= 0:
        device_info = sd.query_devices(DEVICE_ID)
        CHANNELS = int(device_info['max_input_channels'])
    else:
        DEVICE_ID = None
        CHANNELS = 1
except Exception as e:
    logger.warning(f"Could not query audio devices: {e}. Defaulting to 1 channel.")
    DEVICE_ID = None
    CHANNELS = 1

SAMPLE_RATE = 16000

_model = None


def get_model():
    global _model
    if _model is None:
        logger.info("Loading Faster-Whisper...")
        import torch
        from faster_whisper import WhisperModel
        device  = "cuda" if torch.cuda.is_available() else "cpu"
        compute = "float16" if device == "cuda" else "int8"
        _model = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
        logger.info(f"Faster-Whisper loaded on {device}")
    return _model


def record_until_silence(
    min_duration: int    = 2,
    max_duration: int    = 30,
    silence_threshold: float = 0.0015,   # catches quieter speech
    silence_duration: float  = 2.5,
    speech_start_timeout: float = 15.0, # 15s to start speaking
) -> np.ndarray:
    """
    Records audio using sd.rec() per chunk — same approach as wake_word.py.
    sd.rec() + sd.wait() blocks for EXACTLY chunk_size/SAMPLE_RATE seconds,
    guaranteeing real-time mic audio with no stale-buffer issues.
    """
    # We no longer call sd.stop() here because forcing PortAudio to stop from another thread causes segfaults on Windows.
    # The wake_word listener gracefully yields the mic because _handling.is_set() is now true.
    time.sleep(0.5)   # let the wake word listener finish its current chunk and go to sleep

    logger.info("Listening — speak now...")

    chunk_size           = int(0.3 * SAMPLE_RATE)         # 300ms per chunk
    all_audio            = []
    silent_chunks        = 0
    speaking_started     = False
    total_chunks         = 0
    max_chunks           = int(max_duration / 0.3)
    silence_chunks_needed = int(silence_duration / 0.3)
    min_chunks           = int(min_duration / 0.3)
    start_timeout_chunks = int(speech_start_timeout / 0.3)

    while total_chunks < max_chunks:
        # sd.rec() + sd.wait() = guaranteed 300ms of REAL mic audio per iteration.
        # Unlike sd.InputStream, this cannot return stale buffered zeros.
        try:
            raw = sd.rec(
                chunk_size,
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                device=DEVICE_ID,
            )
            sd.wait()   # blocks until hardware captures chunk_size fresh samples
        except Exception as e:
            logger.error(f"Failed to record audio (no device?): {e}")
            return np.array([], dtype=np.float32)

        # flatten to 1-D
        chunk = raw.flatten() if raw.ndim <= 1 else raw.mean(axis=1)
        # Protect against mic hardware glitching and returning giant garbage numbers
        chunk = np.nan_to_num(chunk, posinf=1.0, neginf=-1.0)
        chunk = np.clip(chunk, -1.0, 1.0)
        
        all_audio.append(chunk)
        total_chunks += 1

        energy = float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2)))

        if energy > silence_threshold:
            speaking_started = True
            silent_chunks    = 0
        elif speaking_started:
            silent_chunks += 1
            if silent_chunks >= silence_chunks_needed and total_chunks >= min_chunks:
                logger.debug(f"Silence detected — stopping after {total_chunks * 0.3:.1f}s")
                break
        else:
            # still waiting for speech to start
            if total_chunks >= start_timeout_chunks:
                logger.debug(f"No speech detected within {speech_start_timeout:.0f}s")
                return np.array([], dtype=np.float32)

    if not speaking_started:
        return np.array([], dtype=np.float32)

    audio   = np.concatenate(all_audio)
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
            speech_start_timeout=min(duration, 15.0),
        )
    finally:
        clear_handling() # return mic to wake-word listener

    return transcribe_audio(audio, language=language)