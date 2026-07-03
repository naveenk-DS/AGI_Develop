import pyautogui
from loguru import logger

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

def click(x: int = None, y: int = None) -> str:
    try:
        if x and y:
            pyautogui.click(x, y)
        else:
            pyautogui.click()
        logger.info(f"Clicked at {x},{y}")
        return "Clicked"
    except Exception as e:
        return f"Could not click: {e}"

def right_click(x: int = None, y: int = None) -> str:
    try:
        if x and y:
            pyautogui.rightClick(x, y)
        else:
            pyautogui.rightClick()
        return "Right clicked"
    except Exception as e:
        return f"Could not right click: {e}"

def double_click(x: int = None, y: int = None) -> str:
    try:
        if x and y:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.doubleClick()
        return "Double clicked"
    except Exception as e:
        return f"Could not double click: {e}"

def move_mouse(x: int, y: int) -> str:
    try:
        pyautogui.moveTo(x, y, duration=0.5)
        return f"Moved mouse to {x},{y}"
    except Exception as e:
        return f"Could not move mouse: {e}"

def scroll(direction: str = "down", amount: int = 3) -> str:
    try:
        if direction == "down":
            pyautogui.scroll(-amount)
        else:
            pyautogui.scroll(amount)
        return f"Scrolled {direction}"
    except Exception as e:
        return f"Could not scroll: {e}"
