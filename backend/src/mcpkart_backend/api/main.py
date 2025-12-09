"""FastAPI application for MCP Kart backend."""

import asyncio
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

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
    TileType,
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


def _render_ascii_track(state: GameState) -> str:
    """Render ASCII art representation of the track with racer positions."""
    # Build track row
    track_cells = []
    for tile in state.track.tiles:
        if tile.tile_type == TileType.TURN_LEFT:
            prefix = "T"
        elif tile.has_item_box:
            prefix = "I"
        else:
            prefix = " "
        track_cells.append(f"[{prefix}{tile.index:2d}]")

    track_line = "".join(track_cells)

    # Build position markers for each racer
    racer_lines = []
    for player_id, racer in state.racers.items():
        # Calculate position in the track string
        # Each cell is 5 chars wide: [X##]
        marker_pos = racer.tile_index * 5 + 2  # Center of the cell
        marker_line = " " * marker_pos + f"^{player_id[:8]}"
        racer_lines.append(marker_line)

    return track_line + "\n" + "\n".join(racer_lines)


def _render_racer_status(state: GameState) -> str:
    """Render racer status information."""
    lines = []
    for player_id, racer in state.racers.items():
        power_up = racer.power_up.value if racer.power_up else "none"
        boost = f" BOOSTING({racer.boost_seconds_remaining}s)" if racer.boost_seconds_remaining > 0 else ""
        turn_status = " [ON TURN]" if racer.on_turn_tile else ""
        drift_zone = " [DRIFT ZONE]" if racer.in_drift_zone else ""
        drift_enabled = " [DRIFTING]" if racer.drift_enabled else ""
        lines.append(
            f"- {player_id}: tile {racer.tile_index}.{racer.tile_subunit}, "
            f"speed {racer.speed} (target: {racer.controls.target_speed}), "
            f"lap {racer.current_lap}/{state.laps_required}, "
            f"status: {racer.status.value}{boost}{turn_status}{drift_zone}{drift_enabled}, "
            f"item: {power_up}, crashes: {racer.total_crashes}"
        )
    return "\n".join(lines)


def _render_phase_badge(state: GameState) -> str:
    """Render a colored badge for the current phase."""
    from mcpkart_backend.models import RacePhase

    phase_colors = {
        RacePhase.LOBBY: "#00bfff",  # Blue
        RacePhase.PLANNING: "#ffa500",  # Orange
        RacePhase.RACING: "#00ff00",  # Green
        RacePhase.FINISHED: "#ff00ff",  # Magenta
    }
    color = phase_colors.get(state.phase, "#ffffff")
    return f'<span style="background: {color}; color: black; padding: 2px 8px; font-weight: bold;">{state.phase.value.upper()}</span>'


def _render_lobby_info(state: GameState, race_id: str) -> str:
    """Render lobby-specific information."""
    players_list = "\n".join(
        f"  - {pid}" + (" (creator)" if pid == state.creator_id else "")
        for pid in state.racers.keys()
    )
    return f"""<h2>Lobby Info</h2>
<pre>
Creator: {state.creator_id}
Players ({len(state.racers)}/{state.max_racers}):
{players_list}
</pre>
<h2>Join Instructions</h2>
<pre>
Race ID: {race_id}

Share this race ID with friends to join!
They can use: join_race(player_id="their_id", race_id="{race_id}")
</pre>"""


def _render_planning_info(state: GameState) -> str:
    """Render planning phase countdown."""
    if state.planning_ends_at:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        remaining = (state.planning_ends_at - now).total_seconds()
        remaining = max(0, int(remaining))
    else:
        remaining = "?"

    return f"""<h2 style="color: #ffa500;">⏱️ PLANNING PHASE</h2>
<pre style="color: #ffa500; font-size: 18px;">
Race starts in: {remaining} seconds

All racers can set their initial inputs now!
Use: control(race_id="...", player_id="...", target_speed=3)
</pre>"""


@app.get("/debug/{race_id}", response_class=HTMLResponse)
async def debug_race(race_id: str) -> str:
    """Debug visualization page for a race.

    Shows ASCII track, racer status, and event log with auto-refresh.
    """
    from mcpkart_backend.models import RacePhase

    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    try:
        handle = client.get_workflow_handle(workflow_id)
        state: GameState = await handle.query(RaceWorkflow.get_state)
    except Exception as e:
        return f"<html><body><h1>Race not found: {race_id}</h1><p>{e}</p></body></html>"

    phase_badge = _render_phase_badge(state)

    # Build phase-specific content
    phase_content = ""
    if state.phase == RacePhase.LOBBY:
        phase_content = _render_lobby_info(state, race_id)
    elif state.phase == RacePhase.PLANNING:
        phase_content = _render_planning_info(state)
        # Also show racers during planning
        racer_status = _render_racer_status(state)
        phase_content += f"\n<h2>Racers</h2>\n<pre>{racer_status}</pre>"
    elif state.phase in (RacePhase.RACING, RacePhase.FINISHED):
        ascii_track = _render_ascii_track(state)
        racer_status = _render_racer_status(state)
        events_log = "\n".join(reversed(state.events))  # Newest first
        phase_content = f"""
    <h2>Track (I=item box, T=turn)</h2>
    <pre class="track">{ascii_track}</pre>

    <h2>Racers</h2>
    <pre>{racer_status}</pre>

    <h2>Event Log (newest first)</h2>
    <pre>{events_log if events_log else "(no events yet)"}</pre>"""

    # Status line varies by phase
    if state.phase == RacePhase.LOBBY:
        status_line = f"Waiting for players... ({len(state.racers)}/{state.max_racers})"
    elif state.phase == RacePhase.PLANNING:
        status_line = "Preparing to race..."
    else:
        status_line = f"Race Clock: {state.race_clock}/{state.max_race_clock} (tick {state.current_tick}/{state.max_ticks})"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>MCP Kart Debug - Race {race_id}</title>
    <style>
        body {{ font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px; }}
        pre {{ margin: 0; white-space: pre-wrap; }}
        h2 {{ color: #ffff00; margin-top: 20px; }}
        .track {{ font-size: 14px; overflow-x: auto; }}
        .header {{ display: flex; align-items: center; gap: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MCP Kart - Race {race_id}</h1>
        {phase_badge}
    </div>
    <p>{status_line}</p>
    {phase_content}
    {f'<script>setTimeout(() => location.reload(), 500);</script>' if state.phase != RacePhase.FINISHED else '<!-- Race finished, no auto-refresh -->'}
</body>
</html>"""

    return html
