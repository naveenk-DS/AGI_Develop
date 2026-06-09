from loguru import logger
import httpx
import asyncio

EMOTION_RESPONSES = {
    "joy":      "That's great! ",
    "sadness":  "I hear you Naveen. ",
    "anger":    "I get it. ",
    "fear":     "Don't worry. ",
    "surprise": "Oh wow! ",
    "neutral":  ""
}

async def detect_emotion_async(text: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model": "llama3.1",
                    "prompt": (
                        f"Detect emotion in one word only from: joy, sadness, anger, fear, surprise, neutral.\n"
                        f"Text: {text[:150]}\n"
                        f"Emotion:"
                    ),
                    "stream": False
                }
            )
            if r.status_code == 200:
                emotion = r.json().get("response", "").strip().lower()
                for e in ["joy", "sadness", "anger", "fear", "surprise", "neutral"]:
                    if e in emotion:
                        return e
    except Exception as e:
        logger.warning(f"Emotion detect failed: {e}")
    return "neutral"

def detect_emotion(text: str) -> str:
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