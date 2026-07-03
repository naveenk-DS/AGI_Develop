import pyautogui
from loguru import logger
import tempfile

def take_screenshot(save_path: str = "screenshot.png") -> str:
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        logger.info(f"Screenshot saved: {save_path}")
        return f"Screenshot saved to {save_path}"
    except Exception as e:
        return f"Could not take screenshot: {e}"

def take_temp_screenshot(region=None) -> str:
    try:
        screenshot = pyautogui.screenshot(region=region)
        from PIL import Image
        
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

def get_screen_size() -> tuple:
    return pyautogui.size()
