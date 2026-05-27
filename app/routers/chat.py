from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.ollama import chat as ollama_chat
from app.db.memory import save_message, get_history, clear_history
from app.db.logger import log_event
from loguru import logger
import time

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    session_id: str       # unique ID per user or conversation
    message: str
    system: str = "You are a helpful AI assistant."

class ClearRequest(BaseModel):
    session_id: str

@router.post("/message")
async def chat_message(body: ChatRequest, db: AsyncSession = Depends(get_db)):
    start = time.time()

    # load previous conversation from postgres
    history = await get_history(db, body.session_id)
    logger.info(f"Session {body.session_id} — history: {len(history)} messages")

    # call ollama with full history
    reply = await ollama_chat(
        prompt=body.message,
        system=body.system,
        history=history
    )

    # save user message and assistant reply to postgres
    await save_message(db, body.session_id, "user", body.message)
    await save_message(db, body.session_id, "assistant", reply)

    duration_ms = int((time.time() - start) * 1000)

    # log the event
    await log_event(db, body.session_id, "chat", {
        "message_length": len(body.message),
        "reply_length": len(reply),
        "history_count": len(history),
        "duration_ms": duration_ms
    })

    return {
        "session_id": body.session_id,
        "reply": reply,
        "history_count": len(history),
        "duration_ms": duration_ms
    }

@router.post("/clear")
async def clear_chat(body: ClearRequest, db: AsyncSession = Depends(get_db)):
    await clear_history(db, body.session_id)
    return {"status": "cleared", "session_id": body.session_id}

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, db: AsyncSession = Depends(get_db)):
    history = await get_history(db, session_id, last_n=50)
    return {"session_id": session_id, "messages": history, "count": len(history)}


@router.post("/message")
@limiter.limit("30/minute")
async def chat_message(request: Request, body: ChatRequest, db: AsyncSession = Depends(get_db)):
    start = time.time()
    history = await get_history(db, body.session_id)
    reply = await ollama_chat(
        prompt=body.message,
        system=body.system,
        history=history
    )
    await save_message(db, body.session_id, "user", body.message)
    await save_message(db, body.session_id, "assistant", reply)
    duration_ms = int((time.time() - start) * 1000)
    await log_event(db, body.session_id, "chat", {
        "message_length": len(body.message),
        "reply_length": len(reply),
        "history_count": len(history),
        "duration_ms": duration_ms
    })
    return {
        "session_id": body.session_id,
        "reply": reply,
        "history_count": len(history),
        "duration_ms": duration_ms
    }