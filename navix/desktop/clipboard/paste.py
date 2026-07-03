from navix.desktop.keyboard.shortcuts import hotkey

def paste() -> str:
    hotkey("ctrl", "v")
    return "Pasted"
