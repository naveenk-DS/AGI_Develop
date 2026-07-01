import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from .exceptions import BrowserError

logger = logging.getLogger(__name__)

class WhatsAppBrowser:
    def __init__(self, user_data_dir: str = "./whatsapp_session", headless: bool = False):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._is_running = False

    async def start(self):
        if self._is_running:
            return
            
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                ],
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()
            
            # Anti-detection scripts
            await self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            await self.page.goto("https://web.whatsapp.com/")
            self._is_running = True
            logger.info("WhatsApp Browser started.")
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise BrowserError(f"Could not start browser: {e}")

    async def stop(self):
        if not self._is_running:
            return
            
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
        self._is_running = False
        self.page = None
        self.browser = None
        self.playwright = None
        logger.info("WhatsApp Browser stopped.")

    @property
    def get_page(self) -> Page:
        if not self.page:
            raise BrowserError("Browser page is not initialized.")
        return self.page
