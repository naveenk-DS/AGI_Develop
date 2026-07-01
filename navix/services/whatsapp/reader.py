import logging
from typing import List, Optional
from playwright.async_api import Page, ElementHandle
from .selectors import Selectors
from .exceptions import WhatsAppError

logger = logging.getLogger(__name__)

class WhatsAppReader:
    def __init__(self, page: Page):
        self.page = page

    async def get_unread_chats(self) -> List[str]:
        """Returns a list of chat titles that have unread messages."""
        try:
            unread_chats = []
            
            # Find all chat items directly instead of waiting for a specific container
            chat_items = await self.page.query_selector_all(Selectors.CHAT_ITEM)
            
            for item in chat_items:
                unread_badge = await item.query_selector(Selectors.UNREAD_BADGE)
                if unread_badge:
                    # Find the title within this chat item
                    title_elem = await item.query_selector(Selectors.CHAT_TITLE)
                    if title_elem:
                        title = await title_elem.get_attribute("title")
                        if title and title not in unread_chats:
                            unread_chats.append(title)
            return unread_chats
        except Exception as e:
            logger.error(f"Error getting unread chats: {e}")
            return []

    async def open_chat(self, chat_name: str) -> bool:
        """Opens a chat by its name."""
        try:
            # Clear search box first if needed, but simpler to search directly
            search_input = await self.page.wait_for_selector(Selectors.SEARCH_INPUT, timeout=5000)
            if not search_input:
                return False
                
            await search_input.click()
            # Select all and delete
            await self.page.keyboard.press("Control+A")
            await self.page.keyboard.press("Backspace")
            
            await search_input.fill(chat_name)
            await self.page.wait_for_timeout(1000) # Wait for search results
            
            # Click the first matching result
            chat_item = await self.page.wait_for_selector(f"span[title='{chat_name}']", timeout=5000)
            if chat_item:
                await chat_item.click()
                await self.page.wait_for_selector(Selectors.MESSAGE_LIST, timeout=5000)
                return True
            return False
        except Exception as e:
            logger.error(f"Error opening chat {chat_name}: {e}")
            return False

    async def get_raw_messages(self, limit: int = 20) -> List[ElementHandle]:
        """Gets raw message elements from the currently open chat."""
        try:
            messages = await self.page.query_selector_all(Selectors.MESSAGE_IN)
            return messages[-limit:] if messages else []
        except Exception as e:
            logger.error(f"Error getting raw messages: {e}")
            return []
