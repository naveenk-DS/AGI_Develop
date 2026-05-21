from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import Config
from app.crypto.encrypt import encrypt, decrypt
from loguru import logger

router = APIRouter(prefix="/configs", tags=["configs"])

class ConfigSet(BaseModel):
    customer_id: str
    key: str
    value: dict

class ConfigGet(BaseModel):
    customer_id: str
    key: str

@router.post("/set")
async def set_config(body: ConfigSet, db: AsyncSession = Depends(get_db)):
    encrypted = encrypt(body.value)

    result = await db.execute(
        select(Config).where(
            Config.customer_id == body.customer_id,
            Config.key == body.key
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.value = encrypted
    else:
        db.add(Config(
            customer_id=body.customer_id,
            key=body.key,
            value=encrypted
        ))

    await db.commit()
    logger.info(f"Config saved: {body.customer_id}/{body.key}")
    return {"status": "saved"}

@router.get("/get/{customer_id}/{key}")
async def get_config(customer_id: str, key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Config).where(
            Config.customer_id == customer_id,
            Config.key == key
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        return {"value": None}
    return {"value": decrypt(row.value)}