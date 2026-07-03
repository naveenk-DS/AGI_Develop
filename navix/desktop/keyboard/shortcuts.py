import pyautogui
from loguru import logger

def hotkey(*keys) -> str:
    try:
        pyautogui.hotkey(*keys)
        logger.info(f"Hotkey: {'+'.join(keys)}")
        return f"Pressed {'+'.join(keys)}"
    except Exception as e:
        return f"Could not press hotkey: {e}"
