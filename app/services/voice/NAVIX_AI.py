"""
NAVIX_AI.py — Core voice conversation engine.
All responses come from the navix-personality model via Ollama directly.
Zero hardcoded sentences. NAVIX speaks like a friend, not a chatbot.
"""
import asyncio
import re
import threading
import time
from datetime import datetime
from loguru import logger
from app.services.voice.language_config import USER_PROFILE, SUPPORTED_LANGUAGES
from app.services.voice.speaker import speak, interrupt_speech, is_speaking
from app.services.voice.listener import listen_once
from app.services.voice.wake_word import start_wake_word_listener, add_wake_callback
import httpx

# ── Model config — direct Ollama, no FastAPI middleman ────────────────────────
OLLAMA_URL  = "http://localhost:11434/api/generate"
NAVIX_MODEL = "navix-personality"   # your trained model

# ── System prompt injected into every conversation turn ───────────────────────
SYSTEM_PROMPT = (
    "You are NAVIX, Naveen's personal AI companion. "
    "Talk naturally like a close friend who knows him well. "
    "Be warm, casual, and direct. Keep responses under 2 sentences for voice. "
    "Never use bullet points, markdown, or lists. "
    "React naturally — say 'hmm', 'oh interesting', 'got it' when appropriate. "
    "Never repeat yourself. "
    "To keep the conversation going continuously, frequently ask short, natural follow-up questions."
)


async def ask_model(prompt: str, context: str = "") -> str:
    """
    Call navix-personality directly on Ollama.
    No FastAPI server dependency — works even when the backend is down.
    """
    full_prompt = f"{context}\n\n{prompt}".strip() if context else prompt
    try:
        async with httpx.AsyncClient(timeout=20) as client:
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
                # strip any markdown that slipped through
                text = re.sub(r'\*+', '', text)
                text = re.sub(r'#+\s*', '', text)
                text = text.strip('"').strip("'").strip()
                logger.debug(f"[model] → {text!r}")
                return text
    except Exception as e:
        logger.error(f"Ollama error: {e}")
    return ""


def get_period() -> str:
    hour = datetime.now().hour
    if 5  <= hour < 12: return "morning"
    if 12 <= hour < 17: return "afternoon"
    if 17 <= hour < 21: return "evening"
    return "night"


# ── Startup session — morning/night rituals ────────────────────────────────────
async def navix_session():
    from app.services.planner import get_todays_plan, save_daily_plan, get_yesterdays_plan
    from app.services.reminder import start_reminder_loop
    from navix_tray import set_tray_state
    from app.services.voice.wake_word import set_handling, clear_handling

    hour   = datetime.now().hour
    period = get_period()

    # ── MORNING (5 AM – 11 AM) ───────────────────────────────────────────────
    if 5 <= hour < 12:
        yesterday_plan = await get_yesterdays_plan()
        if yesterday_plan:
            intro = await ask_model(
                f"Good morning. Naveen's plan yesterday was: '{yesterday_plan}'. "
                "Briefly mention it and ask what he plans to do today. 2-3 sentences."
            )
        else:
            intro = await ask_model(
                "Give Naveen a warm good morning and ask what his plan is for today. 1-2 sentences."
            )

        if intro:
            set_tray_state("talking")
            speak(intro)

        # Listen for today's plan — lock mic first
        set_handling()
        set_tray_state("active")
        spoken_plan = listen_once(duration=20)
        clear_handling()

        if spoken_plan and spoken_plan.strip():
            await save_daily_plan(spoken_plan.strip())
            confirm = await ask_model(
                f"Naveen's plan for today: '{spoken_plan}'. Acknowledge it warmly. 1 sentence."
            )
            if confirm:
                set_tray_state("talking")
                speak(confirm)

        # Morning news briefing (6–9 AM only)
        if 6 <= hour <= 9:
            try:
                from app.services.news_briefing import get_quick_headlines
                headlines = await get_quick_headlines()
                if headlines:
                    brief = await ask_model(
                        f"Read these news headlines naturally to Naveen in 2 sentences: {headlines}"
                    )
                    if brief:
                        set_tray_state("talking")
                        speak(brief)
            except Exception as e:
                logger.warning(f"Briefing error: {e}")

    # ── NIGHT CLOSING (9 PM – 11 PM) ─────────────────────────────────────────
    elif 21 <= hour <= 23:
        today_plan = await get_todays_plan()
        closing = await ask_model(
            f"Good night closing for Naveen. "
            f"{'His plan today was: ' + today_plan + '. Ask how it went.' if today_plan else 'Ask how his day went.'} "
            "Wish him good night. 2 sentences."
        )
        if closing:
            set_tray_state("talking")
            speak(closing)

        # Listen for reflection — lock mic
        set_handling()
        set_tray_state("active")
        reflection = listen_once(duration=20)
        clear_handling()

        if reflection and reflection.strip():
            from app.services.planner import save_completed
            await save_completed(reflection.strip())
            night_reply = await ask_model(
                f"Naveen said about his day: '{reflection}'. "
                "Respond warmly, wish him good night. 1-2 sentences."
            )
            if night_reply:
                set_tray_state("talking")
                speak(night_reply)

    # ── OTHER TIMES — simple greeting ─────────────────────────────────────────
    else:
        greeting = await ask_model(
            f"Greet Naveen naturally for {period}. 1 sentence."
        )
        if greeting:
            set_tray_state("talking")
            speak(greeting)

    asyncio.create_task(start_reminder_loop())
    set_tray_state("sleeping")


_conversation_active = False

# ── Wake word → conversation ───────────────────────────────────────────────────
def on_wake_word(text: str):
    global _conversation_active
    if _conversation_active:
        logger.debug("Wake word heard, but conversation already active.")
        return
    _conversation_active = True
    t = threading.Thread(target=_run_conversation, daemon=True)
    t.start()


def _run_conversation():
    global _conversation_active
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(handle_wake_word(""))
    finally:
        loop.close()
        _conversation_active = False


def start_navix():
    logger.info("Starting NAVIX...")
    add_wake_callback(on_wake_word)
    start_wake_word_listener()
    logger.info("NAVIX ready")


# ── Main conversation loop ─────────────────────────────────────────────────────
async def handle_wake_word(text: str):
    from app.services.voice.personality import thinking_sound, acknowledgement
    from navix_tray import set_tray_state

    set_tray_state("listening")

    # Activation greeting — model decides what to say
    activation = await ask_model(
        "Naveen just activated you. Say one short natural response showing you're ready. Max 5 words."
    )
    set_tray_state("talking")
    speak(activation)

    silence_retries = 0
    MAX_SILENCE = 5            # give 5 empty listens before giving up
    while True:
        set_tray_state("active")
        command = listen_once(duration=30)

        if not command or not command.strip():
            silence_retries += 1
            if silence_retries >= MAX_SILENCE:
                logger.info("NAVIX went to sleep due to silence.")
                farewell = await ask_model(
                    "Naveen went quiet. Say a short natural goodbye and go back to sleep. 1 sentence."
                )
                set_tray_state("talking")
                speak(farewell)
                set_tray_state("sleeping")
                break
            continue
        silence_retries = 0

        command_lower = command.lower().strip()
        logger.info(f"Command: {command}")

        # (Stop/bye commands removed at user request — NAVIX will respond conversationally instead)

        # ── Lock ───────────────────────────────────────────────────────────────
        if any(w in command_lower for w in ["lock", "lock navix", "lock yourself"]):
            from app.services.voice.pin_auth import lock
            lock()
            lock_msg = await ask_model("You are being locked. Confirm briefly. 1 sentence.")
            set_tray_state("talking")
            speak(lock_msg)
            set_tray_state("sleeping")
            break

        # ── Reminder ───────────────────────────────────────────────────────────
        remind_match = re.search(
            r"remind me (?:to )?(.+?) at (\d+)(?::(\d+))?\s*(am|pm)?",
            command_lower
        )
        if remind_match:
            from app.services.reminder import add_reminder
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
            speak(confirm)
            continue

        # ── PC / browser commands ──────────────────────────────────────────────
        from app.services.command_parser import execute_browser_command
        from app.services.pc_command_parser import execute_pc_command

        pc_result = await execute_pc_command(command)
        if pc_result:
            response = await ask_model(
                f"You just did: {pc_result}. Confirm casually in 1 sentence."
            )
            set_tray_state("talking")
            speak(response)
            continue

        browser_result = await execute_browser_command(command)
        if browser_result:
            response = await ask_model(
                f"You just did: {browser_result}. Confirm casually in 1 sentence."
            )
            set_tray_state("talking")
            speak(response)
            continue

        # ── Everything else — model handles it fully ───────────────────────────
        set_tray_state("talking")
        thinking = thinking_sound()
        speak(thinking)

        response = await ask_model(command)
        if response:
            speak(response)
        set_tray_state("active")