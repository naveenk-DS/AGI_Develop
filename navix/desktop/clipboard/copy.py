from navix.desktop.keyboard.shortcuts import hotkey

def copy() -> str:
    hotkey("ctrl", "c")
    return "Copied"

def select_all() -> str:
    hotkey("ctrl", "a")
    return "Selected all"
