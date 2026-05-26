from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.crypto.encrypt import encrypt, decrypt
from sqlalchemy import select
from loguru import logger
from typing import Any
from app.db.models import Config

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULTS = {
    "default_model":     "llama3",
    "default_system":    "You are a helpful AI assistant.",
    "max_history":       10,
    "chunk_size":        400,
    "chunk_overlap":     50,
    "rag_top_k":         3,
    "stream_enabled":    True,
    "backup_enabled":    True,
    "log_level":         "INFO"
}

CUSTOMER_ID = "system"

class SettingUpdate(BaseModel):
    key: str
    value: Any

@router.get("/all")
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Config).where(Config.customer_id == CUSTOMER_ID)
    )
    rows = result.scalars().all()

    saved = {}
    for row in rows:
        try:
            saved[row.key] = decrypt(row.value)
        except:
            saved[row.key] = {}

    # merge with defaults
    merged = {}
    for key, default_val in DEFAULTS.items():
        if key in saved and "value" in saved[key]:
            merged[key] = saved[key]["value"]
        else:
            merged[key] = default_val

    return {"settings": merged}

@router.post("/update")
async def update_setting(body: SettingUpdate, db: AsyncSession = Depends(get_db)):
    if body.key not in DEFAULTS:
        return {"error": f"Unknown setting: {body.key}. Valid: {list(DEFAULTS.keys())}"}

    encrypted = encrypt({"value": body.value})

    result = await db.execute(
        select(Config).where(
            Config.customer_id == CUSTOMER_ID,
            Config.key == body.key
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.value = encrypted
    else:
        db.add(Config(
            customer_id=CUSTOMER_ID,
            key=body.key,
            value=encrypted
        ))

    await db.commit()
    logger.info(f"Setting updated: {body.key} = {body.value}")
    return {"status": "updated", "key": body.key, "value": body.value}

@router.post("/reset")
async def reset_settings(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete
    await db.execute(
        delete(Config).where(Config.customer_id == CUSTOMER_ID)
    )
    await db.commit()
    return {"status": "reset", "defaults": DEFAULTS}

@router.get("/get/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    if key not in DEFAULTS:
        return {"error": f"Unknown setting: {key}"}

    result = await db.execute(
        select(Config).where(
            Config.customer_id == CUSTOMER_ID,
            Config.key == key
        )
    )
    row = result.scalar_one_or_none()

    if not row:
        return {"key": key, "value": DEFAULTS[key], "source": "default"}

    try:
        data = decrypt(row.value)
        return {"key": key, "value": data["value"], "source": "database"}
    except:
        return {"key": key, "value": DEFAULTS[key], "source": "default"}