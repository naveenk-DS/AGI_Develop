import os
import asyncio
import logging
from typing import Optional
from playwright.async_api import Page
from .selectors import Selectors
from .exceptions import MessageSendError, ChatNotFoundError

logger = logging.getLogger(__name__)

class WhatsAppSender:
    def __init__(self, page: Page):
        self.page = page

    async def _ensure_chat_open(self, chat_name: str) -> bool:
        """Helper to open a chat if not already open."""
        # Check if chat is already open (could check header title, but search is safe)
        try:
            search_input = await self.page.wait_for_selector(Selectors.SEARCH_INPUT, timeout=5000)
            if not search_input:
                return False
                
            await search_input.click()
            await self.page.keyboard.press("Control+A")
            await self.page.keyboard.press("Backspace")
            
            await search_input.fill(chat_name)
            await self.page.wait_for_timeout(1000)
            
            chat_item = await self.page.wait_for_selector(f"span[title='{chat_name}']", timeout=5000)
            if chat_item:
                await chat_item.click()
                await self.page.wait_for_selector(Selectors.MESSAGE_LIST, timeout=5000)
                return True
            raise ChatNotFoundError(f"Chat '{chat_name}' not found.")
        except Exception as e:
            logger.error(f"Failed to open chat: {e}")
            return False

    async def send_text(self, chat_name: str, text: str) -> bool:
        try:
            if not await self._ensure_chat_open(chat_name):
                return False
                
            compose_box = await self.page.wait_for_selector(Selectors.COMPOSE_BOX, timeout=5000)
            if not compose_box:
                raise MessageSendError("Compose box not found")
                
            await compose_box.fill(text)
            
            send_button = await self.page.wait_for_selector(Selectors.SEND_BUTTON, timeout=5000)
            if not send_button:
                # Sometimes send button appears only after typing
                await self.page.keyboard.press("Enter")
            else:
                await send_button.click()
                
            return True
        except Exception as e:
            logger.error(f"Failed to send text to {chat_name}: {e}")
            raise MessageSendError(f"Failed to send text: {e}")

    async def _send_attachment(self, chat_name: str, file_path: str, attachment_type: str) -> bool:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        try:
            if not await self._ensure_chat_open(chat_name):
                return False
                
            attach_btn = await self.page.wait_for_selector(Selectors.ATTACH_BUTTON, timeout=5000)
            await attach_btn.click()
            
            selector = Selectors.ATTACH_IMAGE if attachment_type == "image" else Selectors.ATTACH_DOCUMENT
            file_input = await self.page.wait_for_selector(selector, state="attached")
            await file_input.set_input_files(file_path)
            
            # Wait for preview to load and send button to appear
            send_btn = await self.page.wait_for_selector(Selectors.SEND_BUTTON, timeout=10000)
            await send_btn.click()
            return True
        except Exception as e:
            logger.error(f"Failed to send {attachment_type} to {chat_name}: {e}")
            raise MessageSendError(f"Failed to send {attachment_type}: {e}")

    async def send_image(self, chat_name: str, image_path: str) -> bool:
        return await self._send_attachment(chat_name, image_path, "image")

    async def send_document(self, chat_name: str, doc_path: str) -> bool:
        return await self._send_attachment(chat_name, doc_path, "document")
        
    async def send_voice_note(self, chat_name: str, voice_path: str) -> bool:
        # WhatsApp Web doesn't easily support uploading voice notes as native voice messages via input file.
        # Usually sent as documents or handled via mic mock, which is complex.
        # For this package, we'll send it as a document as a fallback.
        return await self.send_document(chat_name, voice_path)
