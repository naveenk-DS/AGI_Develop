import inspect
from loguru import logger
from typing import Callable, Dict, Any

# Global registry of all available automation tools
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}

def tool(name: str, description: str):
    """
    Decorator to register a function as an automation tool.
    The Tool Selector uses this registry to dynamically find and execute actions.
    """
    def decorator(func: Callable):
        TOOL_REGISTRY[name] = {
            "name": name,
            "description": description,
            "func": func,
            "signature": str(inspect.signature(func))
        }
        logger.debug(f"Registered automation tool: {name}")
        return func
    return decorator

def get_tool(name: str) -> Callable | None:
    """Retrieve a registered tool by its name."""
    tool_info = TOOL_REGISTRY.get(name)
    if tool_info:
        return tool_info["func"]
    return None

# Import all tool modules to populate the registry automatically
from . import browser_tools
from . import communication_tools
from . import desktop_tools
