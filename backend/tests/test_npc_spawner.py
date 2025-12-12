"""Tests for NPC spawner."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcpkart_backend.npc.config import (
    CLIConfig,
    NPCConfig,
    NPCDefinition,
    SpawnerConfig,
    _expand_env_vars,
    load_npc_config,
)
from mcpkart_backend.npc.spawner import NPCSpawner, NPC_TOKEN_KEY_PREFIX


class TestEnvVarExpansion:
    def test_expand_with_default_no_env(self):
        """Test ${VAR:-default} when env var is not set."""
        result = _expand_env_vars("${NONEXISTENT_VAR:-http://default}")
        assert result == "http://default"

    def test_expand_with_default_env_set(self, monkeypatch):
        """Test ${VAR:-default} when env var is set."""
        monkeypatch.setenv("TEST_VAR", "http://custom")
        result = _expand_env_vars("${TEST_VAR:-http://default}")
        assert result == "http://custom"

    def test_expand_without_default(self):
        """Test ${VAR} without default keeps original when not set."""
        result = _expand_env_vars("${NONEXISTENT_VAR}")
        assert result == "${NONEXISTENT_VAR}"

    def test_expand_multiple_vars(self, monkeypatch):
        """Test multiple env vars in one string."""
        monkeypatch.setenv("HOST", "localhost")
        result = _expand_env_vars("http://${HOST}:${PORT:-8080}")
        assert result == "http://localhost:8080"


class TestNPCConfig:
    def test_load_missing_config(self, tmp_path):
        """Test loading non-existent config returns empty config."""
        config = load_npc_config(tmp_path / "nonexistent.yaml")
        assert config.npcs == []
        assert config.spawner.mcp_server_url == "http://localhost:8080"

    def test_load_valid_config(self, tmp_path):
        """Test loading valid YAML config with new structure."""
        config_path = tmp_path / "npcs.yaml"
        config_path.write_text("""
npcs:
  - name: TestBot
    token_username: test-bot
    cli_tool: vibe
  - name: TestBot2
    token_username: test-bot-2
    cli_tool: vibe
spawner:
  mcp_server_url: http://test:8080
  spawn_delay_ms: 100
  cli_configs:
    vibe:
      command: custom-vibe
      args: ["--auto-approve", "--quiet"]
""")
        config = load_npc_config(config_path)
        assert len(config.npcs) == 2
        assert config.npcs[0].name == "TestBot"
        assert config.npcs[0].token_username == "test-bot"
        assert config.npcs[0].cli_tool == "vibe"
        assert config.spawner.spawn_delay_ms == 100
        assert config.spawner.cli_configs["vibe"].command == "custom-vibe"
        assert config.spawner.cli_configs["vibe"].args == ["--auto-approve", "--quiet"]
        assert config.spawner.mcp_server_url == "http://test:8080"

    def test_load_config_with_env_var_expansion(self, tmp_path, monkeypatch):
        """Test env var expansion in mcp_server_url."""
        monkeypatch.setenv("MCP_SERVER_URL", "http://custom:9090")
        config_path = tmp_path / "npcs.yaml"
        config_path.write_text("""
npcs: []
spawner:
  mcp_server_url: "${MCP_SERVER_URL:-http://default:8080}"
""")
        config = load_npc_config(config_path)
        assert config.spawner.mcp_server_url == "http://custom:9090"

    def test_load_empty_config(self, tmp_path):
        """Test loading empty YAML file."""
        config_path = tmp_path / "npcs.yaml"
        config_path.write_text("")
        config = load_npc_config(config_path)
        assert config.npcs == []

    def test_cli_tool_default(self):
        """Test that cli_tool defaults to vibe."""
        npc = NPCDefinition(name="Bot", token_username="bot-1")
        assert npc.cli_tool == "vibe"


class TestNPCSpawner:
    @pytest.fixture
    def spawner_config(self):
        return NPCConfig(
            npcs=[
                NPCDefinition(name="Bot1", token_username="bot-1", cli_tool="vibe"),
                NPCDefinition(name="Bot2", token_username="bot-2", cli_tool="vibe"),
                NPCDefinition(name="Bot3", token_username="bot-3", cli_tool="vibe"),
            ],
            spawner=SpawnerConfig(
                spawn_delay_ms=0,
                cli_configs={
                    "vibe": CLIConfig(command="vibe", args=["--auto-approve"]),
                },
            ),
        )

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock = AsyncMock()
        mock.get.return_value = None  # No existing processes
        return mock

    @pytest.fixture
    def mock_docker_client(self):
        """Create a mock Docker client."""
        mock = MagicMock()
        mock_container = MagicMock()
        mock_container.id = "abc123def456"
        mock.containers.run.return_value = mock_container
        return mock

    @pytest.fixture
    def spawner(self, spawner_config, mock_redis, mock_docker_client):
        with patch("docker.from_env", return_value=mock_docker_client):
            return NPCSpawner(
                config=spawner_config,
                redis_client=mock_redis,
            )

    @pytest.mark.asyncio
    async def test_spawn_respects_count_limit(self, spawner, mock_docker_client):
        """Test that spawner respects the count parameter."""
        result = await spawner.spawn_npcs("race-1", count=1)

        assert len(result) == 1
        assert result[0].npc_name == "Bot1"
        assert result[0].container_id == "abc123def456"
        assert mock_docker_client.containers.run.call_count == 1

    @pytest.mark.asyncio
    async def test_spawn_multiple_npcs(self, spawner, mock_docker_client):
        """Test spawning multiple NPCs."""
        result = await spawner.spawn_npcs("race-1", count=3)

        assert len(result) == 3
        assert [npc.npc_name for npc in result] == ["Bot1", "Bot2", "Bot3"]
        assert mock_docker_client.containers.run.call_count == 3

    @pytest.mark.asyncio
    async def test_spawn_requires_redis(self, spawner_config):
        """Test that spawning requires Redis client for token storage."""
        with patch("docker.from_env"):
            spawner = NPCSpawner(config=spawner_config, redis_client=None)
        result = await spawner.spawn_npcs("race-1", count=1)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_spawn_with_no_npcs_configured(self, mock_redis, mock_docker_client):
        """Test spawning with no NPCs in config."""
        config = NPCConfig(npcs=[])
        with patch("docker.from_env", return_value=mock_docker_client):
            spawner = NPCSpawner(config=config, redis_client=mock_redis)

        result = await spawner.spawn_npcs("race-1", count=1)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_spawn_caps_at_available_npcs(self, spawner, mock_docker_client):
        """Test that spawn count is capped at available NPCs."""
        # Request 10 NPCs but only 3 are configured
        result = await spawner.spawn_npcs("race-1", count=10)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_spawn_generates_dynamic_token(self, spawner, mock_redis, mock_docker_client):
        """Test that spawned containers get dynamically generated tokens."""
        await spawner.spawn_npcs("race-1", count=1, mcp_server_url="http://test:9000")

        # Check that the container was called with correct env
        call_kwargs = mock_docker_client.containers.run.call_args.kwargs
        env = call_kwargs["environment"]
        assert env["MCP_SERVER_URL"] == "http://test:9000"

        # Token should be dynamic format: npc-{username}:{race_id}:{secret}
        auth_token = env["MCP_AUTH_TOKEN"]
        assert auth_token.startswith("npc-bot-1:race-1:")
        # Secret should be URL-safe base64 (32 bytes = 43 chars)
        parts = auth_token.split(":")
        assert len(parts) == 3
        assert len(parts[2]) == 43  # secrets.token_urlsafe(32) produces 43 chars

    @pytest.mark.asyncio
    async def test_spawn_stores_token_in_redis(self, spawner, mock_redis, mock_docker_client):
        """Test that tokens are stored in Redis."""
        await spawner.spawn_npcs("race-1", count=1)

        # Find the token storage call (not the process tracking call)
        token_calls = [
            call for call in mock_redis.set.call_args_list
            if call[0][0].startswith(NPC_TOKEN_KEY_PREFIX)
        ]
        assert len(token_calls) == 1

        key, value = token_calls[0][0][0], token_calls[0][0][1]
        assert key == f"{NPC_TOKEN_KEY_PREFIX}:bot-1:race-1"

        data = json.loads(value)
        assert "secret" in data
        assert data["race_id"] == "race-1"
        assert data["npc_name"] == "Bot1"
        assert data["cli_tool"] == "vibe"
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_spawn_stores_mcp_client_name_in_redis(self, mock_redis, mock_docker_client):
        """Test that mcp_client_name from NPC config is stored in Redis token data."""
        config = NPCConfig(
            npcs=[
                NPCDefinition(
                    name="MistralBot",
                    token_username="mistral-bot",
                    cli_tool="vibe",
                    mcp_client_name="Mistral Vibe",
                ),
            ],
            spawner=SpawnerConfig(spawn_delay_ms=0),
        )
        with patch("docker.from_env", return_value=mock_docker_client):
            spawner = NPCSpawner(config=config, redis_client=mock_redis)

        await spawner.spawn_npcs("race-1", count=1)

        # Find the token storage call
        token_calls = [
            call for call in mock_redis.set.call_args_list
            if call[0][0].startswith(NPC_TOKEN_KEY_PREFIX)
        ]
        assert len(token_calls) == 1

        data = json.loads(token_calls[0][0][1])
        assert data["mcp_client_name"] == "Mistral Vibe"

    @pytest.mark.asyncio
    async def test_spawn_uses_docker_network(self, spawner, mock_docker_client):
        """Test that containers are spawned on the mcpkart_default network."""
        await spawner.spawn_npcs("race-1", count=1)

        call_kwargs = mock_docker_client.containers.run.call_args.kwargs
        assert call_kwargs["network"] == "mcpkart_default"

    @pytest.mark.asyncio
    async def test_spawn_continues_on_individual_failure(self, spawner_config, mock_redis):
        """Test that spawning continues if one NPC fails."""
        mock_docker_client = MagicMock()
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Container spawn failed")
            mock_container = MagicMock()
            mock_container.id = f"container{call_count}"
            return mock_container

        mock_docker_client.containers.run.side_effect = mock_run

        with patch("docker.from_env", return_value=mock_docker_client):
            spawner = NPCSpawner(config=spawner_config, redis_client=mock_redis)

        result = await spawner.spawn_npcs("race-1", count=3)

        # Should have 2 successful spawns (1st and 3rd)
        assert len(result) == 2
        assert result[0].npc_name == "Bot1"
        assert result[1].npc_name == "Bot3"

    @pytest.mark.asyncio
    async def test_cleanup_stops_containers(self, mock_docker_client):
        """Test that cleanup stops Docker containers."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps([
            {"container_id": "container1", "npc_name": "Bot1"},
            {"container_id": "container2", "npc_name": "Bot2"},
        ])

        mock_container = MagicMock()
        mock_docker_client.containers.get.return_value = mock_container

        with patch("docker.from_env", return_value=mock_docker_client):
            spawner = NPCSpawner(redis_client=mock_redis)

        cleaned = await spawner.cleanup_npcs("race-1")

        assert cleaned == 2
        assert mock_container.stop.call_count == 2

        # Verify Redis key is deleted
        mock_redis.delete.assert_called_once_with("npc:race:race-1:processes")

    @pytest.mark.asyncio
    async def test_cleanup_ignores_already_stopped(self):
        """Test that cleanup ignores containers that already stopped."""
        import docker.errors

        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps([
            {"container_id": "container1", "npc_name": "Bot1"},
        ])

        mock_docker_client = MagicMock()
        mock_docker_client.containers.get.side_effect = docker.errors.NotFound("Not found")

        with patch("docker.from_env", return_value=mock_docker_client):
            spawner = NPCSpawner(redis_client=mock_redis)

        cleaned = await spawner.cleanup_npcs("race-1")

        # Should not count as cleaned if container not found
        assert cleaned == 0

    @pytest.mark.asyncio
    async def test_cleanup_with_no_redis(self):
        """Test cleanup returns 0 when no Redis client."""
        with patch("docker.from_env"):
            spawner = NPCSpawner(redis_client=None)
        cleaned = await spawner.cleanup_npcs("race-1")
        assert cleaned == 0

    @pytest.mark.asyncio
    async def test_cleanup_with_no_stored_containers(self):
        """Test cleanup when no containers are stored."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None

        with patch("docker.from_env"):
            spawner = NPCSpawner(redis_client=mock_redis)
        cleaned = await spawner.cleanup_npcs("race-1")

        assert cleaned == 0

    @pytest.mark.asyncio
    async def test_spawn_stores_container_info_in_redis(self, spawner_config, mock_redis, mock_docker_client):
        """Test that spawned NPC container info is stored in Redis."""
        with patch("docker.from_env", return_value=mock_docker_client):
            spawner = NPCSpawner(config=spawner_config, redis_client=mock_redis)

        await spawner.spawn_npcs("race-1", count=1)

        # Find the process tracking call (not the token storage call)
        process_calls = [
            call for call in mock_redis.set.call_args_list
            if call[0][0] == "npc:race:race-1:processes"
        ]
        assert len(process_calls) == 1

        value = json.loads(process_calls[0][0][1])
        assert len(value) == 1
        assert value[0]["container_id"] == "abc123def456"
        assert value[0]["npc_name"] == "Bot1"
        assert value[0]["token_username"] == "bot-1"
