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


@router.post("/pc/command")
async def pc_command(body: CommandRequest):
    try:
        from app.services.pc_command_parser import execute_pc_command
        result = await execute_pc_command(body.command)
        return {"status": "ok", "result": result or "Command not recognized"}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/pc/type")
async def pc_type(body: CommandRequest):
    try:
        from app.services.pc_control import type_text
        result = type_text(body.command)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/pc/screenshot")
async def pc_screenshot():
    try:
        import os
        os.makedirs("F:/naveen/AGI_Start/screenshots", exist_ok=True)
        from app.services.pc_control import take_screenshot
        result = take_screenshot("F:/naveen/AGI_Start/screenshots/screenshot.png")
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/pc/key")
async def pc_key(body: CommandRequest):
    try:
        from app.services.pc_control import press_key
        result = press_key(body.command)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}


@router.get("/news/headlines")
async def headlines():
    import traceback
    try:
        from app.services.news_briefing import get_quick_headlines
        result = await get_quick_headlines()
        return {"headlines": result}
    except Exception as e:
        return {"headlines": f"Error: {str(e)}", "trace": traceback.format_exc()}

@router.get("/news/briefing")
async def morning_briefing():
    try:
        from app.services.news_briefing import build_morning_briefing
        briefing = await build_morning_briefing()
        return {"briefing": briefing}
    except Exception as e:
        return {"briefing": f"Error: {str(e)}"}

@router.get("/news/ai")
async def ai_news():
    try:
        from app.services.news_briefing import fetch_ai_news
        news = await fetch_ai_news()
        return {"ai_news": news}
    except Exception as e:
        return {"ai_news": [], "error": str(e)}
@router.post("/screen/describe")
async def screen_describe():
    from app.services.screen_vision import what_is_on_screen
    result = await what_is_on_screen()
    return {"description": result}

@router.post("/screen/read")
async def screen_read():
    from app.services.screen_vision import read_text_on_screen
    result = await read_text_on_screen()
    return {"text": result}

@router.post("/screen/click")
async def screen_click(body: CommandRequest):
    from app.services.screen_vision import click_element_by_vision
    result = await click_element_by_vision(body.command)
    return {"result": result}

@router.post("/screen/error")
async def screen_error():
    from app.services.screen_vision import analyze_error_on_screen
    result = await analyze_error_on_screen()
    return {"result": result}


@router.get("/news/debug")
async def news_debug():
    import traceback
    import httpx
    import xml.etree.ElementTree as ET
    results = {}
    url = "https://feeds.bbci.co.uk/news/rss.xml"
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, verify=False) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            results["status_code"] = r.status_code
            results["content_length"] = len(r.text)
            try:
                root = ET.fromstring(r.text)
                items = root.findall(".//item/title")
                results["xml_items"] = len(items)
                results["first_title"] = items[0].text if items else "none"
            except Exception as xe:
                results["xml_error"] = str(xe)
                results["raw_start"] = r.text[:200]
    except Exception as e:
        results["error"] = str(e)
        results["error_type"] = type(e).__name__
        results["trace"] = traceback.format_exc()
    return results

@router.get("/world/context")
async def world_context():
    from app.services.world_model import get_world_context
    context = await get_world_context()
    return {"context": context}

@router.get("/world/insight")
async def daily_insight():
    from app.services.world_model import generate_daily_insight
    insight = await generate_daily_insight()
    return {"insight": insight}

@router.post("/world/goal")
async def add_goal(body: dict):
    from app.services.world_model import set_weekly_goal
    result = await set_weekly_goal(body.get("goal", ""))
    return {"status": "ok", "result": result}

@router.post("/world/goal/complete")
async def complete_goal(body: dict):
    from app.services.world_model import complete_goal
    result = await complete_goal(body.get("goal", ""))
    return {"status": "ok", "result": result}

@router.post("/world/mood")
async def record_mood(body: dict):
    from app.services.world_model import record_mood
    await record_mood(body.get("mood", "neutral"))
    return {"status": "recorded"}

@router.post("/world/learn")
async def add_learning(body: dict):
    from app.services.world_model import add_learning_topic
    await add_learning_topic(body.get("topic", ""))
    return {"status": "added"}

@router.get("/graph/stats")
async def graph_stats():
    from app.services.knowledge_graph import get_graph_stats
    return get_graph_stats()

@router.post("/graph/search")
async def graph_search_endpoint(body: CommandRequest):
    from app.services.knowledge_graph import graph_search
    result = await graph_search(body.command)
    return {"result": result or "No connected concepts found"}

@router.post("/learn/file")
async def learn_from_file(body: dict):
    from app.services.continual_learning import process_new_document
    result = await process_new_document(body.get("file_path", ""))
    return result

@router.get("/learn/log")
async def learning_log():
    from pathlib import Path
    log = Path("F:/naveen/AGI_Start/logs/learning.log")
    if not log.exists():
        return {"log": "No learning log yet"}
    lines = log.read_text(encoding="utf-8").strip().split("\n")
    return {"log": lines[-20:], "total_entries": len(lines)}


@router.get("/mcp/tools")
async def mcp_list_tools():
    from core.mcp_tools import list_tools
    tools = list_tools()
    return {"tools": tools, "count": len(tools)}

@router.post("/mcp/execute")
async def mcp_execute(body: dict):
    from core.mcp_tools import execute_tool
    name = body.get("tool")
    params = body.get("params", {})
    result = await execute_tool(name, **params)
    return {"tool": name, "result": result}

@router.post("/mcp/route")
async def mcp_route(body: CommandRequest):
    from core.mcp_tools import route_to_tool, execute_tool
    tool_name = await route_to_tool(body.command)
    if not tool_name:
        return {"tool": "none", "result": "No matching tool found"}
    result = await execute_tool(tool_name)
    return {"tool": tool_name, "result": result}

@router.post("/rag/advanced")
async def advanced_rag(body: dict):
    from core.advanced_rag import advanced_rag_query
    result = await advanced_rag_query(body.get("question", ""))
    return {"answer": result}


@router.post("/crew/research")
async def crew_research(body: CommandRequest):
    try:
        import asyncio
        from core.crew_agents import get_research_crew
        result = await asyncio.get_event_loop().run_in_executor(
            None, get_research_crew, body.command
        )
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@router.post("/crew/advise")
async def crew_advise(body: CommandRequest):
    try:
        import asyncio
        from core.crew_agents import get_advisory_crew
        result = await asyncio.get_event_loop().run_in_executor(
            None, get_advisory_crew, body.command
        )
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@router.post("/crew/plan")
async def crew_plan(body: CommandRequest):
    try:
        import asyncio
        from core.crew_agents import get_planning_crew
        result = await asyncio.get_event_loop().run_in_executor(
            None, get_planning_crew, body.command
        )
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@router.post("/crew/code")
async def crew_code(body: CommandRequest):
    try:
        import asyncio
        from core.crew_agents import get_code_crew
        result = await asyncio.get_event_loop().run_in_executor(
            None, get_code_crew, body.command
        )
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


@router.get("/voice/samples")
async def voice_samples():
    from pathlib import Path
    folder = Path("F:/naveen/AGI_Start/data/voice_samples")
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