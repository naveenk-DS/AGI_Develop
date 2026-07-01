# Language configuration for JARVIS
SUPPORTED_LANGUAGES = {
    "english": {
        "code": "en",
        "whisper_lang": "en",
        "greeting_morning": "Good morning Naveen",
        "greeting_afternoon": "Good afternoon Naveen",
        "greeting_evening": "Good evening Naveen",
        "greeting_night": "Good night Naveen",
        "wake_response": "Yes Naveen, I am listening",
        "ready": "JARVIS ready"
    },
    "tamil": {
        "code": "ta",
        "whisper_lang": "ta",
        "greeting_morning": "காலை வணக்கம் நவீன்",
        "greeting_afternoon": "மதிய வணக்கம் நவீன்",
        "greeting_evening": "மாலை வணக்கம் நவீன்",
        "greeting_night": "இரவு வணக்கம் நவீன்",
        "wake_response": "ஆம் நவீன், நான் கேட்கிறேன்",
        "ready": "ஜார்விஸ் தயார்"
    }
}

# Default language — change anytime
DEFAULT_LANGUAGE = "english"

# User profile
USER_PROFILE = {
    "name": "Naveen",
    "preferred_language": "english",  # english or tamil
    "languages": ["english", "tamil"]
}