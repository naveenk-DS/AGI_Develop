import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger
import sys, os
from navix.db.database import engine, Base
from navix.db import models  # registers all tables with Base
from navix.routers import rag
from navix.routers import chat
from navix.routers import summary
from navix.routers import configs #from navix.routers import configs
from navix.routers import licenses
from navix.routers import dashboard
from navix.routers import agent
from navix.routers import backup
from navix.routers import templates
from navix.routers import sessions
from navix.routers import stream
from navix.routers import webhook
from navix.middleware.auth import APIKeyMiddleware
from navix.routers import analytics
from navix.routers import settings
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from navix.services.utilities.health_monitor import start_health_monitor
from navix.services.ai.ollama import preload_model
from navix.routers import voice_routes
from navix.routers import browser_routes
from navix.routers import desktop_routes
from navix.routers import agent_routes
from navix.routers import memory_routes
from navix.routers import hud
from navix.routers import whatsapp
# from core.mcp_tools import register_all_tools


from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from navix.middleware.error_handler import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

import asyncio
from concurrent.futures import ThreadPoolExecutor

from navix.config.settings import config, setup_logging

# Apply centralized structured logging
setup_logging()

# add at top of main.py
executor = ThreadPoolExecutor(max_workers=1)


# preload all AI models on startup — defined BEFORE lifespan so it can be referenced
async def preload_models():
    try:
        from core.llm import get_llm, get_embeddings
        from core.graph import get_graph
        from core.emotion import get_emotion_classifier

        logger.info("Preloading LLM...")
        get_llm()

        logger.info("Preloading embeddings...")
        get_embeddings()

        logger.info("Preloading graph...")
        await get_graph()

        logger.info("Preloading emotion model...")
        get_emotion_classifier()

        logger.info("All models preloaded")
    except Exception as e:
        logger.warning(f"Preload warning: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")

    from navix.services.utilities.watcher import start_watcher
    loop = asyncio.get_event_loop()
    loop.run_in_executor(executor, start_watcher)
    logger.info("File watcher started")

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from navix.services.utilities.backup import run_backup
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_backup, "cron", hour=3, minute=0)
    scheduler.start()
    logger.info("Scheduler started")

    # start continual learning
    from navix.services.ai.continual_learning import watch_and_learn
    asyncio.create_task(watch_and_learn())
    logger.info("Continual learning started")

    from core.mcp_tools import register_all_tools
    register_all_tools()
    logger.info("MCP tools registered")

    asyncio.create_task(preload_models())
    logger.info("Model preload started")

    asyncio.create_task(start_health_monitor(interval=60))
    logger.info("Health monitor started")



    logger.info("MyAIProduct API started")
    yield

    scheduler.shutdown()
    from navix.services.utilities.watcher import stop_event
    stop_event.set()
    executor.shutdown(wait=True)
    await engine.dispose()
    logger.info("API shutdown")


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AGI_Develop_From_Scratch",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(voice_routes.router)
app.include_router(browser_routes.router)
app.include_router(desktop_routes.router)
app.include_router(agent_routes.router)
app.include_router(memory_routes.router)
app.include_router(hud.router)
app.include_router(whatsapp.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/chat")
async def chat(body: dict):
    from navix.services.ai.ollama import chat as ollama_chat
    reply = await ollama_chat(body.get("message", ""))
    return {"reply": reply}




