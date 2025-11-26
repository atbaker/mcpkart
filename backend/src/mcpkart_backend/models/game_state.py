"""Game state model for MCP Kart."""

from pydantic import BaseModel, Field

from .racer import RacerState, RacerStatus
from .track import Track


class GameState(BaseModel):
    """Complete state of a race."""

    race_id: str
    current_tick: int = 0
    max_ticks: int = 180  # 3 minutes max
    laps_required: int = 3

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
