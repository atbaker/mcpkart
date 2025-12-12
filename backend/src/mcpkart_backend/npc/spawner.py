"""NPC container spawner."""

import asyncio
import json
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import docker
import redis.asyncio as redis

from .config import NPCConfig, NPCDefinition, load_npc_config

logger = logging.getLogger(__name__)

# Redis key prefix for NPC tokens (shared with backend auth)
NPC_TOKEN_KEY_PREFIX = "npc:token"
NPC_TOKEN_TTL_SECONDS = 1200  # 20 minutes

# Map CLI tool names to Docker images
NPC_IMAGES = {
    "vibe": "mcpkart-vibe:latest",
    # Future: "codex": "mcpkart-codex:latest",
}


@dataclass
class SpawnedNPC:
    """Information about a spawned NPC container."""

    npc_name: str
    token_username: str
    spawned_at: str  # ISO format
    container_id: Optional[str] = None


class NPCSpawner:
    """Spawns and manages NPC racer containers."""

    def __init__(
        self,
        config: Optional[NPCConfig] = None,
        redis_client: Optional[redis.Redis] = None,
    ):
        """Initialize spawner.

        Args:
            config: NPC configuration. Loaded from default path if None.
            redis_client: Redis client for process tracking and token storage.
                         Required for spawning (tokens stored in Redis).
        """
        self.config = config or load_npc_config()
        self.redis = redis_client
        self.docker_client = docker.from_env()

    def _redis_key(self, race_id: str) -> str:
        """Get Redis key for storing NPC process info."""
        return f"npc:race:{race_id}:processes"

    async def _store_process_info(self, race_id: str, npc: SpawnedNPC) -> None:
        """Store spawned NPC process info in Redis."""
        if self.redis is None:
            return

        key = self._redis_key(race_id)

        # Get existing list or create new
        existing = await self.redis.get(key)
        processes = json.loads(existing) if existing else []

        processes.append(
            {
                "container_id": npc.container_id,
                "npc_name": npc.npc_name,
                "token_username": npc.token_username,
                "spawned_at": npc.spawned_at,
            }
        )

        # Store with 20-minute expiry (longer than max race time + buffer)
        await self.redis.set(key, json.dumps(processes), ex=1200)

    async def _generate_token(
        self,
        username: str,
        race_id: str,
        npc_name: str,
        cli_tool: str,
        mcp_client_name: Optional[str] = None,
    ) -> str:
        """Generate and store a dynamic NPC token in Redis.

        Args:
            username: NPC token username
            race_id: Race this token is for
            npc_name: Display name of the NPC
            cli_tool: CLI tool being used (vibe, codex, claude-code)
            mcp_client_name: Override for MCP client name (e.g., "Mistral Vibe")

        Returns:
            Full token string: npc-{username}:{race_id}:{secret}
        """
        if self.redis is None:
            raise RuntimeError("Redis client required for token generation")

        secret = secrets.token_urlsafe(32)
        token_key = f"{NPC_TOKEN_KEY_PREFIX}:{username}:{race_id}"

        token_data = {
            "secret": secret,
            "race_id": race_id,
            "npc_name": npc_name,
            "cli_tool": cli_tool,
            "mcp_client_name": mcp_client_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        await self.redis.set(token_key, json.dumps(token_data), ex=NPC_TOKEN_TTL_SECONDS)

        return f"npc-{username}:{race_id}:{secret}"

    async def spawn_npcs(
        self,
        race_id: str,
        count: int,
        mcp_server_url: Optional[str] = None,
    ) -> list[SpawnedNPC]:
        """Spawn NPC racer containers.

        Args:
            race_id: The race to join
            count: Number of NPCs to spawn (will be capped at available NPCs)
            mcp_server_url: Override MCP server URL from config

        Returns:
            List of spawned NPC info
        """
        if not self.config.npcs:
            logger.warning("No NPCs configured, cannot spawn")
            return []

        if self.redis is None:
            logger.error("Redis client required for spawning NPCs (token storage)")
            return []

        # Cap at available NPCs
        npcs_to_spawn = self.config.npcs[:count]

        if len(npcs_to_spawn) < count:
            logger.warning(
                f"Only {len(npcs_to_spawn)} NPCs configured, requested {count}"
            )

        spawner_config = self.config.spawner
        server_url = mcp_server_url or spawner_config.mcp_server_url

        spawned: list[SpawnedNPC] = []

        for i, npc_def in enumerate(npcs_to_spawn):
            try:
                # Add delay between spawns (except for first)
                if i > 0:
                    await asyncio.sleep(spawner_config.spawn_delay_ms / 1000.0)

                spawned_npc = await self._spawn_docker_container(
                    race_id=race_id,
                    npc_def=npc_def,
                    server_url=server_url,
                )

                if spawned_npc:
                    spawned.append(spawned_npc)
                    await self._store_process_info(race_id, spawned_npc)
                    logger.info(
                        f"Spawned NPC {npc_def.name} (container {spawned_npc.container_id[:12]}) "
                        f"for race {race_id}"
                    )

            except Exception as e:
                logger.error(f"Failed to spawn NPC {npc_def.name}: {e}")
                # Continue with other NPCs

        return spawned

    async def _spawn_docker_container(
        self,
        race_id: str,
        npc_def: NPCDefinition,
        server_url: str,
    ) -> Optional[SpawnedNPC]:
        """Spawn a single NPC as a Docker container.

        Args:
            race_id: Race to join
            npc_def: NPC definition
            server_url: MCP server URL

        Returns:
            SpawnedNPC info or None if failed
        """
        if self.docker_client is None:
            logger.error("Docker client not initialized")
            return None

        # Get image for this CLI tool
        image = NPC_IMAGES.get(npc_def.cli_tool)
        if image is None:
            logger.error(
                f"No Docker image for CLI tool '{npc_def.cli_tool}', NPC {npc_def.name}"
            )
            return None

        # Generate dynamic token and store in Redis
        auth_token = await self._generate_token(
            username=npc_def.token_username,
            race_id=race_id,
            npc_name=npc_def.name,
            cli_tool=npc_def.cli_tool,
            mcp_client_name=npc_def.mcp_client_name,
        )

        container_name = f"npc-{race_id[:8]}-{npc_def.name.lower()}"

        # Log the spawn command
        logger.info(
            f"Spawning NPC container {npc_def.name}: "
            f"image={image!r} "
            f"name={container_name!r} "
            f"MCP_SERVER_URL={server_url!r}"
        )

        try:
            container = self.docker_client.containers.run(
                image=image,
                detach=True,
                name=container_name,
                environment={
                    "MCP_SERVER_URL": server_url,
                    "MCP_AUTH_TOKEN": auth_token,
                    "RACE_ID": race_id,
                    "NPC_NAME": npc_def.name,
                    "MISTRAL_API_KEY": os.environ.get("MISTRAL_API_KEY", ""),
                },
                network="mcpkart_default",  # Same network as other services
                # auto_remove=True,  # Disabled for debugging - re-enable later
            )

            return SpawnedNPC(
                npc_name=npc_def.name,
                token_username=npc_def.token_username,
                spawned_at=datetime.now(timezone.utc).isoformat(),
                container_id=container.id,
            )

        except docker.errors.ImageNotFound:
            logger.error(
                f"Docker image '{image}' not found. "
                f"Build it with: docker build -t {image} ./npcs/vibe/"
            )
            return None
        except docker.errors.APIError as e:
            logger.error(f"Docker API error spawning NPC {npc_def.name}: {e}")
            return None

    async def cleanup_npcs(self, race_id: str) -> int:
        """Clean up all NPC containers for a race.

        Args:
            race_id: Race ID to clean up

        Returns:
            Number of NPCs cleaned up
        """
        if self.redis is None:
            return 0

        key = self._redis_key(race_id)
        existing = await self.redis.get(key)

        if not existing:
            return 0

        containers = json.loads(existing)
        cleaned = 0

        for container_info in containers:
            container_id = container_info.get("container_id")
            if not container_id:
                continue

            try:
                container = self.docker_client.containers.get(container_id)
                container.stop(timeout=5)
                cleaned += 1
                logger.info(f"Stopped NPC container {container_id[:12]}")
            except docker.errors.NotFound:
                # Container already stopped/removed
                pass
            except Exception as e:
                logger.warning(f"Failed to stop container {container_id[:12]}: {e}")

        # Clean up Redis key
        await self.redis.delete(key)

        return cleaned
