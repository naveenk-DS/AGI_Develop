from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent.parent / "config" / ".env")

WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY", "")

# routes that require API key
PROTECTED_PREFIXES = ["/webhook"]

# routes always open
PUBLIC_ROUTES = [
    "/health",
    "/docs",
    "/openapi.json",
    "/dashboard",
    "/redoc"
]

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # always allow public routes
        for pub in PUBLIC_ROUTES:
            if path.startswith(pub):
                return await call_next(request)

        # check protected routes
        for protected in PROTECTED_PREFIXES:
            if path.startswith(protected):
                api_key = (
                    request.headers.get("X-API-Key") or
                    request.query_params.get("api_key")
                )
                if not api_key or api_key != WEBHOOK_API_KEY:
                    return JSONResponse(
                        status_code=401,
                        content={"error": "Invalid or missing API key"}
                    )

        return await call_next(request)