from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger

class CommandRequest(BaseModel):
    command: str

class BrowserRequest(BaseModel):
    url: str = None
    query: str = None

router = APIRouter(prefix="/memory", tags=['memory'])

@router.get@router.get("/planner/today")
async def get_today_plan():
    from navix.services.ai.planner import get_todays_plan
    plan = await get_todays_plan()
    return {"plan": plan, "has_plan": bool(plan)}

@router.get@router.get("/planner/weekly")
async def get_weekly():
    from navix.services.ai.planner import get_weekly_summary
    summary = await get_weekly_summary()
    return {"summary": summary, "count": len(summary)}

@router.post@router.post("/planner/save")
async def save_plan(body: dict):
    from navix.services.ai.planner import save_daily_plan
    await save_daily_plan(body.get("plan", ""))
    return {"status": "saved"}

# ── Reminder ──────────────────────────────────────────────────────────────────

@router.post@router.post("/reminder/add")
async def add_reminder_endpoint(body: dict):
    from navix.services.utilities.reminder import add_reminder
    await add_reminder(
        body.get("message", ""),
        body.get("hour", 9),
        body.get("minute", 0)
    )
    return {"status": "reminder added"}


@router.get@router.get("/world/context")
async def world_context():
    from navix.services.memory.world_model import get_world_context
    context = await get_world_context()
    return {"context": context}

@router.get@router.get("/world/insight")
async def daily_insight():
    from navix.services.memory.world_model import generate_daily_insight
    insight = await generate_daily_insight()
    return {"insight": insight}

@router.post@router.post("/world/goal")
async def add_goal(body: dict):
    from navix.services.memory.world_model import set_weekly_goal
    result = await set_weekly_goal(body.get("goal", ""))
    return {"status": "ok", "result": result}

@router.post@router.post("/world/goal/complete")
async def complete_goal(body: dict):
    from navix.services.memory.world_model import complete_goal
    result = await complete_goal(body.get("goal", ""))
    return {"status": "ok", "result": result}

@router.post@router.post("/world/mood")
async def record_mood(body: dict):
    from navix.services.memory.world_model import record_mood
    await record_mood(body.get("mood", "neutral"))
    return {"status": "recorded"}

@router.post@router.post("/world/learn")
async def add_learning(body: dict):
    from navix.services.memory.world_model import add_learning_topic
    await add_learning_topic(body.get("topic", ""))
    return {"status": "added"}

@router.get@router.get("/graph/stats")
async def graph_stats():
    from navix.services.memory.knowledge_graph import get_graph_stats
    return get_graph_stats()

@router.post@router.post("/graph/search")
async def graph_search_endpoint(body: CommandRequest):
    from navix.services.memory.knowledge_graph import graph_search
    result = await graph_search(body.command)
    return {"result": result or "No connected concepts found"}

@router.post@router.post("/learn/file")
async def learn_from_file(body: dict):
    from navix.services.ai.continual_learning import process_new_document
    result = await process_new_document(body.get("file_path", ""))
    return result

@router.get@router.get("/learn/log")
async def learning_log():
    from pathlib import Path
    log = Path("F:/naveen/AGI_Start/logs/learning.log")
    if not log.exists():
        return {"log": "No learning log yet"}
    lines = log.read_text(encoding="utf-8").strip().split("\n")
    return {"log": lines[-20:], "total_entries": len(lines)}


