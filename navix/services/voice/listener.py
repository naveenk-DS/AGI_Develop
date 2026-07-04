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
from navix.services.voice.language_config import USER_PROFILE

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

_SKIP_LOOPBACK = ['stereo mix', 'loopback', 'what u hear', 'camo']
_MIC_TEST_TIMEOUT = 5.0   # seconds — increased to 5s to give Bluetooth headsets time to wake up


def _test_mic_with_timeout(m, timeout: float = _MIC_TEST_TIMEOUT) -> bool:
    """
    Test a mic in a daemon thread with a hard timeout.
    Disconnected Bluetooth devices hang indefinitely — this prevents that.
    Returns True if the mic opens AND produces non-zero RMS within `timeout` s.
    """
    import threading
    result = [False]

    def _probe():
        test_frames = int(0.5 * SAMPLE_RATE)
        try:
            with m.recorder(samplerate=SAMPLE_RATE, channels=1,
                            blocksize=test_frames) as rec:
                data = rec.record(numframes=test_frames)
                rms = float(np.sqrt(np.mean(data ** 2)))
                logger.info(f"  [{m.name}] RMS={rms:.6f}")
                result[0] = rms > 0.0
        except Exception as e:
            logger.debug(f"  [{m.name}] open failed: {e}")

    t = threading.Thread(target=_probe, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        logger.debug(f"  [{m.name}] timed out after {timeout}s — skipping")
        return False

    return result[0]


def _get_mic():
    """
    Pick and cache the first microphone that actually produces audio.
    Each mic is tested with a hard 2s timeout so disconnected Bluetooth
    devices never freeze startup. Works with any mic type.
    """
    global _mic
    if _mic is not None:
        return _mic

    import soundcard as sc
    all_mics = sc.all_microphones(include_loopback=False)

    # Pass 1 — find first mic that produces non-zero audio within timeout
    for m in all_mics:
        if any(w in m.name.lower() for w in _SKIP_LOOPBACK):
            continue
        if _test_mic_with_timeout(m):
            _mic = m
            logger.info(f"Mic selected: {m.name}")
            return _mic

    # Pass 2 — room may be silent; accept any mic that opens within timeout
    logger.warning("All mics returned RMS=0 — room silent? Accepting first mic that opens.")
    for m in all_mics:
        if any(w in m.name.lower() for w in _SKIP_LOOPBACK):
            continue

        def _try_open(mic=m):
            try:
                with mic.recorder(samplerate=SAMPLE_RATE, channels=1, blocksize=4800):
                    pass
                return True
            except Exception:
                return False

        import threading
        ok = [False]
        def _run(mic=m):
            ok[0] = _try_open(mic)
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=_MIC_TEST_TIMEOUT)
        if not t.is_alive() and ok[0]:
            _mic = m
            logger.info(f"Mic selected (silent-room fallback): {m.name}")
            return _mic

    logger.error("No working microphone found!")
    return None


def reset_mic():
    """Force mic re-detection on next listen (useful after hot-swap)."""
    global _mic
    _mic = None
    logger.info("Mic cache cleared — will re-detect on next listen.")


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
    silence_threshold: float = 0.005,   # above typical background noise (~0.002-0.004)
    silence_duration: float  = 1.5,
) -> np.ndarray:
    """
    Record from the microphone using sounddevice.
    Stops when the user goes silent. Returns a 1-D float32 numpy array.
    """
    chunk_dur            = 0.3            # seconds per chunk
    chunk_size           = int(chunk_dur * SAMPLE_RATE)
    max_chunks           = int(max_duration / chunk_dur)
    min_chunks           = int(min_duration / chunk_dur)
    silence_chunks_needed = int(silence_duration / chunk_dur)
    max_silent_before_speech = int(20 / chunk_dur)  # wait up to 20s for speech to start

    all_audio        = []
    silent_chunks    = 0
    speaking_started = False
    total_chunks     = 0
    _log_every       = int(3 / chunk_dur)

    try:
        import sounddevice as sd
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', device=DEVICE_ID) as stream:
            logger.debug(f"Mic open — listening... (threshold={silence_threshold})")
            while total_chunks < max_chunks:
                chunk, overflowed = stream.read(chunk_size)
                audio_chunk = chunk[:, 0].copy()

                all_audio.append(audio_chunk)
                total_chunks += 1
                energy = float(np.sqrt(np.mean(audio_chunk ** 2)))

                if total_chunks % _log_every == 0:
                    logger.debug(f"[mic] energy={energy:.5f} threshold={silence_threshold} speaking={speaking_started}")

                if energy > silence_threshold:
                    speaking_started = True
                    silent_chunks    = 0
                elif speaking_started:
                    silent_chunks += 1
                    if silent_chunks >= silence_chunks_needed and total_chunks >= min_chunks:
                        logger.debug("Silence detected — stopping recording")
                        break
                else:
                    if total_chunks > max_silent_before_speech:
                        logger.debug(f"No speech detected after {total_chunks} chunks — giving up")
                        return np.array([], dtype=np.float32)

    except Exception as e:
        logger.error(f"Recording error: {e}")
        import time
        time.sleep(2)
        return np.array([], dtype=np.float32)

    if not speaking_started or not all_audio:
        logger.debug("record_until_silence: no speech detected")
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
    from navix.services.voice.wake_word import set_handling, clear_handling

    set_handling()
    try:
        audio = record_until_silence(
            min_duration=0.5,    # reduced: capture short commands faster
            max_duration=duration,
            silence_duration=0.8,  # reduced from 2.5s → respond right after you stop talking
        )
    finally:
        clear_handling()

    return transcribe_audio(audio, language=language)