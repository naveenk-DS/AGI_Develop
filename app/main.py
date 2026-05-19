from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger
import sys, os
from app.db.database import engine, Base
from app.db import models  # registers all tables with Base

# Log to file + terminal
logger.remove()
logger.add(sys.stdout, level="INFO")
logger.add("logs/app.log", rotation="10 MB",
           retention="7 days", level="INFO")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables ready")
    logger.info("✅ MyAIProduct API started")
    yield
    await engine.dispose()
    logger.info("API shutdown")

app = FastAPI(
    title="MyAIProduct API",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/chat")
async def chat(body: dict):
    from app.services.ollama import chat as ollama_chat
    reply = await ollama_chat(body.get("message", ""))
    return {"reply": reply}