from datetime import datetime, date
from loguru import logger
from app.db.database import AsyncSessionLocal
from app.db.models import Config
from app.crypto.encrypt import encrypt, decrypt
from sqlalchemy import select

WORLD_MODEL_KEY = "naveen_world_model"
CUSTOMER_ID = "naveen_world"

DEFAULT_WORLD = {
    "daily_patterns": {},
    "frequent_apps": {},
    "frequent_commands": {},
    "topics_of_interest": [],
    "work_hours": {"start": None, "end": None},
    "productivity_score": [],
    "weekly_goals": [],
    "completed_goals": [],
    "mood_history": [],
    "learning_topics": [],
    "project_context": "Building NAVIX AI assistant",
    "last_updated": None,
    "total_interactions": 0,
    "insights": []
}

async def load_world() -> dict:
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Config).where(
                    Config.customer_id == CUSTOMER_ID,
                    Config.key == WORLD_MODEL_KEY
                )
            )
            row = result.scalar_one_or_none()
            if row and row.value:
                data = decrypt(row.value)
                return data.get("value", DEFAULT_WORLD.copy())
    except Exception as e:
        logger.error(f"World model load error: {e}")
    return DEFAULT_WORLD.copy()

async def save_world(world: dict):
    try:
        world["last_updated"] = datetime.utcnow().isoformat()
        async with AsyncSessionLocal() as db:
            encrypted = encrypt({"value": world})
            result = await db.execute(
                select(Config).where(
                    Config.customer_id == CUSTOMER_ID,
                    Config.key == WORLD_MODEL_KEY
                )
            )
            row = result.scalar_one_or_none()
            if row:
                row.value = encrypted
            else:
                from app.models import Config as ConfigModel
                db.add(ConfigModel(
                    customer_id=CUSTOMER_ID,
                    key=WORLD_MODEL_KEY,
                    value=encrypted
                ))
            await db.commit()
    except Exception as e:
        logger.error(f"World model save error: {e}")

async def record_interaction(command: str, tool_used: str, hour: int = None):
    world = await load_world()
    if hour is None:
        hour = datetime.now().hour

    # track daily patterns
    hour_key = str(hour)
    world["daily_patterns"][hour_key] = world["daily_patterns"].get(hour_key, 0) + 1

    # track frequent commands
    cmd_lower = command.lower()[:50]
    world["frequent_commands"][cmd_lower] = world["frequent_commands"].get(cmd_lower, 0) + 1

    # track tool usage
    world["frequent_apps"][tool_used] = world["frequent_apps"].get(tool_used, 0) + 1

    # total interactions
    world["total_interactions"] = world.get("total_interactions", 0) + 1

    await save_world(world)

async def add_insight(insight: str):
    world = await load_world()
    world["insights"].append({
        "text": insight,
        "date": str(date.today())
    })
    world["insights"] = world["insights"][-20:]
    await save_world(world)

async def set_weekly_goal(goal: str):
    world = await load_world()
    world["weekly_goals"].append({
        "goal": goal,
        "date": str(date.today()),
        "done": False
    })
    await save_world(world)
    return f"Weekly goal added: {goal}"

async def complete_goal(goal_text: str):
    world = await load_world()
    for g in world["weekly_goals"]:
        if goal_text.lower() in g["goal"].lower():
            g["done"] = True
            world["completed_goals"].append(g)
    await save_world(world)
    return f"Goal marked complete: {goal_text}"

async def add_learning_topic(topic: str):
    world = await load_world()
    if topic not in world["learning_topics"]:
        world["learning_topics"].append(topic)
    await save_world(world)

async def record_mood(mood: str):
    world = await load_world()
    world["mood_history"].append({
        "mood": mood,
        "date": str(date.today()),
        "time": datetime.now().strftime("%H:%M")
    })
    world["mood_history"] = world["mood_history"][-30:]
    await save_world(world)

async def get_world_context() -> str:
    world = await load_world()

    # find most active hours
    patterns = world.get("daily_patterns", {})
    if patterns:
        peak_hour = max(patterns, key=patterns.get)
        peak_str = f"Most active at {peak_hour}:00"
    else:
        peak_str = "Activity pattern not yet established"

    # top tools
    apps = world.get("frequent_apps", {})
    top_tools = sorted(apps.items(), key=lambda x: x[1], reverse=True)[:3]
    tools_str = ", ".join([t[0] for t in top_tools]) if top_tools else "none yet"

    # active goals
    goals = [g["goal"] for g in world.get("weekly_goals", []) if not g.get("done")]
    goals_str = "; ".join(goals[:3]) if goals else "no active goals"

    # recent mood
    moods = world.get("mood_history", [])
    mood_str = moods[-1]["mood"] if moods else "unknown"

    # insights
    insights = world.get("insights", [])
    insights_str = "; ".join([i["text"] for i in insights[-3:]]) if insights else "none yet"

    context = f"""World model for Naveen:
- Project: {world.get('project_context', 'NAVIX AI')}
- Total interactions: {world.get('total_interactions', 0)}
- {peak_str}
- Most used tools: {tools_str}
- Active goals: {goals_str}
- Recent mood: {mood_str}
- Key insights: {insights_str}
- Learning: {', '.join(world.get('learning_topics', [])[:3]) or 'not tracked yet'}"""

    return context.strip()

async def generate_daily_insight() -> str:
    try:
        world = await load_world()
        from core.llm import get_llm
        from langchain_core.messages import HumanMessage, SystemMessage

        context = await get_world_context()
        llm = get_llm()

        messages = [
            SystemMessage(content="You are a personal advisor for Naveen. Give one specific, actionable insight in 2 sentences maximum."),
            HumanMessage(content=f"Based on this data about Naveen, give one useful insight:\n{context}")
        ]
        result = await llm.ainvoke(messages)
        insight = result.content.strip()
        await add_insight(insight)
        return insight
    except Exception as e:
        logger.error(f"Insight generation error: {e}")
        return "Keep building consistently every day."