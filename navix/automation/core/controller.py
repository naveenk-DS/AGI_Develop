import asyncio
from loguru import logger
from navix.automation.core.planner import decompose_goal
from navix.automation.core.executor import execute_task
from navix.automation.core.verifier import verify_task_success
from navix.automation.core.human_approval import request_approval

async def execute_autonomous_workflow(goal: str):
    """
    The main orchestrator for the Agentic Workflow Engine.
    Takes a high-level goal, plans it, and executes steps sequentially.
    """
    logger.info(f"=== Starting Autonomous Workflow ===")
    logger.info(f"Goal: {goal}")
    
    # 1. Plan
    tasks = await decompose_goal(goal)
    if not tasks:
        logger.error("Workflow failed: Planner could not decompose the goal.")
        return "I couldn't figure out how to plan that task."
        
    logger.info(f"Workflow planned with {len(tasks)} steps.")
    
    # 2. Execute & Verify Loop
    for task in tasks:
        # Human-in-the-loop check
        if task.get("requires_approval", False):
            approved = await request_approval(task.get("description"))
            if not approved:
                logger.warning(f"Workflow aborted by user at step {task.get('step')}.")
                return "Task aborted by user."
        
        # Execute
        result = await execute_task(task)
        
        # Verify
        success = await verify_task_success(task, result)
        if not success:
            logger.error(f"Workflow failed at step {task.get('step')}. Attempting recovery...")
            # TODO: Add retry/recovery logic
            return f"I ran into an issue while trying to: {task.get('description')}"
            
        # Small delay between tasks for stability
        await asyncio.sleep(1.0)
        
    logger.info("=== Autonomous Workflow Complete ===")
    return "I have successfully completed all the steps for your request."
