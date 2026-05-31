import re
from loguru import logger

def parse_browser_command(text: str) -> dict:
    text_lower = text.lower().strip()

    # YouTube commands
    if "youtube" in text_lower:
        search_match = re.search(
            r"(?:play|search|find|open youtube (?:and )?(?:play|search)?)\s+(.+)",
            text_lower
        )
        if search_match:
            query = search_match.group(1).strip()
            return {"action": "youtube", "query": query}
        return {"action": "youtube", "query": None}

    # Google search
    if any(w in text_lower for w in ["search", "google", "look up", "find"]):
        search_match = re.search(
            r"(?:search|google|look up|find)\s+(?:for\s+)?(.+)",
            text_lower
        )
        if search_match:
            query = search_match.group(1).strip()
            return {"action": "search", "query": query}

    # Open website
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
        }
        for site, url in sites.items():
            if site in text_lower:
                return {"action": "open", "url": url, "site": site}

        # open any URL mentioned
        url_match = re.search(r"open\s+([\w\.-]+\.\w+)", text_lower)
        if url_match:
            return {"action": "open", "url": url_match.group(1)}

    # Scroll
    if "scroll down" in text_lower:
        return {"action": "scroll_down"}

    # Go back
    if "go back" in text_lower or "back" in text_lower:
        return {"action": "back"}

    # Close browser
    if "close" in text_lower and "browser" in text_lower:
        return {"action": "close"}

    return {"action": "none"}

async def execute_browser_command(text: str) -> str:
    from app.services.browser import (
        open_url, search_google, open_youtube,
        close_browser, scroll_down, go_back
    )

    cmd = parse_browser_command(text)
    logger.info(f"Browser command: {cmd}")

    if cmd["action"] == "youtube":
        return await open_youtube(cmd.get("query"))

    elif cmd["action"] == "search":
        return await search_google(cmd["query"])

    elif cmd["action"] == "open":
        return await open_url(cmd["url"])

    elif cmd["action"] == "scroll_down":
        return await scroll_down()

    elif cmd["action"] == "back":
        return await go_back()

    elif cmd["action"] == "close":
        await close_browser()
        return "Browser closed"

    return None