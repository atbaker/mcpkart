"""Anonymous racer name generation and session management."""

import random
from typing import Optional

import redis.asyncio as aioredis

# Unicode animal emojis for anonymous racers
# Tuple format: (name, emoji)
ANIMAL_EMOJIS = [
    ("Dog", "🐕"),
    ("Cat", "🐈"),
    ("Mouse", "🐁"),
    ("Rabbit", "🐇"),
    ("Fox", "🦊"),
    ("Bear", "🐻"),
    ("Panda", "🐼"),
    ("Koala", "🐨"),
    ("Tiger", "🐯"),
    ("Lion", "🦁"),
    ("Cow", "🐄"),
    ("Pig", "🐷"),
    ("Frog", "🐸"),
    ("Monkey", "🐵"),
    ("Chicken", "🐔"),
    ("Penguin", "🐧"),
    ("Bird", "🐦"),
    ("Eagle", "🦅"),
    ("Duck", "🦆"),
    ("Owl", "🦉"),
    ("Wolf", "🐺"),
    ("Horse", "🐴"),
    ("Unicorn", "🦄"),
    ("Zebra", "🦓"),
    ("Deer", "🦌"),
    ("Giraffe", "🦒"),
    ("Elephant", "🐘"),
    ("Rhino", "🦏"),
    ("Hippo", "🦛"),
    ("Camel", "🐪"),
    ("Llama", "🦙"),
    ("Kangaroo", "🦘"),
    ("Sloth", "🦥"),
    ("Otter", "🦦"),
    ("Skunk", "🦨"),
    ("Badger", "🦡"),
    ("Raccoon", "🦝"),
    ("Hedgehog", "🦔"),
    ("Bat", "🦇"),
    ("Dragon", "🐉"),
    ("Snake", "🐍"),
    ("Turtle", "🐢"),
    ("Crocodile", "🐊"),
    ("Whale", "🐋"),
    ("Dolphin", "🐬"),
    ("Fish", "🐟"),
    ("Shark", "🦈"),
    ("Octopus", "🐙"),
    ("Butterfly", "🦋"),
    ("Bee", "🐝"),
]

REDIS_KEY_PREFIX = "mcpkart:anon:"
SESSION_TTL_SECONDS = 86400  # 24 hours


async def get_or_create_anonymous_name(
    redis_client: aioredis.Redis,
    session_id: str,
) -> tuple[str, str]:
    """Get existing or create new anonymous name for a session.

    Args:
        redis_client: Redis async client
        session_id: Unique session identifier

    Returns:
        Tuple of (animal_name, emoji) e.g. ("Eagle", "🦅")
    """
    key = f"{REDIS_KEY_PREFIX}{session_id}"

    # Check if session already has an assigned animal
    existing = await redis_client.get(key)
    if existing:
        # Format: "Eagle:🦅"
        name, emoji = existing.split(":", 1)
        # Refresh TTL on access
        await redis_client.expire(key, SESSION_TTL_SECONDS)
        return (name, emoji)

    # Assign random animal
    animal_name, emoji = random.choice(ANIMAL_EMOJIS)

    # Store with TTL
    await redis_client.setex(key, SESSION_TTL_SECONDS, f"{animal_name}:{emoji}")

    return (animal_name, emoji)


def format_anonymous_player_id(session_id: str) -> str:
    """Create the internal player_id for an anonymous session.

    Args:
        session_id: Unique session identifier

    Returns:
        Player ID in format "anon:{session_id}"
    """
    return f"anon:{session_id}"


def format_display_name(animal_name: str, emoji: str, suffix: Optional[int] = None) -> str:
    """Format the display name for an anonymous racer.

    Args:
        animal_name: The animal name (e.g., "Eagle")
        emoji: The emoji (e.g., "🦅")
        suffix: Optional numeric suffix for uniqueness (e.g., 2)

    Returns:
        Display name like "Anonymous Eagle 🦅" or "Anonymous Eagle 🦅 2"
    """
    base = f"Anonymous {animal_name} {emoji}"
    if suffix and suffix > 1:
        return f"{base} {suffix}"
    return base


def is_anonymous_player(player_id: str) -> bool:
    """Check if a player_id represents an anonymous user.

    Args:
        player_id: The player identifier to check

    Returns:
        True if the player is anonymous
    """
    return player_id.startswith("anon:")
