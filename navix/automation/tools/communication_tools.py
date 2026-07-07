from navix.automation.tools import tool
from loguru import logger
from navix.services.whatsapp.parser import WhatsAppParser

@tool(
    name="whatsapp_send_message", 
    description="Sends a WhatsApp message to a specific contact. (NOTE: WhatsApp runs automatically in the background. DO NOT attempt to open WhatsApp manually before using this tool. Just call this directly.)"
)
async def whatsapp_send_message(contact: str, message: str):
    try:
        from navix.routers import whatsapp as wa_router
        if not wa_router._whatsapp_client or not getattr(wa_router._whatsapp_client, 'sender', None):
            logger.info("Initializing WhatsApp client...")
            await wa_router.start_whatsapp_background()
            
        _whatsapp_client = wa_router._whatsapp_client
        if not _whatsapp_client or not getattr(_whatsapp_client, 'sender', None):
            return "Failed to initialize WhatsApp client."
        success = await _whatsapp_client.send_message(contact, message)
        return "Message sent successfully." if success else f"Failed to send message to {contact}."
    except Exception as e:
        logger.error(f"WhatsApp sender module error: {e}")
        return f"Failed to send WhatsApp message: {e}"
    
@tool(
    name="whatsapp_read_unread", 
    description="Reads all unread WhatsApp messages. (NOTE: WhatsApp runs automatically in the background. DO NOT attempt to open WhatsApp manually before using this tool. Just call this directly.)"
)
async def whatsapp_read_unread(query: str = ""):
    try:
        from navix.routers import whatsapp as wa_router
        if not wa_router._whatsapp_client or not getattr(wa_router._whatsapp_client, 'reader', None):
            logger.info("Initializing WhatsApp client...")
            await wa_router.start_whatsapp_background()
            
        _whatsapp_client = wa_router._whatsapp_client
        if not _whatsapp_client or not getattr(_whatsapp_client, 'reader', None):
            return "Failed to initialize WhatsApp client."
            
        unread_chats = await _whatsapp_client.reader.get_unread_chats()
        if not unread_chats:
            return "No unread messages found."
            
        results = []
        for chat in unread_chats:
            success = await _whatsapp_client.reader.open_chat(chat)
            if success:
                raw_msgs = await _whatsapp_client.reader.get_raw_messages(5)
                chat_msgs = []
                for raw in raw_msgs:
                    parsed = await WhatsAppParser.parse_message(raw, chat)
                    if parsed and parsed.content:
                        chat_msgs.append(f"[{parsed.sender_name}]: {parsed.content}")
                if chat_msgs:
                    results.append(f"--- Chat: {chat} ---\n" + "\n".join(chat_msgs))
                    
        return "\n\n".join(results) if results else "No readable text found in unread chats."
    except Exception as e:
        logger.error(f"WhatsApp reader module error: {e}")
        return f"Failed to read WhatsApp messages: {e}"
