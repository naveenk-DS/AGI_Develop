import hashlib
import json
from loguru import logger

# Simple in-memory cache
_cache: dict = {}
_cache_hits = 0
_cache_misses = 0

def make_key(prefix: str, data: dict) -> str:
    content = json.dumps(data, sort_keys=True)
    return f"{prefix}:{hashlib.md5(content.encode()).hexdigest()}"

def get_cached(key: str):
    global _cache_hits, _cache_misses
    if key in _cache:
        _cache_hits += 1
        logger.debug(f"Cache HIT: {key[:30]}")
        return _cache[key]
    _cache_misses += 1
    return None

def set_cached(key: str, value, ttl_seconds: int = 300):
    import time
    _cache[key] = {
        "value": value,
        "expires": time.time() + ttl_seconds
    }

def get_cache_stats() -> dict:
    total = _cache_hits + _cache_misses
    hit_rate = round(_cache_hits / total * 100, 1) if total > 0 else 0
    return {
        "hits":     _cache_hits,
        "misses":   _cache_misses,
        "hit_rate": f"{hit_rate}%",
        "cached_items": len(_cache)
    }

def clear_cache():
    global _cache, _cache_hits, _cache_misses
    _cache = {}
    _cache_hits = 0
    _cache_misses = 0
    logger.info("Cache cleared")

def cleanup_expired():
    import time
    expired = [k for k, v in _cache.items() if v["expires"] < time.time()]
    for k in expired:
        del _cache[k]
    if expired:
        logger.info(f"Cleaned {len(expired)} expired cache entries")