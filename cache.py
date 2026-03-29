"""Semantic query cache — avoids redundant LLM calls for repeated queries."""

import hashlib
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Default TTL: 5 minutes
DEFAULT_TTL = 300

_cache: dict[str, dict] = {}


def _make_key(query: str, model: str = "", filters: str = "") -> str:
    """Create a cache key from query + model + filters."""
    raw = f"{query.strip().lower()}|{model}|{filters}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get(query: str, model: str = "", filters: str = "") -> Optional[str]:
    """Get cached response. Returns None if not found or expired."""
    key = _make_key(query, model, filters)
    entry = _cache.get(key)
    if entry is None:
        return None

    if time.time() - entry['timestamp'] > entry['ttl']:
        # Expired
        del _cache[key]
        logger.debug(f"Cache expired for key {key}")
        return None

    logger.info(f"Cache hit for key {key} (age: {time.time() - entry['timestamp']:.0f}s)")
    return entry['response']


def put(query: str, response: str, model: str = "", filters: str = "", ttl: int = DEFAULT_TTL):
    """Store a response in cache."""
    key = _make_key(query, model, filters)
    _cache[key] = {
        'response': response,
        'timestamp': time.time(),
        'ttl': ttl,
        'query': query[:100],  # Store truncated query for debugging
    }
    logger.debug(f"Cached response for key {key} (TTL: {ttl}s)")


def invalidate_all():
    """Clear all cached entries. Call after re-indexing."""
    count = len(_cache)
    _cache.clear()
    logger.info(f"Cache invalidated: {count} entries cleared")


def stats() -> dict:
    """Return cache statistics."""
    now = time.time()
    active = {k: v for k, v in _cache.items() if now - v['timestamp'] <= v['ttl']}
    expired = len(_cache) - len(active)
    return {
        'total_entries': len(_cache),
        'active_entries': len(active),
        'expired_entries': expired,
    }
