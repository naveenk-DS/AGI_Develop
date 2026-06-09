from loguru import logger
from functools import lru_cache

EMOTION_RESPONSES = {
    "joy":      "I am glad to hear that! ",
    "sadness":  "I am sorry to hear that Naveen. ",
    "anger":    "I understand your frustration. ",
    "fear":     "Don't worry Naveen, I am here. ",
    "surprise": "Oh interesting! ",
    "neutral":  ""
}

async def detect_emotion_ollama(text: str) -> str:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "llama3.1",
                    "prompt": (
                        f"Classify the emotion in this text into exactly one word: "
                        f"joy, sadness, anger, fear, surprise, or neutral.\n"
                        f"Text: {text[:200]}\n"
                        f"Emotion:"
                    ),
                    "stream": False
                }
            )
            if r.status_code == 200:
                emotion = r.json().get("response", "").strip().lower()
                # clean up
                for e in ["joy", "sadness", "anger", "fear", "surprise", "neutral"]:
                    if e in emotion:
                        return e
    except Exception as e:
        logger.warning(f"Ollama emotion failed: {e}")
    return "neutral"

def detect_emotion(text: str) -> str:
    # sync keyword fallback
    text_lower = text.lower()
    if any(w in text_lower for w in ["happy", "great", "amazing", "love", "excellent"]):
        return "joy"
    if any(w in text_lower for w in ["sad", "sorry", "bad", "terrible", "miss"]):
        return "sadness"
    if any(w in text_lower for w in ["angry", "frustrated", "hate", "annoyed"]):
        return "anger"
    if any(w in text_lower for w in ["scared", "worried", "afraid", "nervous"]):
        return "fear"
    if any(w in text_lower for w in ["wow", "really", "seriously", "unexpected"]):
        return "surprise"
    return "neutral"

def get_emotional_prefix(text: str) -> str:
    emotion = detect_emotion(text)
    return EMOTION_RESPONSES.get(emotion, "")

def get_emotion_classifier():
    return None