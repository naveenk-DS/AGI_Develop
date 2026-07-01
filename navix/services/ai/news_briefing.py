import httpx
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from loguru import logger

async def fetch_top_news(max_items: int = 5) -> list[str]:
    sources = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://feeds.skynews.com/feeds/rss/home.xml",
    ]
    
    for url in sources:
        try:
            async with httpx.AsyncClient(
                timeout=15,
                follow_redirects=True,
                verify=False         # ← disable SSL verification
            ) as client:
                r = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/rss+xml, application/xml, text/xml, */*"
                    }
                )
                if r.status_code != 200:
                    logger.warning(f"News source {url} returned {r.status_code}")
                    continue

                try:
                    root = ET.fromstring(r.text)
                    items = root.findall(".//item/title")
                    titles = [i.text.strip() for i in items if i.text and len(i.text.strip()) > 10]
                    if titles:
                        logger.info(f"News fetched from {url} — {len(titles)} items")
                        return titles[:max_items]
                except ET.ParseError as pe:
                    logger.warning(f"XML parse error for {url}: {pe}")
                    # regex fallback
                    titles = re.findall(r"<title>(?:<!\[CDATA\[)?(.+?)(?:\]\]>)?</title>", r.text)
                    titles = [t.strip() for t in titles if len(t.strip()) > 10 and "RSS" not in t and "Feed" not in t]
                    if titles:
                        return titles[:max_items]

        except Exception as e:
            logger.warning(f"News source {url} failed: {type(e).__name__}: {e}")
            continue

    return []


async def fetch_ai_news() -> list[str]:
    sources = [
        "https://techcrunch.com/tag/artificial-intelligence/feed/",
        "https://feeds.skynews.com/feeds/rss/technology.xml",
    ]
    for url in sources:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True, verify=False) as client:
                r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code != 200:
                    continue
                try:
                    root = ET.fromstring(r.text)
                    items = root.findall(".//item/title")
                    titles = [i.text.strip() for i in items if i.text and len(i.text.strip()) > 10]
                    if titles:
                        return titles[:3]
                except ET.ParseError:
                    titles = re.findall(r"<title>(?:<!\[CDATA\[)?(.+?)(?:\]\]>)?</title>", r.text)
                    titles = [t.strip() for t in titles if len(t.strip()) > 10]
                    if titles:
                        return titles[:3]
        except Exception as e:
            logger.warning(f"AI news {url} failed: {e}")
            continue
    return []


async def fetch_tech_news() -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, verify=False) as client:
            r = await client.get(
                "https://techcrunch.com/feed/",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            root = ET.fromstring(r.text)
            items = root.findall(".//item/title")
            return [i.text.strip() for i in items[:3] if i.text and len(i.text.strip()) > 10]
    except Exception as e:
        logger.warning(f"Tech news failed: {e}")
        return []

async def build_morning_briefing() -> str:
    hour = datetime.now().hour

    top  = await fetch_top_news(5)
    ai   = await fetch_ai_news()
    tech = await fetch_tech_news()

    lines = []

    if 5 <= hour < 12:
        lines.append("Good morning Naveen. Here is your morning briefing.")
    elif 12 <= hour < 17:
        lines.append("Here is your afternoon news update Naveen.")
    else:
        lines.append("Here is your evening briefing Naveen.")

    if top:
        lines.append("Top news today.")
        for i, t in enumerate(top[:3], 1):
            lines.append(f"{i}. {t}.")
    else:
        lines.append("Could not fetch top news right now.")

    if ai:
        lines.append("In AI news.")
        lines.append(ai[0] + ".")
        if len(ai) > 1:
            lines.append(ai[1] + ".")

    if tech:
        lines.append("In technology.")
        lines.append(tech[0] + ".")

    lines.append("That is your briefing Naveen. Have a productive day.")
    return " ".join(lines)

async def get_quick_headlines() -> str:
    top = await fetch_top_news(5)
    if not top:
        return "Could not fetch news right now."
    result = "Here are today's top headlines. "
    for i, t in enumerate(top, 1):
        result += f"{i}. {t}. "
    return result