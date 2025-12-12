"""NPC configuration loader."""

import os
import re
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class NPCDefinition(BaseModel):
    """Individual NPC racer definition."""

    name: str
    token_username: str
    cli_tool: str = "vibe"  # Which CLI tool to use: vibe, codex, claude-code
    mcp_client_name: Optional[str] = None  # Override MCP client name (e.g., "Mistral Vibe")


class CLIConfig(BaseModel):
    """Configuration for a specific CLI tool."""

    command: str
    args: list[str] = Field(default_factory=list)


class SpawnerConfig(BaseModel):
    """Spawner configuration."""

    mcp_server_url: str = "http://localhost:8080"
    cli_configs: dict[str, CLIConfig] = Field(
        default_factory=lambda: {
            "vibe": CLIConfig(command="vibe", args=["--auto-approve"]),
        }
    )
    prompt_template: str = (
        "Join MCP Kart race {race_id} and race immediately. Play to win!"
    )
    spawn_delay_ms: int = 500
    process_timeout_minutes: int = 15


class NPCConfig(BaseModel):
    """Complete NPC configuration."""

    npcs: list[NPCDefinition] = Field(default_factory=list)
    spawner: SpawnerConfig = Field(default_factory=SpawnerConfig)


def _expand_env_vars(value: str) -> str:
    """Expand ${VAR:-default} syntax in a string.

    Supports:
    - ${VAR} - Required env var
    - ${VAR:-default} - Env var with default value
    """
    pattern = r"\$\{([^}:]+)(?::-([^}]*))?\}"

    def replace(match: re.Match) -> str:
        var_name = match.group(1)
        default = match.group(2)
        value = os.environ.get(var_name)
        if value is not None:
            return value
        if default is not None:
            return default
        return match.group(0)  # Return original if no match and no default

    return re.sub(pattern, replace, value)


def load_npc_config(config_path: Optional[Path] = None) -> NPCConfig:
    """Load NPC configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to backend/config/npcs.yaml

    Returns:
        Loaded and validated NPC configuration
    """
    if config_path is None:
        # Default to backend/config/npcs.yaml relative to this file
        config_path = (
            Path(__file__).parent.parent.parent.parent / "config" / "npcs.yaml"
        )

    if not config_path.exists():
        # Return empty config if file doesn't exist
        return NPCConfig()

    with open(config_path) as f:
        raw_config = yaml.safe_load(f)

    if not raw_config:
        return NPCConfig()

    # Expand environment variables in spawner config
    if "spawner" in raw_config:
        spawner = raw_config["spawner"]
        if "mcp_server_url" in spawner:
            spawner["mcp_server_url"] = _expand_env_vars(spawner["mcp_server_url"])

    return NPCConfig(**raw_config)
