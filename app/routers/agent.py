from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.agent import run_agent
from app.db.memory import get_history, save_message
from app.db.logger import log_event
from loguru import logger
import time

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/agent", tags=["agent"])

class AgentRequest(BaseModel):
    session_id: str
    message: str

@router.post("/run")
async def run(body: AgentRequest, db: AsyncSession = Depends(get_db)):
    start = time.time()

    # load conversation history
    history = await get_history(db, body.session_id)

    # run agent — it decides what to do
    result = await run_agent(
        user_message=body.message,
        session_id=body.session_id,
        history=history
    )

    # save to memory
    await save_message(db, body.session_id, "user", body.message)
    await save_message(db, body.session_id, "assistant", result["answer"])

    duration_ms = int((time.time() - start) * 1000)

    # log it
    await log_event(db, body.session_id, "agent_run", {
        "tool_used": result["tool_used"],
        "duration_ms": duration_ms,
        "context_chunks": result["context_chunks"]
    })

    return {
        "session_id": body.session_id,
        "message": body.message,
        "answer": result["answer"],
        "tool_used": result["tool_used"],
        "context_chunks": result["context_chunks"],
        "duration_ms": duration_ms
    }

@router.get("/tools")
async def list_tools():
    from app.services.agent import TOOLS
    return {"tools": TOOLS}


@router.post("/run")
@limiter.limit("20/minute")
async def run(request: Request, body: AgentRequest, db: AsyncSession = Depends(get_db)):
    start = time.time()
    history = await get_history(db, body.session_id)
    result = await run_agent(
        user_message=body.message,
        session_id=body.session_id,
        history=history
    )
    await save_message(db, body.session_id, "user", body.message)
    await save_message(db, body.session_id, "assistant", result["answer"])
    duration_ms = int((time.time() - start) * 1000)
    await log_event(db, body.session_id, "agent_run", {
        "tool_used": result["tool_used"],
        "duration_ms": duration_ms,
        "context_chunks": result["context_chunks"]
    })
    return {
        "session_id": body.session_id,
        "message": body.message,
        "answer": result["answer"],
        "tool_used": result["tool_used"],
        "context_chunks": result["context_chunks"],
        "duration_ms": duration_ms
    }