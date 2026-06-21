"""
personality.py — All NAVIX phrases are AI-generated via Ollama.
No hardcoded sentences. Every response is freshly predicted.
"""

import re
import requests
from loguru import logger

# ── Ollama config ──────────────────────────────────────────────────────────────
_OLLAMA_URL   = "http://localhost:11434/api/generate"
_NAVIX_MODEL  = "navix-personality"   # created from training/Modelfile
_FALLBACK_MODEL = "qwen2.5:7b"          # fallback if navix-personality not found

# ── Tight prompts for each personality slot ───────────────────────────────────
_PROMPTS = {
    "greeting": (
        "Generate ONE short casual greeting that NAVIX says when Naveen just woke it up. "
        "Vary it each time — don't start with 'Hey'. "
        "1 sentence, no punctuation overload, no emojis, voice-friendly."
    ),
    "confused": (
        "NAVIX didn't hear anything clearly. Generate ONE short natural phrase asking Naveen "
        "to repeat, vary it each time. "
        "1 sentence, voice-friendly, casual."
    ),
    "follow_up": (
        "Generate ONE short casual follow-up NAVIX says after completing a task, asking if "
        "Naveen needs anything else. Vary it. 1 sentence, voice-friendly."
    ),
    "done": (
        "Generate ONE short casual phrase NAVIX says after finishing a task, confirming it's "
        "done and asking what's next. 1 sentence, voice-friendly."
    ),
    "thinking": (
        "Generate ONE very short thinking filler sound or phrase NAVIX says while it's "
        "processing. Examples style: 'Hmm...', 'Let me think...', 'One moment...'. "
        "Under 5 words, vary each time."
    ),
    "resuming": (
        "Generate ONE short phrase NAVIX says when resuming a previous topic. "
        "1 sentence, voice-friendly, casual."
    ),
    "acknowledgement": (
        "Generate ONE short casual acknowledgement word or phrase. "
        "Examples style: 'Got it', 'Sure', 'On it'. Under 4 words."
    ),
}

# ── Last-resort strings (single word only — used ONLY if model is fully offline) ──
_LAST_RESORT = {
    "greeting":        "Yes?",
    "confused":        "Pardon?",
    "follow_up":       "Anything else?",
    "done":            "Done.",
    "thinking":        "Hmm...",
    "resuming":        "Continuing...",
    "acknowledgement": "Okay.",
}

# ── Lightweight fallback prompts (shorter, faster — used when primary call fails) ─
_FALLBACK_PROMPTS = {
    "greeting":        "Say one very short greeting. Under 4 words.",
    "confused":        "Ask to repeat in 3 words or less.",
    "follow_up":       "Ask if anything else is needed. Under 5 words.",
    "done":            "Confirm task done in 2 words.",
    "thinking":        "Say a thinking filler. Under 4 words.",
    "resuming":        "Say you're continuing. Under 4 words.",
    "acknowledgement": "Acknowledge in 2 words or less.",
}


def _call_ollama(prompt: str, model: str, timeout: float = 6) -> str:
    """Single Ollama call — returns cleaned text or empty string."""
    resp = requests.post(
        _OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.9,
                "top_p": 0.95,
                "num_predict": 40,
                "repeat_penalty": 1.4,
                "stop": ["\n", "User:", "Naveen:"],
            },
        },
        timeout=timeout,
    )
    if resp.status_code != 200:
        return ""
    text = resp.json().get("response", "").strip()
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+\s*', '', text)
    text = text.strip('"').strip("'").strip()
    return text if 2 < len(text) < 120 else ""


def _generate(slot: str) -> str:
    """
    Generate a fresh phrase for the given slot.
    Tier 1 → navix-personality model with full prompt
    Tier 2 → fallback model with lightweight prompt (also model-predicted)
    Tier 3 → last-resort single hardcoded word (only if fully offline)
    """
    full_prompt  = _PROMPTS.get(slot, "Say something brief and friendly.")
    light_prompt = _FALLBACK_PROMPTS.get(slot, "Say something brief.")

    # Tier 1 — primary model, full prompt
    for model in [_NAVIX_MODEL, _FALLBACK_MODEL]:
        try:
            text = _call_ollama(full_prompt, model, timeout=6)
            if text:
                logger.debug(f"[personality:{slot}] tier1 model={model} → {text!r}")
                return text
        except requests.exceptions.ConnectionError:
            logger.warning(f"[personality] Ollama not reachable (slot={slot}), trying light prompt")
            break
        except Exception as e:
            logger.warning(f"[personality] Ollama error (slot={slot}): {e}")
            break

    # Tier 2 — fallback model with a lighter, faster prompt (still model-predicted)
    try:
        text = _call_ollama(light_prompt, _FALLBACK_MODEL, timeout=3)
        if text:
            logger.debug(f"[personality:{slot}] tier2 light → {text!r}")
            return text
    except Exception:
        pass

    # Tier 3 — fully offline last resort
    choice = _LAST_RESORT.get(slot, "Okay.")
    logger.debug(f"[personality:{slot}] tier3 last-resort → {choice!r}")
    return choice


# ── Public API (matches existing imports in NAVIX_AI.py) ─────────────────────

def thinking_sound() -> str:
    return _generate("thinking")

def acknowledgement() -> str:
    return _generate("acknowledgement")

def greeting() -> str:
    return _generate("greeting")

def follow_up() -> str:
    return _generate("follow_up")

def done() -> str:
    return _generate("done")

def confused() -> str:
    return _generate("confused")

def resuming() -> str:
    return _generate("resuming")


def get_action_response(action: str) -> str:
    action_lower = action.lower()
    if "weather" in action_lower:
        prompt = (
            "NAVIX is pulling up weather info for Naveen. "
            "Generate ONE short casual phrase confirming this. 1 sentence."
        )
    elif any(w in action_lower for w in ["open", "browser", "youtube", "chrome"]):
        prompt = (
            "NAVIX is opening something in the browser for Naveen. "
            "Generate ONE short casual phrase confirming it's opening. 1 sentence."
        )
    else:
        return _generate("acknowledgement")

    # inline generate with custom prompt
    for model in [_NAVIX_MODEL, _FALLBACK_MODEL]:
        try:
            resp = requests.post(
                _OLLAMA_URL,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.85,
                        "num_predict": 35,
                        "stop": ["\n", "User:"],
                    },
                },
                timeout=5,
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip().strip('"').strip("'")
                text = re.sub(r'\*+', '', text).strip()
                if 2 < len(text) < 100:
                    return text
        except Exception:
            break

    return _generate("acknowledgement")


def wrap_as_friend(response: str, emotion: str = "neutral") -> str:
    """Clean markdown and add an AI-generated emotional prefix."""
    response = response.strip()

    # remove markdown
    response = re.sub(r'\*\*(.+?)\*\*', r'\1', response)
    response = re.sub(r'\*(.+?)\*', r'\1', response)
    response = re.sub(r'#+\s', '', response)
    response = re.sub(r'^\d+\.\s', '', response, flags=re.MULTILINE)
    response = re.sub(r'^-\s', '', response, flags=re.MULTILINE)

    # AI-generated prefix based on emotion
    if emotion in ("neutral", ""):
        return response  # no prefix needed — keep it clean

    emotion_prompts = {
        "joy":      "Naveen shared something positive. Generate ONE short joyful prefix (under 6 words).",
        "sadness":  "Naveen shared something sad. Generate ONE short empathetic prefix (under 6 words).",
        "anger":    "Naveen is frustrated. Generate ONE short understanding prefix (under 6 words).",
        "fear":     "Naveen seems worried. Generate ONE short reassuring prefix (under 6 words).",
        "surprise": "Naveen said something surprising. Generate ONE short surprised prefix (under 6 words).",
    }

    prompt = emotion_prompts.get(emotion, "")
    if not prompt:
        return response

    try:
        resp = requests.post(
            _OLLAMA_URL,
            json={
                "model": _NAVIX_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.9, "num_predict": 20, "stop": ["\n"]},
            },
            timeout=4,
        )
        if resp.status_code == 200:
            prefix = resp.json().get("response", "").strip().strip('"').strip("'")
            prefix = re.sub(r'\*+', '', prefix).strip()
            if 1 < len(prefix) < 50:
                return f"{prefix} {response}"
    except Exception:
        pass

    return response