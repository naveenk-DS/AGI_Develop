import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from playwright.async_api import ElementHandle
from .models import Message, MessageType, Attachment
from .selectors import Selectors

logger = logging.getLogger(__name__)

class WhatsAppParser:
    @staticmethod
    async def parse_message(element: ElementHandle, chat_id: str) -> Optional[Message]:
        try:
            # Generate a pseudo-ID based on content/timestamp if real ID not easily accessible
            html_content = await element.inner_html()
            msg_id = hashlib.md5(html_content.encode('utf-8')).hexdigest()
            
            msg_type = MessageType.UNKNOWN
            content = ""
            attachments = []
            
            # Extract timestamp
            timestamp_str = "Unknown"
            time_elem = await element.query_selector(Selectors.MESSAGE_TIME)
            if time_elem:
                timestamp_str = await time_elem.inner_text()
                
            # Attempt to determine type and extract content
            
            # Text Message
            text_elem = await element.query_selector(Selectors.MESSAGE_TEXT)
            if text_elem:
                content = await text_elem.inner_text()
                msg_type = MessageType.TEXT
                
            # Image Message
            if await element.query_selector(Selectors.IMAGE_CONTAINER):
                msg_type = MessageType.IMAGE
                img_tag = await element.query_selector("img")
                if img_tag:
                    src = await img_tag.get_attribute("src")
                    attachments.append(Attachment(url=src, mime_type="image/*"))
                    
            # Video Message
            elif await element.query_selector(Selectors.VIDEO_CONTAINER):
                msg_type = MessageType.DOCUMENT
                
            # Voice Note
            elif await element.query_selector(Selectors.VOICE_NOTE):
                msg_type = MessageType.VOICE_NOTE
                
            # Sticker
            elif await element.query_selector(Selectors.STICKER):
                msg_type = MessageType.STICKER
                
            # GIF
            elif await element.query_selector(Selectors.GIF):
                msg_type = MessageType.GIF
                
            # Poll
            elif await element.query_selector(Selectors.POLL_CONTAINER):
                msg_type = MessageType.POLL
                
            # Location, Contact, Status handling can be added similarly
            
            # Extract author if group chat
            author_name = chat_id
            author_elem = await element.query_selector(Selectors.AUTHOR_NAME)
            if author_elem:
                author_name = await author_elem.inner_text()
                
            # Only return message if we resolved its type to something or it has text
            if msg_type == MessageType.UNKNOWN and not content:
                return None
                
            return Message(
                id=msg_id,
                chat_id=chat_id,
                sender=author_name,
                sender_name=author_name,
                type=msg_type,
                timestamp=datetime.now(), # Real parsed timestamp could be added if parseable
                content=content,
                attachments=attachments,
                is_from_me=False # Parser only processes IN messages based on reader logic
            )
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None
