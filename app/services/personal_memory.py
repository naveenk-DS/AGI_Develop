from datetime import datetime, date
from loguru import logger
from app.db.database import AsyncSessionLocal
from app.db.models import Config
from app.crypto.encrypt import encrypt, decrypt
from sqlalchemy import select
import json
import time

# ── In-memory context cache (avoids DB hit on every voice command) ─────────────
_context_cache: str | None = None
_context_cache_ts: float = 0.0
_CONTEXT_CACHE_TTL: float = 30.0  # seconds

MEMORY_CUSTOMER_ID = "naveen_personal"

# Default personal profile
DEFAULT_PROFILE = {
    "name": "",
    "language": "english",
    "location": "",
    "occupation": "",
    "birthday": "",
    "family": {},
    "friends": [],
    "favourites": {
        "music": "",
        "food": "",
        "sport": "",
        "hobby": ""
    },
    "important_dates": {},
    "goals": [],
    "preferences": {
        "wake_word": "Naveen",
        "pin": "6777",
        "voice": "female",
        "language": "english"
    },
    "memories": [],
    "onboarded": False
}

async def load_profile() -> dict:
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Config).where(
                    Config.customer_id == MEMORY_CUSTOMER_ID,
                    Config.key == "personal_profile"
                )
            )
            row = result.scalar_one_or_none()
            if row and row.value:
                data = decrypt(row.value)
                return data.get("value", DEFAULT_PROFILE)
    except Exception as e:
        logger.error(f"Profile load error: {e}")
    return DEFAULT_PROFILE.copy()

async def save_profile(profile: dict):
    global _context_cache, _context_cache_ts
    try:
        async with AsyncSessionLocal() as db:
            encrypted = encrypt({"value": profile})
            result = await db.execute(
                select(Config).where(
                    Config.customer_id == MEMORY_CUSTOMER_ID,
                    Config.key == "personal_profile"
                )
            )
            row = result.scalar_one_or_none()
            if row:
                row.value = encrypted
            else:
                db.add(Config(
                    customer_id=MEMORY_CUSTOMER_ID,
                    key="personal_profile",
                    value=encrypted
                ))
            await db.commit()
            # Invalidate cache so next call reads fresh data
            _context_cache = None
            _context_cache_ts = 0.0
            logger.info("Profile saved")
    except Exception as e:
        logger.error(f"Profile save error: {e}")

async def add_memory(memory: str):
    profile = await load_profile()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    profile["memories"].append({
        "text": memory,
        "time": timestamp
    })
    # keep last 100 memories
    profile["memories"] = profile["memories"][-100:]
    await save_profile(profile)
    logger.info(f"Memory added: {memory}")

async def add_family(name: str, relation: str):
    profile = await load_profile()
    profile["family"][name] = relation
    await save_profile(profile)
    return f"Got it. I will remember that {name} is your {relation}."

async def add_friend(name: str):
    profile = await load_profile()
    if name not in profile["friends"]:
        profile["friends"].append(name)
    await save_profile(profile)
    return f"Got it. I will remember {name} as your friend."

async def set_favourite(category: str, value: str):
    profile = await load_profile()
    profile["favourites"][category] = value
    await save_profile(profile)
    return f"Got it. I will remember your favourite {category} is {value}."

async def add_birthday(name: str, date_str: str):
    profile = await load_profile()
    profile["important_dates"][name] = date_str
    await save_profile(profile)
    return f"Got it. I will remember {name}'s birthday is {date_str}."

async def check_birthdays() -> list:
    profile = await load_profile()
    today = date.today().strftime("%m-%d")
    birthdays = []
    for name, date_str in profile["important_dates"].items():
        if date_str.endswith(today):
            birthdays.append(name)
    return birthdays

async def get_context_for_ai() -> str:
    global _context_cache, _context_cache_ts

    # Return cached value if still fresh
    if _context_cache is not None and (time.monotonic() - _context_cache_ts) < _CONTEXT_CACHE_TTL:
        logger.debug("Context from cache")
        return _context_cache

    profile = await load_profile()
    family_str = ", ".join([f"{n} ({r})" for n, r in profile["family"].items()])
    friends_str = ", ".join(profile["friends"])
    favs = profile["favourites"]
    recent_memories = profile["memories"][-5:]
    memory_str = "; ".join([m["text"] for m in recent_memories])

    context = f"""
Personal information about the user:
- Name: {profile['name']}
- Location: {profile['location']}
- Occupation: {profile['occupation']}
- Family: {family_str or 'not specified'}
- Friends: {friends_str or 'not specified'}
- Favourite music: {favs.get('music', 'not specified')}
- Favourite food: {favs.get('food', 'not specified')}
- Hobby: {favs.get('hobby', 'not specified')}
- Recent memories: {memory_str or 'none yet'}
"""
    _context_cache = context.strip()
    _context_cache_ts = time.monotonic()
    return _context_cache

async def is_onboarded() -> bool:
    profile = await load_profile()
    return profile.get("onboarded", False) and bool(profile.get("name"))

async def complete_onboarding(name: str, location: str = "", occupation: str = ""):
    profile = await load_profile()
    profile["name"] = name
    profile["location"] = location
    profile["occupation"] = occupation
    profile["onboarded"] = True
    await save_profile(profile)
    return f"Great, {name}! I've got your info saved."