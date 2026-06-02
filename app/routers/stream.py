from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.ollama import chat_stream, chat as ollama_chat
from app.db.memory import get_history, save_message
from app.db.logger import log_event
from loguru import logger
import time

router = APIRouter(prefix="/stream", tags=["stream"])

class StreamRequest(BaseModel):
    session_id: str
    message: str
    system: str = "You are a helpful AI assistant."
    model: str = "llama3"

@router.post("/chat")
async def stream_chat(body: StreamRequest, db: AsyncSession = Depends(get_db)):
    history = await get_history(db, body.session_id)
    full_reply = []

    async def generate():
        async for token in chat_stream(
            prompt=body.message,
            model=body.model,
            system=body.system,
            history=history
        ):
            full_reply.append(token)
            yield token

    async def generate_and_save():
        async for token in chat_stream(
            prompt=body.message,
            model=body.model,
            system=body.system,
            history=history
        ):
            full_reply.append(token)
            yield token

        # save to memory after streaming complete
        complete_reply = "".join(full_reply)
        await save_message(db, body.session_id, "user", body.message)
        await save_message(db, body.session_id, "assistant", complete_reply)
        await log_event(db, body.session_id, "stream_chat", {
            "message_length": len(body.message),
            "reply_length": len(complete_reply)
        })

    return StreamingResponse(
        generate_and_save(),
        media_type="text/plain"
    )

@router.post("/agent")
async def stream_agent(body: StreamRequest, db: AsyncSession = Depends(get_db)):
    history = await get_history(db, body.session_id)

    # Simple tool routing matching core.graph.router_node logic
    msg = body.message.lower()
    if any(w in msg for w in ["document", "file", "pdf", "what does", "according to"]):
        tool = "rag"
    elif any(w in msg for w in ["open", "search", "youtube", "google", "browser"]):
        tool = "browser"
    else:
        tool = "chat"

    full_reply = []

    async def generate():
        async for token in chat_stream(
            prompt=body.message,
            model=body.model,
            system=body.system,
            history=history
        ):
            full_reply.append(token)
            yield token

        complete_reply = "".join(full_reply)
        await save_message(db, body.session_id, "user", body.message)
        await save_message(db, body.session_id, "assistant", complete_reply)
        await log_event(db, body.session_id, "stream_agent", {
            "tool_used": tool,
            "reply_length": len(complete_reply)
        })

    return StreamingResponse(generate(), media_type="text/plain")
