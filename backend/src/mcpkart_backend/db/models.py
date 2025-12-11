"""SQLAlchemy models for race results persistence."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


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

    # New fields for full spectator state reconstruction
    laps_required: Mapped[int] = mapped_column(Integer, default=3)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    max_ticks: Mapped[int] = mapped_column(Integer, default=600)
    events: Mapped[list[str]] = mapped_column(JSON, default=list)

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
    mcp_client: Mapped[str] = mapped_column(String(64), default="unknown")

    # Performance
    finish_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    finish_tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_crashes: Mapped[int] = mapped_column(Integer, default=0)
    items_used: Mapped[int] = mapped_column(Integer, default=0)

    # Final state for spectator view reconstruction
    tile_index: Mapped[int] = mapped_column(Integer, default=0)
    tile_subunit: Mapped[int] = mapped_column(Integer, default=0)
    speed: Mapped[int] = mapped_column(Integer, default=0)
    current_lap: Mapped[int] = mapped_column(Integer, default=0)
    finish_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relationship
    race: Mapped["RaceResult"] = relationship(back_populates="racer_results")


class User(Base):
    """GitHub authenticated user."""

    __tablename__ = "users"

    # GitHub user ID is numeric and stable (username can change)
    github_user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Display name (GitHub login/username)
    github_username: Mapped[str] = mapped_column(String(39), unique=True, index=True)

    # Email (may be null if user has private email)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Organizations the user belongs to (for future leaderboard features)
    organizations: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
