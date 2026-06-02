from transformers import pipeline
from functools import lru_cache
from loguru import logger

@lru_cache(maxsize=1)
def get_emotion_classifier():
    logger.info("Loading emotion model...")
    return pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=1
    )

def detect_emotion(text: str) -> str:
    try:
        classifier = get_emotion_classifier()
        result = classifier(text[:512])
        emotion = result[0][0]["label"].lower()
        logger.info(f"Emotion detected: {emotion}")
        return emotion
    except Exception as e:
        logger.warning(f"Emotion detection failed: {e}")
        return "neutral"

EMOTION_RESPONSES = {
    "joy":      "I am glad to hear that! ",
    "sadness":  "I am sorry to hear that Naveen. ",
    "anger":    "I understand your frustration. ",
    "fear":     "Don't worry Naveen, I am here. ",
    "surprise": "Oh interesting! ",
    "disgust":  "I understand. ",
    "neutral":  ""
}

def get_emotional_prefix(text: str) -> str:
    emotion = detect_emotion(text)
    return EMOTION_RESPONSES.get(emotion, "")