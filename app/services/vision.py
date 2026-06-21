import base64
import pyautogui
import httpx
from loguru import logger

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

async def describe_screen(question: str = "What is on this screen?") -> str:
    try:
        screenshot = pyautogui.screenshot()
        screenshot = screenshot.resize((1024, int(1024 * screenshot.height / screenshot.width)))

        import io
        buf = io.BytesIO()
        screenshot.save(buf, format="PNG")
        img_b64 = base64.b64encode(buf.getvalue()).decode()

        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(OLLAMA_URL, json={
                "model": "llava:7b",
                "prompt": question,
                "images": [img_b64],
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 150}
            })
            if r.status_code == 200:
                text = r.json().get("response", "").strip()
                logger.info(f"Vision: {text[:100]}")
                return text
        return "I couldn't read the screen right now."
    except Exception as e:
        logger.error(f"Vision error: {e}")
        return "I couldn't see the screen right now."