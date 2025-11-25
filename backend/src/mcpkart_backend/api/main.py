"""FastAPI application for MCP Kart backend."""

import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException

from mcpkart_backend.api.dependencies import get_temporal_client, lifespan_context
from mcpkart_backend.models import (
    CreateRaceRequest,
    GameState,
    PlayerInput,
    PlayerInputRequest,
    Steering,
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
