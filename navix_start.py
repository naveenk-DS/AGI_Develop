import asyncio
import threading
from loguru import logger
from app.services.voice.NAVIX_AI import start_navix, navix_session
from navix_tray import start_tray, set_tray_state

async def main():
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

def _run_async():
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    tray = start_tray()

    t = threading.Thread(target=_run_async, daemon=True)
    t.start()

    # protect mainloop from spurious KeyboardInterrupt on Windows
    while True:
        try:
            tray.run()
            break
        except KeyboardInterrupt:
            logger.warning("Spurious KeyboardInterrupt caught in tray — resuming")
            continue