import httpx
from loguru import logger

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
INTENT_MODEL = "qwen2.5:7b"

INTENT_PROMPT = """Classify the user's message into exactly one category. Reply with only the category word, nothing else.

Categories:
- browser: user wants to open a website, search the web, play something on YouTube, check news
- pc: user wants to control the computer — click, type, screenshot, volume, open an app, file manager
- rag: user wants information that might be in ingested documents, or asks to explain/define/describe a concept
- vision: user asks what is on screen, what they are looking at, or to read/describe the current screen
- code: user wants you to write, create, or generate actual code or a script
- chat: general conversation, opinions, casual talk, anything not fitting above

Message: "{message}"

Category:"""

async def classify_intent(message: str) -> str:
    prompt = INTENT_PROMPT.format(message=message)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(OLLAMA_URL, json={
                "model": INTENT_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 5}
            })
            if r.status_code == 200:
                label = r.json().get("response", "").strip().lower()
                for valid in ("browser", "pc", "rag", "vision", "code", "chat"):
                    if valid in label:
                        return valid
    except Exception as e:
        logger.error(f"Intent classify error: {e}")
    return "chat"