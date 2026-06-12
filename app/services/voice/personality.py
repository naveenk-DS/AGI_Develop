"""
personality.py — All NAVIX phrases are AI-generated via Ollama.
No hardcoded sentences. Every response is freshly predicted.
"""
import random
import re
import requests
from loguru import logger

# ── Ollama config ──────────────────────────────────────────────────────────────
_OLLAMA_URL   = "http://localhost:11434/api/generate"
_NAVIX_MODEL  = "navix-personality"   # created from training/Modelfile
_FALLBACK_MODEL = "llama3.1"          # fallback if navix-personality not found

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

# ── Hardcoded emergency fallbacks (only used when Ollama is unreachable) ──────
_FALLBACKS = {
    "greeting":      ["Go ahead.", "I'm here.", "Yes?", "What's up?"],
    "confused":      ["Say that again?", "Didn't catch that.", "One more time?"],
    "follow_up":     ["What else?", "Anything else?", "I'm listening."],
    "done":          ["Done.", "All set.", "There you go."],
    "thinking":      ["Hmm...", "Let me check...", "One sec..."],
    "resuming":      ["So as I was saying...", "Right, continuing..."],
    "acknowledgement": ["Got it.", "Sure.", "Okay."],
}


def _generate(slot: str) -> str:
    """
    Call Ollama to generate a fresh phrase for the given personality slot.
    Falls back gracefully if Ollama is unavailable.
    """
    prompt = _PROMPTS.get(slot, "Say something brief and friendly.")

    for model in [_NAVIX_MODEL, _FALLBACK_MODEL]:
        try:
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
                timeout=6,
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
                # strip markdown artifacts
                text = re.sub(r'\*+', '', text)
                text = re.sub(r'#+\s*', '', text)
                text = text.strip('"').strip("'").strip()
                # sanity — must be non-empty and reasonable length
                if 2 < len(text) < 120:
                    logger.debug(f"[personality:{slot}] model={model} → {text!r}")
                    return text
        except requests.exceptions.ConnectionError:
            logger.warning(f"[personality] Ollama not reachable (slot={slot}), using fallback")
            break
        except Exception as e:
            logger.warning(f"[personality] Ollama error (slot={slot}): {e}")
            break

    # fallback
    choice = random.choice(_FALLBACKS.get(slot, ["Okay."]))
    logger.debug(f"[personality:{slot}] fallback → {choice!r}")
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

    return random.choice(["On it!", "Sure thing!", "Opening that now."])


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