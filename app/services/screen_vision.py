import base64
import httpx
import pyautogui
import tempfile
import os
from PIL import Image
from loguru import logger

OLLAMA_URL = "http://127.0.0.1:11434"
VISION_MODEL = "llava"

def take_screenshot(region=None) -> str:
    try:
        screenshot = pyautogui.screenshot(region=region)
        
        # resize to reduce tokens — LLaVA works fine at 1024px width
        w, h = screenshot.size
        if w > 1024:
            ratio = 1024 / w
            screenshot = screenshot.resize(
                (1024, int(h * ratio)),
                Image.LANCZOS
            )
        
        tmp = tempfile.mktemp(suffix=".png")
        screenshot.save(tmp)
        logger.info(f"Screenshot saved: {tmp}")
        return tmp
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return ""

def image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

async def ask_llava(question: str, image_path: str = None) -> str:
    try:
        if not image_path:
            image_path = take_screenshot()
        
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

async def find_element_on_screen(element: str) -> dict:
    result = await ask_llava(
        f"Find the '{element}' on this screen. "
        f"Tell me approximately where it is — top-left, top-right, center, "
        f"bottom-left, or bottom-right of the screen. "
        f"Also describe what it looks like. Be brief."
    )
    return {"description": result, "element": element}

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

async def click_element_by_vision(element: str) -> str:
    try:
        screenshot_path = take_screenshot()
        img = Image.open(screenshot_path)
        screen_w, screen_h = pyautogui.size()
        
        result = await ask_llava(
            f"Where exactly is the '{element}' on this screen? "
            f"Give me the approximate position as a percentage. "
            f"Example: 'The element is at approximately 30% from left and 20% from top.' "
            f"Only give the position, nothing else.",
            screenshot_path
        )
        
        import re
        # parse percentage from LLaVA response
        left_match = re.search(r"(\d+)%?\s*from\s*left", result, re.IGNORECASE)
        top_match  = re.search(r"(\d+)%?\s*from\s*top", result, re.IGNORECASE)
        
        if left_match and top_match:
            x_pct = int(left_match.group(1)) / 100
            y_pct = int(top_match.group(1)) / 100
            x = int(screen_w * x_pct)
            y = int(screen_h * y_pct)
            pyautogui.click(x, y)
            logger.info(f"Clicked '{element}' at ({x}, {y})")
            return f"Clicked {element} at position {x}, {y}"
        else:
            return f"Could not find exact position of {element}. LLaVA said: {result}"
    except Exception as e:
        logger.error(f"Vision click error: {e}")
        return f"Could not click {element}"