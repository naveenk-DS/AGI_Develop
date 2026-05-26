from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger
import sys, os
from app.db.database import engine, Base
from app.db import models  # registers all tables with Base
from app.routers import rag
from app.routers import chat
from app.routers import summary
from app.routers import configs #from app.routers import configs
from app.routers import licenses
from app.routers import dashboard
from app.routers import agent
from app.routers import backup
from app.routers import templates
from app.routers import sessions
from app.routers import stream
from app.routers import webhook
from app.middleware.auth import APIKeyMiddleware

import asyncio
from concurrent.futures import ThreadPoolExecutor

# Log to file + terminal
logger.remove()
sys.stdout.reconfigure(encoding='utf-8')
logger.add(sys.stdout, level="INFO")
logger.add("logs/app.log", rotation="10 MB",
           retention="7 days", level="INFO")

# add at top of main.py
executor = ThreadPoolExecutor(max_workers=1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")

    # start file watcher in background thread
    from app.services.watcher import start_watcher
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, start_watcher)
    logger.info("File watcher started")

    logger.info("MyAIProduct API started")
    yield
    from app.services.watcher import stop_event
    stop_event.set()
    executor.shutdown(wait=True)
    await engine.dispose()
    logger.info("API shutdown")

app = FastAPI(
    title="AGI_Develop_From_Scartch",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(rag.router)
app.include_router(chat.router)
app.include_router(summary.router)
app.include_router(configs.router)
app.include_router(licenses.router)
app.include_router(dashboard.router)
app.include_router(agent.router)
app.include_router(backup.router)
app.include_router(templates.router)
app.include_router(sessions.router)
app.include_router(stream.router)
app.include_router(webhook.router)



@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/chat")
async def chat(body: dict):
    from app.services.ollama import chat as ollama_chat
    reply = await ollama_chat(body.get("message", ""))
    return {"reply": reply}




