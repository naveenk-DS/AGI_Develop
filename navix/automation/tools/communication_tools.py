from navix.automation.tools import tool
from loguru import logger
from navix.services.whatsapp.parser import WhatsAppParser

@tool(
    name="whatsapp_send_message", 
    description="Sends a WhatsApp message to a specific contact. (NOTE: WhatsApp runs automatically in the background. DO NOT attempt to open WhatsApp manually before using this tool. Just call this directly.)"
)
async def whatsapp_send_message(contact: str, message: str):
    try:
        from navix.routers.whatsapp import _whatsapp_client
        if not _whatsapp_client or not _whatsapp_client.sender:
            return "WhatsApp client or sender module is not initialized. Please ensure the background service is active and fully started."
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
        from navix.routers.whatsapp import _whatsapp_client
        if not _whatsapp_client or not _whatsapp_client.reader:
            return "WhatsApp client or reader module is not initialized. Please ensure the background service is active and fully started."
            
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
