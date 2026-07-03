from navix.desktop.keyboard.shortcuts import hotkey

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
