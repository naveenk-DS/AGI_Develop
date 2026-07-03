from navix.desktop.vision.screen_reader import ask_llava

async def find_element_on_screen(element: str) -> dict:
    result = await ask_llava(
        f"Find the '{element}' on this screen. "
        f"Tell me approximately where it is — top-left, top-right, center, "
        f"bottom-left, or bottom-right of the screen. "
        f"Also describe what it looks like. Be brief."
    )
    return {"description": result, "element": element}
