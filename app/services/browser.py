import asyncio
import httpx
import re
from playwright.async_api import async_playwright, Browser, Page
from loguru import logger
from typing import Optional

_browser: Optional[Browser] = None
_page: Optional[Page] = None
_playwright = None

async def get_browser():
    global _browser, _playwright
    if _browser is None or not _browser.is_connected():
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=False,
            args=["--start-maximized"]
        )
        logger.info("Browser started")
    return _browser

async def get_page():
    global _page
    browser = await get_browser()
    if _page is None or _page.is_closed():
        context = await browser.new_context(viewport=None)
        _page = await context.new_page()
        logger.info("New page created")
    return _page

async def open_url(url: str) -> str:
    try:
        page = await get_page()
        if not url.startswith("http"):
            url = "https://" + url
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        title = await page.title()
        logger.info(f"Opened: {url} — {title}")
        return f"Opened {title}"
    except Exception as e:
        logger.error(f"Browser open error: {e}")
        return f"Could not open {url}"

async def search_google(query: str) -> str:
    try:
        page = await get_page()
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        logger.info(f"Searched Google: {query}")
        return f"Searched Google for {query}"
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Could not search for {query}"

async def open_youtube(search: str = None) -> str:
    try:
        page = await get_page()
        if search:
            url = f"https://www.youtube.com/results?search_query={search.replace(' ', '+')}"
        else:
            url = "https://www.youtube.com"
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        logger.info(f"YouTube opened: {search or 'home'}")
        return f"Opened YouTube{' — searching for ' + search if search else ''}"
    except Exception as e:
        logger.error(f"YouTube error: {e}")
        return f"Could not open YouTube"

async def click_element(selector: str) -> str:
    try:
        page = await get_page()
        await page.click(selector, timeout=5000)
        return f"Clicked {selector}"
    except Exception as e:
        return f"Could not click {selector}: {e}"

async def type_text(text: str) -> str:
    try:
        page = await get_page()
        await page.keyboard.type(text)
        return f"Typed: {text}"
    except Exception as e:
        return f"Could not type: {e}"

async def get_page_text() -> str:
    try:
        page = await get_page()
        text = await page.inner_text("body")
        return text[:2000]
    except Exception as e:
        return f"Could not get page text: {e}"

async def close_browser():
    global _browser, _page, _playwright
    try:
        if _page:
            await _page.close()
        if _browser:
            await _browser.close()
        if _playwright:
            await _playwright.stop()
        _browser = None
        _page = None
        _playwright = None
        logger.info("Browser closed")
    except Exception as e:
        logger.error(f"Close error: {e}")

async def scroll_down():
    try:
        page = await get_page()
        await page.keyboard.press("PageDown")
        return "Scrolled down"
    except Exception as e:
        return f"Could not scroll: {e}"

async def scroll_up() -> str:
    try:
        page = await get_page()
        await page.keyboard.press("PageUp")
        return "Scrolled up"
    except Exception as e:
        return f"Could not scroll: {e}"

async def go_back():
    try:
        page = await get_page()
        await page.go_back()
        return "Went back"
    except Exception as e:
        return f"Could not go back: {e}"

async def open_new_tab(url: str = "https://www.google.com") -> str:
    try:
        browser = await get_browser()
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        new_page = await context.new_page()
        if not url.startswith("http"):
            url = "https://" + url
        await new_page.goto(url, wait_until="domcontentloaded", timeout=15000)
        title = await new_page.title()
        logger.info(f"New tab opened: {url}")
        return f"Opened new tab: {title}"
    except Exception as e:
        logger.error(f"New tab error: {e}")
        return f"Could not open new tab"

async def open_new_window(url: str = "https://www.google.com") -> str:
    try:
        browser = await get_browser()
        context = await browser.new_context(viewport=None)
        new_page = await context.new_page()
        if not url.startswith("http"):
            url = "https://" + url
        await new_page.goto(url, wait_until="domcontentloaded", timeout=15000)
        title = await new_page.title()
        logger.info(f"New window opened: {url}")
        return f"Opened new window: {title}"
    except Exception as e:
        logger.error(f"New window error: {e}")
        return f"Could not open new window"

async def search_youtube_and_play(query: str) -> str:
    try:
        page = await get_page()
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_selector("ytd-video-renderer", timeout=5000)
        await page.click("ytd-video-renderer a#video-title")
        logger.info(f"Playing YouTube: {query}")
        return f"Playing {query} on YouTube"
    except Exception as e:
        logger.error(f"YouTube play error: {e}")
        return f"Opened YouTube search for {query}"

async def get_news() -> list:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            titles = re.findall(r"<title><!\[CDATA\[(.+?)\]\]></title>", r.text)
            return titles[1:6]
    except Exception as e:
        logger.error(f"News error: {e}")
        return ["Could not fetch news right now"]

async def search_wikipedia(query: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/" +
                query.replace(" ", "_"),
                headers={"User-Agent": "NAVIX-AI/1.0"}
            )
            if r.status_code == 200:
                data = r.json()
                extract = data.get("extract", "")
                sentences = extract.split(". ")
                return ". ".join(sentences[:3]) + "."
            return f"Could not find Wikipedia article for {query}"
    except Exception as e:
        logger.error(f"Wikipedia error: {e}")
        return f"Could not search Wikipedia for {query}"

async def zoom_in() -> str:
    try:
        page = await get_page()
        await page.keyboard.press("Control+=")
        return "Zoomed in"
    except Exception as e:
        return f"Could not zoom: {e}"

async def zoom_out() -> str:
    try:
        page = await get_page()
        await page.keyboard.press("Control+-")
        return "Zoomed out"
    except Exception as e:
        return f"Could not zoom: {e}"

async def refresh_page() -> str:
    try:
        page = await get_page()
        await page.reload()
        return "Page refreshed"
    except Exception as e:
        return f"Could not refresh: {e}"

async def close_tab() -> str:
    try:
        page = await get_page()
        await page.close()
        global _page
        _page = None
        return "Tab closed"
    except Exception as e:
        return f"Could not close tab: {e}"