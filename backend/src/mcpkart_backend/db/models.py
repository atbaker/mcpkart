"""SQLAlchemy models for race results persistence."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class RaceResult(Base):
    """Persisted race results after a race completes."""

    __tablename__ = "race_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    # Race metadata
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime] = mapped_column(DateTime)
    total_ticks: Mapped[int] = mapped_column(Integer)

    # Results - JSON array of player_ids in finish order
    standings: Mapped[list[str]] = mapped_column(JSON)

    # Relationship to individual racer results
    racer_results: Mapped[list["RacerResult"]] = relationship(
        back_populates="race", cascade="all, delete-orphan"
    )


class RacerResult(Base):
    """Individual racer's performance in a race."""

    __tablename__ = "racer_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("race_results.race_id"), index=True
    )
    player_id: Mapped[str] = mapped_column(String(64), index=True)

    # Performance
    finish_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    finish_tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_crashes: Mapped[int] = mapped_column(Integer, default=0)
    items_used: Mapped[int] = mapped_column(Integer, default=0)

    # Relationship
    race: Mapped["RaceResult"] = relationship(back_populates="racer_results")
