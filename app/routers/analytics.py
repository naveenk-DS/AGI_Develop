from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.db.database import get_db
from app.models import UsageLog, Conversation
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    since_24h = datetime.utcnow() - timedelta(hours=24)
    since_7d  = datetime.utcnow() - timedelta(days=7)

    total_events = await db.execute(select(func.count(UsageLog.id)))
    events_24h   = await db.execute(
        select(func.count(UsageLog.id))
        .where(UsageLog.created_at >= since_24h)
    )
    events_7d    = await db.execute(
        select(func.count(UsageLog.id))
        .where(UsageLog.created_at >= since_7d)
    )
    total_msgs   = await db.execute(select(func.count(Conversation.id)))
    total_sessions = await db.execute(
        select(func.count(func.distinct(Conversation.session_id)))
    )

    return {
        "total_events":    total_events.scalar(),
        "events_last_24h": events_24h.scalar(),
        "events_last_7d":  events_7d.scalar(),
        "total_messages":  total_msgs.scalar(),
        "total_sessions":  total_sessions.scalar()
    }

@router.get("/tools")
async def tool_usage(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            UsageLog.event_type,
            func.count(UsageLog.id).label("count")
        )
        .group_by(UsageLog.event_type)
        .order_by(func.count(UsageLog.id).desc())
    )
    rows = result.all()
    return {
        "tool_usage": [
            {"event_type": r.event_type, "count": r.count}
            for r in rows
        ]
    }

@router.get("/daily")
async def daily_usage(days: int = 7, db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date_trunc("day", UsageLog.created_at).label("day"),
            func.count(UsageLog.id).label("count")
        )
        .where(UsageLog.created_at >= since)
        .group_by(text("day"))
        .order_by(text("day ASC"))
    )
    rows = result.all()
    return {
        "daily": [
            {"day": str(r.day)[:10], "count": r.count}
            for r in rows
        ],
        "days": days
    }

@router.get("/top-sessions")
async def top_sessions(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Conversation.session_id,
            func.count(Conversation.id).label("message_count"),
            func.max(Conversation.created_at).label("last_active")
        )
        .group_by(Conversation.session_id)
        .order_by(func.count(Conversation.id).desc())
        .limit(limit)
    )
    rows = result.all()
    return {
        "top_sessions": [
            {
                "session_id": r.session_id,
                "message_count": r.message_count,
                "last_active": str(r.last_active)
            }
            for r in rows
        ]
    }

@router.get("/response-times")
async def response_times(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UsageLog.event_data)
        .where(UsageLog.event_type.in_(["chat", "agent_run", "stream_chat"]))
        .order_by(UsageLog.created_at.desc())
        .limit(100)
    )
    rows = result.scalars().all()

    times = []
    for row in rows:
        if row and "duration_ms" in row:
            times.append(row["duration_ms"])

    if not times:
        return {"avg_ms": 0, "min_ms": 0, "max_ms": 0, "samples": 0}

    return {
        "avg_ms":  round(sum(times) / len(times)),
        "min_ms":  min(times),
        "max_ms":  max(times),
        "samples": len(times)
    }

@router.get("/errors")
async def error_log(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.event_type == "error")
        .order_by(UsageLog.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return {
        "errors": [
            {
                "customer_id": r.customer_id,
                "event_data":  r.event_data,
                "created_at":  str(r.created_at)
            }
            for r in rows
        ],
        "count": len(rows)
    }

@router.get("/rate-limits")
async def rate_limits():
    return {
        "limits": {
            "chat_message": "30 per minute",
            "agent_run": "20 per minute",
            "rag_ingest": "10 per minute",
            "general": "unlimited"
        },
        "note": "Limits are per IP address"
    }

@router.get("/errors/recent")
async def recent_errors(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UsageLog)
        .where(UsageLog.event_type == "error")
        .order_by(UsageLog.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return {
        "errors": [
            {
                "path": r.event_data.get("path") if r.event_data else None,
                "error": r.event_data.get("error") if r.event_data else None,
                "created_at": str(r.created_at)
            }
            for r in rows
        ],
        "count": len(rows)
    }