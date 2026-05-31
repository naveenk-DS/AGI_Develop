import asyncio
from datetime import datetime
from loguru import logger
from app.services.voice.speaker import speak

reminders = []

async def add_reminder(message: str, hour: int, minute: int = 0):
    reminders.append({
        "message": message,
        "hour": hour,
        "minute": minute,
        "done": False
    })
    logger.info(f"Reminder added: {message} at {hour}:{minute:02d}")

async def start_reminder_loop():
    logger.info("Reminder loop started")
    while True:
        now = datetime.now()
        for r in reminders:
            if (not r["done"] and
                r["hour"] == now.hour and
                r["minute"] == now.minute):
                speak(f"Reminder: {r['message']}")
                r["done"] = True
                logger.info(f"Reminder fired: {r['message']}")
        await asyncio.sleep(30)