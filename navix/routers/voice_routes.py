from navix.services.voice.language_config import USER_PROFILE, SUPPORTED_LANGUAGES
from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger
from navix.services.voice.speaker import speak

class LanguageSwitch(BaseModel):
    language: str

class SpeakRequest(BaseModel):
    text: str
    language: str = None

class CommandRequest(BaseModel):
    command: str

class BrowserRequest(BaseModel):
    url: str = None
    query: str = None

router = APIRouter(prefix="/voice", tags=['voice'])

@router.get("/status")
async def navix_status():
    return {
        "status": "online",
        "user": USER_PROFILE["name"],
        "language": USER_PROFILE["preferred_language"],
        "supported_languages": USER_PROFILE["languages"]
    }

@router.get("/greeting")
async def get_greeting_endpoint():
    from navix.services.voice.NAVIX_AI import get_greeting
    greeting = get_greeting()
    return {"greeting": greeting}

@router.post("/language")
async def switch_language(body: LanguageSwitch):
    if body.language not in SUPPORTED_LANGUAGES:
        return {"error": f"Unsupported. Choose from: {list(SUPPORTED_LANGUAGES.keys())}"}
    USER_PROFILE["preferred_language"] = body.language
    logger.info(f"Language switched to: {body.language}")
    return {"status": "switched", "language": body.language}

# ── Voice ─────────────────────────────────────────────────────────────────────

@router.post("/speak")
async def speak_text(body: SpeakRequest):
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, speak, body.text, body.language)
    return {"status": "speaking", "text": body.text}

@router.post("/test-voice")
async def test_voice():
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, speak, "Hello Naveen, NAVIX AI voice is working correctly", "english")
    return {"status": "speaking", "message": "Hello Naveen, NAVIX AI voice is working correctly"}

# ── Browser ───────────────────────────────────────────────────────────────────

@router.get("/voice/samples")
async def voice_samples():
    from pathlib import Path
    folder = Path("C:/Users/Naveen/AGI_Develop/data/voice_samples")
    if not folder.exists():
        return {"count": 0, "size_mb": 0}
    
    wav_files = list(folder.glob("*.wav"))
    total_size = sum(f.stat().st_size for f in wav_files)
    
    return {
        "count": len(wav_files),
        "size_mb": round(total_size / 1024 / 1024, 1),
        "folder": str(folder),
        "status": "collecting — keep using NAVIX daily"
    }