from loguru import logger

async def execute_task(task: dict) -> any:
    """
    Takes an atomic task and routes it to the correct tool/domain for execution.
    """
    action = task.get("action", "").lower()
    description = task.get("description", "")
    
    logger.info(f"Executing [{action}]: {description}")
    
    try:
        from navix.automation.tools import get_tool
        
        # We assume the planner passes the exact tool name in 'action' for Phase 2/3
        tool_func = get_tool(action)
        
        if tool_func:
            # Execute the dynamically resolved tool
            return await tool_func(description)
        else:
            logger.warning(f"No specific tool found in registry for: {action}. Simulating execution.")
            return {"status": "ok", "result": f"Simulated execution of {description}"}
            
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return {"status": "error", "error": str(e)}
