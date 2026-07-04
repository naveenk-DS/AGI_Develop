import json
from loguru import logger
from navix.services.ai.ollama import ask_model

async def decompose_goal(goal: str) -> list[dict]:
    """
    Takes a high-level user goal and uses the LLM to break it down into sequential tasks.
    Returns a list of task dictionaries.
    """
    prompt = f"""
You are the NAVIX Automation Planner.
The user has requested the following goal: "{goal}"

Break this goal down into a sequence of atomic tasks. 
Each task should have:
1. "step": integer
2. "action": string (the tool or domain to use, e.g., 'browser', 'whatsapp', 'email', 'desktop', 'vision')
3. "description": string (what exactly to do)
4. "requires_approval": boolean (true if this sends a message, makes a payment, or submits data)

Return ONLY a valid JSON array of these tasks. No markdown formatting or explanations.
"""
    try:
        response = await ask_model(prompt, fallback="[]")
        # Try to parse the JSON array
        # Clean up possible markdown code blocks if the LLM adds them
        clean_json = response.replace("```json", "").replace("```", "").strip()
        tasks = json.loads(clean_json)
        logger.info(f"Planner generated {len(tasks)} tasks for goal: '{goal}'")
        return tasks
    except Exception as e:
        logger.error(f"Failed to plan tasks: {e}")
        return []
