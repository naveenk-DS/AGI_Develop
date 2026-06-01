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

class BrowserRequest(BaseModel):
    url: str = None
    query: str = None

class CommandRequest(BaseModel):
    command: str

# ── Status & Language ─────────────────────────────────────────────────────────

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

@router.post("/browser/open")
async def browser_open(body: BrowserRequest):
    try:
        from app.services.browser import open_url
        result = await open_url(body.url)
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.error(f"Browser open error: {e}")
        return {"status": "error", "result": str(e)}

@router.post("/browser/youtube")
async def browser_youtube(body: BrowserRequest):
    try:
        from app.services.browser import open_youtube
        result = await open_youtube(body.query)
        return {"status": "ok", "result": result}
    except Exception as e:
        import traceback
        logger.error(f"YouTube FULL error: {traceback.format_exc()}")
        return {"status": "error", "result": str(e)}

@router.post("/browser/search")
async def browser_search(body: BrowserRequest):
    try:
        from app.services.browser import search_google
        result = await search_google(body.query)
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"status": "error", "result": str(e)}

@router.post("/browser/command")
async def browser_command(body: CommandRequest):
    try:
        from app.services.command_parser import execute_browser_command
        result = await execute_browser_command(body.command)
        return {"status": "ok", "result": result or "No browser action needed"}
    except Exception as e:
        logger.error(f"Command error: {e}")
        return {"status": "error", "result": str(e)}

@router.post("/browser/close")
async def browser_close():
    try:
        from app.services.browser import close_browser
        await close_browser()
        return {"status": "closed"}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/browser/new-tab")
async def browser_new_tab(body: BrowserRequest):
    try:
        from app.services.browser import open_new_tab
        url = body.url or "https://google.com"
        result = await open_new_tab(url)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/browser/new-window")
async def browser_new_window(body: BrowserRequest):
    try:
        from app.services.browser import open_new_window
        result = await open_new_window()
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/browser/news")
async def browser_news():
    try:
        from app.services.browser import get_news
        headlines = await get_news()
        return {"status": "ok", "headlines": headlines}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/browser/wikipedia")
async def browser_wikipedia(body: BrowserRequest):
    try:
        from app.services.browser import search_wikipedia
        result = await search_wikipedia(body.query)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

# ── Planner ───────────────────────────────────────────────────────────────────

@router.get("/planner/today")
async def get_today_plan():
    from app.services.planner import get_todays_plan
    plan = await get_todays_plan()
    return {"plan": plan, "has_plan": bool(plan)}

@router.get("/planner/weekly")
async def get_weekly():
    from app.services.planner import get_weekly_summary
    summary = await get_weekly_summary()
    return {"summary": summary, "count": len(summary)}

@router.post("/planner/save")
async def save_plan(body: dict):
    from app.services.planner import save_daily_plan
    await save_daily_plan(body.get("plan", ""))
    return {"status": "saved"}

# ── Reminder ──────────────────────────────────────────────────────────────────

@router.post("/reminder/add")
async def add_reminder_endpoint(body: dict):
    from app.services.reminder import add_reminder
    await add_reminder(
        body.get("message", ""),
        body.get("hour", 9),
        body.get("minute", 0)
    )
    return {"status": "reminder added"}


@router.post("/app/open")
async def open_app(body: CommandRequest):
    try:
        from app.services.command_parser import launch_app
        result = await launch_app(body.command.lower())
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.get("/app/list")
async def list_apps():
    from app.services.command_parser import APPS
    return {"apps": list(APPS.keys()), "count": len(APPS)}