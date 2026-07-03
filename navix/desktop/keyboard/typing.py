import pyautogui
from loguru import logger

def type_text(text: str) -> str:
    try:
        pyautogui.typewrite(text, interval=0.05)
        logger.info(f"Typed: {text}")
        return f"Typed: {text}"
    except Exception as e:
        return f"Could not type: {e}"

def press_key(key: str) -> str:
    try:
        pyautogui.press(key)
        logger.info(f"Pressed: {key}")
        return f"Pressed {key}"
    except Exception as e:
        return f"Could not press {key}: {e}"
