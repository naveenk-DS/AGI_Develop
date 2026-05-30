import os
import asyncio
from loguru import logger

# Ensure ffmpeg is in PATH for Whisper
ffmpeg_path = r"F:\naveen\AGI_Start\ffmpeg\ffmpeg-master-latest-win64-gpl\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + ffmpeg_path

from app.services.voice.NAVIX_AI import start_navix, navix_session

async def main():
    logger.info("=== NAVIX Starting ===")
    
    # startup greeting
    await navix_session()
    
    # start wake word listener
    start_navix()
    
    # keep running
    logger.info("NAVIX running — press Ctrl+C to stop")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("NAVIX shutdown")

if __name__ == "__main__":
    asyncio.run(main())