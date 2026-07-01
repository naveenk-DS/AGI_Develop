import asyncio
import logging
from typing import List, Dict, Any
from fastapi import APIRouter
from navix.services.whatsapp import WhatsAppClient, Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# A global queue to hold messages until the HUD fetches them
message_queue: List[Dict[str, Any]] = []
_whatsapp_client = None

async def handle_new_message(msg: Message):
    logger.info(f"WhatsApp API received message from {msg.sender_name}: {msg.content}")
    message_queue.append({
        "id": msg.id,
        "chat_id": msg.chat_id,
        "sender": msg.sender,
        "sender_name": msg.sender_name,
        "type": msg.type.name if hasattr(msg.type, 'name') else str(msg.type),
        "timestamp": msg.timestamp.isoformat(),
        "content": msg.content
    })

async def start_whatsapp_background():
    global _whatsapp_client
    if _whatsapp_client is None:
        logger.info("Starting background WhatsApp Client for API...")
        _whatsapp_client = WhatsAppClient(session_dir="./whatsapp_session", headless=True)
        _whatsapp_client.on_message(handle_new_message)
        await _whatsapp_client.start()

async def stop_whatsapp_background():
    global _whatsapp_client
    if _whatsapp_client:
        await _whatsapp_client.stop()

@router.get("/events")
async def get_whatsapp_events():
    """Endpoint polled by the HUD to get new messages."""
    global message_queue
    if not message_queue:
        return []
    
    # Return current queue and clear it
    events_to_return = message_queue.copy()
    message_queue.clear()
    return events_to_return
