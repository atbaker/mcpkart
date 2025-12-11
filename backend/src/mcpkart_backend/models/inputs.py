"""Input and API models for MCP Kart."""

from typing import Optional

from pydantic import BaseModel


class PlayerInput(BaseModel):
    """Input sent by player via MCP/API."""

    player_id: str
    target_speed: Optional[int] = None  # None = don't change, 0-3 (or 0-5 with boost)
    drift: bool = False  # Enable drift mode (must be in drift zone)
    use_item: bool = False
    ready: bool = False  # Signal ready to start (public matchmaking only)


class CreateRaceRequest(BaseModel):
    """Request to create a new race."""

    player_ids: list[str]


class PlayerInputRequest(BaseModel):
    """API request for sending player input."""

    player_id: str
    target_speed: Optional[int] = None  # 0-3 (or 0-5 with boost)
    drift: bool = False  # Enable drift mode (must be in drift zone)
    use_item: bool = False
    ready: bool = False  # Signal ready to start (public matchmaking only)


class CreateLobbyRequest(BaseModel):
    """Request to create a new race lobby."""

    creator_id: str  # MCP client provides their own player ID
    max_racers: int = 8  # Optional, defaults to 8
    is_public: bool = False  # True for public matchmaking, False for private lobbies
    mcp_client: str = "unknown"  # MCP client name (e.g., "claude-code", "cursor")


class JoinLobbyRequest(BaseModel):
    """Request to join an existing lobby."""

    player_id: str  # MCP client provides their own player ID
    mcp_client: str = "unknown"  # MCP client name (e.g., "claude-code", "cursor")


class StartRaceRequest(BaseModel):
    """Request to start the race (transitions LOBBY -> PLANNING)."""

    player_id: str  # Must match creator_id for authorization


class JoinMatchmakingRequest(BaseModel):
    """Request to join public matchmaking."""

    player_id: str  # MCP client provides their own player ID
    mcp_client: str = "unknown"  # MCP client name (e.g., "claude-code", "cursor")
