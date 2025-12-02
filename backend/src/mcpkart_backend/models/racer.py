"""Racer state and controls models for MCP Kart."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field

from . import format_race_clock


class PowerUp(str, Enum):
    """Available power-ups."""

    SPEED_BOOST = "speed_boost"


class RacerStatus(str, Enum):
    """Current status of a racer."""

    RACING = "racing"
    CRASHED = "crashed"  # In penalty cooldown
    FINISHED = "finished"


class RacerControls(BaseModel):
    """Current control inputs for a racer (persist between ticks)."""

    target_speed: int = 0  # Desired speed 0-3 (or up to 5 with boost)
    drift: bool = False  # Enable drift mode (must be in drift zone)
    use_item: bool = False  # One-shot flag, consumed after use


class RacerState(BaseModel):
    """Complete state for a single racer."""

    player_id: str

    # Position (each tile has 3 subunits)
    tile_index: int = 0
    tile_subunit: int = 0  # 0, 1, or 2

    # Movement
    speed: int = 0  # 0-3 normally, up to 5 with boost

    # Lap tracking
    current_lap: int = 0  # 0 = hasn't crossed start yet, 1-3 during race

    # Power-ups
    power_up: Optional[PowerUp] = None
    boost_ticks_remaining: int = 0  # Countdown when boost is active

    # Status
    status: RacerStatus = RacerStatus.RACING
    penalty_ticks_remaining: int = 0  # Ticks until can move after crash
    finish_position: Optional[int] = None
    finish_tick: Optional[int] = None  # Tick when finished

    # Controls (updated via player input)
    controls: RacerControls = Field(default_factory=RacerControls)

    # Stats tracking
    total_crashes: int = 0
    items_used: int = 0

    # Turn/Drift tracking
    on_turn_tile: bool = False
    in_drift_zone: bool = False  # Currently in 3 tiles before a turn
    drift_enabled: bool = False  # Drift was enabled in drift zone

    @property
    def total_subunits(self) -> int:
        """Absolute position in subunits (for comparison)."""
        return (self.current_lap * 60) + (self.tile_index * 3) + self.tile_subunit

    @property
    def effective_max_speed(self) -> int:
        """Max speed considering active boosts."""
        return 5 if self.boost_ticks_remaining > 0 else 3

    @computed_field
    @property
    def finish_time(self) -> Optional[str]:
        """Finish time in MM:SS format (None if not finished)."""
        if self.finish_tick is None:
            return None
        return format_race_clock(self.finish_tick)

    @computed_field
    @property
    def boost_seconds_remaining(self) -> int:
        """Boost time remaining in seconds (1 tick = 1 second)."""
        return self.boost_ticks_remaining

    @computed_field
    @property
    def penalty_seconds_remaining(self) -> int:
        """Penalty time remaining in seconds (1 tick = 1 second)."""
        return self.penalty_ticks_remaining
