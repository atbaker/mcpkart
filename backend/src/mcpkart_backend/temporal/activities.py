"""Temporal activities for MCP Kart."""

from datetime import datetime

from temporalio import activity

from mcpkart_backend.db import RaceResult, RacerResult, SessionLocal


@activity.defn
async def store_race_results(
    race_id: str,
    started_at: str,  # ISO format datetime string
    finished_at: str,  # ISO format datetime string
    total_ticks: int,
    standings: list[str],
    racer_stats: dict[str, dict],
) -> None:
    """Store race results in the database.

    Args:
        race_id: Unique race identifier
        started_at: ISO format datetime when race started
        finished_at: ISO format datetime when race finished
        total_ticks: Total number of game ticks
        standings: Ordered list of player_ids by finish position
        racer_stats: Dict mapping player_id to their stats
    """
    db = SessionLocal()
    try:
        race_result = RaceResult(
            race_id=race_id,
            started_at=datetime.fromisoformat(started_at),
            finished_at=datetime.fromisoformat(finished_at),
            total_ticks=total_ticks,
            standings=standings,
        )
        db.add(race_result)

        for player_id, stats in racer_stats.items():
            racer_result = RacerResult(
                race_id=race_id,
                player_id=player_id,
                finish_position=stats.get("finish_position"),
                finish_tick=stats.get("finish_tick"),
                total_crashes=stats.get("total_crashes", 0),
                items_used=stats.get("items_used", 0),
            )
            db.add(racer_result)

        db.commit()
        activity.logger.info(f"Stored results for race {race_id}")
    except Exception as e:
        db.rollback()
        activity.logger.error(f"Failed to store results for race {race_id}: {e}")
        raise
    finally:
        db.close()
