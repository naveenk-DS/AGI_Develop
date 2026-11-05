import json
import asyncio
from pathlib import Path
from loguru import logger
from core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

EXPERIENCE_DB_PATH = Path("C:/Users/Naveen/AGI_Develop/data/experience_db.json")
PREFERENCES_DB_PATH = Path("C:/Users/Naveen/AGI_Develop/data/user_preferences.json")

def _load_db(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return []

def _save_db(path: Path, data: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=4), encoding="utf-8")

async def log_task_experience(task_goal: str, tool_used: str, result: str, success: bool):
    """Logs an executed task into the experience database for future reflection."""
    db = _load_db(EXPERIENCE_DB_PATH)
    db.append({
        "goal": task_goal,
        "tool": tool_used,
        "result": result,
        "success": success,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })
    _save_db(EXPERIENCE_DB_PATH, db)
    logger.info(f"Task logged to experience DB: {task_goal}")

async def run_reflection_cycle():
    """
    Analyzes the experience database to:
    1. Extract new user preferences.
    2. Identify recurring errors and generate optimization rules.
    3. Consolidate memory.
    """
    logger.info("Starting nightly reflection cycle...")
    experiences = _load_db(EXPERIENCE_DB_PATH)
    if len(experiences) < 5:
        logger.info("Not enough new experiences for reflection yet.")
        return

    # Extract recent experiences
    recent = experiences[-10:]
    history_text = "\n".join([f"Goal: {e['goal']}, Success: {e['success']}, Result: {e['result']}" for e in recent])

    llm = get_llm()
    prompt = f"""
You are the Reflection Engine for NAVIX. Analyze these recent interactions:
{history_text}

Task 1: Identify any implicit user preferences (e.g., likes concise answers, prefers certain apps).
Task 2: Identify any repeated failures and suggest a behavioral fix.

Format your response exactly like this:
PREFERENCES: [list any preferences found, or NONE]
FIXES: [list any behavioral rules to avoid failures, or NONE]
"""
    try:
        messages = [SystemMessage(content="You are an AI introspection engine."), HumanMessage(content=prompt)]
        res = await llm.ainvoke(messages)
        content = res.content
        
        # Save extracted preferences
        if "PREFERENCES: NONE" not in content.upper():
            prefs = _load_db(PREFERENCES_DB_PATH)
            prefs.append({"timestamp": __import__('datetime').datetime.now().isoformat(), "insight": content})
            _save_db(PREFERENCES_DB_PATH, prefs)
            logger.info("New user preferences extracted and saved.")
            
        # Optimization logic can be added here based on FIXES
        logger.info("Reflection cycle completed successfully.")
        
    except Exception as e:
        logger.error(f"Reflection cycle failed: {e}")
