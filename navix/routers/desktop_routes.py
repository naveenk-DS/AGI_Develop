from fastapi import APIRouter
from pydantic import BaseModel
from loguru import logger

class CommandRequest(BaseModel):
    command: str

class BrowserRequest(BaseModel):
    url: str = None
    query: str = None

router = APIRouter(prefix="/desktop", tags=['desktop'])

@router.post("/app/open")
async def open_app(body: CommandRequest):
    try:
        from navix.services.ai.command_parser import launch_app
        result = await launch_app(body.command.lower())
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.get("/app/list")
async def list_apps():
    from navix.services.ai.command_parser import APPS
    return {"apps": list(APPS.keys()), "count": len(APPS)}


@router.post("/pc/command")
async def pc_command(body: CommandRequest):
    try:
        from navix.desktop.automation.actions import execute_pc_command
        result = await execute_pc_command(body.command)
        return {"status": "ok", "result": result or "Command not recognized"}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/pc/type")
async def pc_type(body: CommandRequest):
    try:
        from navix.desktop.keyboard.typing import type_text
        result = type_text(body.command)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/pc/screenshot")
async def pc_screenshot():
    try:
        import os
        os.makedirs("C:/Users/Naveen/AGI_Develop/screenshots", exist_ok=True)
        from navix.desktop.screen.screenshot import take_screenshot
        result = take_screenshot("C:/Users/Naveen/AGI_Develop/screenshots/screenshot.png")
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/pc/key")
async def pc_key(body: CommandRequest):
    try:
        from navix.desktop.keyboard.typing import press_key
        result = press_key(body.command)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}
