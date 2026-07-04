import asyncio
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from loguru import logger
from navix.services.voice.NAVIX_AI import start_navix, navix_session
from navix_tray import start_tray, set_tray_state

_main_loop = None
HUD_PORT   = 5500
HUD_DIR    = Path(__file__).parent / "navix_hud_ui"


def _start_hud_server():
    """Serve the web HUD on localhost:HUD_PORT in a daemon thread."""
    class _Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(HUD_DIR), **kw)
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            super().end_headers()
        def log_message(self, *_): pass  # suppress access logs

    try:
        srv = HTTPServer(('127.0.0.1', HUD_PORT), _Handler)
        logger.info(f"HUD server → http://localhost:{HUD_PORT}")
        srv.serve_forever()
    except OSError:
        logger.warning(f"HUD server port {HUD_PORT} already in use — skipping.")


def launch_hud():
    """Start HTTP server + open browser."""
    t = threading.Thread(target=_start_hud_server, daemon=True)
    t.start()
    # Small delay so server is ready before browser opens
    threading.Timer(0.8, webbrowser.open, args=(f"http://localhost:{HUD_PORT}",)).start()


async def main():
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    logger.info("=== NAVIX Starting ===")
    set_tray_state("sleeping")
    try:
        await navix_session()
    except Exception as e:
        logger.error(f"Session error: {e}")
    set_tray_state("sleeping")
    try:
        start_navix()
    except Exception as e:
        logger.error(f"Start error: {e}")
    logger.info("NAVIX running — say Naveen to activate")
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("NAVIX shutdown")

def get_main_loop():
    return _main_loop

def _run_async():
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")

def _start_api_server():
    import uvicorn
    # Start the backend API on port 8001 so the HUD can poll it
    uvicorn.run("navix.main:app", host="127.0.0.1", port=8001, log_level="warning")

if __name__ == "__main__":
    # Start the API server in background
    api_t = threading.Thread(target=_start_api_server, daemon=True)
    api_t.start()
    
    launch_hud()          # ← open HUD in browser first
    tray = start_tray()
    t = threading.Thread(target=_run_async, daemon=True)
    t.start()
    while True:
        try:
            tray.run()
            break
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt caught — shutting down NAVIX")
            import sys
            sys.exit(0)