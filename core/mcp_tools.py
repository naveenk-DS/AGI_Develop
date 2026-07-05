from core.advanced_rag import advanced_rag_query
from loguru import logger
from typing import Callable, Any
import asyncio

# MCP Tool Registry
_tools: dict[str, dict] = {}

def register_tool(
    name: str,
    description: str,
    func: Callable,
    parameters: dict = None
):
    _tools[name] = {
        "name": name,
        "description": description,
        "func": func,
        "parameters": parameters or {}
    }
    logger.info(f"MCP tool registered: {name}")

def get_tool(name: str) -> dict:
    return _tools.get(name)

def list_tools() -> list[dict]:
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "parameters": t["parameters"]
        }
        for t in _tools.values()
    ]

async def execute_tool(name: str, **kwargs) -> Any:
    tool = _tools.get(name)
    if not tool:
        return f"Tool not found: {name}"
    try:
        func = tool["func"]
        if asyncio.iscoroutinefunction(func):
            return await func(**kwargs)
        return func(**kwargs)
    except Exception as e:
        logger.error(f"Tool execution error [{name}]: {e}")
        return f"Tool error: {e}"

async def route_to_tool(user_input: str) -> str:
    if not _tools:
        return None
    try:
        from core.llm import get_llm
        from langchain_core.messages import HumanMessage, SystemMessage

        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in list_tools()
        ])

        llm = get_llm()
        messages = [
            SystemMessage(content=(
                f"You are a tool router. Available tools:\n{tools_desc}\n\n"
                f"Return ONLY the tool name that best matches the request, "
                f"or 'none' if no tool matches. Nothing else."
            )),
            HumanMessage(content=user_input)
        ]
        result = await llm.ainvoke(messages)
        tool_name = result.content.strip().lower()

        if tool_name in _tools:
            logger.info(f"MCP routed to tool: {tool_name}")
            return tool_name
        return None
    except Exception as e:
        logger.error(f"Tool routing error: {e}")
        return None


# ── Register all NAVIX tools ──────────────────────────────────────────────────

def register_all_tools():

    # Browser tools
    async def tool_open_youtube(query: str = "") -> str:
        from navix.services.browser.browser import open_youtube
        return await open_youtube(query)

    async def tool_search_google(query: str) -> str:
        from navix.services.browser.browser import search_google
        return await search_google(query)

    async def tool_open_url(url: str) -> str:
        from navix.services.browser.browser import open_url
        return await open_url(url)

    async def tool_get_news() -> str:
        from navix.services.ai.news_briefing import get_quick_headlines
        return await get_quick_headlines()

    async def tool_wikipedia(query: str) -> str:
        from navix.services.browser.browser import search_wikipedia
        return await search_wikipedia(query)

    # PC tools
    async def tool_screenshot() -> str:
        from navix.desktop.vision.screen_reader import what_is_on_screen
        return await what_is_on_screen()

    async def tool_type_text(text: str) -> str:
        from navix.desktop.keyboard.typing import type_text
        return type_text(text)

    async def tool_volume_up() -> str:
        from navix.desktop.volume.controller import volume_up
        return volume_up()

    async def tool_volume_down() -> str:
        from navix.desktop.volume.controller import volume_down
        return volume_down()

    # Knowledge tools
    async def tool_rag_search(query: str) -> str:
        return await advanced_rag_query(query)

    async def tool_graph_search(query: str) -> str:
        from navix.services.memory.knowledge_graph import graph_search
        result = await graph_search(query)
        return result or "No connected concepts found"

    async def tool_daily_briefing() -> str:
        from navix.services.ai.news_briefing import build_morning_briefing
        return await build_morning_briefing()

    async def tool_world_insight() -> str:
        from navix.services.memory.world_model import generate_daily_insight
        return await generate_daily_insight()

    # Memory tools
    async def tool_remember(text: str) -> str:
        from navix.services.memory.personal_memory import add_memory
        await add_memory(text)
        return f"Remembered: {text}"

    async def tool_planner_today() -> str:
        from navix.services.ai.planner import get_todays_plan
        plan = await get_todays_plan()
        return plan or "No plan set for today"

    # WhatsApp tools
    async def tool_whatsapp_send(contact: str, message: str) -> str:
        from navix.automation.tools.communication_tools import whatsapp_send_message
        return await whatsapp_send_message(contact, message)

    async def tool_whatsapp_read() -> str:
        from navix.automation.tools.communication_tools import whatsapp_read_unread
        return str(await whatsapp_read_unread())

    # Register all
    register_tool("open_youtube",    "Open YouTube and search for videos", tool_open_youtube, {"query": "search term"})
    register_tool("search_google",   "Search Google for information", tool_search_google, {"query": "search term"})
    register_tool("open_url",        "Open any website URL", tool_open_url, {"url": "website url"})
    register_tool("get_news",        "Get today's top news headlines", tool_get_news)
    register_tool("wikipedia",       "Search Wikipedia for information", tool_wikipedia, {"query": "topic"})
    register_tool("screenshot",      "Take screenshot and describe screen", tool_screenshot)
    register_tool("type_text",       "Type text on keyboard", tool_type_text, {"text": "text to type"})
    register_tool("volume_up",       "Increase system volume", tool_volume_up)
    register_tool("volume_down",     "Decrease system volume", tool_volume_down)
    register_tool("rag_search",      "Search through documents and files", tool_rag_search, {"query": "question"})
    register_tool("graph_search",    "Search knowledge graph for connected concepts", tool_graph_search, {"query": "concept"})
    register_tool("daily_briefing",  "Get morning news and AI briefing", tool_daily_briefing)
    register_tool("world_insight",   "Get personalized daily insight", tool_world_insight)
    register_tool("remember",        "Remember something important", tool_remember, {"text": "thing to remember"})
    register_tool("planner_today",   "Get today's plan", tool_planner_today)
    register_tool("whatsapp_send",   "Send a WhatsApp message to a contact", tool_whatsapp_send, {"contact": "exact contact name", "message": "message text"})
    register_tool("whatsapp_read",   "Read unread WhatsApp messages", tool_whatsapp_read)

    logger.info(f"MCP: {len(_tools)} tools registered")