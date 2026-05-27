from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.db.logger import log_event
from loguru import logger
import traceback

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Invalid request data",
            "details": exc.errors(),
            "path": str(request.url.path)
        }
    )

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    tb = traceback.format_exc()
    logger.error(f"Unhandled error on {request.url.path}: {error_msg}\n{tb}")

    # try to log to database
    try:
        from app.db.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await log_event(db, "system", "error", {
                "path": str(request.url.path),
                "method": request.method,
                "error": error_msg,
                "traceback": tb[:500]
            })
    except Exception as log_err:
        logger.error(f"Could not log error to DB: {log_err}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Something went wrong. Please try again.",
            "path": str(request.url.path)
        }
    )