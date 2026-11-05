import json
from loguru import logger
from core.llm import get_llm
from langchain_core.messages import SystemMessage
from navix.automation.tools import TOOL_REGISTRY

async def decompose_goal(goal: str) -> list[dict]:
    """
    Takes a high-level user goal and uses the LLM to break it down into sequential tasks.
    Returns a list of task dictionaries.
    """
    available_tools = "\n".join([f"- {name}: {info['description']}" for name, info in TOOL_REGISTRY.items()])
    
    prompt = f"""
You are the NAVIX Automation Planner, an intelligent executive AI assistant.
The user has requested the following goal: "{goal}"

CORE PRINCIPLES:
1. Brfore you start any task, first understand the context of the situation(Give me some Update)
2. Screen Understanding First: You must know what is visible before taking ation. 
3. Automation Priority: Choose the best method in this order:
   - Native API (Preferd, Whatsapp API, Email API)
   - Application Accessibil.g., UI Automation)
   - Browser Automae.g., Playwright)
   - Desktop Automation (Keyboard/Mouse)
   - Vision Automation (Screen capture/OCR, only if necessary)
4. Safety First: You MUST flag any irreversible actions (sending messages, deleting files, payments) as requiring user approval.

AVAILABLE TOOLS:
{available_tools}

Break this goal down into a sequence of atomic tasks. 
Each task should have:
1. "step": integer
2. "action": string (MUST be the exact name of one of the AVAILABLE TOOLS above)
3. "description": string (what exactly to do)
4. "requires_approval": boolean (true if this sends a message, makes a payment, or submits data)

Return ONLY a valid JSON array of these tasks. No markdown formatting or explanations.
"""
    try:
        llm = get_llm(temperature=0.3)
        result = await llm.ainvoke([SystemMessage(content=prompt)])
        response = result.content
        # Try to parse the JSON array
        # Clean up possible markdown code blocks if the LLM adds them
        clean_json = response.replace("```json", "").replace("```", "").strip()
        tasks = json.loads(clean_json)
        logger.info(f"Planner generated {len(tasks)} tasks for goal: '{goal}'")
        return tasks
    except Exception as e:
        logger.error(f"Failed to plan tasks: {e}")
        return []
