# MCP Kart Implementation Plan

This document outlines the technical implementation plan for MCP Kart's backend (FastAPI + Temporal) and MCP server (FastMCP).

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Models](#data-models)
3. [Temporal Workflow Design](#temporal-workflow-design)
4. [FastAPI Endpoints](#fastapi-endpoints)
5. [FastMCP Server Tools](#fastmcp-server-tools)
6. [Database (SQLAlchemy + Alembic)](#database-sqlalchemy--alembic)
7. [Testing (Temporal Test Framework)](#testing-temporal-test-framework)
8. [Project Structure](#project-structure)
9. [Implementation Steps](#implementation-steps)

---

## Architecture Overview

```
┌─────────────────┐     HTTP      ┌─────────────────┐    Temporal    ┌─────────────────┐
│                 │    requests   │                 │     Client     │                 │
│   MCP Client    │◄────────────►│   FastMCP       │◄──────────────►│   FastAPI       │
│   (Claude, etc) │   (MCP tools) │   Server        │                │   Backend       │
│                 │               │                 │                │                 │
└─────────────────┘               └─────────────────┘                └────────┬────────┘
                                                                              │
                                                                              │ Workflow
                                                                              │ Start/Query/Update
                                                                              ▼
                                                                     ┌─────────────────┐
                                                                     │                 │
                                                                     │   Temporal      │
                                                                     │   Server        │
                                                                     │                 │
                                                                     └────────┬────────┘
                                                                              │
                                                                              │ Executes
                                                                              ▼
                                                                     ┌─────────────────┐
                                                                     │                 │
                                                                     │   Temporal      │
                                                                     │   Worker        │
                                                                     │   (Race Logic)  │
                                                                     │                 │
                                                                     └─────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **FastMCP Server** | Exposes MCP tools for AI assistants to join races, get state, and send input |
| **FastAPI Backend** | HTTP API layer; starts workflows, queries/updates them via Temporal client |
| **Temporal Worker** | Executes the race workflow (game loop, physics, state management) |
| **Temporal Server** | Orchestrates workflow execution, handles durability and replay |

---

## Data Models

### Track Model

The track is a loop of tiles. For the PoC, we use a simple oval with 20 tiles.

```python
from dataclasses import dataclass, field
from typing import Literal
from enum import Enum

class TileType(str, Enum):
    STRAIGHT = "straight"
    TURN_LEFT = "turn_left"

@dataclass
class Tile:
    index: int
    tile_type: TileType
    has_item_box: bool = False

@dataclass
class Track:
    tiles: list[Tile]

    @property
    def total_tiles(self) -> int:
        return len(self.tiles)

    @classmethod
    def create_oval(cls) -> "Track":
        """Create the PoC oval track: 20 tiles, 4 turns, 4 item boxes."""
        tiles = []
        # Layout: 5 straight, turn, 5 straight, turn, 5 straight, turn, 5 straight, turn
        # Turns at indices: 4, 9, 14, 19
        # Item boxes at indices: 0, 5, 10, 15
        turn_indices = {4, 9, 14, 19}
        item_box_indices = {0, 5, 10, 15}

        for i in range(20):
            tile_type = TileType.TURN_LEFT if i in turn_indices else TileType.STRAIGHT
            has_item_box = i in item_box_indices
            tiles.append(Tile(index=i, tile_type=tile_type, has_item_box=has_item_box))

        return cls(tiles=tiles)
```

### Racer State Model

```python
from typing import Optional

class Steering(str, Enum):
    LEFT = "left"
    STRAIGHT = "straight"
    RIGHT = "right"

class PowerUp(str, Enum):
    SPEED_BOOST = "speed_boost"

class RacerStatus(str, Enum):
    RACING = "racing"
    CRASHED = "crashed"  # In penalty cooldown
    FINISHED = "finished"

@dataclass
class RacerControls:
    """Current control inputs for a racer (persist between ticks)."""
    accelerating: bool = True  # Default: pedal down
    braking: bool = False
    steering: Steering = Steering.STRAIGHT
    use_item: bool = False  # One-shot flag, consumed after use

@dataclass
class RacerState:
    """Complete state for a single racer."""
    player_id: str

    # Position (each tile has 3 subunits)
    tile_index: int = 0
    tile_subunit: int = 0  # 0, 1, or 2

    # Movement
    speed: int = 0  # 0-3 normally, up to 5 with boost
    current_lap: int = 0  # 0 = hasn't crossed start yet, 1-3 during race

    # Power-ups
    power_up: Optional[PowerUp] = None
    boost_ticks_remaining: int = 0  # Countdown when boost is active

    # Status
    status: RacerStatus = RacerStatus.RACING
    penalty_ticks_remaining: int = 0  # Ticks until can move after crash
    finish_position: Optional[int] = None

    # Controls (updated via player input)
    controls: RacerControls = field(default_factory=RacerControls)

    @property
    def total_subunits(self) -> int:
        """Absolute position in subunits (for comparison)."""
        return (self.current_lap * 60) + (self.tile_index * 3) + self.tile_subunit

    @property
    def effective_max_speed(self) -> int:
        """Max speed considering active boosts."""
        return 5 if self.boost_ticks_remaining > 0 else 3
```

### Game State Model

```python
@dataclass
class GameState:
    """Complete state of a race."""
    race_id: str
    current_tick: int = 0
    max_ticks: int = 180  # 3 minutes max
    laps_required: int = 3

    track: Track = field(default_factory=Track.create_oval)
    racers: dict[str, RacerState] = field(default_factory=dict)

    # Finish order (player_ids)
    standings: list[str] = field(default_factory=list)

    @property
    def is_finished(self) -> bool:
        """Race ends when all racers finish or max ticks reached."""
        all_finished = all(r.status == RacerStatus.FINISHED for r in self.racers.values())
        return all_finished or self.current_tick >= self.max_ticks

    @property
    def next_finish_position(self) -> int:
        """Position for next racer to finish (1-indexed)."""
        return len(self.standings) + 1
```

### Input Models (for API)

```python
@dataclass
class PlayerInput:
    """Input sent by player via MCP/API."""
    player_id: str
    accelerating: Optional[bool] = None  # None = don't change
    braking: Optional[bool] = None
    steering: Optional[Steering] = None
    use_item: bool = False

@dataclass
class CreateRaceRequest:
    """Request to create a new race."""
    player_ids: list[str]

@dataclass
class RaceCreatedResponse:
    """Response after creating a race."""
    race_id: str
    workflow_id: str
    state: GameState
```

---

## Temporal Workflow Design

### Overview

The race is implemented as a single Temporal workflow that:
1. Initializes game state with the track and racers
2. Runs a game loop, sleeping 1 second between ticks
3. Accepts player input via **workflow updates** (synchronous, returns state)
4. Exposes current state via **workflow queries** (read-only)
5. Ends when all racers finish or max ticks reached

### Why Updates vs Signals?

| Mechanism | Use Case | Returns Value? |
|-----------|----------|----------------|
| **Signal** | Fire-and-forget state mutation | No |
| **Update** | State mutation with response | Yes |
| **Query** | Read-only state inspection | Yes |

We use **Updates** for player input because we want to return the current game state after applying the input. This gives players immediate feedback.

Reference: [Temporal Workflow Message Passing](https://docs.temporal.io/develop/python/message-passing)

### Workflow Implementation

```python
import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.workflow import defn, run, query, update

with workflow.unsafe.imports_passed_through():
    from models import GameState, RacerState, PlayerInput, Track, RacerStatus, Steering, PowerUp, TileType

@defn
class RaceWorkflow:
    """Temporal workflow representing a single race."""

    def __init__(self):
        self.game_state: GameState | None = None

    @run
    async def run(self, race_id: str, player_ids: list[str]) -> GameState:
        """Main race loop."""
        # Initialize game state
        self.game_state = GameState(race_id=race_id)
        for player_id in player_ids:
            self.game_state.racers[player_id] = RacerState(player_id=player_id)

        # Main game loop
        while not self.game_state.is_finished:
            # Process tick
            self._process_tick()

            # Wait for next tick (1 second)
            await asyncio.sleep(1)

        # Race complete - could store results via activity here
        # await workflow.execute_activity(
        #     store_race_results,
        #     self.game_state,
        #     start_to_close_timeout=timedelta(seconds=30)
        # )

        return self.game_state

    @query
    def get_state(self) -> GameState:
        """Query handler: return current game state."""
        return self.game_state

    @update
    async def apply_input(self, input: PlayerInput) -> GameState:
        """Update handler: apply player input and return current state."""
        if input.player_id not in self.game_state.racers:
            raise ValueError(f"Unknown player: {input.player_id}")

        racer = self.game_state.racers[input.player_id]
        controls = racer.controls

        # Apply input (None means "don't change")
        if input.accelerating is not None:
            controls.accelerating = input.accelerating
        if input.braking is not None:
            controls.braking = input.braking
        if input.steering is not None:
            controls.steering = input.steering
        if input.use_item:
            controls.use_item = True

        return self.game_state

    def _process_tick(self):
        """Process one game tick: update all racers."""
        self.game_state.current_tick += 1

        for racer in self.game_state.racers.values():
            if racer.status == RacerStatus.FINISHED:
                continue

            # Handle penalty cooldown
            if racer.penalty_ticks_remaining > 0:
                racer.penalty_ticks_remaining -= 1
                racer.status = RacerStatus.CRASHED if racer.penalty_ticks_remaining > 0 else RacerStatus.RACING
                continue

            # Handle boost countdown
            if racer.boost_ticks_remaining > 0:
                racer.boost_ticks_remaining -= 1

            # Process item use
            if racer.controls.use_item and racer.power_up == PowerUp.SPEED_BOOST:
                racer.boost_ticks_remaining = 3
                racer.power_up = None
                racer.controls.use_item = False

            # Update speed based on controls
            self._update_speed(racer)

            # Move racer
            self._move_racer(racer)

    def _update_speed(self, racer: RacerState):
        """Update racer speed based on controls."""
        if racer.controls.accelerating and not racer.controls.braking:
            racer.speed = min(racer.speed + 1, racer.effective_max_speed)
        elif racer.controls.braking and not racer.controls.accelerating:
            racer.speed = max(racer.speed - 1, 0)
        # If both or neither: speed unchanged

    def _move_racer(self, racer: RacerState):
        """Move racer based on current speed, handle turns and items."""
        subunits_to_move = racer.speed
        if racer.boost_ticks_remaining > 0:
            subunits_to_move = 5  # Boost overrides normal speed

        while subunits_to_move > 0:
            # Move one subunit
            racer.tile_subunit += 1
            subunits_to_move -= 1

            # Check if crossed into new tile
            if racer.tile_subunit >= 3:
                racer.tile_subunit = 0
                old_tile_index = racer.tile_index
                racer.tile_index = (racer.tile_index + 1) % self.game_state.track.total_tiles

                # Check for lap completion
                if racer.tile_index == 0 and old_tile_index == self.game_state.track.total_tiles - 1:
                    racer.current_lap += 1
                    if racer.current_lap >= self.game_state.laps_required:
                        racer.status = RacerStatus.FINISHED
                        racer.finish_position = self.game_state.next_finish_position
                        self.game_state.standings.append(racer.player_id)
                        return

                # Get new tile
                new_tile = self.game_state.track.tiles[racer.tile_index]

                # Check for turn handling
                if new_tile.tile_type == TileType.TURN_LEFT:
                    # Must be at speed 1 and steering left
                    if racer.speed > 1 or racer.controls.steering != Steering.LEFT:
                        # Crash! Reset to previous tile
                        racer.tile_index = old_tile_index
                        racer.tile_subunit = 0
                        racer.speed = 0
                        racer.penalty_ticks_remaining = 2
                        racer.status = RacerStatus.CRASHED
                        racer.boost_ticks_remaining = 0  # Lose boost on crash
                        return

                # Check for item box
                if new_tile.has_item_box and racer.power_up is None:
                    racer.power_up = PowerUp.SPEED_BOOST  # Only one power-up for now
```

### Workflow Event History Estimate

For a 3-minute race (180 ticks):
- Initial workflow events: ~5
- Per tick (sleep + workflow task): ~6-8 events
- Player inputs (updates): ~4-6 events each

**Estimated total: ~1,500-2,000 events**

This is well under Temporal's 51,200 event limit and even under the 10,240 warning threshold.

---

## FastAPI Endpoints

### Endpoint Summary

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/races` | Create a new race |
| `GET` | `/races/{race_id}/state` | Get current game state |
| `POST` | `/races/{race_id}/input` | Send player input |

### Implementation

```python
import uuid
from fastapi import FastAPI, HTTPException
from temporalio.client import Client
from pydantic import BaseModel

app = FastAPI(title="MCP Kart Backend")

# Pydantic models for API
class CreateRaceRequest(BaseModel):
    player_ids: list[str]

class PlayerInputRequest(BaseModel):
    player_id: str
    accelerating: bool | None = None
    braking: bool | None = None
    steering: str | None = None  # "left", "straight", "right"
    use_item: bool = False

class GameStateResponse(BaseModel):
    race_id: str
    current_tick: int
    # ... full game state serialized
    class Config:
        # Allow arbitrary types for complex nested objects
        arbitrary_types_allowed = True

# Global Temporal client (initialized on startup)
temporal_client: Client | None = None

@app.on_event("startup")
async def startup():
    global temporal_client
    temporal_client = await Client.connect("localhost:7233")

@app.post("/races")
async def create_race(request: CreateRaceRequest) -> dict:
    """Create a new race with the specified players."""
    race_id = str(uuid.uuid4())[:8]
    workflow_id = f"race-{race_id}"

    # Start the workflow
    handle = await temporal_client.start_workflow(
        RaceWorkflow.run,
        args=[race_id, request.player_ids],
        id=workflow_id,
        task_queue="mcpkart-task-queue",
    )

    # Query initial state
    state = await handle.query(RaceWorkflow.get_state)

    return {
        "race_id": race_id,
        "workflow_id": workflow_id,
        "state": state,  # Serialized GameState
    }

@app.get("/races/{race_id}/state")
async def get_race_state(race_id: str) -> dict:
    """Get current game state for a race."""
    workflow_id = f"race-{race_id}"

    try:
        handle = temporal_client.get_workflow_handle(workflow_id)
        state = await handle.query(RaceWorkflow.get_state)
        return {"state": state}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Race not found: {race_id}")

@app.post("/races/{race_id}/input")
async def send_input(race_id: str, request: PlayerInputRequest) -> dict:
    """Send player input and get updated state."""
    workflow_id = f"race-{race_id}"

    try:
        handle = temporal_client.get_workflow_handle(workflow_id)

        # Convert to domain model
        player_input = PlayerInput(
            player_id=request.player_id,
            accelerating=request.accelerating,
            braking=request.braking,
            steering=Steering(request.steering) if request.steering else None,
            use_item=request.use_item,
        )

        # Execute update (synchronous, returns state)
        state = await handle.execute_update(
            RaceWorkflow.apply_input,
            player_input,
        )

        return {"state": state}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Running the API

```bash
cd backend
uv run uvicorn mcpkart_backend.api.main:app --reload --port 8000
```

---

## FastMCP Server Tools

### Tool Summary

| Tool | Description | Returns |
|------|-------------|---------|
| `join_race` | Create/join a race | Race ID + initial state |
| `get_state` | Get current game state | Full game state |
| `control` | Send input controls | Updated game state |

### Implementation

```python
from fastmcp import FastMCP
import httpx
from typing import Optional

mcp = FastMCP("MCP Kart")

BACKEND_URL = "http://localhost:8000"

@mcp.tool()
async def join_race() -> dict:
    """
    Join a new race. For the PoC, this creates a solo race.

    Returns the race_id and initial game state. You'll need the race_id
    for all subsequent calls.

    The race starts immediately after joining. You have ~3 minutes to complete 3 laps.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/races",
            json={"player_ids": ["player1"]},  # PoC: single player
        )
        response.raise_for_status()
        data = response.json()

        return {
            "race_id": data["race_id"],
            "message": "Race started! You have 3 minutes to complete 3 laps.",
            "state": _format_state_for_ai(data["state"]),
        }

@mcp.tool()
async def get_state(race_id: str) -> dict:
    """
    Get the current game state for your race.

    Args:
        race_id: The race ID returned from join_race

    Returns:
        Current game state including your position, speed, upcoming track, etc.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BACKEND_URL}/races/{race_id}/state")
        response.raise_for_status()
        data = response.json()

        return _format_state_for_ai(data["state"])

@mcp.tool()
async def control(
    race_id: str,
    accelerate: Optional[bool] = None,
    brake: Optional[bool] = None,
    steer: Optional[str] = None,
    use_item: bool = False,
) -> dict:
    """
    Send control inputs for your kart. Inputs persist until changed.

    Args:
        race_id: The race ID returned from join_race
        accelerate: Set to True to press gas pedal, False to release.
                   When accelerating, speed increases by 1 each tick (max 3).
        brake: Set to True to brake, False to release.
               When braking, speed decreases by 1 each tick (min 0).
        steer: Set steering direction: "left", "straight", or "right".
               IMPORTANT: You must steer "left" AND be at speed 1 to make turns!
        use_item: Set to True to use your held item (if any).

    Returns:
        Updated game state after applying your input.

    Tips:
        - On straight tiles, accelerate to max speed (3)
        - Before turns, brake to speed 1 and set steering to "left"
        - If you crash (wrong speed/steering on turn), you'll be penalized 2 ticks
        - Item boxes give you speed boosts - use them on straightaways!
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/races/{race_id}/input",
            json={
                "player_id": "player1",  # PoC: single player
                "accelerating": accelerate,
                "braking": brake,
                "steering": steer,
                "use_item": use_item,
            },
        )
        response.raise_for_status()
        data = response.json()

        return _format_state_for_ai(data["state"])

def _format_state_for_ai(state: dict) -> dict:
    """
    Format game state in a way that's easy for AI assistants to understand.
    Includes helpful derived information like upcoming tiles.
    """
    racer = state["racers"].get("player1", {})
    track = state["track"]

    # Calculate upcoming tiles (next 5)
    current_tile = racer.get("tile_index", 0)
    total_tiles = len(track["tiles"])
    upcoming = []
    for i in range(1, 6):
        tile_idx = (current_tile + i) % total_tiles
        tile = track["tiles"][tile_idx]
        upcoming.append({
            "distance_tiles": i,
            "type": tile["tile_type"],
            "has_item_box": tile["has_item_box"],
        })

    return {
        "race_id": state["race_id"],
        "tick": state["current_tick"],
        "max_ticks": state["max_ticks"],
        "your_racer": {
            "position": {
                "tile": racer.get("tile_index", 0),
                "subunit": racer.get("tile_subunit", 0),
                "lap": racer.get("current_lap", 0),
            },
            "speed": racer.get("speed", 0),
            "max_speed": racer.get("effective_max_speed", 3),
            "steering": racer.get("controls", {}).get("steering", "straight"),
            "accelerating": racer.get("controls", {}).get("accelerating", True),
            "braking": racer.get("controls", {}).get("braking", False),
            "power_up": racer.get("power_up"),
            "boost_ticks_remaining": racer.get("boost_ticks_remaining", 0),
            "status": racer.get("status", "racing"),
            "penalty_ticks_remaining": racer.get("penalty_ticks_remaining", 0),
        },
        "track": {
            "total_tiles": total_tiles,
            "laps_required": state["laps_required"],
            "current_tile": track["tiles"][current_tile],
        },
        "upcoming_tiles": upcoming,
        "race_status": "finished" if state.get("is_finished") else "in_progress",
        "standings": state.get("standings", []),
    }
```

### Running the MCP Server

```bash
cd mcp_server
uv run fastmcp run mcpkart_mcp/server.py
```

---

## Database (SQLAlchemy + Alembic)

We use SQLAlchemy for ORM and Alembic for migrations. SQLite for PoC, Postgres for production.

### RaceResult Model

When a race completes, we store the results in the database via a Temporal activity.

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
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

    # Results
    standings: Mapped[list[str]] = mapped_column(JSON)  # Ordered list of player_ids

    # Relationship to individual racer results
    racer_results: Mapped[list["RacerResult"]] = relationship(back_populates="race")

class RacerResult(Base):
    """Individual racer's performance in a race."""
    __tablename__ = "racer_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[str] = mapped_column(String(32), ForeignKey("race_results.race_id"))
    player_id: Mapped[str] = mapped_column(String(64), index=True)

    # Performance
    finish_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    finish_tick: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_crashes: Mapped[int] = mapped_column(Integer, default=0)
    items_used: Mapped[int] = mapped_column(Integer, default=0)

    # Relationship
    race: Mapped["RaceResult"] = relationship(back_populates="racer_results")
```

### Database Configuration

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# PoC: SQLite
DATABASE_URL = "sqlite:///./mcpkart.db"

# Production: Postgres
# DATABASE_URL = "postgresql://user:pass@localhost/mcpkart"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # SQLite only
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Alembic Setup

Initialize Alembic in the backend directory:

```bash
cd backend
uv run alembic init alembic
```

Configure `alembic.ini`:
```ini
sqlalchemy.url = sqlite:///./mcpkart.db
```

Update `alembic/env.py` to import models:
```python
from mcpkart_backend.db.models import Base
target_metadata = Base.metadata
```

Create and run migrations:
```bash
uv run alembic revision --autogenerate -m "Initial race results tables"
uv run alembic upgrade head
```

### Activity to Store Results

```python
from temporalio import activity
from sqlalchemy.orm import Session
from datetime import datetime

@activity.defn
async def store_race_results(
    race_id: str,
    started_at: datetime,
    finished_at: datetime,
    total_ticks: int,
    standings: list[str],
    racer_stats: dict[str, dict],  # player_id -> stats
) -> None:
    """Store race results in the database."""
    # Note: In practice, you'd inject the DB session via activity context
    db = SessionLocal()
    try:
        race_result = RaceResult(
            race_id=race_id,
            started_at=started_at,
            finished_at=finished_at,
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
    finally:
        db.close()
```

### Workflow Update for Storing Results

Update the workflow to call the activity when the race ends:

```python
@run
async def run(self, race_id: str, player_ids: list[str]) -> GameState:
    started_at = datetime.utcnow()

    # ... game loop ...

    finished_at = datetime.utcnow()

    # Store results
    await workflow.execute_activity(
        store_race_results,
        args=[
            race_id,
            started_at,
            finished_at,
            self.game_state.current_tick,
            self.game_state.standings,
            self._get_racer_stats(),
        ],
        start_to_close_timeout=timedelta(seconds=30),
    )

    return self.game_state
```

---

## Testing (Temporal Test Framework)

Temporal provides a testing framework with **automatic time-skipping**, perfect for testing workflows with sleeps.

### Key Features

| Feature | Description |
|---------|-------------|
| **Auto time-skip** | `WorkflowEnvironment.start_time_skipping()` fast-forwards through `sleep()` calls |
| **Manual advance** | `env.sleep(seconds)` to manually jump forward |
| **Full workflow test** | Start workflow, send updates, query state, verify results |
| **Activity mocking** | Provide mock implementations to isolate workflow logic |

### Example: Full Race Test

```python
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from mcpkart_backend.temporal.workflows import RaceWorkflow
from mcpkart_backend.models import PlayerInput, Steering

@pytest.fixture
async def workflow_env():
    """Create a time-skipping test environment."""
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env

@pytest.mark.asyncio
async def test_race_completes_three_laps(workflow_env):
    """Test that a race completes when racer finishes 3 laps."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
    ):
        # Start race
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-race-1",
            task_queue="test-queue",
        )

        # Simulate player inputs (accelerate, handle turns)
        # This runs near-instantly despite 180 sleep(1) calls!

        # Get final result
        result = await handle.result()

        assert result.is_finished
        assert "player1" in result.standings

@pytest.mark.asyncio
async def test_crash_on_turn_at_high_speed(workflow_env):
    """Test that racer crashes when hitting turn at speed > 1."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-crash-1",
            task_queue="test-queue",
        )

        # Let racer accelerate (default behavior)
        # First turn is at tile 4, racer will hit it at speed 3
        await workflow_env.sleep(10)  # Advance time

        # Query state
        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Should have crashed and be in penalty
        assert racer.status.value == "crashed" or racer.penalty_ticks_remaining > 0

@pytest.mark.asyncio
async def test_successful_turn_navigation(workflow_env):
    """Test that racer can navigate turn at speed 1 with left steering."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-turn-1",
            task_queue="test-queue",
        )

        # Wait until near the turn (tile 4)
        await workflow_env.sleep(3)

        # Brake and steer left
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", braking=True, steering=Steering.LEFT),
        )

        # Wait for turn navigation
        await workflow_env.sleep(5)

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Should be past the turn (tile > 4) without crashing
        assert racer.tile_index > 4
        assert racer.status.value == "racing"
```

### Running Tests

```bash
cd backend
uv run pytest tests/ -v
```

### Note on ARM Architecture

The time-skipping test server doesn't work on ARM Linux/Windows. On ARM Mac, it works via Rosetta emulation. For CI, use x64 runners.

---

## Project Structure

```
mcpkart/
├── research/
│   ├── project_concept.md
│   └── implementation_plan.md
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini                      # Alembic config
│   ├── alembic/                         # Alembic migrations
│   │   ├── env.py
│   │   └── versions/
│   └── src/
│       └── mcpkart_backend/
│           ├── __init__.py
│           ├── api/
│           │   ├── __init__.py
│           │   ├── main.py              # FastAPI app + endpoints
│           │   └── dependencies.py      # Temporal client setup
│           ├── temporal/
│           │   ├── __init__.py
│           │   ├── workflows.py         # RaceWorkflow
│           │   ├── activities.py        # store_race_results activity
│           │   └── worker.py            # Worker entrypoint
│           ├── db/
│           │   ├── __init__.py
│           │   ├── models.py            # SQLAlchemy models (RaceResult, RacerResult)
│           │   └── database.py          # Engine, SessionLocal, get_db
│           └── models/
│               ├── __init__.py
│               ├── track.py             # Track, Tile (Pydantic)
│               ├── racer.py             # RacerState, RacerControls (Pydantic)
│               ├── game_state.py        # GameState (Pydantic)
│               └── inputs.py            # PlayerInput, API models (Pydantic)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py                  # pytest fixtures
│       ├── test_workflow.py             # Temporal workflow tests
│       └── test_game_logic.py           # Unit tests for game mechanics
│
├── mcp_server/
│   ├── pyproject.toml
│   └── src/
│       └── mcpkart_mcp/
│           ├── __init__.py
│           └── server.py                # FastMCP tools
│
└── README.md
```

### Dependencies

**backend/pyproject.toml:**
```toml
[project]
name = "mcpkart-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "temporalio>=1.4.0",
    "pydantic>=2.0.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.13.0",
]

[project.optional-dependencies]
test = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**mcp_server/pyproject.toml:**
```toml
[project]
name = "mcpkart-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=0.1.0",
    "httpx>=0.26.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Implementation Steps

### Phase 1: Backend Foundation

1. **Set up backend project structure**
   - Initialize with `uv init`
   - Create directory structure
   - Add dependencies (FastAPI, Temporal, SQLAlchemy, Alembic)

2. **Implement Pydantic data models**
   - Track and Tile models
   - RacerState and RacerControls
   - GameState
   - API request/response models

3. **Set up database**
   - Initialize Alembic: `uv run alembic init alembic`
   - Create SQLAlchemy models (RaceResult, RacerResult)
   - Create initial migration
   - Run migration to create SQLite database

4. **Implement Temporal workflow**
   - RaceWorkflow with game loop
   - Query handler for state
   - Update handler for input
   - Tick processing logic (movement, turns, items)

5. **Implement Temporal activities**
   - `store_race_results` activity to persist results after race ends

6. **Implement Temporal worker**
   - Worker entrypoint script
   - Register workflow and activities

7. **Implement FastAPI endpoints**
   - POST /races
   - GET /races/{race_id}/state
   - POST /races/{race_id}/input
   - Temporal client setup

### Phase 2: MCP Server

8. **Set up MCP server project**
   - Initialize with `uv init`
   - Add FastMCP dependency

9. **Implement MCP tools**
   - join_race tool
   - get_state tool
   - control tool
   - State formatting helper

### Phase 3: Testing & Polish

10. **Set up testing infrastructure**
    - Configure pytest and pytest-asyncio
    - Create fixtures for WorkflowEnvironment

11. **Write workflow tests**
    - Test full race completion
    - Test crash mechanics on turns
    - Test successful turn navigation
    - Test item box pickup and boost usage

12. **Local testing setup**
    - Docker compose for Temporal server
    - Scripts to start worker, API, and MCP server

13. **Manual end-to-end testing**
    - Test race creation via API
    - Test playing a race via MCP tools
    - Verify results are stored in database

---

## Resolved Design Decisions

1. **Serialization**: Use Pydantic models everywhere. Temporal officially supports Pydantic for workflow inputs/outputs.

2. **Error handling**: Current "happy path" design is appropriate for single-player PoC. Will revisit for multiplayer.

3. **Race results persistence**: Store results in database via `store_race_results` activity when race ends. SQLite for PoC, Postgres for production. Let Temporal handle workflow cleanup via retention policy.

4. **Concurrent input**: Inputs applied in order received. Fast MCP clients get a slight advantage - this is intentional and becomes more interesting with missiles.

5. **Testing**: Use Temporal's time-skipping test framework with pytest. Enables testing 3-minute races in milliseconds.

## Future Considerations

1. **State size**: GameState should stay small (few KB) - worth monitoring as we add features.

2. **NPC players**: Plan to implement via separate processes running Claude Code/Cline/Codex CLI with our MCP server.

3. **OAuth**: Future implementation for player identity, likely GitHub-based.

4. **Multiplayer lobbies**: Race creation will need lobby/matchmaking logic when we support multiple human players.

---

## References

- [Temporal Python SDK](https://docs.temporal.io/develop/python)
- [Temporal Workflow Message Passing](https://docs.temporal.io/develop/python/message-passing)
- [Temporal Python Testing Suite](https://docs.temporal.io/develop/python/testing-suite)
- [FastMCP Documentation](https://gofastmcp.com/getting-started/welcome)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic ORM Mode](https://docs.pydantic.dev/latest/examples/orms/)
