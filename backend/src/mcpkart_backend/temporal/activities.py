"""Temporal activities for MCP Kart."""

from datetime import datetime

from temporalio import activity

from mcpkart_backend.db import AsyncSessionLocal, RaceResult, RacerResult


@activity.defn
async def store_race_results(
    race_id: str,
    started_at: str,  # ISO format datetime string
    finished_at: str,  # ISO format datetime string
    total_ticks: int,
    max_ticks: int,
    laps_required: int,
    is_public: bool,
    standings: list[str],
    racer_states: list[dict],
    events: list[str],
    racer_history: dict | None = None,
) -> None:
    """Store race results in the database.

    Args:
        race_id: Unique race identifier
        started_at: ISO format datetime when race started
        finished_at: ISO format datetime when race finished
        total_ticks: Total number of game ticks when race ended
        max_ticks: Maximum allowed ticks for the race
        laps_required: Number of laps required to finish
        is_public: Whether this was a public matchmaking race
        standings: Ordered list of player_ids by finish position
        racer_states: List of racer state dicts with final positions
        events: Event log for the race
        racer_history: Tick-by-tick racer positions for replay support
    """
    async with AsyncSessionLocal() as db:
        try:
            race_result = RaceResult(
                race_id=race_id,
                started_at=datetime.fromisoformat(started_at),
                finished_at=datetime.fromisoformat(finished_at),
                total_ticks=total_ticks,
                max_ticks=max_ticks,
                laps_required=laps_required,
                is_public=is_public,
                standings=standings,
                events=events,
                racer_history=racer_history,
            )
            db.add(race_result)

            for racer in racer_states:
                racer_result = RacerResult(
                    race_id=race_id,
                    player_id=racer["player_id"],
                    mcp_client=racer.get("mcp_client", "unknown"),
                    finish_position=racer.get("finish_position"),
                    finish_tick=racer.get("finish_tick"),
                    total_crashes=racer.get("total_crashes", 0),
                    items_used=racer.get("items_used", 0),
                    tile_index=racer.get("tile_index", 0),
                    tile_subunit=racer.get("tile_subunit", 0),
                    speed=racer.get("speed", 0),
                    current_lap=racer.get("current_lap", 0),
                    finish_time=racer.get("finish_time"),
                )
                db.add(racer_result)

            await db.commit()
            activity.logger.info(f"Stored results for race {race_id}")
        except Exception as e:
            await db.rollback()
            activity.logger.error(f"Failed to store results for race {race_id}: {e}")
            raise
