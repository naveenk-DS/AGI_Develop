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
from app.routers import analytics
from app.routers import settings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.services.health_monitor import start_health_monitor
from app.services.ollama import preload_model


from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

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

    asyncio.create_task(preload_model("llama3"))
    logger.info("Model preload started")
    asyncio.create_task(start_health_monitor(interval=60))
    logger.info("Health monitor started")

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
app.include_router(analytics.router)
app.include_router(settings.router)
app.state.limiter = Limiter(key_func=get_remote_address)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)



@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/chat")
async def chat(body: dict):
    from app.services.ollama import chat as ollama_chat
    reply = await ollama_chat(body.get("message", ""))
    return {"reply": reply}




