"""Game state model for MCP Kart."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field

from . import format_race_clock
from .racer import RacePhase, RacerState, RacerStatus
from .track import Track


class GameState(BaseModel):
    """Complete state of a race."""

    race_id: str
    current_tick: int = 0
    max_ticks: int = 600  # 10 minutes max
    laps_required: int = 3

    # Lobby/Phase fields
    phase: RacePhase = RacePhase.LOBBY
    creator_id: Optional[str] = None  # Player who created the lobby
    max_racers: int = 8  # Default, overridden at workflow creation
    is_public: bool = False  # True for public matchmaking, False for private lobbies

    # Ready-up tracking for public matchmaking
    ready_players: set[str] = Field(default_factory=set)

    # Timing fields
    created_at: Optional[datetime] = None  # When lobby was created
    lobby_expires_at: Optional[datetime] = None  # 1 hour after creation
    matchmaking_ends_at: Optional[datetime] = None  # When matchmaking auto-starts
    planning_ends_at: Optional[datetime] = None  # When PLANNING countdown ends
    race_started_at: Optional[datetime] = None  # When RACING phase began

    @computed_field
    @property
    def race_clock(self) -> str:
        """Current race time in MM:SS format."""
        return format_race_clock(self.current_tick)

    @computed_field
    @property
    def max_race_clock(self) -> str:
        """Maximum race time in MM:SS format."""
        return format_race_clock(self.max_ticks)

    track: Track = Field(default_factory=Track.create_oval)
    racers: dict[str, RacerState] = Field(default_factory=dict)

    # Finish order (player_ids)
    standings: list[str] = Field(default_factory=list)

    # Event log for debugging
    events: list[str] = Field(default_factory=list)

    @property
    def is_finished(self) -> bool:
        """Race ends when all racers finish or max ticks reached."""
        if not self.racers:
            return False
        all_finished = all(
            r.status == RacerStatus.FINISHED for r in self.racers.values()
        )
        return all_finished or self.current_tick >= self.max_ticks

    @property
    def next_finish_position(self) -> int:
        """Position for next racer to finish (1-indexed)."""
        return len(self.standings) + 1

    @property
    def is_lobby_full(self) -> bool:
        """Check if lobby has reached max capacity."""
        return len(self.racers) >= self.max_racers
