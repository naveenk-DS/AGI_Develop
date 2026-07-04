from navix.automation.tools import tool
from navix.desktop.automation.actions import execute_pc_command
from navix.desktop.vision.screen_reader import describe_screen, read_text_on_screen
from navix.desktop.vision.ocr import click_element_by_vision

@tool(
    name="desktop_command", 
    description="Executes a system-level PC command like opening an app, typing, or pressing shortcuts."
)
async def desktop_command(command: str):
    return await execute_pc_command(command)

@tool(
    name="vision_describe", 
    description="Takes a screenshot and returns a visual description of what is on the screen."
)
async def vision_describe(query: str = ""):
    return await describe_screen(query)

@tool(
    name="vision_read_text", 
    description="Uses OCR to read all visible text on the screen."
)
async def vision_read_text(query: str = ""):
    return await read_text_on_screen()

@tool(
    name="vision_click", 
    description="Uses OCR and computer vision to find an element on the screen and click it."
)
async def vision_click(element_name: str):
    return await click_element_by_vision(element_name)
