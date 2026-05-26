from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.db.models import License
from app.crypto.encrypt import get_machine_id
from datetime import datetime
from loguru import logger

router = APIRouter(prefix="/license", tags=["license"])

class ActivateRequest(BaseModel):
    license_key: str

class LicenseCreate(BaseModel):
    license_key: str
    plan: str = "starter"

@router.post("/activate")
async def activate(body: ActivateRequest, db: AsyncSession = Depends(get_db)):
    machine_id = get_machine_id()

    result = await db.execute(
        select(License).where(License.license_key == body.license_key)
    )
    lic = result.scalar_one_or_none()

    if not lic:
        return {"valid": False, "reason": "License key not found"}

    if not lic.is_active:
        return {"valid": False, "reason": "License deactivated"}

    if lic.expires_at and lic.expires_at < datetime.utcnow():
        return {"valid": False, "reason": "License expired"}

    if lic.machine_id and lic.machine_id != machine_id:
        return {"valid": False, "reason": "License bound to another machine"}

    # bind to this machine on first use
    if not lic.machine_id:
        lic.machine_id = machine_id
        lic.activated_at = datetime.utcnow()
        await db.commit()
        logger.info(f"License {body.license_key} activated on machine {machine_id[:8]}...")

    return {"valid": True, "plan": lic.plan, "message": "License valid"}

@router.post("/create")
async def create_license(body: LicenseCreate, db: AsyncSession = Depends(get_db)):
    # this endpoint is for YOU only — to generate keys for customers
    existing = await db.execute(
        select(License).where(License.license_key == body.license_key)
    )
    if existing.scalar_one_or_none():
        return {"status": "already exists"}

    db.add(License(
        license_key=body.license_key,
        plan=body.plan,
        is_active=True
    ))
    await db.commit()
    return {"status": "created", "key": body.license_key, "plan": body.plan}

@router.get("/status")
async def license_status(db: AsyncSession = Depends(get_db)):
    machine_id = get_machine_id()
    result = await db.execute(
        select(License)
        .where(License.machine_id == machine_id)
        .limit(1)
    )
    lic = result.scalar_one_or_none()
    if not lic:
        return {"status": "no license activated on this machine"}
    return {
        "status": "active" if lic.is_active else "inactive",
        "plan": lic.plan,
        "activated_at": str(lic.activated_at),
        "expires_at": str(lic.expires_at)
    }