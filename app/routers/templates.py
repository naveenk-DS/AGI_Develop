from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models import PromptTemplate
from app.services.ollama import chat as ollama_chat
from app.db.memory import get_history, save_message
from loguru import logger
from typing import Optional

router = APIRouter(prefix="/templates", tags=["templates"])

class TemplateCreate(BaseModel):
    name: str
    description: str = ""
    system: str
    user_prefix: str = ""
    user_suffix: str = ""
    model: str = "llama3"

class TemplateRun(BaseModel):
    template_name: str
    message: str
    session_id: str = "default"

@router.post("/create")
async def create_template(body: TemplateCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(PromptTemplate).where(PromptTemplate.name == body.name)
    )
    row = existing.scalar_one_or_none()

    if row:
        row.description = body.description
        row.system      = body.system
        row.user_prefix = body.user_prefix
        row.user_suffix = body.user_suffix
        row.model       = body.model
    else:
        db.add(PromptTemplate(
            name=body.name,
            description=body.description,
            system=body.system,
            user_prefix=body.user_prefix,
            user_suffix=body.user_suffix,
            model=body.model
        ))

    await db.commit()
    logger.info(f"Template saved: {body.name}")
    return {"status": "saved", "name": body.name}

@router.get("/list")
async def list_templates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PromptTemplate).order_by(PromptTemplate.name))
    templates = result.scalars().all()
    return {
        "templates": [
            {
                "name": t.name,
                "description": t.description,
                "model": t.model,
                "created_at": str(t.created_at)
            }
            for t in templates
        ],
        "count": len(templates)
    }

@router.get("/get/{name}")
async def get_template(name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.name == name)
    )
    t = result.scalar_one_or_none()
    if not t:
        return {"error": f"Template not found: {name}"}
    return {
        "name": t.name,
        "description": t.description,
        "system": t.system,
        "user_prefix": t.user_prefix,
        "user_suffix": t.user_suffix,
        "model": t.model
    }

@router.post("/run")
async def run_template(body: TemplateRun, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.name == body.template_name)
    )
    t = result.scalar_one_or_none()
    if not t:
        return {"error": f"Template not found: {body.template_name}"}

    history = await get_history(db, body.session_id)

    full_message = f"{t.user_prefix}{body.message}{t.user_suffix}".strip()

    reply = await ollama_chat(
        prompt=full_message,
        model=t.model,
        system=t.system,
        history=history
    )

    await save_message(db, body.session_id, "user", body.message)
    await save_message(db, body.session_id, "assistant", reply)

    return {
        "template": body.template_name,
        "message": body.message,
        "reply": reply,
        "model": t.model
    }

@router.delete("/delete/{name}")
async def delete_template(name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PromptTemplate).where(PromptTemplate.name == name)
    )
    t = result.scalar_one_or_none()
    if not t:
        return {"error": "Template not found"}
    await db.delete(t)
    await db.commit()
    return {"status": "deleted", "name": name}