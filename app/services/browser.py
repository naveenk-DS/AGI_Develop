import webbrowser
import httpx
import re
from loguru import logger

# ── Basic Browser Control ─────────────────────────────────────────────────────

def open_chrome(url: str) -> bool:
    try:
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        logger.info(f"Opened: {url}")
        return True
    except Exception as e:
        logger.error(f"Open error: {e}")
        return False

async def open_url(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    open_chrome(url)
    return f"Opened {url}"

async def search_google(query: str) -> str:
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    open_chrome(url)
    return f"Searched Google for {query}"

async def open_youtube(search: str = None) -> str:
    if search:
        url = f"https://www.youtube.com/results?search_query={search.replace(' ', '+')}"
    else:
        url = "https://www.youtube.com"
    open_chrome(url)
    return f"Opened YouTube{' — searching for ' + search if search else ''}"

async def search_youtube_and_play(query: str) -> str:
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    open_chrome(url)
    return f"Searching YouTube for {query}"

async def open_new_tab(url: str = "https://google.com") -> str:
    if not url.startswith("http"):
        url = "https://" + url
    open_chrome(url)
    return f"Opened {url}"

async def open_new_window(url: str = "https://google.com") -> str:
    open_chrome(url)
    return f"Opened new window"

async def close_browser() -> str:
    return "Use Alt+F4 to close browser"

async def scroll_down() -> str:
    return "Scroll down — click the page and press Page Down"

async def scroll_up() -> str:
    return "Scroll up — click the page and press Page Up"

async def go_back() -> str:
    return "Press Alt+Left to go back"

async def refresh_page() -> str:
    return "Press F5 to refresh"

async def zoom_in() -> str:
    return "Press Ctrl+Plus to zoom in"

async def zoom_out() -> str:
    return "Press Ctrl+Minus to zoom out"

async def close_tab() -> str:
    return "Press Ctrl+W to close tab"

# ── News ──────────────────────────────────────────────────────────────────────

async def get_news() -> list:
    from app.services.news_briefing import fetch_top_news
    return await fetch_top_news(5)

# ── Wikipedia ─────────────────────────────────────────────────────────────────

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
        return f"Could not search Wikipedia"

# ── Page Text ─────────────────────────────────────────────────────────────────

async def get_page_text() -> str:
    return "Page reading requires Playwright — coming in next update"