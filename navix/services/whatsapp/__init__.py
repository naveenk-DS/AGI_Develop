import asyncio
import logging
from typing import Callable, Awaitable, Optional

from .browser import WhatsAppBrowser
from .reader import WhatsAppReader
from .parser import WhatsAppParser
from .sender import WhatsAppSender
from .listener import WhatsAppListener
from .models import Message, MessageType, Attachment, Chat
from .exceptions import WhatsAppError, WhatsAppNotAuthenticatedError, MessageSendError

logger = logging.getLogger(__name__)

class WhatsAppClient:
    def __init__(self, session_dir: str = "./whatsapp_session", headless: bool = False, poll_interval: float = 2.0):
        self.browser = WhatsAppBrowser(user_data_dir=session_dir, headless=headless)
        self.reader: Optional[WhatsAppReader] = None
        self.sender: Optional[WhatsAppSender] = None
        self.listener: Optional[WhatsAppListener] = None
        self.poll_interval = poll_interval

    async def start(self):
        """Starts the WhatsApp client and underlying browser session."""
        await self.browser.start()
        page = self.browser.get_page
        
        self.reader = WhatsAppReader(page)
        self.sender = WhatsAppSender(page)
        self.listener = WhatsAppListener(self.browser, self.reader, poll_interval=self.poll_interval)
        
        if hasattr(self, '_pending_callback') and self._pending_callback:
            self.listener.on_message(self._pending_callback)
            
        # Wait for login
        try:
            # Simple check if chat list is available, otherwise user needs to scan QR
            await page.wait_for_selector("div[data-testid='chat-list']", timeout=60000)
            logger.info("WhatsApp Web authenticated successfully.")
        except Exception:
            logger.warning("Timeout waiting for chat list. QR scan might be required.")
            # We don't raise here to allow manual QR scanning if not headless
            
        await self.listener.start()

    async def stop(self):
        """Stops the WhatsApp client."""
        if self.listener:
            await self.listener.stop()
        await self.browser.stop()

    def on_message(self, callback: Callable[[Message], Awaitable[None]]):
        """Register an event handler for new messages."""
        if not self.listener:
            # Can store it and apply on start, but for simplicity assuming registered after init
            logger.warning("Client not started. Callback will be registered, but make sure to call start().")
            # Store temporarily or just assume start() initializes listener
            
        # We need a small hack to allow registering before start
        self._pending_callback = callback
        if self.listener:
            self.listener.on_message(callback)

    async def send_message(self, chat_name: str, text: str) -> bool:
        """Send a text message."""
        if not self.sender:
            raise WhatsAppNotAuthenticatedError("Client not started.")
        return await self.sender.send_text(chat_name, text)
        
    async def send_image(self, chat_name: str, image_path: str) -> bool:
        """Send an image attachment."""
        if not self.sender:
            raise WhatsAppNotAuthenticatedError("Client not started.")
        return await self.sender.send_image(chat_name, image_path)

    async def send_document(self, chat_name: str, doc_path: str) -> bool:
        """Send a document attachment."""
        if not self.sender:
            raise WhatsAppNotAuthenticatedError("Client not started.")
        return await self.sender.send_document(chat_name, doc_path)

    async def send_voice_note(self, chat_name: str, voice_path: str) -> bool:
        """Send a voice note."""
        if not self.sender:
            raise WhatsAppNotAuthenticatedError("Client not started.")
        return await self.sender.send_voice_note(chat_name, voice_path)

__all__ = [
    'WhatsAppClient',
    'Message',
    'MessageType',
    'Attachment',
    'Chat',
    'WhatsAppError',
    'MessageSendError'
]
