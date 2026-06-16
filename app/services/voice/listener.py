"""
listener.py  — NAVIX voice input

Uses soundcard (Windows WASAPI) as primary recording engine because it works
directly with Windows audio without PortAudio limitations (WDM-KS -9999 error).
Falls back to sounddevice for non-Windows or if soundcard is unavailable.
"""
import sounddevice as sd
import numpy as np
import tempfile
import soundfile as sf
from pathlib import Path
from datetime import datetime
from loguru import logger
from app.services.voice.language_config import USER_PROFILE

SAMPLE_RATE = 16000
CHANNELS = 1

# Auto detect working microphone
def find_working_device() -> int:
    devices = sd.query_devices()
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            try:
                audio = sd.rec(
                    int(0.5 * SAMPLE_RATE),
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype="float32",
                    device=i
                )
                sd.wait()
                logger.info(f"Mic found: device {i} — {d['name']}")
                return i
            except:
                continue
    logger.error("No working microphone found!")
    return 0

DEVICE_ID = find_working_device()
# ── Voice data collection folder ──────────────────────────────────────────────
VOICE_DATA_DIR = Path("F:/naveen/AGI_Start/data/voice_samples")
VOICE_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Microphone selection (soundcard / WASAPI) ─────────────────────────────────
_mic = None

def _get_mic():
    """Pick and cache the best available microphone using soundcard (WASAPI)."""
    global _mic
    if _mic is not None:
        return _mic

    import soundcard as sc

    # Try default first
    try:
        m = sc.default_microphone()
        _mic = m
        logger.info(f"Mic (default): {m.name}")
        return _mic
    except Exception:
        pass

    # Scan all mics, pick the first real one
    skip_words = ['stereo mix', 'loopback', 'what u hear', 'nvidia', 'realtek digital']
    for m in sc.all_microphones(include_loopback=False):
        name = m.name.lower()
        if any(w in name for w in skip_words):
            continue
        try:
            # Quick test-open
            with m.recorder(samplerate=SAMPLE_RATE, channels=1, blocksize=4800):
                pass
            _mic = m
            logger.info(f"Mic (auto): {m.name}")
            return _mic
        except Exception as e:
            logger.debug(f"Mic skip [{m.name}]: {e}")

    # Last resort — any mic that opens
    for m in sc.all_microphones(include_loopback=False):
        try:
            with m.recorder(samplerate=SAMPLE_RATE, channels=1, blocksize=4800):
                pass
            _mic = m
            logger.info(f"Mic (fallback): {m.name}")
            return _mic
        except Exception:
            pass

    logger.error("No working microphone found! Plug in your USB mic or set a default recording device in Windows Sound Settings.")
    return None


# ── Whisper model ─────────────────────────────────────────────────────────────
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


# ── Helpers ───────────────────────────────────────────────────────────────────
def save_voice_sample(audio: np.ndarray, transcription: str):
    """Save audio + transcription for future fine-tuning (background thread)."""
    try:
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


# ── Core recording ────────────────────────────────────────────────────────────
def record_until_silence(
    min_duration: float  = 1.0,
    max_duration: float  = 30.0,
    silence_threshold: float = 0.006,
    silence_duration: float  = 1.5,
) -> np.ndarray:
    """
    Record from the microphone using soundcard (Windows WASAPI).
    Stops when the user goes silent. Returns a 1-D float32 numpy array.
    """
    mic = _get_mic()
    if mic is None:
        return np.array([], dtype=np.float32)

    chunk_dur            = 0.3            # seconds per chunk
    chunk_size           = int(chunk_dur * SAMPLE_RATE)
    max_chunks           = int(max_duration / chunk_dur)
    min_chunks           = int(min_duration / chunk_dur)
    silence_chunks_needed = int(silence_duration / chunk_dur)
    max_silent_before_speech = int(8 / chunk_dur)

    all_audio        = []
    silent_chunks    = 0
    speaking_started = False
    total_chunks     = 0

    try:
        with mic.recorder(samplerate=SAMPLE_RATE, channels=1, blocksize=chunk_size) as rec:
            logger.debug("Mic open — listening...")
            while total_chunks < max_chunks:
                chunk = rec.record(numframes=chunk_size)          # shape (N, 1)
                audio_chunk = chunk[:, 0].astype(np.float32)      # flatten to 1-D

                all_audio.append(audio_chunk)
                total_chunks += 1
                energy = float(np.sqrt(np.mean(audio_chunk ** 2)))

                if energy > silence_threshold:
                    speaking_started = True
                    silent_chunks    = 0
                elif speaking_started:
                    silent_chunks += 1
                    if silent_chunks >= silence_chunks_needed and total_chunks >= min_chunks:
                        break
                else:
                    if total_chunks > max_silent_before_speech:
                        return np.array([], dtype=np.float32)

    except Exception as e:
        logger.error(f"Recording error: {e}")
        return np.array([], dtype=np.float32)

    if not speaking_started or not all_audio:
        return np.array([], dtype=np.float32)

    audio   = np.concatenate(all_audio)
    max_val = np.max(np.abs(audio))
    if max_val > 0.001:
        audio = audio / max_val * 0.9
    return audio


# ── Transcription ─────────────────────────────────────────────────────────────
def transcribe_audio(audio: np.ndarray, language: str = None) -> str:
    if audio is None or len(audio) == 0:
        return ""

    model = get_model()
    lang  = language or USER_PROFILE.get("preferred_language", "english")
    whisper_lang = "ta" if lang == "tamil" else "en"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, audio, SAMPLE_RATE)
        tmp_path = f.name

    segments, _ = model.transcribe(
        tmp_path,
        language=whisper_lang,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
            threshold=0.35,
        ),
    )

    text = " ".join([s.text for s in segments]).strip()
    if len(text) < 3:
        return ""

    logger.info(f"Transcribed: {text}")

    import threading
    threading.Thread(
        target=save_voice_sample,
        args=(audio.copy(), text),
        daemon=True
    ).start()

    return text


# ── High-level API ────────────────────────────────────────────────────────────
def listen_once(duration: int = 30, language: str = None) -> str:
    """Record one utterance and transcribe it. Pauses wake-word listener."""
    from app.services.voice.wake_word import set_handling, clear_handling

    set_handling()
    try:
        audio = record_until_silence(
            min_duration=1,
            max_duration=duration,
            silence_duration=2.5,
        )
    finally:
        clear_handling()

    return transcribe_audio(audio, language=language)