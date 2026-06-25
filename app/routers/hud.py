"""
app/routers/hud.py
──────────────────
Lightweight HUD event bridge.
- NAVIX voice AI pushes events here via post_hud_event()
- The web HUD polls GET /hud/latest to show live Q&A
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/hud", tags=["HUD"])

# In-memory store for latest interaction
_latest: dict = {
    "question": "",
    "answer":   "",
    "state":    "ready",   # ready | listening | thinking | speaking
}


class HUDEvent(BaseModel):
    question: Optional[str] = None
    answer:   Optional[str] = None
    state:    Optional[str] = None


@router.get("/latest")
async def get_latest():
    """Web HUD polls this to show live conversation."""
    return _latest


@router.post("/event")
async def post_event(ev: HUDEvent):
    """NAVIX voice AI calls this to push updates to the web HUD."""
    if ev.question is not None: _latest["question"] = ev.question
    if ev.answer   is not None: _latest["answer"]   = ev.answer
    if ev.state    is not None: _latest["state"]     = ev.state
    return {"ok": True}


# ── Convenience helper (called from NAVIX_AI.py) ────────────────────────────
import httpx, asyncio

_HUD_URL = "http://127.0.0.1:8001/hud/event"

def push_hud(question: str = None, answer: str = None, state: str = None):
    """
    Fire-and-forget helper. Call from any thread in navix_start.py / NAVIX_AI.py.
    Example:
        from app.routers.hud import push_hud
        push_hud(question="What is AI?", state="thinking")
        push_hud(answer="AI is ...", state="speaking")
    """
    payload = {}
    if question is not None: payload["question"] = question
    if answer   is not None: payload["answer"]   = answer
    if state    is not None: payload["state"]    = state
    try:
        # Non-blocking: run in background thread
        import threading
        def _post():
            try:
                import urllib.request, json
                data = json.dumps(payload).encode()
                req  = urllib.request.Request(_HUD_URL, data=data,
                                              headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=2)
            except Exception:
                pass
        threading.Thread(target=_post, daemon=True).start()
    except Exception:
        pass
