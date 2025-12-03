"""MCP Kart models."""


def format_race_clock(ticks: int) -> str:
    """Convert ticks to MM:SS format (1 tick = 1 second)."""
    minutes = ticks // 60
    seconds = ticks % 60
    return f"{minutes}:{seconds:02d}"


from .game_state import GameState
from .inputs import (
    CreateLobbyRequest,
    CreateRaceRequest,
    JoinLobbyRequest,
    PlayerInput,
    PlayerInputRequest,
    StartRaceRequest,
)
from .racer import PowerUp, RacePhase, RacerControls, RacerState, RacerStatus
from .track import Tile, TileType, Track

__all__ = [
    "format_race_clock",
    "CreateLobbyRequest",
    "CreateRaceRequest",
    "GameState",
    "JoinLobbyRequest",
    "PlayerInput",
    "PlayerInputRequest",
    "PowerUp",
    "RacePhase",
    "RacerControls",
    "RacerState",
    "RacerStatus",
    "StartRaceRequest",
    "Tile",
    "TileType",
    "Track",
]
