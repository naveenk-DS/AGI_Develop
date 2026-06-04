import asyncio
import threading
from loguru import logger
from app.services.voice.NAVIX_AI import start_navix, navix_session
from navix_tray import start_tray, set_tray_state


async def main():
    logger.info("=== NAVIX Starting ===")
    set_tray_state("sleeping")

    await navix_session()

    set_tray_state("listening")
    start_navix()

    logger.info("NAVIX running")
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("NAVIX shutdown")


if __name__ == "__main__":
    # ── Step 1: Create the tray widget IN THE MAIN THREAD.
    #    tkinter requires Tk() and mainloop() to live in the same thread.
    tray = start_tray()

    # ── Step 2: Run the entire asyncio stack in a BACKGROUND daemon thread.
    #    This lets the main thread stay free for the tkinter mainloop.
    def _run_async():
        asyncio.run(main())

    t = threading.Thread(target=_run_async, daemon=True)
    t.start()

    # ── Step 3: Block the MAIN thread with the tkinter mainloop.
    #    Every 60 ms _update_loop drains _state_queue, so set_tray_state()
    #    calls from any thread are applied safely here.
    tray.run()