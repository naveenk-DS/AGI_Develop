import os
import asyncio
from loguru import logger
from navix.automation.core.planner import decompose_goal
from navix.automation.core.executor import execute_task
from navix.automation.core.verifier import verify_task_success
from navix.automation.core.human_approval import request_approval
from core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

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
    workflow_results = []
    
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
            
            # Use the new Root Cause Analysis prompt to diagnose the failure
            diagnosis_prompt_path = os.path.join(os.path.dirname(__file__), "..", "DIAGNOSIS_PROMPT.md")
            try:
                with open(diagnosis_prompt_path, "r", encoding="utf-8") as f:
                    diagnosis_rules = f.read()
                    
                failure_prompt = f"""
{diagnosis_rules}

The following task just failed during execution:
Task: {task.get('description')}
Action/Tool: {task.get('action')}
Result/Error Output: {result}

Follow the rules above. Diagnose the root cause of this failure and generate the Required Diagnostic Report to present to the user.
"""
                llm = get_llm(temperature=0.2)
                diagnostic_response = await llm.ainvoke([SystemMessage(content=failure_prompt)])
                return diagnostic_response.content
            except Exception as e:
                logger.error(f"Failed to generate diagnostic report: {e}")
                return f"I ran into an issue while trying to: {task.get('description')}\nError: {result}"
            
        workflow_results.append({
            "action": task.get("action"),
            "description": task.get("description"),
            "result": result
        })
        
        # Small delay between tasks for stability
        await asyncio.sleep(1.0)
        
    logger.info("=== Autonomous Workflow Complete ===")
    
    # 3. Summarize the results for the user
    summary_prompt = f"""
You are NAVIX, an intelligent AI assistant. 
The user asked you to do the following: "{goal}"

You have just successfully completed this request by executing several autonomous steps.
Here is the raw data and results retrieved from those steps:
{workflow_results}

Your job is to read this data and provide a natural, conversational response back to the user.
If the user asked you to read something, READ IT TO THEM clearly from the data provided. 
If you clicked or typed something, confirm it was done.
Be warm, helpful, and concise. Do NOT use markdown. Do NOT list the steps you took unless asked.
"""
    try:
        llm = get_llm(temperature=0.7)
        final_response = await llm.ainvoke([SystemMessage(content=summary_prompt)])
        return final_response.content
    except Exception as e:
        logger.error(f"Failed to generate final summary: {e}")
        return "I have successfully completed your request."
