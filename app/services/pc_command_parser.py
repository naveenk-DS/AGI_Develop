import re
from loguru import logger
from app.services.pc_control import (
    click, right_click, double_click,
    type_text, press_key, hotkey,
    scroll, take_screenshot,
    minimize_window, maximize_window, close_window,
    switch_window, show_desktop, lock_screen,
    volume_up, volume_down, volume_mute,
    copy, paste, undo, select_all, save_file,
    open_new_tab_keyboard, close_tab_keyboard
)

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