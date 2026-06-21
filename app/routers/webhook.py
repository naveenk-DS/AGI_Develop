from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from core.graph import get_graph
from app.services.personal_memory import get_context_for_ai
from app.db.memory import get_history, save_message
from app.db.logger import log_event
from loguru import logger
import os

router = APIRouter(prefix="/webhook", tags=["webhook"])

WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY", "")

def verify_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != WEBHOOK_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

class WebhookRequest(BaseModel):
    session_id: str = "webhook-default"
    message: str
    source: str = "webhook"

@router.post("/chat")
async def webhook_chat(
    body: WebhookRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_key)
):
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

    await save_message(db, body.session_id, "user", body.message)
    await save_message(db, body.session_id, "assistant", answer)

    await log_event(db, body.session_id, "webhook_chat", {
        "source": body.source,
        "tool_used": result["tool"]
    })

    return {
        "session_id": body.session_id,
        "reply": answer,
        "tool_used": result["tool"]
    }

@router.get("/test")
async def webhook_test(api_key: str = Depends(verify_key)):
    return {"status": "webhook authenticated", "message": "API key is valid"}
