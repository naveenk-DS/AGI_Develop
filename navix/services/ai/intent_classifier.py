import httpx
from loguru import logger

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
INTENT_MODEL = "qwen2.5:7b"

# Fast keyword shortcuts — avoid LLM call for obvious cases
_KEYWORD_INTENTS = {
    "browser":  ["open ", "go to ", "search ", "youtube", "google", "play ", "news", "wikipedia"],
    "pc":       ["click ", "type ", "press ", "volume", "screenshot", "minimize", "maximize", "scroll"],
    "vision":   ["what's on screen", "what is on screen", "read screen", "describe screen", "what do you see"],
    "code":     ["write code", "write a ", "create function", "build ", "fix this code", "debug ", "python script"],
}

INTENT_PROMPT = """Classify the user's message into exactly one category. Reply with only the category word, nothing else.

Categories:
- browser: user wants to open a website, search the web, play something on YouTube, check news
- pc: user wants to control the computer — click, type, screenshot, volume, open an app, file manager
- rag: ONLY use this if the user says words like "the document", "the file", "what I uploaded", "the PDF", or "what I gave you" — referring to a specific file they previously provided- vision: user asks what is on screen, what they are looking at, or to read/describe the current screen
- code: user wants you to write, create, or generate actual code or a script
- chat: the default for almost everything else, including any question starting with "what is", "what are", "explain", "describe", "tell me about", or "how does" — these are general knowledge questions, NOT document questions, unless they also mention a specific file/document
Message: "{message}"

Category:"""

async def classify_intent(message: str) -> str:
    msg_lower = message.lower().strip()

    # Fast keyword path — no LLM call needed for obvious intents
    for intent, keywords in _KEYWORD_INTENTS.items():
        if any(kw in msg_lower for kw in keywords):
            logger.debug(f"Intent (keyword): {intent}")
            return intent

    # LLM fallback for ambiguous input
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
                        logger.debug(f"Intent (LLM): {valid}")
                        return valid
    except Exception as e:
        logger.error(f"Intent classify error: {e}")
    return "chat"