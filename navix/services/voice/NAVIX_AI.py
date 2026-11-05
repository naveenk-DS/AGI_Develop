"""
NAVIX_AI.py – Core voice conversation engine.
"""
from navix.services.ai import continual_learning
import asyncio
import re
import threading
from datetime import datetime
from loguru import logger
from navix.services.voice.language_config import USER_PROFILE, SUPPORTED_LANGUAGES
from navix.services.voice.speaker import speak, interrupt_speech, is_speaking
from navix.services.voice.listener import listen_once
from navix.services.voice.wake_word import start_wake_word_listener, add_wake_callback
import httpx

OLLAMA_URL  = "http://127.0.0.1:11434/api/generate"
NAVIX_MODEL = "qwen2.5:7b"
SYSTEM_PROMPT = (
    "You are NAVIX, Naveen's personal AI companion. "
    "Talk naturally like a close friend who knows him well. "
    "Be warm, casual, and direct. Keep responses under 2 sentences for voice. "
    "Never use bullet points, markdown, or lists. "
    "React naturally — say 'hmm', 'oh interesting', 'got it' when appropriate. "
    "Never repeat yourself."
)


async def ask_model(prompt: str, context: str = "", fallback: str = "") -> str:
    """
    Send a prompt to Ollama. Retries once on timeout.
    Returns `fallback` if the model fails or times out.
    """
    full_prompt = f"{context}\n\n{prompt}".strip() if context else prompt

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=120) as client:   # 120s — model may need cold-start time
                r = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": NAVIX_MODEL,
                        "prompt": full_prompt,
                        "system": SYSTEM_PROMPT,
                        "stream": False,
                        "options": {
                            "temperature": 0.85,
                            "top_p": 0.9,
                            "num_predict": 120,
                            "repeat_penalty": 1.3,
                            "stop": ["\n\n", "User:", "Naveen:"],
                        },
                    },
                )
                if r.status_code == 200:
                    text = r.json().get("response", "").strip()
                    text = re.sub(r'\*+', '', text)
                    text = re.sub(r'#+\s*', '', text)
                    text = text.strip('"').strip("'").strip()
                    if text:
                        logger.debug(f"[model] → {text!r}")
                        return text
                else:
                    logger.error(f"Ollama HTTP {r.status_code} (attempt {attempt+1}): {r.text[:200]}")
        except Exception as e:
            logger.error(f"Ollama error (attempt {attempt+1}) [{type(e).__name__}]: {e}")
            if attempt == 0:
                await asyncio.sleep(2)

    return fallback


async def warmup_model():
    """Send a tiny ping to Ollama so the model is loaded before the first user question."""
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            logger.info(f"Warming up {NAVIX_MODEL}...")
            r = await client.post(OLLAMA_URL, json={
                "model": NAVIX_MODEL,
                "prompt": "hi",
                "stream": False,
                "options": {"num_predict": 1},
            })
            if r.status_code == 200:
                logger.info(f"{NAVIX_MODEL} warm and ready")
            else:
                logger.warning(f"Warmup got HTTP {r.status_code}")
    except Exception as e:
        logger.warning(f"Warmup failed [{type(e).__name__}]: {e}")


def get_period() -> str:
    hour = datetime.now().hour
    if 5  <= hour < 12: return "morning"
    if 12 <= hour < 17: return "afternoon"
    if 17 <= hour < 21: return "evening"
    return "night"

def get_greeting() -> str:
    """Return a simple time-based greeting for the HUD."""
    return f"Good {get_period()}, Naveen!"


async def navix_session():
    from navix.services.memory.personal_memory import is_onboarded, complete_onboarding

    from navix.services.ai.planner import get_todays_plan, save_daily_plan, get_yesterdays_plan
    from navix.services.utilities.reminder import start_reminder_loop
    from navix.services.voice.pin_auth import authenticate, is_authenticated
    from navix_tray import set_tray_state

    loop = asyncio.get_event_loop()
    set_tray_state("sleeping")

    # Warm up Ollama in background so model is loaded before first question
    asyncio.create_task(warmup_model())
    # ── Ask PIN on startup ───────────────────────────────────────────────────
    await loop.run_in_executor(None, speak, "NAVIX starting. Please enter your PIN.")
    success = await loop.run_in_executor(None, authenticate)
    if not success:
        await loop.run_in_executor(None, speak, "Wrong PIN. Shutting down.")
        return

    if not await is_onboarded():
        set_tray_state("talking")
        speak("Hi! I'm NAVIX. Before we start, what's your name?")
        set_tray_state("active")
        name_response = listen_once(duration=10)
        if name_response and name_response.strip():
            speak(f"Nice to meet you, {name_response.strip()}! Where are you based?")
            set_tray_state("active")
            location_response = listen_once(duration=10)
            await complete_onboarding(
                name=name_response.strip(),
                location=location_response.strip() if location_response else ""
            )
            speak("Perfect, I've got that saved. Let's get started!")
        else:
            speak("No problem, we can set that up later.")

    hour   = datetime.now().hour
    period = get_period()

    if 5 <= hour < 12:
        yesterday_plan = await get_yesterdays_plan()
        if yesterday_plan:
            intro = await ask_model(
                f"Good morning. Naveen's plan yesterday was: '{yesterday_plan}'. "
                "Briefly mention it and ask what he plans today. 2 sentences."
            )
        else:
            intro = await ask_model(
                "Give Naveen a warm good morning and ask his plan for today. 1-2 sentences."
            )
        if intro:
            set_tray_state("talking")
            await loop.run_in_executor(None, speak, intro)

        set_tray_state("active")
        spoken_plan = await loop.run_in_executor(None, listen_once, 20)

        if spoken_plan and spoken_plan.strip():
            await save_daily_plan(spoken_plan.strip())
            confirm = await ask_model(
                f"Naveen's plan: '{spoken_plan}'. Acknowledge warmly. 1 sentence."
            )
            if confirm:
                set_tray_state("talking")
                await loop.run_in_executor(None, speak, confirm)

        if 6 <= hour <= 9:
            try:
                from navix.services.ai.news_briefing import get_quick_headlines
                headlines = await get_quick_headlines()
                if headlines:
                    brief = await ask_model(
                        f"Read these headlines naturally in 2 sentences: {headlines}"
                    )
                    if brief:
                        set_tray_state("talking")
                        await loop.run_in_executor(None, speak, brief)
            except Exception as e:
                logger.warning(f"Briefing error: {e}")

    elif 21 <= hour <= 23:
        today_plan = await get_todays_plan()
        closing = await ask_model(
            f"Good night for Naveen. "
            f"{'Plan was: ' + today_plan + '. Ask how it went.' if today_plan else 'Ask how his day went.'} "
            "2 sentences."
        )
        if closing:
            set_tray_state("talking")
            await loop.run_in_executor(None, speak, closing)

        set_tray_state("active")
        reflection = await loop.run_in_executor(None, listen_once, 20)

        if reflection and reflection.strip():
            from navix.services.ai.planner import save_completed
            await save_completed(reflection.strip())
            night_reply = await ask_model(
                f"Naveen said: '{reflection}'. Respond warmly, wish good night. 1-2 sentences."
            )
            if night_reply:
                set_tray_state("talking")
                await loop.run_in_executor(None, speak, night_reply)

    else:
        greeting = await ask_model(f"Greet Naveen naturally for {period}. 1 sentence.")
        if greeting:
            set_tray_state("talking")
            await loop.run_in_executor(None, speak, greeting)

    # ── Background tasks & standby mode ───────────────────────────────────────
    asyncio.create_task(start_reminder_loop())
    logger.info("Startup complete — standing by for wake word 'Naveen'")


_conversation_active = False


def on_wake_word(text: str):
    global _conversation_active
    if _conversation_active:
        logger.debug("Wake word heard, conversation already active.")
        return
    _conversation_active = True

    from navix_start import get_main_loop
    loop = get_main_loop()

    future = asyncio.run_coroutine_threadsafe(handle_wake_word(text), loop)
    def _on_done(f):
        global _conversation_active
        _conversation_active = False
        try:
            f.result()
        except Exception as e:
            logger.error(f"Conversation error: {e}")
    future.add_done_callback(_on_done)

def start_navix():
    logger.info("Starting NAVIX...")
    add_wake_callback(on_wake_word)
    start_wake_word_listener()
    logger.info("NAVIX ready — say Naveen to activate")


async def handle_wake_word(text: str):
    from navix.services.voice.pin_auth import authenticate, is_authenticated
    from navix.services.voice.wake_word import set_handling, clear_handling
    from navix_tray import set_tray_state

    loop = asyncio.get_event_loop()

    set_tray_state("listening")

    # ── PIN check ────────────────────────────────────────────────────────────
    if not is_authenticated():
        await loop.run_in_executor(None, speak, "Please enter your PIN")
        success = authenticate()
        if not success:
            await loop.run_in_executor(None, speak, "Wrong PIN. Locked.")
            set_tray_state("sleeping")
            return

    # ── Activation greeting ──────────────────────────────────────────────────
    activation = await ask_model(
        "Naveen just activated you. Say one short natural response. Max 5 words.",
        fallback="Yes Naveen?"
    )
    set_tray_state("talking")
    await loop.run_in_executor(None, speak, activation)

    # ── Continuous conversation loop ─────────────────────────────────────────
    empty_turns = 0
    while True:
        set_tray_state("active")
        from navix.routers.hud import push_hud
        push_hud(state="listening")
        # Run blocking listen_once() in executor so event loop stays responsive
        command = await loop.run_in_executor(None, listen_once, 15)

        if not command or not command.strip():
            empty_turns += 1
            if empty_turns >= 2:
                logger.info("No speech detected — returning to sleep mode")
                set_tray_state("sleeping")
                push_hud(state="ready")
                break
            continue
        empty_turns = 0

        command_lower = command.lower().strip()
        logger.info(f"Command: {command}")
        push_hud(question=command, state="thinking")

        # ── Only exit on stop/bye ────────────────────────────────────────────
        if any(w in command_lower for w in [
            "stop", "bye", "goodbye", "that's all",
            "ok bye", "okay bye", "exit",
            "go to sleep", "sleep navix", "close navix"
        ]):
            farewell = await ask_model(
                "Naveen said bye. Short warm goodbye. 1 sentence."
            )
            set_tray_state("talking")
            await loop.run_in_executor(None, speak, farewell or "Okay Naveen, talk later!")
            set_tray_state("sleeping")
            break

        # ── Lock ─────────────────────────────────────────────────────────────
        if any(w in command_lower for w in ["lock", "lock navix"]):
            from navix.services.voice.pin_auth import lock
            lock()
            lock_msg = await ask_model("You are locked. Confirm briefly. 1 sentence.")
            set_tray_state("talking")
            push_hud(answer=lock_msg or "Locked.", state="speaking")
            await loop.run_in_executor(None, speak, lock_msg or "Locked.")
            set_tray_state("sleeping")
            push_hud(state="ready")
            break

        # ── Reminder ─────────────────────────────────────────────────────────
        remind_match = re.search(
            r"remind me (?:to )?(.+?) at (\d+)(?::(\d+))?\s*(am|pm)?",
            command_lower
        )
        if remind_match:
            from navix.services.utilities.reminder import add_reminder
            message = remind_match.group(1)
            hour    = int(remind_match.group(2))
            minute  = int(remind_match.group(3) or 0)
            ampm    = remind_match.group(4)
            if ampm == "pm" and hour < 12:
                hour += 12
            await add_reminder(message, hour, minute)
            confirm = await ask_model(
                f"Reminder set for '{message}' at {hour}:{minute:02d}. Confirm naturally. 1 sentence."
            )
            set_tray_state("talking")
            await loop.run_in_executor(None, speak, confirm)
            continue

        # ── Intent-based routing ──────────────────────────────────────────────
        # ── Intent classification — model decides routing ────────────────────
        from navix.services.ai.intent_classifier import classify_intent
        intent = await classify_intent(command)
        logger.info(f"Intent: {intent}")

        if intent in ["pc", "browser", "vision", "automation"]:
            from navix.automation.core.controller import execute_autonomous_workflow
            set_tray_state("working")
            push_hud(answer="Planning and executing workflow...", state="thinking")
            
            response = await execute_autonomous_workflow(command)
            
            set_tray_state("talking")
            push_hud(answer=response, state="speaking")
            await loop.run_in_executor(None, speak, response)
            set_tray_state("active")
            continue

        elif intent == "code":
            set_tray_state("talking")
            from navix.services.ai.code_writer import write_code_to_file
            response = await write_code_to_file(command)
            push_hud(answer=response, state="speaking")
            await loop.run_in_executor(None, speak, response)
            set_tray_state("active")
            continue

        
        elif intent == "rag":
            set_tray_state("talking")
            response = None
            try:
                from core.rag_chain import get_rag_chain
                chain = get_rag_chain()
                result = await loop.run_in_executor(
                    None, lambda: chain.invoke({"query": command})
                )
                response = result if isinstance(result, str) else (
                    result.get("result", str(result)) if isinstance(result, dict) else str(result)
                )
                # If RAG returned a non-answer, treat it as a failure
                if not response or len(response.strip()) < 5:
                    response = None
            except Exception as e:
                logger.error(f"RAG error (falling back to chat): {e}")
                response = None

            # Fall back to Ollama chat if RAG failed or returned nothing
            if response is None:
                logger.info("RAG fallback → asking chat model")
                response = await ask_model(
                    command,
                    fallback="I didn't quite get that, Naveen. Can you say it again?"
                )
            push_hud(answer=response, state="speaking")
            await loop.run_in_executor(None, speak, response)
            set_tray_state("active")
            continue

        else:  # chat
            set_tray_state("talking")
            response = await ask_model(
                command,
                fallback="I didn't quite get that, Naveen. Can you say it again?"
            )
            push_hud(answer=response, state="speaking")
            await loop.run_in_executor(None, speak, response)
            set_tray_state("active")
            continue




# ── Direct command processing (bypasses LangGraph checkpointer) ──────────────
# NOTE: The LangGraph graph with AsyncSqliteSaver is NOT used here.
# Reason: aiosqlite ties its internal I/O thread to the event loop that created
# the connection. When ainvoke() is called from a different async context
# (e.g. via run_coroutine_threadsafe from a wake-word callback thread) the
# connection's internal queue dispatch deadlocks → 90-100 s hang.
# Fix: call Ollama / RAG chain directly — same net result, no checkpointer.

async def process_command(text: str, thread_id: str = "navix-main", known_intent: str = None) -> str:
    """
    Handle rag / chat commands directly — no LangGraph checkpointer involved.
    This avoids the aiosqlite event-loop mismatch that caused ainvoke() hangs.
    """
    import asyncio
    try:
        from navix.services.memory.personal_memory import get_context_for_ai
        personal_context = await get_context_for_ai()

        tool = known_intent or "chat"

        if tool == "rag":
            from core.rag_chain import get_rag_chain
            chain = get_rag_chain()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: chain.invoke({"query": text})
            )
            return result if isinstance(result, str) else (
                result.get("result", str(result)) if isinstance(result, dict) else str(result)
            )
        else:
            # chat — call Ollama directly via ask_model()
            return await ask_model(
                text,
                context=personal_context,
                fallback="I didn't quite catch that, Naveen."
            )

    except Exception as e:
        logger.error(f"process_command error: {e}")
        return "Sorry, something went wrong."