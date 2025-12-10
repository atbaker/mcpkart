"""FastAPI application for MCP Kart backend."""

from dotenv import load_dotenv

# Load .env from current working directory (backend/)
load_dotenv()

import asyncio
import secrets
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException

from mcpkart_backend.api.auth import AuthenticatedUser, get_current_user
from mcpkart_backend.api.cache import (
    calculate_ttl_until_next_tick,
    close_redis,
    get_cached_spectator_state,
    set_cached_spectator_state,
)
from mcpkart_backend.api.dependencies import get_temporal_client, lifespan_context
from mcpkart_backend.db import RaceResult, RacerResult, SessionLocal
from temporalio.common import SearchAttributePair, TypedSearchAttributes

from mcpkart_backend.models import (
    CreateLobbyRequest,
    CreateRaceRequest,
    format_race_clock,
    GameState,
    JoinLobbyRequest,
    JoinMatchmakingRequest,
    PlayerInput,
    PlayerInputRequest,
    RacerStatus,
    StartRaceRequest,
    TileType,
)
from mcpkart_backend.temporal import RaceWorkflow
from mcpkart_backend.temporal.search_attributes import IS_PUBLIC, PHASE, RACER_COUNT

TASK_QUEUE = "mcpkart-task-queue"

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
    # Clean up Redis connection on shutdown
    await close_redis()


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
async def create_lobby(
    request: CreateLobbyRequest,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new race lobby.

    Args:
        request: Contains creator_id, optional max_racers, and is_public flag
        user: Authenticated user from GitHub OAuth

    Returns:
        race_id, workflow_id, and initial lobby state
    """
    client = await get_temporal_client()

    race_id = generate_race_id()
    workflow_id = f"race-{race_id}"

    # Use authenticated username as creator_id (overrides request)
    creator_id = user.github_username if user else request.creator_id

    # Determine initial phase based on public/private
    initial_phase = "MATCHMAKING" if request.is_public else "LOBBY"

    # Start workflow with creator_id and is_public flag
    handle = await client.start_workflow(
        RaceWorkflow.run,
        args=[race_id, creator_id, request.is_public],
        id=workflow_id,
        task_queue=TASK_QUEUE,
        search_attributes=TypedSearchAttributes([
            SearchAttributePair(IS_PUBLIC, request.is_public),
            SearchAttributePair(PHASE, initial_phase),
            SearchAttributePair(RACER_COUNT, 1),  # Creator is first racer
        ]),
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
async def join_lobby(
    race_id: str,
    request: JoinLobbyRequest,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
) -> dict[str, Any]:
    """Join an existing race lobby.

    Args:
        race_id: The race/lobby identifier
        request: Contains player_id
        user: Authenticated user from GitHub OAuth

    Returns:
        Updated lobby state
    """
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    # Use authenticated username as player_id (overrides request)
    player_id = user.github_username if user else request.player_id

    try:
        handle = client.get_workflow_handle(workflow_id)
        state: GameState = await handle.execute_update(
            RaceWorkflow.join_lobby,
            args=[player_id],
        )
        return {"state": state.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Lobby not found: {race_id}") from e


@app.post("/lobbies/{race_id}/start")
async def start_race_endpoint(
    race_id: str,
    request: StartRaceRequest,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
) -> dict[str, Any]:
    """Start the race (lobby creator only).

    Transitions from LOBBY to PLANNING phase (60-second countdown).

    Args:
        race_id: The race/lobby identifier
        request: Contains player_id (must be creator)
        user: Authenticated user from GitHub OAuth

    Returns:
        Updated state with PLANNING phase
    """
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    # Use authenticated username as player_id (overrides request)
    player_id = user.github_username if user else request.player_id

    try:
        handle = client.get_workflow_handle(workflow_id)
        state: GameState = await handle.execute_update(
            RaceWorkflow.start_race,
            args=[player_id],
        )
        return {"state": state.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Lobby not found: {race_id}") from e


# --- Matchmaking Endpoints ---


@app.post("/matchmaking/join")
async def join_matchmaking(
    request: JoinMatchmakingRequest,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
) -> dict[str, Any]:
    """Join public matchmaking to find a race.

    This endpoint:
    1. Queries Temporal for an open public lobby (MATCHMAKING phase, < 8 players)
    2. If found, joins the player to that lobby
    3. If not found, creates a new public lobby

    Args:
        request: Contains player_id
        user: Authenticated user from GitHub OAuth

    Returns:
        race_id, state, and whether a new lobby was created
    """
    client = await get_temporal_client()

    # Use authenticated username as player_id (overrides request)
    player_id = user.github_username if user else request.player_id

    # Query for open public lobbies
    query = 'IsPublic = true AND Phase = "MATCHMAKING" AND RacerCount < 8'

    try:
        async for workflow in client.list_workflows(query):
            # Found an open lobby - try to join it
            race_id = workflow.id.replace("race-", "")
            handle = client.get_workflow_handle(workflow.id)

            try:
                state: GameState = await handle.execute_update(
                    RaceWorkflow.join_lobby,
                    args=[player_id],
                )
                return {
                    "race_id": race_id,
                    "state": state.model_dump(),
                    "created": False,
                }
            except ValueError as e:
                # Lobby might be full now (race condition) or player already in lobby
                # Try next one or create new
                if "already in lobby" in str(e).lower():
                    # Player is already in this lobby - return current state
                    state = await handle.query(RaceWorkflow.get_state)
                    return {
                        "race_id": race_id,
                        "state": state.model_dump(),
                        "created": False,
                    }
                continue
            except Exception:
                # Workflow might have ended - try next one
                continue
    except Exception:
        # Query failed - fall through to create new lobby
        pass

    # No open lobby found - create a new public one
    race_id = generate_race_id()
    workflow_id = f"race-{race_id}"

    handle = await client.start_workflow(
        RaceWorkflow.run,
        args=[race_id, player_id, True],  # is_public=True
        id=workflow_id,
        task_queue=TASK_QUEUE,
        search_attributes=TypedSearchAttributes([
            SearchAttributePair(IS_PUBLIC, True),
            SearchAttributePair(PHASE, "MATCHMAKING"),
            SearchAttributePair(RACER_COUNT, 1),
        ]),
    )

    await asyncio.sleep(0.1)  # Small delay for initialization

    try:
        state = await handle.query(RaceWorkflow.get_state)
    except Exception:
        return {
            "race_id": race_id,
            "state": None,
            "created": True,
            "message": "Lobby created, query state to get current status",
        }

    return {
        "race_id": race_id,
        "state": state.model_dump(),
        "created": True,
    }


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
        "is_public": state.is_public,
        "race_clock": state.race_clock,
        "max_race_clock": state.max_race_clock,
        "matchmaking_ends_at": state.matchmaking_ends_at.isoformat() if state.matchmaking_ends_at else None,
        "planning_ends_at": state.planning_ends_at.isoformat() if state.planning_ends_at else None,
        "ready_players": list(state.ready_players),
        "track": {"tiles": track_tiles},
        "racers": racers_list,
        "standings": standings,
        "events": state.events[-20:],  # Last 20 events
    }


def _get_standard_track_tiles() -> list[dict[str, Any]]:
    """Generate the standard 44-tile oval track for finished races."""
    # Match the track from Track.create_oval()
    turn_tiles = {7, 15, 29, 37}
    item_box_tiles = {11, 22, 33}
    tiles = []
    for i in range(44):
        tiles.append({
            "index": i,
            "tile_type": TileType.TURN_LEFT.value if i in turn_tiles else TileType.STRAIGHT.value,
            "has_item_box": i in item_box_tiles,
        })
    return tiles


def _reconstruct_from_db(race_result: RaceResult, db) -> dict[str, Any]:
    """Reconstruct SpectatorState from database records for finished races."""
    racer_results = db.query(RacerResult).filter(
        RacerResult.race_id == race_result.race_id
    ).all()

    # Build racers list
    racers_list = []
    for rr in racer_results:
        racers_list.append({
            "id": rr.player_id,
            "name": rr.player_id,
            "tile_index": rr.tile_index,
            "tile_subunit": rr.tile_subunit,
            "speed": rr.speed,
            "current_lap": rr.current_lap,
            "power_up": None,
            "boost_ticks_remaining": 0,
            "status": "finished",
            "penalty_ticks_remaining": 0,
            "finish_position": rr.finish_position,
            "finish_time": rr.finish_time,
            "total_crashes": rr.total_crashes,
            "on_turn_tile": False,
            "in_drift_zone": False,
            "drift_enabled": False,
        })

    # Build standings from stored order
    standings = []
    for i, player_id in enumerate(race_result.standings):
        racer = next((r for r in racers_list if r["id"] == player_id), None)
        if racer:
            standings.append({
                "position": i + 1,
                "racer_id": player_id,
                "name": player_id,
                "lap": racer["current_lap"],
                "tile_index": racer["tile_index"],
                "status": "finished",
                "finish_time": racer["finish_time"],
            })

    return {
        "race_id": race_result.race_id,
        "current_tick": race_result.total_ticks,
        "max_ticks": race_result.max_ticks,
        "laps_required": race_result.laps_required,
        "status": "finished",
        "is_public": race_result.is_public,
        "race_clock": format_race_clock(race_result.total_ticks),
        "max_race_clock": format_race_clock(race_result.max_ticks),
        "matchmaking_ends_at": None,
        "planning_ends_at": None,
        "ready_players": [],
        "track": {"tiles": _get_standard_track_tiles()},
        "racers": racers_list,
        "standings": standings,
        "events": race_result.events or [],
    }


@app.get("/api/races/{race_id}/spectator-state")
async def get_spectator_state(race_id: str) -> dict[str, Any]:
    """Get race state optimized for spectator frontend.

    This endpoint:
    - Uses Redis cache to handle many viewers efficiently
    - Returns a transformed format with racers as array and computed standings
    - Renames 'phase' to 'status' for frontend consistency
    - Falls back to database for finished races
    - No authentication required (public spectator view)

    Args:
        race_id: The race identifier

    Returns:
        Spectator-optimized race state
    """
    # Check Redis cache first
    cached = await get_cached_spectator_state(race_id)
    if cached:
        return cached

    # Try Temporal workflow (for live/active races)
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    try:
        handle = client.get_workflow_handle(workflow_id)
        state: GameState = await handle.query(RaceWorkflow.get_state)

        # Transform and cache in Redis with dynamic TTL
        spectator_state = _transform_to_spectator_state(state)

        # Calculate TTL based on when next tick occurs (aligns cache expiration with tick boundaries)
        ttl = calculate_ttl_until_next_tick(state.race_started_at, state.current_tick)
        await set_cached_spectator_state(race_id, spectator_state, ttl=ttl)

        return spectator_state
    except Exception:
        pass  # Workflow not found or query failed, try database

    # Fall back to database (for finished races)
    db = SessionLocal()
    try:
        race_result = db.query(RaceResult).filter(
            RaceResult.race_id == race_id
        ).first()
        if not race_result:
            raise HTTPException(status_code=404, detail=f"Race not found: {race_id}")

        spectator_state = _reconstruct_from_db(race_result, db)
        # Cache with long TTL for finished races (1 hour)
        await set_cached_spectator_state(race_id, spectator_state, ttl=3600)
        return spectator_state
    finally:
        db.close()


@app.post("/races/{race_id}/input")
async def send_input(
    race_id: str,
    request: PlayerInputRequest,
    user: Optional[AuthenticatedUser] = Depends(get_current_user),
) -> dict[str, Any]:
    """Send player input (applied immediately).

    Args:
        race_id: The race identifier
        request: Player input request with target_speed, drift, use_item, and ready
        user: Authenticated user from GitHub OAuth

    Returns:
        Updated game state after applying input
    """
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    # Use authenticated username as player_id (overrides request)
    player_id = user.github_username if user else request.player_id

    try:
        handle = client.get_workflow_handle(workflow_id)

        # Convert to domain model
        player_input = PlayerInput(
            player_id=player_id,
            target_speed=request.target_speed,
            drift=request.drift,
            use_item=request.use_item,
            ready=request.ready,
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
