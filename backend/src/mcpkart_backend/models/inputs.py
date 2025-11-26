"""Input and API models for MCP Kart."""

from typing import Optional

from pydantic import BaseModel

from .racer import Steering


class PlayerInput(BaseModel):
    """Input sent by player via MCP/API."""

    player_id: str
    target_speed: Optional[int] = None  # None = don't change, 0-3 (or 0-5 with boost)
    steering: Optional[Steering] = None
    use_item: bool = False


class CreateRaceRequest(BaseModel):
    """Request to create a new race."""

    player_ids: list[str]


class PlayerInputRequest(BaseModel):
    """API request for sending player input."""

    player_id: str
    target_speed: Optional[int] = None  # 0-3 (or 0-5 with boost)
    steering: Optional[str] = None  # "left", "straight", "right"
    use_item: bool = False
    execute_at_tick: Optional[int] = None  # If set, schedule for future tick
