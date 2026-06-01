import re
from loguru import logger

def parse_browser_command(text: str) -> dict:
    text_lower = text.lower().strip()

    # News
    if any(w in text_lower for w in ["news", "today's news", "latest news", "what's happening"]):
        return {"action": "news"}

    # Wikipedia
    wiki_match = re.search(
        r"(?:what is|who is|tell me about|wikipedia|search wiki)\s+(.+)",
        text_lower
    )
    if wiki_match:
        return {"action": "wikipedia", "query": wiki_match.group(1).strip()}

    # YouTube play
    play_match = re.search(
        r"(?:play|play on youtube)\s+(.+)",
        text_lower
    )
    if play_match and "youtube" in text_lower or "play" in text_lower:
        query = play_match.group(1) if play_match else None
        if query:
            return {"action": "youtube_play", "query": query}

    # YouTube search
    if "youtube" in text_lower:
        search_match = re.search(
            r"(?:youtube|search youtube|open youtube)\s+(?:and\s+)?(?:search|play|find)?\s*(.+)?",
            text_lower
        )
        query = search_match.group(1).strip() if search_match and search_match.group(1) else None
        return {"action": "youtube", "query": query}

    # New tab
    if "new tab" in text_lower:
        url_match = re.search(r"new tab\s+(?:and\s+open\s+)?(.+)?", text_lower)
        url = url_match.group(1).strip() if url_match and url_match.group(1) else "https://google.com"
        return {"action": "new_tab", "url": url}

    # New window
    if "new window" in text_lower:
        return {"action": "new_window"}

    # Google search
    if any(w in text_lower for w in ["search", "google", "look up", "find"]):
        search_match = re.search(
            r"(?:search|google|look up|find)\s+(?:for\s+)?(.+)",
            text_lower
        )
        if search_match:
            return {"action": "search", "query": search_match.group(1).strip()}

    # Open specific sites
    if "open" in text_lower:
        sites = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "github": "https://github.com",
            "gmail": "https://gmail.com",
            "whatsapp": "https://web.whatsapp.com",
            "twitter": "https://twitter.com",
            "linkedin": "https://linkedin.com",
            "netflix": "https://netflix.com",
            "spotify": "https://open.spotify.com",
            "chatgpt": "https://chat.openai.com",
            "wikipedia": "https://wikipedia.org",
            "bbc": "https://bbc.com",
            "cnn": "https://cnn.com",
            "reddit": "https://reddit.com",
            "stackoverflow": "https://stackoverflow.com",
            "instagram": "https://instagram.com",
        }
        for site, url in sites.items():
            if site in text_lower:
                return {"action": "open", "url": url, "site": site}

        url_match = re.search(r"open\s+([\w\.-]+\.\w+)", text_lower)
        if url_match:
            return {"action": "open", "url": url_match.group(1)}

    # Navigation
    if "scroll down" in text_lower:
        return {"action": "scroll_down"}
    if "scroll up" in text_lower:
        return {"action": "scroll_up"}
    if "go back" in text_lower or "back" in text_lower:
        return {"action": "back"}
    if "refresh" in text_lower or "reload" in text_lower:
        return {"action": "refresh"}
    if "zoom in" in text_lower:
        return {"action": "zoom_in"}
    if "zoom out" in text_lower:
        return {"action": "zoom_out"}
    if "close tab" in text_lower:
        return {"action": "close_tab"}
    if "close browser" in text_lower or "close chrome" in text_lower:
        return {"action": "close"}

    return {"action": "none"}


async def execute_browser_command(text: str) -> str:
    from app.services.browser import (
        open_url, search_google, open_youtube,
        close_browser, scroll_down, scroll_up,
        go_back, open_new_tab, open_new_window,
        search_youtube_and_play, get_news,
        search_wikipedia, zoom_in, zoom_out,
        refresh_page, close_tab
    )

    cmd = parse_browser_command(text)
    logger.info(f"Command parsed: {cmd}")

    if cmd["action"] == "news":
        headlines = await get_news()
        if headlines:
            result = "Here are today's top news headlines. " + ". ".join(headlines)
            return result
        return "Could not fetch news right now"

    elif cmd["action"] == "wikipedia":
        summary = await search_wikipedia(cmd["query"])
        return summary

    elif cmd["action"] == "youtube_play":
        return await search_youtube_and_play(cmd["query"])

    elif cmd["action"] == "youtube":
        return await open_youtube(cmd.get("query"))

    elif cmd["action"] == "search":
        return await search_google(cmd["query"])

    elif cmd["action"] == "open":
        return await open_url(cmd["url"])

    elif cmd["action"] == "new_tab":
        return await open_new_tab(cmd.get("url", "https://google.com"))

    elif cmd["action"] == "new_window":
        return await open_new_window()

    elif cmd["action"] == "scroll_down":
        return await scroll_down()

    elif cmd["action"] == "scroll_up":
        return await scroll_up()

    elif cmd["action"] == "back":
        return await go_back()

    elif cmd["action"] == "refresh":
        return await refresh_page()

    elif cmd["action"] == "zoom_in":
        return await zoom_in()

    elif cmd["action"] == "zoom_out":
        return await zoom_out()

    elif cmd["action"] == "close_tab":
        return await close_tab()

    elif cmd["action"] == "close":
        await close_browser()
        return "Browser closed"

    return None