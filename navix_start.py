import asyncio
from loguru import logger
from app.services.voice.NAVIX_AI import start_navix, navix_session

async def main():
    logger.info("=== NAVIX Starting ===")
    await navix_session()
    start_navix()
    logger.info("NAVIX running — press Ctrl+C to stop")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("NAVIX shutdown")

if __name__ == "__main__":
    asyncio.run(main())