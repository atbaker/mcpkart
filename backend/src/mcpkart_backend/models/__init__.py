"""MCP Kart models."""


def format_race_clock(ticks: int) -> str:
    """Convert ticks to MM:SS format (1 tick = 1 second)."""
    minutes = ticks // 60
    seconds = ticks % 60
    return f"{minutes}:{seconds:02d}"


from .game_state import GameState
from .inputs import CreateRaceRequest, PlayerInput, PlayerInputRequest
from .racer import PowerUp, RacerControls, RacerState, RacerStatus
from .track import Tile, TileType, Track

__all__ = [
    "format_race_clock",
    "CreateRaceRequest",
    "GameState",
    "PlayerInput",
    "PlayerInputRequest",
    "PowerUp",
    "RacerControls",
    "RacerState",
    "RacerStatus",
    "Tile",
    "TileType",
    "Track",
]
