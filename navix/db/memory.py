from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from navix.db.models import Conversation
from loguru import logger

async def save_message(db: AsyncSession, session_id: str, role: str, content: str):
    msg = Conversation(
        session_id=session_id,
        role=role,
        content=content
    )
    db.add(msg)
    await db.commit()

async def get_history(db: AsyncSession, session_id: str, last_n: int = 10) -> list[dict]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.created_at.desc())
        .limit(last_n)
    )
    rows = result.scalars().all()
    # reverse so oldest first
    rows = list(reversed(rows))
    return [{"role": r.role, "content": r.content} for r in rows]

async def clear_history(db: AsyncSession, session_id: str):
    from sqlalchemy import delete
    await db.execute(
        delete(Conversation).where(Conversation.session_id == session_id)
    )
    await db.commit()
    logger.info(f"Cleared history for session: {session_id}")
