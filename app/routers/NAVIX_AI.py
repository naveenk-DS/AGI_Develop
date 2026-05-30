from fastapi import APIRouter
from pydantic import BaseModel
from app.services.voice.language_config import USER_PROFILE, SUPPORTED_LANGUAGES
from app.services.voice.speaker import speak
from loguru import logger

router = APIRouter(prefix="/navix", tags=["navix"])

class LanguageSwitch(BaseModel):
    language: str

class SpeakRequest(BaseModel):
    text: str
    language: str = None

@router.get("/status")
async def jarvis_status():
    return {
        "status": "online",
        "user": USER_PROFILE["name"],
        "language": USER_PROFILE["preferred_language"],
        "supported_languages": USER_PROFILE["languages"]
    }

@router.get("/greeting")
async def get_greeting_endpoint():
    from app.services.voice.NAVIX_AI import get_greeting
    greeting = get_greeting()
    # don't speak here — just return the text
    # speaking happens in jarvis_start.py
    return {"greeting": greeting}

@router.post("/speak")
async def speak_text(body: SpeakRequest):
    # run speak in background so API doesn't freeze
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, speak, body.text, body.language)
    return {"status": "speaking", "text": body.text}


@router.post("/language")
async def switch_language(body: LanguageSwitch):
    if body.language not in SUPPORTED_LANGUAGES:
        return {"error": f"Unsupported language. Choose from: {list(SUPPORTED_LANGUAGES.keys())}"}
    USER_PROFILE["preferred_language"] = body.language
    logger.info(f"Language switched to: {body.language}")
    return {"status": "switched", "language": body.language}

@router.post("/test-voice")
async def test_voice():
    import asyncio
    from app.services.voice.speaker import speak
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, speak, "Hello Naveen, NAVIX AI voice is working correctly", "english")
    return {"status": "speaking", "message": "Hello Naveen, NAVIX AI voice is working correctly"}