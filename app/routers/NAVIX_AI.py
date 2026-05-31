from fastapi import APIRouter
from pydantic import BaseModel
from app.services.voice.language_config import USER_PROFILE, SUPPORTED_LANGUAGES
from app.services.voice.speaker import speak
from loguru import logger

from pydantic import BaseModel


router = APIRouter(prefix="/navix", tags=["navix"])

class LanguageSwitch(BaseModel):
    language: str

class SpeakRequest(BaseModel):
    text: str
    language: str = None

class BrowserRequest(BaseModel):
    url: str = None
    query: str = None

class CommandRequest(BaseModel):
    command: str


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



@router.post("/browser/open")
async def browser_open(body: BrowserRequest):
    from app.services.browser import open_url
    result = await open_url(body.url)
    return {"status": "ok", "result": result}

@router.post("/browser/youtube")
async def browser_youtube(body: BrowserRequest):
    from app.services.browser import open_youtube
    result = await open_youtube(body.query)
    return {"status": "ok", "result": result}

@router.post("/browser/search")
async def browser_search(body: BrowserRequest):
    from app.services.browser import search_google
    result = await search_google(body.query)
    return {"status": "ok", "result": result}

@router.post("/browser/command")
async def browser_command(body: CommandRequest):
    from app.services.command_parser import execute_browser_command
    result = await execute_browser_command(body.command)
    return {"status": "ok", "result": result or "No browser action needed"}

@router.post("/browser/close")
async def browser_close():
    from app.services.browser import close_browser
    await close_browser()
    return {"status": "closed"}