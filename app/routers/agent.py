from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from core.graph import get_graph
from app.services.personal_memory import get_context_for_ai
from app.db.memory import get_history, save_message
from app.db.logger import log_event
from loguru import logger
import time
from core.graph import get_graph

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentRequest(BaseModel):
    session_id: str
    message: str

@router.post("/run")
async def run(body: AgentRequest, db: AsyncSession = Depends(get_db)):
    start = time.time()
    personal_context = await get_context_for_ai()
    history = await get_history(db, body.session_id)

    graph = await get_graph()
    state = {
        "messages": history,
        "user_input": body.message,
        "emotion": "neutral",
        "tool": "chat",
        "response": "",
        "personal_context": personal_context
    }

    result = await graph.ainvoke(state)
    answer = result["response"]
    duration_ms = int((time.time() - start) * 1000)

    await save_message(db, body.session_id, "user", body.message)
    await save_message(db, body.session_id, "assistant", answer)
    await log_event(db, body.session_id, "agent_run", {
        "tool_used": result["tool"],
        "emotion": result["emotion"],
        "duration_ms": duration_ms
    })

    return {
        "session_id": body.session_id,
        "answer": answer,
        "tool_used": result["tool"],
        "emotion": result["emotion"],
        "duration_ms": duration_ms
    }

@router.get("/tools")
async def list_tools():
    return {
        "tools": {
            "rag": "Search through ingested documents",
            "chat": "General conversation and questions",
            "browser": "Open websites, search, YouTube",
            "pc": "Control mouse, keyboard, apps",
            "memory": "Remember personal information"
        }
    }