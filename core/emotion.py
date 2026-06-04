import sys
import os
sys.path.insert(0, r'C:\Users\gowth\AppData\Local\Programs\Python\Python312\Lib\site-packages')

from transformers import pipeline as hf_pipeline
from functools import lru_cache
from loguru import logger
import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

@lru_cache(maxsize=1)
def get_emotion_classifier():
    logger.info(f"Loading emotion model on {DEVICE}...")
    return hf_pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=1,
        device=0 if DEVICE == "cuda" else -1
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