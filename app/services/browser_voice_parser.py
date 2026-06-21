"""
Parses natural voice commands into browser automation actions.
Examples:
  "go to google.com and click sign in"
  "fill email field with naveen@gmail.com"
  "click the login button"
"""
import re
from loguru import logger

# Track current page URL across commands in same conversation
_current_url = "https://www.google.com"


def set_current_url(url: str):
    global _current_url
    _current_url = url


def get_current_url() -> str:
    return _current_url


async def execute_voice_browser_command(text: str) -> str:
    """Main entry point — figures out if this is click, fill, or navigate."""
    text_lower = text.lower().strip()

    # ── Navigate ──────────────────────────────────────────────────────────────
    nav_match = re.search(r"(?:go to|open|navigate to)\s+([\w\.\-/:]+)", text_lower)
    if nav_match and "click" not in text_lower and "fill" not in text_lower:
        url = nav_match.group(1)
        if not url.startswith("http"):
            url = f"https://{url}" if "." in url else f"https://www.google.com/search?q={url}"
        set_current_url(url)
        return f"Opened {url}"

    # ── Fill ──────────────────────────────────────────────────────────────────
    fill_match = re.search(r"fill\s+(.+?)\s+(?:with|as)\s+(.+)", text_lower)
    if fill_match:
        from app.services.playwright_automation import voice_fill
        field = fill_match.group(1).strip()
        value = fill_match.group(2).strip()
        result = voice_fill(get_current_url(), field, value)
        return result

    # ── Click ─────────────────────────────────────────────────────────────────
    click_match = re.search(r"click\s+(?:on\s+)?(?:the\s+)?(.+)", text_lower)
    if click_match:
        from app.services.playwright_automation import voice_click
        target = click_match.group(1).strip()
        result = voice_click(get_current_url(), target)
        return result

    return None