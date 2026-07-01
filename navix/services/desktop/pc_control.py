import pyautogui
import subprocess
import time
from loguru import logger

# Safety — move mouse to corner to abort
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

# ── Mouse Control ─────────────────────────────────────────────────────────────

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

# ── Keyboard Control ──────────────────────────────────────────────────────────

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

def hotkey(*keys) -> str:
    try:
        pyautogui.hotkey(*keys)
        logger.info(f"Hotkey: {'+'.join(keys)}")
        return f"Pressed {'+'.join(keys)}"
    except Exception as e:
        return f"Could not press hotkey: {e}"

def take_screenshot(save_path: str = "screenshot.png") -> str:
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save(save_path)
        logger.info(f"Screenshot saved: {save_path}")
        return f"Screenshot saved to {save_path}"
    except Exception as e:
        return f"Could not take screenshot: {e}"

def get_screen_size() -> tuple:
    return pyautogui.size()

# ── Window Control ────────────────────────────────────────────────────────────

def minimize_window() -> str:
    hotkey("win", "down")
    return "Window minimized"

def maximize_window() -> str:
    hotkey("win", "up")
    return "Window maximized"

def close_window() -> str:
    hotkey("alt", "f4")
    return "Window closed"

def switch_window() -> str:
    hotkey("alt", "tab")
    return "Switched window"

def show_desktop() -> str:
    hotkey("win", "d")
    return "Showing desktop"

def lock_screen() -> str:
    hotkey("win", "l")
    return "Screen locked"

def volume_up() -> str:
    for _ in range(3):
        press_key("volumeup")
    return "Volume increased"

def volume_down() -> str:
    for _ in range(3):
        press_key("volumedown")
    return "Volume decreased"

def volume_mute() -> str:
    press_key("volumemute")
    return "Volume muted"

def copy() -> str:
    hotkey("ctrl", "c")
    return "Copied"

def paste() -> str:
    hotkey("ctrl", "v")
    return "Pasted"

def undo() -> str:
    hotkey("ctrl", "z")
    return "Undone"

def select_all() -> str:
    hotkey("ctrl", "a")
    return "Selected all"

def save_file() -> str:
    hotkey("ctrl", "s")
    return "Saved"

def open_new_tab_keyboard() -> str:
    hotkey("ctrl", "t")
    return "Opened new tab"

def close_tab_keyboard() -> str:
    hotkey("ctrl", "w")
    return "Closed tab"