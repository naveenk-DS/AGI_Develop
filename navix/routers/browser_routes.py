from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger

class CommandRequest(BaseModel):
    command: str

class BrowserRequest(BaseModel):
    url: str = None
    query: str = None

router = APIRouter(prefix="/browser", tags=['browser'])

@router.post@router.post("/browser/open")
async def browser_open(body: BrowserRequest):
    try:
        from navix.services.browser.browser import open_url
        result = await open_url(body.url)
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.error(f"Browser open error: {e}")
        return {"status": "error", "result": str(e)}

@router.post@router.post("/browser/youtube")
async def browser_youtube(body: BrowserRequest):
    try:
        from navix.services.browser.browser import open_youtube
        result = await open_youtube(body.query)
        return {"status": "ok", "result": result}
    except Exception as e:
        import traceback
        logger.error(f"YouTube FULL error: {traceback.format_exc()}")
        return {"status": "error", "result": str(e)}

@router.post@router.post("/browser/search")
async def browser_search(body: BrowserRequest):
    try:
        from navix.services.browser.browser import search_google
        result = await search_google(body.query)
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"status": "error", "result": str(e)}

@router.post@router.post("/browser/command")
async def browser_command(body: CommandRequest):
    try:
        from navix.services.ai.command_parser import execute_browser_command
        result = await execute_browser_command(body.command)
        return {"status": "ok", "result": result or "No browser action needed"}
    except Exception as e:
        logger.error(f"Command error: {e}")
        return {"status": "error", "result": str(e)}

@router.post@router.post("/browser/close")
async def browser_close():
    try:
        from navix.services.browser.browser import close_browser
        await close_browser()
        return {"status": "closed"}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post@router.post("/browser/new-tab")
async def browser_new_tab(body: BrowserRequest):
    try:
        from navix.services.browser.browser import open_new_tab
        url = body.url or "https://google.com"
        result = await open_new_tab(url)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post@router.post("/browser/new-window")
async def browser_new_window(body: BrowserRequest):
    try:
        from navix.services.browser.browser import open_new_window
        result = await open_new_window()
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post@router.post("/browser/news")
async def browser_news():
    try:
        from navix.services.browser.browser import get_news
        headlines = await get_news()
        return {"status": "ok", "headlines": headlines}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post@router.post("/browser/wikipedia")
async def browser_wikipedia(body: BrowserRequest):
    try:
        from navix.services.browser.browser import search_wikipedia
        result = await search_wikipedia(body.query)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

# ── Planner ───────────────────────────────────────────────────────────────────

