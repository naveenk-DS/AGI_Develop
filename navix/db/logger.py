from navix.db.models import UsageLog
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

async def log_event(db: AsyncSession, customer_id: str, event_type: str, event_data: dict = {}):
    try:
        entry = UsageLog(
            customer_id=customer_id,
            event_type=event_type,
            event_data=event_data
        )
        db.add(entry)
        await db.commit()
    except Exception as e:
        logger.error(f"Log failed: {e}")
        # never crash the app because of a logging failure