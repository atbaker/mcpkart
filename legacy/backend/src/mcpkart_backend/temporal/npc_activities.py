"""Temporal activities for NPC spawning and cleanup."""

import os

import redis.asyncio as redis
from temporalio import activity

from mcpkart_backend.npc import NPCSpawner, load_npc_config


@activity.defn
async def spawn_npcs(race_id: str, count: int) -> dict:
    """Spawn NPC racers for a race.

    This is a fire-and-forget activity - it spawns Docker containers and returns
    immediately without waiting for them to complete.

    NPC tokens are dynamically generated and stored in Redis at spawn time.

    Args:
        race_id: Race to spawn NPCs for
        count: Number of NPCs to spawn

    Returns:
        Dict with spawned NPC info
    """
    activity.logger.info(f"Spawning {count} NPCs for race {race_id}")

    # Load configuration
    config = load_npc_config()

    # Connect to Redis for process tracking and token storage
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url)

    try:
        spawner = NPCSpawner(
            config=config,
            redis_client=redis_client,
        )

        # Get MCP server URL from environment (overrides config)
        mcp_server_url = os.environ.get("MCP_SERVER_URL")

        spawned = await spawner.spawn_npcs(
            race_id=race_id,
            count=count,
            mcp_server_url=mcp_server_url,
        )

        return {
            "spawned": len(spawned),
            "npcs": [
                {
                    "name": npc.npc_name,
                    "container_id": npc.container_id[:12] if npc.container_id else None,
                }
                for npc in spawned
            ],
        }

    finally:
        await redis_client.aclose()


@activity.defn
async def cleanup_npcs(race_id: str) -> dict:
    """Clean up NPC containers for a finished race.

    Args:
        race_id: Race to clean up

    Returns:
        Dict with cleanup info
    """
    activity.logger.info(f"Cleaning up NPCs for race {race_id}")

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    redis_client = redis.from_url(redis_url)

    try:
        spawner = NPCSpawner(redis_client=redis_client)
        cleaned = await spawner.cleanup_npcs(race_id)

        return {"cleaned": cleaned}

    finally:
        await redis_client.aclose()
