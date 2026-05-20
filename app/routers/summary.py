from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.db.models import UsageLog, Conversation
from app.services.ollama import chat as ollama_chat
from app.db.logger import log_event
from datetime import datetime, timedelta

router = APIRouter(prefix="/summary", tags=["summary"])

@router.post("/daily")
async def daily_summary(db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=24)

    # count events in last 24 hours
    result = await db.execute(
        select(func.count(UsageLog.id))
        .where(UsageLog.created_at >= since)
    )
    total_events = result.scalar()

    # count conversations
    conv_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.created_at >= since)
    )
    total_messages = conv_result.scalar()

    prompt = f"""Generate a short daily summary report for an AI product.
Stats from last 24 hours:
- Total events: {total_events}
- Total chat messages: {total_messages}

Write 3 sentences: what happened, what looks good, what to watch."""

    summary = await ollama_chat(prompt)

    await log_event(db, "system", "daily_summary", {
        "summary": summary,
        "total_events": total_events,
        "total_messages": total_messages
    })

    return {
        "date": datetime.utcnow().isoformat(),
        "summary": summary,
        "stats": {
            "total_events": total_events,
            "total_messages": total_messages
        }
    }