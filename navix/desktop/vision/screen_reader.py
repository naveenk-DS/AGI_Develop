import base64
import httpx
import os
import pyautogui
from loguru import logger
from navix.desktop.screen.screenshot import take_temp_screenshot

OLLAMA_URL = "http://127.0.0.1:11434"
VISION_MODEL = "llava"

def image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

async def ask_llava(question: str, image_path: str = None) -> str:
    try:
        if not image_path:
            image_path = take_temp_screenshot()
        
        if not image_path or not os.path.exists(image_path):
            return "Could not take screenshot."

        img_b64 = image_to_base64(image_path)

        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": VISION_MODEL,
                    "prompt": question,
                    "images": [img_b64],
                    "stream": False
                }
            )
            if r.status_code == 200:
                result = r.json().get("response", "")
                logger.info(f"LLaVA response: {result[:100]}")
                return result
            return "Could not analyze screen."
    except Exception as e:
        logger.error(f"LLaVA error: {e}")
        return f"Screen analysis failed: {e}"
    finally:
        if image_path and os.path.exists(image_path):
            try:
                os.unlink(image_path)
            except:
                pass

async def what_is_on_screen() -> str:
    return await ask_llava(
        "Describe what you see on this screen in 2-3 sentences. "
        "Focus on what app is open, what content is visible, "
        "and what the user seems to be doing. Be concise."
    )

async def read_text_on_screen() -> str:
    return await ask_llava(
        "Read and return all visible text on this screen. "
        "Include headings, buttons, menu items, and body text. "
        "Format it cleanly."
    )

async def analyze_error_on_screen() -> str:
    return await ask_llava(
        "Is there any error message, warning, or problem visible on this screen? "
        "If yes describe it clearly. If no, say the screen looks normal."
    )

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
        logger.error(f"Vision description error: {e}")
        return "I couldn't read the screen right now."
