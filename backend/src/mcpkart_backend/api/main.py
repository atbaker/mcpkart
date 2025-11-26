"""FastAPI application for MCP Kart backend."""

import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from mcpkart_backend.api.dependencies import get_temporal_client, lifespan_context
from mcpkart_backend.models import (
    CreateRaceRequest,
    GameState,
    PlayerInput,
    PlayerInputRequest,
    Steering,
    TileType,
)
from mcpkart_backend.temporal import RaceWorkflow

TASK_QUEUE = "mcpkart-task-queue"


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


@app.post("/races")
async def create_race(request: CreateRaceRequest) -> dict[str, Any]:
    """Create a new race with the specified players.

    Args:
        request: Race creation request with player IDs

    Returns:
        Race ID, workflow ID, and initial game state
    """
    client = await get_temporal_client()

    race_id = str(uuid.uuid4())[:8]
    workflow_id = f"race-{race_id}"

    # Start the workflow
    handle = await client.start_workflow(
        RaceWorkflow.run,
        args=[race_id, request.player_ids],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    # Query initial state (may need a small delay for workflow to initialize)
    import asyncio

    await asyncio.sleep(0.1)  # Small delay to ensure workflow starts

    try:
        state = await handle.query(RaceWorkflow.get_state)
    except Exception:
        # If query fails, return minimal info
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


@app.post("/races/{race_id}/input")
async def send_input(race_id: str, request: PlayerInputRequest) -> dict[str, Any]:
    """Send player input and get updated state.

    Args:
        race_id: The race identifier
        request: Player input request

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
            accelerating=request.accelerating,
            braking=request.braking,
            steering=Steering(request.steering) if request.steering else None,
            use_item=request.use_item,
        )

        # Execute update (synchronous, returns state)
        state: GameState = await handle.execute_update(
            RaceWorkflow.apply_input,
            player_input,
        )

        return {"state": state.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to send input: {str(e)}"
        ) from e


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
        boost = f" BOOSTING({racer.boost_ticks_remaining})" if racer.boost_ticks_remaining > 0 else ""
        lines.append(
            f"- {player_id}: tile {racer.tile_index}.{racer.tile_subunit}, "
            f"speed {racer.speed}, lap {racer.current_lap}/{state.laps_required}, "
            f"status: {racer.status.value}{boost}, "
            f"steering: {racer.controls.steering.value}, "
            f"item: {power_up}, crashes: {racer.total_crashes}"
        )
    return "\n".join(lines)


@app.get("/debug/{race_id}", response_class=HTMLResponse)
async def debug_race(race_id: str) -> str:
    """Debug visualization page for a race.

    Shows ASCII track, racer status, and event log with auto-refresh.
    """
    client = await get_temporal_client()
    workflow_id = f"race-{race_id}"

    try:
        handle = client.get_workflow_handle(workflow_id)
        state: GameState = await handle.query(RaceWorkflow.get_state)
    except Exception as e:
        return f"<html><body><h1>Race not found: {race_id}</h1><p>{e}</p></body></html>"

    ascii_track = _render_ascii_track(state)
    racer_status = _render_racer_status(state)
    events_log = "\n".join(state.events[-50:])  # Last 50 events

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>MCP Kart Debug - Race {race_id}</title>
    <style>
        body {{ font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px; }}
        pre {{ margin: 0; }}
        h2 {{ color: #ffff00; margin-top: 20px; }}
        .track {{ font-size: 14px; overflow-x: auto; }}
        .finished {{ color: #ff00ff; }}
    </style>
</head>
<body>
    <h1>MCP Kart Debug - Race {race_id}</h1>
    <p>Tick: {state.current_tick}/{state.max_ticks} | Status: {"FINISHED" if state.is_finished else "RACING"}</p>

    <h2>Track (I=item box, T=turn)</h2>
    <pre class="track">{ascii_track}</pre>

    <h2>Racers</h2>
    <pre>{racer_status}</pre>

    <h2>Event Log (last 50)</h2>
    <pre>{events_log if events_log else "(no events yet)"}</pre>

    <script>
        // Auto-refresh every 500ms
        setTimeout(() => location.reload(), 500);
    </script>
</body>
</html>"""

    return html
