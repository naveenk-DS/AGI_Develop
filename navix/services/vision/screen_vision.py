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
        screen_w, screen_h = pyautogui.size()
        
        # 1. Try PaddleOCR for exact text matching
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_angle_cls=False, lang='en', show_log=False)
            result = ocr.ocr(screenshot_path, cls=False)
            
            if result and result[0]:
                for line in result[0]:
                    box = line[0]
                    text = line[1][0]
                    
                    if element.lower() in text.lower():
                        # box is a list of 4 points: [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                        center_x = int((box[0][0] + box[1][0]) / 2)
                        center_y = int((box[0][1] + box[2][1]) / 2)
                        pyautogui.click(center_x, center_y)
                        logger.info(f"PaddleOCR Clicked '{text}' at ({center_x}, {center_y})")
                        return f"Found and clicked '{text}' at exact coordinates {center_x}, {center_y} using PaddleOCR"
        except ImportError:
            logger.warning("PaddleOCR not installed. Falling back to LLaVA.")
        except Exception as oe:
            logger.error(f"PaddleOCR error: {oe}")
            
        # 2. Fallback to LLaVA (percentage guessing)
        result = await ask_llava(
            f"Where exactly is the '{element}' on this screen? "
            f"Give me the approximate position as a percentage. "
            f"Example: 'The element is at approximately 30% from left and 20% from top.' "
            f"Only give the position, nothing else.",
            screenshot_path
        )
        
        import re
        left_match = re.search(r"(\d+)%?\s*from\s*left", result, re.IGNORECASE)
        top_match  = re.search(r"(\d+)%?\s*from\s*top", result, re.IGNORECASE)
        
        if left_match and top_match:
            x_pct = int(left_match.group(1)) / 100
            y_pct = int(top_match.group(1)) / 100
            x = int(screen_w * x_pct)
            y = int(screen_h * y_pct)
            pyautogui.click(x, y)
            logger.info(f"LLaVA Clicked '{element}' at ({x}, {y})")
            return f"Clicked {element} at position {x}, {y} using LLaVA fallback"
        else:
            return f"Could not find exact position of {element}. LLaVA said: {result}"
    except Exception as e:
        logger.error(f"Vision click error: {e}")
        return f"Could not click {element}"

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
