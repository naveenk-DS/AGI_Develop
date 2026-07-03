import os
import shutil

base_dir = r"f:\naveen\AGI_Start\navix\desktop"
files_to_create = {
    "__init__.py": "",
    "mouse/__init__.py": "",
    "mouse/controller.py": """import pyautogui
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
""",
    "keyboard/__init__.py": "",
    "keyboard/typing.py": """import pyautogui
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
""",
    "keyboard/shortcuts.py": """import pyautogui
from loguru import logger

def hotkey(*keys) -> str:
    try:
        pyautogui.hotkey(*keys)
        logger.info(f"Hotkey: {'+'.join(keys)}")
        return f"Pressed {'+'.join(keys)}"
    except Exception as e:
        return f"Could not press hotkey: {e}"
""",
    "screen/__init__.py": "",
    "screen/screenshot.py": """import pyautogui
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
""",
    "windows/__init__.py": "",
    "windows/manager.py": """from navix.desktop.keyboard.shortcuts import hotkey

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
""",
    "volume/__init__.py": "",
    "volume/controller.py": """from navix.desktop.keyboard.typing import press_key

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
""",
    "clipboard/__init__.py": "",
    "clipboard/copy.py": """from navix.desktop.keyboard.shortcuts import hotkey

def copy() -> str:
    hotkey("ctrl", "c")
    return "Copied"

def select_all() -> str:
    hotkey("ctrl", "a")
    return "Selected all"
""",
    "clipboard/paste.py": """from navix.desktop.keyboard.shortcuts import hotkey

def paste() -> str:
    hotkey("ctrl", "v")
    return "Pasted"
""",
    "automation/__init__.py": "",
    "automation/macros.py": """from navix.desktop.keyboard.shortcuts import hotkey

def undo() -> str:
    hotkey("ctrl", "z")
    return "Undone"

def save_file() -> str:
    hotkey("ctrl", "s")
    return "Saved"

def open_new_tab_keyboard() -> str:
    hotkey("ctrl", "t")
    return "Opened new tab"

def close_tab_keyboard() -> str:
    hotkey("ctrl", "w")
    return "Closed tab"
""",
    "automation/actions.py": """import re
from loguru import logger

# New localized imports
from navix.desktop.mouse.controller import click, right_click, double_click, scroll
from navix.desktop.keyboard.typing import type_text, press_key
from navix.desktop.keyboard.shortcuts import hotkey
from navix.desktop.screen.screenshot import take_screenshot
from navix.desktop.windows.manager import minimize_window, maximize_window, close_window, switch_window, show_desktop, lock_screen
from navix.desktop.volume.controller import volume_up, volume_down, volume_mute
from navix.desktop.clipboard.copy import copy, select_all
from navix.desktop.clipboard.paste import paste
from navix.desktop.automation.macros import undo, save_file, open_new_tab_keyboard, close_tab_keyboard

def parse_pc_command(text: str) -> dict:
    t = text.lower().strip()

    # Type text
    type_match = re.search(r"(?:type|write|input)\s+(.+)", t)
    if type_match:
        return {"action": "type", "text": type_match.group(1)}

    # Press key
    key_map = {
        "enter": "enter", "return": "enter",
        "space": "space", "spacebar": "space",
        "escape": "esc", "tab": "tab",
        "backspace": "backspace", "delete": "delete",
        "up": "up", "down": "down", "left": "left", "right": "right",
        "home": "home", "end": "end",
        "page up": "pageup", "page down": "pagedown",
        "f1": "f1", "f2": "f2", "f3": "f3", "f4": "f4",
        "f5": "f5", "f11": "f11", "f12": "f12"
    }
    for word, key in key_map.items():
        if f"press {word}" in t or t == word:
            return {"action": "press", "key": key}

    # Hotkeys
    if "copy" in t:
        return {"action": "copy"}
    if "paste" in t:
        return {"action": "paste"}
    if "undo" in t:
        return {"action": "undo"}
    if "select all" in t:
        return {"action": "select_all"}
    if "save" in t and "file" in t or t == "save":
        return {"action": "save"}
    if "new tab" in t:
        return {"action": "new_tab_keyboard"}
    if "close tab" in t:
        return {"action": "close_tab_keyboard"}

    # Screenshot
    if "screenshot" in t or "take a screenshot" in t or "capture screen" in t:
        return {"action": "screenshot"}

    # Window control
    if "minimize" in t:
        return {"action": "minimize"}
    if "maximize" in t:
        return {"action": "maximize"}
    if "close window" in t:
        return {"action": "close_window"}
    if "switch window" in t or "alt tab" in t:
        return {"action": "switch_window"}
    if "show desktop" in t:
        return {"action": "show_desktop"}
    if "lock screen" in t or "lock computer" in t:
        return {"action": "lock_screen"}

    # Volume
    if "volume up" in t or "increase volume" in t or "louder" in t:
        return {"action": "volume_up"}
    if "volume down" in t or "decrease volume" in t or "quieter" in t:
        return {"action": "volume_down"}
    if "mute" in t:
        return {"action": "mute"}

    # Scroll
    if "scroll down" in t:
        return {"action": "scroll", "direction": "down"}
    if "scroll up" in t:
        return {"action": "scroll", "direction": "up"}

    # Click
    if "click" in t and "right" in t:
        return {"action": "right_click"}
    if "double click" in t:
        return {"action": "double_click"}
    if "click" in t:
        return {"action": "click"}

    return {"action": "none"}

async def execute_pc_command(text: str) -> str:
    cmd = parse_pc_command(text)
    logger.info(f"PC command: {cmd}")

    if cmd["action"] == "type":
        return type_text(cmd["text"])
    elif cmd["action"] == "press":
        return press_key(cmd["key"])
    elif cmd["action"] == "copy":
        return copy()
    elif cmd["action"] == "paste":
        return paste()
    elif cmd["action"] == "undo":
        return undo()
    elif cmd["action"] == "select_all":
        return select_all()
    elif cmd["action"] == "save":
        return save_file()
    elif cmd["action"] == "new_tab_keyboard":
        return open_new_tab_keyboard()
    elif cmd["action"] == "close_tab_keyboard":
        return close_tab_keyboard()
    elif cmd["action"] == "screenshot":
        path = "F:/naveen/AGI_Start/screenshots/screenshot.png"
        import os
        os.makedirs("F:/naveen/AGI_Start/screenshots", exist_ok=True)
        return take_screenshot(path)
    elif cmd["action"] == "minimize":
        return minimize_window()
    elif cmd["action"] == "maximize":
        return maximize_window()
    elif cmd["action"] == "close_window":
        return close_window()
    elif cmd["action"] == "switch_window":
        return switch_window()
    elif cmd["action"] == "show_desktop":
        return show_desktop()
    elif cmd["action"] == "lock_screen":
        return lock_screen()
    elif cmd["action"] == "volume_up":
        return volume_up()
    elif cmd["action"] == "volume_down":
        return volume_down()
    elif cmd["action"] == "mute":
        return volume_mute()
    elif cmd["action"] == "scroll":
        return scroll(cmd["direction"])
    elif cmd["action"] == "click":
        return click()
    elif cmd["action"] == "right_click":
        return right_click()
    elif cmd["action"] == "double_click":
        return double_click()

    return None
""",
    "vision/__init__.py": "",
    "vision/screen_reader.py": """import base64
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
""",
    "vision/ui_detection.py": """from navix.desktop.vision.screen_reader import ask_llava

async def find_element_on_screen(element: str) -> dict:
    result = await ask_llava(
        f"Find the '{element}' on this screen. "
        f"Tell me approximately where it is — top-left, top-right, center, "
        f"bottom-left, or bottom-right of the screen. "
        f"Also describe what it looks like. Be brief."
    )
    return {"description": result, "element": element}
""",
    "vision/ocr.py": """import pyautogui
from loguru import logger
from navix.desktop.screen.screenshot import take_temp_screenshot
from navix.desktop.vision.screen_reader import ask_llava

async def click_element_by_vision(element: str) -> str:
    try:
        screenshot_path = take_temp_screenshot()
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
"""
}

for rel_path, content in files_to_create.items():
    full_path = os.path.join(base_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
print("Migration files created successfully!")
