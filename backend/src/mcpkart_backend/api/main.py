"""FastAPI application for MCP Kart backend."""

import asyncio
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException

from mcpkart_backend.api.dependencies import get_temporal_client, lifespan_context
from mcpkart_backend.models import (
    CreateLobbyRequest,
    CreateRaceRequest,
    GameState,
    JoinLobbyRequest,
    PlayerInput,
    PlayerInputRequest,
    RacerStatus,
    StartRaceRequest,
)
from mcpkart_backend.temporal import RaceWorkflow

TASK_QUEUE = "mcpkart-task-queue"

# --- Spectator State Cache ---
# Simple in-memory TTL cache to decouple viewer count from Temporal query load
_spectator_cache: dict[str, tuple[dict[str, Any], float]] = {}
CACHE_TTL = 0.8  # seconds - slightly less than tick rate

# Human-friendly race ID character set (excludes confusable chars: 0/O, 1/I/l)
RACE_ID_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_race_id() -> str:
    """Generate a human-friendly 6-character race ID.

    Uses 32 possible characters, 6 positions = 32^6 = ~1 billion combinations.
    """
    return "".join(secrets.choice(RACE_ID_CHARS) for _ in range(6))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    async with lifespan_context():
        yield


app = FastAPI(
    title="MCP Kart Backend",
    description="Backend API for MCP Kart racing game",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# --- Lobby Endpoints ---


@app.post("/lobbies")
async def create_lobby(request: CreateLobbyRequest) -> dict[str, Any]:
    """Create a new race lobby.

    Args:
        request: Contains creator_id (and optional max_racers)

    Returns:
        race_id, workflow_id, and initial lobby state
    """
    client = await get_temporal_client()

    race_id = generate_race_id()
    workflow_id = f"race-{race_id}"

    # Start workflow with creator_id
    handle = await client.start_workflow(
        RaceWorkflow.run,
        args=[race_id, request.creator_id],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    await asyncio.sleep(0.1)  # Small delay for initialization

    try:
        state = await handle.query(RaceWorkflow.get_state)
    except Exception:
        return {
            "race_id": race_id,
            "workflow_id": workflow_id,
            "message": "Lobby created, query state to get current status",
        }

    return {
        "race_id": race_id,
        "workflow_id": workflow_id,
        "state": state.model_dump(),
    }


@app.post("/lobbies/{race_id}/join")
async def join_lobby(race_id: str, request: JoinLobbyRequest) -> dict[str, Any]:
    """Join an existing race lobby.

    Args:
        race_id: The race/lobby identifier
        request: Contains player_id

    Returns:
        Updated lobby state
    """
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    try:
        handle = client.get_workflow_handle(workflow_id)
        state: GameState = await handle.execute_update(
            RaceWorkflow.join_lobby,
            args=[request.player_id],
        )
        return {"state": state.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Lobby not found: {race_id}") from e


@app.post("/lobbies/{race_id}/start")
async def start_race_endpoint(race_id: str, request: StartRaceRequest) -> dict[str, Any]:
    """Start the race (lobby creator only).

    Transitions from LOBBY to PLANNING phase (60-second countdown).

    Args:
        race_id: The race/lobby identifier
        request: Contains player_id (must be creator)

    Returns:
        Updated state with PLANNING phase
    """
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    try:
        handle = client.get_workflow_handle(workflow_id)
        state: GameState = await handle.execute_update(
            RaceWorkflow.start_race,
            args=[request.player_id],
        )
        return {"state": state.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Lobby not found: {race_id}") from e


# --- Legacy Race Endpoints ---


@app.post("/races", deprecated=True)
async def create_race(request: CreateRaceRequest) -> dict[str, Any]:
    """Create a new race with the specified players (DEPRECATED).

    Use POST /lobbies instead. This endpoint creates a lobby with the first
    player as creator, adds remaining players, and auto-starts the race.

    Args:
        request: Race creation request with player IDs

    Returns:
        Race ID, workflow ID, and initial game state
    """
    if not request.player_ids:
        raise HTTPException(status_code=400, detail="At least one player required")

    client = await get_temporal_client()

    race_id = generate_race_id()
    workflow_id = f"race-{race_id}"

    creator_id = request.player_ids[0]

    # Start the workflow with creator
    handle = await client.start_workflow(
        RaceWorkflow.run,
        args=[race_id, creator_id],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    await asyncio.sleep(0.1)  # Small delay to ensure workflow starts

    # Add additional players if any
    for player_id in request.player_ids[1:]:
        try:
            await handle.execute_update(
                RaceWorkflow.join_lobby,
                args=[player_id],
            )
        except Exception:
            pass  # Ignore errors adding players for backward compat

    # Auto-start the race (skip lobby phase)
    try:
        await handle.execute_update(
            RaceWorkflow.start_race,
            args=[creator_id],
        )
    except Exception:
        pass  # Ignore if already started

    try:
        state = await handle.query(RaceWorkflow.get_state)
    except Exception:
        return {
            "race_id": race_id,
            "workflow_id": workflow_id,
            "message": "Race started, query state to get current status",
        }

    return {
        "race_id": race_id,
        "workflow_id": workflow_id,
        "state": state.model_dump(),
    }


@app.get("/races/{race_id}/state")
async def get_race_state(race_id: str) -> dict[str, Any]:
    """Get current game state for a race.

    Args:
        race_id: The race identifier

    Returns:
        Current game state
    """
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    try:
        handle = client.get_workflow_handle(workflow_id)
        state: GameState = await handle.query(RaceWorkflow.get_state)
        return {"state": state.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Race not found: {race_id}") from e


def _transform_to_spectator_state(state: GameState) -> dict[str, Any]:
    """Transform GameState to frontend-friendly spectator format."""
    # Convert racers dict to array with computed standings
    racers_list = []
    for player_id, racer in state.racers.items():
        racers_list.append({
            "id": player_id,
            "name": player_id,  # Use player_id as name for now
            "tile_index": racer.tile_index,
            "tile_subunit": racer.tile_subunit,
            "speed": racer.speed,
            "current_lap": racer.current_lap,
            "power_up": racer.power_up.value if racer.power_up else None,
            "boost_ticks_remaining": racer.boost_ticks_remaining,
            "status": racer.status.value,
            "penalty_ticks_remaining": racer.penalty_ticks_remaining,
            "finish_position": racer.finish_position,
            "finish_time": racer.finish_time,
            "total_crashes": racer.total_crashes,
            "on_turn_tile": racer.on_turn_tile,
            "in_drift_zone": racer.in_drift_zone,
            "drift_enabled": racer.drift_enabled,
        })

    # Sort racers by position for standings
    # Finished racers first (by finish_position), then by lap desc, then tile_index desc
    def racer_sort_key(r: dict) -> tuple:
        if r["status"] == "finished" and r["finish_position"] is not None:
            return (0, r["finish_position"], 0, 0)
        return (1, 0, -r["current_lap"], -r["tile_index"])

    sorted_racers = sorted(racers_list, key=racer_sort_key)

    standings = []
    for i, r in enumerate(sorted_racers):
        standings.append({
            "position": i + 1,
            "racer_id": r["id"],
            "name": r["name"],
            "lap": r["current_lap"],
            "tile_index": r["tile_index"],
            "status": r["status"],
            "finish_time": r["finish_time"],
        })

    # Transform track tiles
    track_tiles = []
    for tile in state.track.tiles:
        track_tiles.append({
            "index": tile.index,
            "tile_type": tile.tile_type.value,
            "has_item_box": tile.has_item_box,
        })

    return {
        "race_id": state.race_id,
        "current_tick": state.current_tick,
        "max_ticks": state.max_ticks,
        "laps_required": state.laps_required,
        "status": state.phase.value,  # Rename phase -> status for frontend
        "race_clock": state.race_clock,
        "max_race_clock": state.max_race_clock,
        "planning_ends_at": state.planning_ends_at.isoformat() if state.planning_ends_at else None,
        "track": {"tiles": track_tiles},
        "racers": racers_list,
        "standings": standings,
        "events": state.events[-20:],  # Last 20 events
    }


@app.get("/api/races/{race_id}/spectator-state")
async def get_spectator_state(race_id: str) -> dict[str, Any]:
    """Get race state optimized for spectator frontend.

    This endpoint:
    - Uses a short-TTL cache to handle many viewers efficiently
    - Returns a transformed format with racers as array and computed standings
    - Renames 'phase' to 'status' for frontend consistency

    Args:
        race_id: The race identifier

    Returns:
        Spectator-optimized race state
    """
    now = time.time()

    # Check cache first
    cached = _spectator_cache.get(race_id)
    if cached and (now - cached[1]) < CACHE_TTL:
        return cached[0]

    # Cache miss - query Temporal and transform
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    try:
        handle = client.get_workflow_handle(workflow_id)
        state: GameState = await handle.query(RaceWorkflow.get_state)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Race not found: {race_id}") from e

    # Transform and cache
    spectator_state = _transform_to_spectator_state(state)
    _spectator_cache[race_id] = (spectator_state, now)

    return spectator_state


@app.post("/races/{race_id}/input")
async def send_input(race_id: str, request: PlayerInputRequest) -> dict[str, Any]:
    """Send player input (applied immediately).

    Args:
        race_id: The race identifier
        request: Player input request with target_speed, drift, and use_item

    Returns:
        Updated game state after applying input
    """
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    try:
        handle = client.get_workflow_handle(workflow_id)

        # Convert to domain model
        player_input = PlayerInput(
            player_id=request.player_id,
            target_speed=request.target_speed,
            drift=request.drift,
            use_item=request.use_item,
        )

        # Execute update (synchronous, returns state)
        state: GameState = await handle.execute_update(
            RaceWorkflow.apply_input,
            args=[player_input],
        )

        return {"state": state.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to send input: {str(e)}") from e
