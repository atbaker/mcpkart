"""Redis cache for spectator state."""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import redis.asyncio as redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
DEFAULT_CACHE_TTL = 1.0  # seconds - fallback for non-racing phases


def calculate_ttl_until_next_tick(
    race_started_at: Optional[datetime],
    current_tick: int,
    now: Optional[datetime] = None,
) -> float:
    """Calculate seconds until next tick occurs.

    Returns TTL with small buffer to ensure fresh data is available.
    Falls back to default if timing data unavailable.

    Args:
        race_started_at: When the racing phase began
        current_tick: Current tick number
        now: Current time (defaults to utcnow, mainly for testing)

    Returns:
        TTL in seconds, clamped to [0.1, 2.0] range
    """
    if race_started_at is None:
        return DEFAULT_CACHE_TTL

    if now is None:
        now = datetime.now(timezone.utc)

    # Ensure race_started_at is timezone-aware
    if race_started_at.tzinfo is None:
        race_started_at = race_started_at.replace(tzinfo=timezone.utc)

    # Next tick occurs at: race_started_at + (current_tick + 1) seconds
    next_tick_time = race_started_at + timedelta(seconds=current_tick + 1)

    # Add small buffer (100ms) to ensure tick has processed
    ttl = (next_tick_time - now).total_seconds() + 0.1

    # Clamp to reasonable range [0.1, 2.0] seconds
    return max(0.1, min(ttl, 2.0))

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client (lazy initialization)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


async def get_cached_spectator_state(race_id: str) -> Optional[dict[str, Any]]:
    """Get cached spectator state for a race.

    Args:
        race_id: The race identifier

    Returns:
        Cached spectator state dict, or None if not cached
    """
    client = await get_redis()
    cached = await client.get(f"spectator:{race_id}")
    if cached:
        return json.loads(cached)
    return None


async def set_cached_spectator_state(
    race_id: str, state: dict[str, Any], ttl: float = DEFAULT_CACHE_TTL
) -> None:
    """Cache spectator state for a race.

    Args:
        race_id: The race identifier
        state: Spectator state dict to cache
        ttl: Time-to-live in seconds (supports sub-second precision)
    """
    client = await get_redis()
    # Use PSETEX for millisecond precision
    ttl_ms = int(ttl * 1000)
    await client.psetex(f"spectator:{race_id}", ttl_ms, json.dumps(state))
