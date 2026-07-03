from navix.desktop.keyboard.shortcuts import hotkey

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
