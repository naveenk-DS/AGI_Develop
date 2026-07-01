from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, distinct
from navix.db.database import get_db
from navix.db.models import Conversation, UsageLog
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("/list")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Conversation.session_id,
            func.count(Conversation.id).label("message_count"),
            func.max(Conversation.created_at).label("last_active"),
            func.min(Conversation.created_at).label("started_at")
        ).group_by(Conversation.session_id)
        .order_by(func.max(Conversation.created_at).desc())
    )
    rows = result.all()
    return {
        "sessions": [
            {
                "session_id": r.session_id,
                "message_count": r.message_count,
                "last_active": str(r.last_active),
                "started_at": str(r.started_at)
            }
            for r in rows
        ],
        "total": len(rows)
    }

@router.get("/get/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.created_at.asc())
    )
    messages = result.scalars().all()
    if not messages:
        return {"error": "Session not found"}
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_at": str(m.created_at)
            }
            for m in messages
        ]
    }

@router.delete("/delete/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    await db.execute(
        delete(Conversation).where(Conversation.session_id == session_id)
    )
    await db.commit()
    logger.info(f"Session deleted: {session_id}")
    return {"status": "deleted", "session_id": session_id}

@router.delete("/cleanup")
async def cleanup_old_sessions(days: int = 7, db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(distinct(Conversation.session_id))
        .where(Conversation.created_at < cutoff)
    )
    old_sessions = result.scalars().all()

    if old_sessions:
        await db.execute(
            delete(Conversation).where(Conversation.session_id.in_(old_sessions))
        )
        await db.commit()

    logger.info(f"Cleaned up {len(old_sessions)} old sessions older than {days} days")
    return {
        "status": "cleaned",
        "sessions_deleted": len(old_sessions),
        "older_than_days": days
    }

@router.get("/stats")
async def session_stats(db: AsyncSession = Depends(get_db)):
    total_sessions = await db.execute(
        select(func.count(distinct(Conversation.session_id)))
    )
    total_messages = await db.execute(
        select(func.count(Conversation.id))
    )
    return {
        "total_sessions": total_sessions.scalar(),
        "total_messages": total_messages.scalar()
    }