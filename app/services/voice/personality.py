import random
from loguru import logger

# ── Filler sounds ─────────────────────────────────────────────────────────────
THINKING_SOUNDS = [
    "Hmm...", "Oh okay...", "Let me think...",
    "Wait...", "Ah...", "Right...", "Okay so...",
    "Mmm let me check...", "Oh interesting...", "Sure sure..."
]

ACKNOWLEDGEMENTS = [
    "Got it!", "Sure!", "Of course!", "Absolutely!",
    "No problem!", "On it!", "Yeah sure!", "Okay!"
]

GREETINGS = [
    "Hey Naveen! What's up?",
    "Naveen! Good to hear you.",
    "Hey! How's it going?",
    "Naveen! What are we doing today?",
    "Hey there! What do you need?",
]

FOLLOW_UPS = [
    "Anything else?",
    "What else you got?",
    "Need anything more?",
    "What's next?",
    "I'm here, what else?",
]

DONE = [
    "Done! What else?",
    "There you go! Anything else?",
    "All good! What's next?",
    "Got it sorted! Need anything else?",
]

CONFUSED = [
    "Hmm I didn't quite catch that, say again?",
    "Wait, can you repeat that?",
    "Sorry didn't get that, say again?",
    "Hmm what was that?",
]

RESUMING = [
    "Anyway, as I was saying...",
    "So where was I... right...",
    "Coming back to what I said...",
    "Okay so continuing...",
]

WEATHER_RESPONSES = [
    "Sure! Let me check that for you.",
    "On it! Pulling up weather now.",
    "Yeah sure, checking Chennai weather.",
]

BROWSER_RESPONSES = [
    "Sure, opening that for you!",
    "On it!",
    "Yeah no problem, opening now.",
    "Got it, pulling that up.",
]

def thinking_sound() -> str:
    return random.choice(THINKING_SOUNDS)

def acknowledgement() -> str:
    return random.choice(ACKNOWLEDGEMENTS)

def greeting() -> str:
    return random.choice(GREETINGS)

def follow_up() -> str:
    return random.choice(FOLLOW_UPS)

def done() -> str:
    return random.choice(DONE)

def confused() -> str:
    return random.choice(CONFUSED)

def resuming() -> str:
    return random.choice(RESUMING)

def get_action_response(action: str) -> str:
    if "weather" in action.lower():
        return random.choice(WEATHER_RESPONSES)
    if any(w in action.lower() for w in ["open", "browser", "youtube", "chrome"]):
        return random.choice(BROWSER_RESPONSES)
    return random.choice(ACKNOWLEDGEMENTS)

def wrap_as_friend(response: str, emotion: str = "neutral") -> str:
    response = response.strip()

    # remove markdown
    import re
    response = re.sub(r'\*\*(.+?)\*\*', r'\1', response)
    response = re.sub(r'\*(.+?)\*', r'\1', response)
    response = re.sub(r'#+\s', '', response)
    response = re.sub(r'^\d+\.\s', '', response, flags=re.MULTILINE)
    response = re.sub(r'^-\s', '', response, flags=re.MULTILINE)

    # add natural prefix based on emotion
    prefixes = {
        "joy":      ["Oh nice! ", "That's great! ", "Love it! "],
        "sadness":  ["Aw Naveen... ", "Hey I hear you... ", "That's tough... "],
        "anger":    ["I get it, that's frustrating. ", "Yeah that's annoying. "],
        "fear":     ["Hey don't worry. ", "It's okay Naveen. "],
        "surprise": ["Oh wow! ", "Wait seriously?! ", "No way! "],
        "neutral":  ["", "", "So, ", "Okay so, "]
    }

    prefix_list = prefixes.get(emotion, prefixes["neutral"])
    prefix = random.choice(prefix_list)

    return f"{prefix}{response}"