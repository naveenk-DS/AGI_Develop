from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger

class CommandRequest(BaseModel):
    command: str

class BrowserRequest(BaseModel):
    url: str = None
    query: str = None

router = APIRouter(prefix="/agent", tags=['agent'])

@router.get("/news/headlines")
async def headlines():
    import traceback
    try:
        from navix.services.ai.news_briefing import get_quick_headlines
        result = await get_quick_headlines()
        return {"headlines": result}
    except Exception as e:
        return {"headlines": f"Error: {str(e)}", "trace": traceback.format_exc()}

@router.get("/news/briefing")
async def morning_briefing():
    try:
        from navix.services.ai.news_briefing import build_morning_briefing
        briefing = await build_morning_briefing()
        return {"briefing": briefing}
    except Exception as e:
        return {"briefing": f"Error: {str(e)}"}

@router.get("/news/ai")
async def ai_news():
    try:
        from navix.services.ai.news_briefing import fetch_ai_news
        news = await fetch_ai_news()
        return {"ai_news": news}
    except Exception as e:
        return {"ai_news": [], "error": str(e)}
@router.post("/screen/describe")
async def screen_describe():
    from navix.desktop.vision.screen_reader import what_is_on_screen
    result = await what_is_on_screen()
    return {"description": result}

@router.post("/screen/read")
async def screen_read():
    from navix.desktop.vision.screen_reader import read_text_on_screen
    result = await read_text_on_screen()
    return {"text": result}

@router.post("/screen/click")
async def screen_click(body: CommandRequest):
    from navix.desktop.vision.ocr import click_element_by_vision
    result = await click_element_by_vision(body.command)
    return {"result": result}

@router.post("/screen/error")
async def screen_error():
    from navix.desktop.vision.screen_reader import analyze_error_on_screen
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


