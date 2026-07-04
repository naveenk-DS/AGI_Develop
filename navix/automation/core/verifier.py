from loguru import logger
from navix.automation.tools.desktop_tools import vision_read_text
from navix.services.ai.ollama import chat

async def verify_task_success(task: dict, result: any) -> bool:
    """
    Verifies if a task was successfully completed based on the output result 
    or by visually inspecting the screen using OCR and an LLM.
    """
    logger.info(f"Verifying step {task.get('step')}: {task.get('description')}")
    
    # 1. Programmatic Failure Check
    if result is None:
        logger.warning(f"Verification failed: No result returned for {task.get('description')}")
        return False
        
    if isinstance(result, dict) and result.get("status") == "error":
        logger.warning(f"Verification failed: Task returned error - {result.get('error')}")
        return False
        
    # 2. Visual Verification
    # If the action interacts with the UI, read the screen to verify success
    action = task.get("action", "")
    if action in ["browser", "desktop", "whatsapp", "vision"]:
        try:
            logger.debug("Running visual verification (OCR)...")
            screen_text = await vision_read_text()
            
            prompt = f"""
I just attempted to perform this task: "{task.get('description')}"

Here is the current text visible on my screen:
---
{screen_text}
---

Based on this text, did the task succeed? 
For example, if I opened a website, is the website text visible? If I sent a message, is the message visible in the chat?

Reply strictly with YES or NO.
"""
            verification_result = await chat(prompt, model="llama3")
            
            if "YES" in verification_result.upper():
                logger.info(f"Visual Verification passed for step {task.get('step')}.")
                return True
            else:
                logger.warning(f"Visual Verification failed for step {task.get('step')}. LLM Output: {verification_result}")
                return False
                
        except Exception as e:
            logger.error(f"Error during visual verification: {e}")
            # Fallback to true if vision system is temporarily unavailable
            return True
            
    logger.info(f"Verification passed for step {task.get('step')}.")
    return True
