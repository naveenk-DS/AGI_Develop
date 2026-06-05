import re
import os
import subprocess
import glob
from loguru import logger

# ── App Definitions ───────────────────────────────────────────────────────────

def _get_username() -> str:
    return os.environ.get("USERNAME", "user")

APPS = {
    # Development
    "vs code":      r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vscode":       r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "notepad":      "notepad.exe",
    "notepad++":    r"C:\Program Files\Notepad++\notepad++.exe",

    # Browsers
    "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":      r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "edge":         r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

    # Music & Media
    "spotify":      r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "vlc":          r"C:\Program Files\VideoLAN\VLC\vlc.exe",

    # Communication
    "whatsapp":     r"C:\Users\{user}\AppData\Local\WhatsApp\WhatsApp.exe",
    "telegram":     r"C:\Users\{user}\AppData\Roaming\Telegram Desktop\Telegram.exe",
    "discord":      r"C:\Users\{user}\AppData\Local\Discord\app-*\Discord.exe",
    "zoom":         r"C:\Users\{user}\AppData\Roaming\Zoom\bin\Zoom.exe",

    # System
    "calculator":   "calc.exe",
    "paint":        "mspaint.exe",
    "file explorer": "explorer.exe",
    "explorer":     "explorer.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "settings":     "ms-settings:",
    "command prompt": "cmd.exe",
    "powershell":   "powershell.exe",
    "snipping tool": "snippingtool.exe",

    # Office
    "word":         r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":        r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":   r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "outlook":      r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",

    # Other
    "steam":        r"C:\Program Files (x86)\Steam\steam.exe",
    "obs":          r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
    "postman":      r"C:\Users\{user}\AppData\Local\Postman\Postman.exe",
}

def _find_app_path(app_name: str) -> str:
    username = _get_username()
    path = APPS.get(app_name, "")
    if not path:
        return ""
    path = path.replace("{user}", username)
    if "*" in path:
        matches = glob.glob(path)
        return matches[0] if matches else ""
    return path

def _check_app_command(text: str) -> dict:
    if not any(w in text for w in ["open", "launch", "start", "run"]):
        return None
    clean = text
    for w in ["open", "launch", "start", "run", "please", "can you"]:
        clean = clean.replace(w, "").strip()
    for app_name in APPS.keys():
        if app_name in clean:
            return {"action": "open_app", "app_name": app_name}
    return None

async def launch_app(app_name: str) -> str:
    app_name = app_name.lower().strip()
    path = _find_app_path(app_name)
    try:
        if path.startswith("ms-"):
            subprocess.Popen(["start", path], shell=True)
        elif path and os.path.exists(path):
            subprocess.Popen([path])
        elif path and not os.path.isabs(path):
            subprocess.Popen(path, shell=True)
        else:
            subprocess.Popen(app_name, shell=True)
        logger.info(f"Launched: {app_name}")
        return f"Opening {app_name}"
    except Exception as e:
        logger.error(f"App launch error: {e}")
        return f"Could not open {app_name}"

# ── Command Parser ────────────────────────────────────────────────────────────

def parse_browser_command(text: str) -> dict:
    text_lower = text.lower().strip()

    # Screen understanding commands
    if any(w in text_lower for w in [
        "what is on my screen", "what's on my screen",
        "describe my screen", "what do you see",
        "look at my screen", "read my screen"
    ]):
        return {"action": "screen_describe"}

    if any(w in text_lower for w in ["read text on screen", "read the screen", "read screen"]):
        return {"action": "screen_read"}

    if any(w in text_lower for w in ["any error", "error on screen", "what error"]):
        return {"action": "screen_error"}

    # Click by vision
    click_vision_match = re.search(
        r"click (?:the )?(.+?)(?:\s+on screen|\s+button|\s+link)?$",
        text_lower
    )
    if click_vision_match and "click" in text_lower:
        return {"action": "screen_click", "element": click_vision_match.group(1).strip()}

    # News commands
    if any(w in text_lower for w in [
        "morning briefing", "news briefing", "daily briefing",
        "what happened today", "today's briefing"
    ]):
        return {"action": "news_briefing"}

    if any(w in text_lower for w in [
        "ai news", "artificial intelligence news", "latest ai"
    ]):
        return {"action": "ai_news"}

    # App launch — check first
    app_cmd = _check_app_command(text_lower)
    if app_cmd:
        return app_cmd

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
    play_match = re.search(r"(?:play|play on youtube)\s+(.+)", text_lower)
    if play_match and ("youtube" in text_lower or "play" in text_lower):
        query = play_match.group(1)
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

    # Open specific websites
    if "open" in text_lower:
        sites = {
            "youtube":      "https://youtube.com",
            "google":       "https://google.com",
            "github":       "https://github.com",
            "gmail":        "https://gmail.com",
            "whatsapp":     "https://web.whatsapp.com",
            "twitter":      "https://twitter.com",
            "linkedin":     "https://linkedin.com",
            "netflix":      "https://netflix.com",
            "spotify":      "https://open.spotify.com",
            "chatgpt":      "https://chat.openai.com",
            "wikipedia":    "https://wikipedia.org",
            "bbc":          "https://bbc.com",
            "cnn":          "https://cnn.com",
            "reddit":       "https://reddit.com",
            "stackoverflow": "https://stackoverflow.com",
            "instagram":    "https://instagram.com",
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


# ── Command Executor ──────────────────────────────────────────────────────────

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

    if cmd["action"] == "open_app":
        return await launch_app(cmd["app_name"])

    elif cmd["action"] == "news":
        headlines = await get_news()
        if headlines:
            return "Here are today's top news headlines. " + ". ".join(headlines)
        return "Could not fetch news right now"

    elif cmd["action"] == "wikipedia":
        return await search_wikipedia(cmd["query"])

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

    elif cmd["action"] == "screen_describe":
        from app.services.screen_vision import what_is_on_screen
        return await what_is_on_screen()

    elif cmd["action"] == "screen_read":
        from app.services.screen_vision import read_text_on_screen
        return await read_text_on_screen()

    elif cmd["action"] == "screen_error":
        from app.services.screen_vision import analyze_error_on_screen
        return await analyze_error_on_screen()

    elif cmd["action"] == "screen_click":
        from app.services.screen_vision import click_element_by_vision
        return await click_element_by_vision(cmd["element"])

    elif cmd["action"] == "news_briefing":
        from app.services.news_briefing import build_morning_briefing
        return await build_morning_briefing()

    elif cmd["action"] == "ai_news":
        from app.services.news_briefing import fetch_ai_news
        news = await fetch_ai_news()
        return "Here is the latest AI news. " + ". ".join(news) if news else "No AI news found."

    return None