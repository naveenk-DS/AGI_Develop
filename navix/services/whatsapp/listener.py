import asyncio
import logging
from typing import Callable, Awaitable, Set, Dict, List
from .browser import WhatsAppBrowser
from .reader import WhatsAppReader
from .parser import WhatsAppParser
from .models import Message

logger = logging.getLogger(__name__)

class WhatsAppListener:
    def __init__(self, browser: WhatsAppBrowser, reader: WhatsAppReader, poll_interval: float = 2.0):
        self.browser = browser
        self.reader = reader
        self.poll_interval = poll_interval
        self._on_message_callback: Callable[[Message], Awaitable[None]] = None
        self._is_listening = False
        self._processed_messages: Set[str] = set()
        
    def on_message(self, callback: Callable[[Message], Awaitable[None]]):
        """Register a callback for new messages."""
        self._on_message_callback = callback
        
    async def start(self):
        if self._is_listening:
            return
            
        if not self._on_message_callback:
            logger.warning("No message callback registered.")
            
        self._is_listening = True
        logger.info(f"Started listening for messages (interval: {self.poll_interval}s)")
        
        asyncio.create_task(self._poll_loop())
        
    async def stop(self):
        self._is_listening = False
        logger.info("Stopped listening for messages")
        
    async def _poll_loop(self):
        while self._is_listening:
            try:
                # 1. Process any chats with unread badges
                unread_chats = await self.reader.get_unread_chats()
                for chat_name in unread_chats:
                    if await self.reader.open_chat(chat_name):
                        await self._process_active_chat(chat_name)
                        
                # 2. Also process the CURRENTLY open chat (if any) because messages 
                # received while looking at a chat don't get an "unread" badge!
                active_chat_title_elem = await self.browser.get_page.query_selector("header[data-testid='conversation-header'] span[dir='auto'][title]")
                if active_chat_title_elem:
                    active_chat_name = await active_chat_title_elem.get_attribute("title")
                    if active_chat_name:
                        await self._process_active_chat(active_chat_name)
                        
            except Exception as e:
                logger.error(f"Error in poll loop: {e}")
                
            await asyncio.sleep(self.poll_interval)
            
    async def _process_active_chat(self, chat_name: str):
        """Helper to process messages in whatever chat is currently on screen"""
        raw_messages = await self.reader.get_raw_messages(limit=5)
        for raw_msg in raw_messages:
            parsed_msg = await WhatsAppParser.parse_message(raw_msg, chat_id=chat_name)
            
            if parsed_msg and parsed_msg.id not in self._processed_messages:
                self._processed_messages.add(parsed_msg.id)
                
                # Limit memory usage for processed messages
                if len(self._processed_messages) > 1000:
                    self._processed_messages.clear()
                    
                if self._on_message_callback:
                    await self._on_message_callback(parsed_msg)
