from datetime import datetime, date
from sqlalchemy import select, delete
from loguru import logger
from app.db.database import AsyncSessionLocal
from app.models import UsageLog

async def save_daily_plan(plan: str, customer_id: str = "naveen"):
    async with AsyncSessionLocal() as db:
        db.add(UsageLog(
            customer_id=customer_id,
            event_type="daily_plan",
            event_data={
                "plan": plan,
                "date": str(date.today()),
                "created_at": datetime.utcnow().isoformat()
            }
        ))
        await db.commit()
    logger.info(f"Plan saved: {plan[:50]}")

async def get_todays_plan(customer_id: str = "naveen") -> str:
    today = str(date.today())
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UsageLog)
            .where(
                UsageLog.customer_id == customer_id,
                UsageLog.event_type == "daily_plan"
            )
            .order_by(UsageLog.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row and row.event_data:
            if row.event_data.get("date") == today:
                return row.event_data.get("plan", "")
    return ""

async def save_completed(completed: str, customer_id: str = "naveen"):
    async with AsyncSessionLocal() as db:
        db.add(UsageLog(
            customer_id=customer_id,
            event_type="daily_completed",
            event_data={
                "completed": completed,
                "date": str(date.today()),
                "created_at": datetime.utcnow().isoformat()
            }
        ))
        await db.commit()
    logger.info(f"Completed saved: {completed[:50]}")

async def get_weekly_summary(customer_id: str = "naveen") -> list:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UsageLog)
            .where(
                UsageLog.customer_id == customer_id,
                UsageLog.event_type.in_(["daily_plan", "daily_completed"])
            )
            .order_by(UsageLog.created_at.desc())
            .limit(14)
        )
        rows = result.scalars().all()
        return [
            {
                "type": r.event_type,
                "data": r.event_data,
                "date": str(r.created_at)
            }
            for r in rows
        ]