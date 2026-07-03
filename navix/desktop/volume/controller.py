from navix.desktop.keyboard.typing import press_key

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
