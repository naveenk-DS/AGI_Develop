from loguru import logger
import asyncio

async def request_approval(task_description: str) -> bool:
    """
    Pauses execution and asks the user for explicit approval before proceeding
    with a destructive or outbound action.
    """
    from navix.services.voice.speaker import speak
    from navix_tray import set_tray_state
    
    logger.info(f"Human-in-the-loop required for: {task_description}")
    
    set_tray_state("talking")
    prompt = f"I am ready to {task_description}. Should I proceed?"
    # Fire and forget the speech so we don't block heavily
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, speak, prompt)
    set_tray_state("listening")
    
    # TODO: In Phase 4, we will hook this up directly to the microphone listener 
    # to wait for a 'yes' or 'no'. For now, we simulate approval or log the pause.
    logger.warning("Approval simulation: Assuming YES for now during Phase 1 testing.")
    return True
