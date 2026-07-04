from navix.automation.tools import tool
from loguru import logger

# Note: In Phase 2, we wrap the existing WhatsApp features. 
# Depending on the whatsapp parser implementation, we map them here.

@tool(
    name="whatsapp_send_message", 
    description="Sends a WhatsApp message to a specific contact."
)
async def whatsapp_send_message(contact: str, message: str):
    try:
        from navix.services.whatsapp.sender import send_whatsapp_message
        return await send_whatsapp_message(contact, message)
    except ImportError:
        logger.error("WhatsApp sender module not found.")
        return "Failed to import WhatsApp sender."
    
@tool(
    name="whatsapp_read_unread", 
    description="Reads all unread WhatsApp messages."
)
async def whatsapp_read_unread(query: str = ""):
    try:
        from navix.services.whatsapp.reader import get_unread_messages
        return await get_unread_messages()
    except ImportError:
        logger.error("WhatsApp reader module not found.")
        return "Failed to import WhatsApp reader."
