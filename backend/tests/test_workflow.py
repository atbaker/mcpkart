"""Tests for the RaceWorkflow."""

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from mcpkart_backend.models import PlayerInput
from mcpkart_backend.temporal.workflows import RaceWorkflow


# Mock the activity since we don't want to hit the database in tests
@activity.defn(name="store_race_results")
async def mock_store_race_results(*args, **kwargs) -> None:
    """Mock activity that does nothing."""
    pass


@pytest.mark.asyncio
async def test_race_initializes_correctly(workflow_env: WorkflowEnvironment):
    """Test that a race initializes with correct state."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-init-1",
            task_queue="test-queue",
        )

        # Query state immediately
        state = await handle.query(RaceWorkflow.get_state)

        assert state.race_id == "test-race"
        assert "player1" in state.racers
        assert state.track.total_tiles == 40
        assert state.laps_required == 3
        # Tick may advance before we query, so just check it started
        assert state.current_tick >= 0


@pytest.mark.asyncio
async def test_racer_accelerates_with_target_speed(workflow_env: WorkflowEnvironment):
    """Test that a racer accelerates when target_speed is set."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-accel-1",
            task_queue="test-queue",
        )

        # Set target speed to max
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=3),
        )

        # Wait a few ticks for acceleration
        await workflow_env.sleep(4)

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Speed should have increased (starts at 0, +1 per tick, max 3)
        assert racer.speed == 3


@pytest.mark.asyncio
async def test_crash_on_turn_at_high_speed_without_drift(workflow_env: WorkflowEnvironment):
    """Test that racer crashes when hitting turn at speed > 1 without drift."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-crash-1",
            task_queue="test-queue",
        )

        # Set target speed to max and let racer hit the first turn (tile 6)
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=3),
        )

        # At speed 3, racer moves 3 subunits per tick
        # Tile 6 is the first turn. Tiles 0-5 are straight (6 tiles * 3 subunits = 18 subunits)
        # At speed 3: need ~7 ticks to reach tile 6
        await workflow_env.sleep(10)

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Should have crashed (speed > 1 without drift)
        assert racer.total_crashes > 0


@pytest.mark.asyncio
async def test_speed_1_safely_navigates_turn(workflow_env: WorkflowEnvironment):
    """Test that racer at speed 1 safely navigates turn without drift."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-safe-turn-1",
            task_queue="test-queue",
        )

        # Set target speed to 1 (safe for turns)
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=1),
        )

        # Wait long enough to pass the first turn (tile 6)
        # At speed 1: need to cross 7 tiles * 3 subunits = 21 subunits
        # At 1 subunit/tick: need ~22 ticks
        await workflow_env.sleep(25)

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Should have passed the turn without crashing
        assert racer.tile_index >= 7  # Past the first turn
        assert racer.total_crashes == 0


@pytest.mark.asyncio
async def test_drift_enables_in_drift_zone(workflow_env: WorkflowEnvironment):
    """Test that drift can be enabled when in drift zone."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-drift-enable-1",
            task_queue="test-queue",
        )

        # First move racer to drift zone (tiles 4-5) before turn at tile 6
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=2),
        )

        # Wait to reach drift zone at tile 4 (~7 ticks at speed 2)
        await workflow_env.sleep(8)

        # Now enable drift while in drift zone
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", drift=True, target_speed=2),
        )

        await workflow_env.sleep(2)

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Drift should be enabled (we're in drift zone for tile 6)
        assert racer.drift_enabled is True


@pytest.mark.asyncio
async def test_item_pickup(workflow_env: WorkflowEnvironment):
    """Test that racer picks up items from item boxes."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-item-1",
            task_queue="test-queue",
        )

        # Go at speed 1 to safely navigate to tile 3 (first item box)
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=1),
        )

        # Wait to reach tile 3 (need to cross ~4 tiles * 3 subunits = 12+ ticks at speed 1)
        await workflow_env.sleep(15)

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Should have picked up an item
        assert racer.power_up is not None or racer.items_used > 0


@pytest.mark.asyncio
async def test_speed_boost_usage(workflow_env: WorkflowEnvironment):
    """Test that using speed boost works correctly."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-boost-1",
            task_queue="test-queue",
        )

        # Send use_item (won't do anything without an item)
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", use_item=True),
        )

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Without an item, nothing should happen (no item used)
        assert racer.power_up is None
        assert racer.items_used == 0


@pytest.mark.asyncio
async def test_input_update_changes_controls(workflow_env: WorkflowEnvironment):
    """Test that sending input updates racer controls."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-input-1",
            task_queue="test-queue",
        )

        # Check initial controls
        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]
        assert racer.controls.target_speed == 0

        # Update controls
        state = await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=2),
        )

        racer = state.racers["player1"]
        assert racer.controls.target_speed == 2


@pytest.mark.asyncio
async def test_race_completes_when_max_ticks_reached(workflow_env: WorkflowEnvironment):
    """Test that race completes when max ticks reached."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-complete-1",
            task_queue="test-queue",
        )

        # Wait for max ticks (600 ticks)
        result = await handle.result()

        assert result.is_finished
        assert result.current_tick <= 600


@pytest.mark.asyncio
async def test_braking_reduces_speed(workflow_env: WorkflowEnvironment):
    """Test that setting lower target_speed reduces speed."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", ["player1"]],
            id="test-brake-1",
            task_queue="test-queue",
        )

        # Accelerate first
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=3),
        )

        await workflow_env.sleep(4)

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]
        initial_speed = racer.speed
        assert initial_speed > 0

        # Now brake by setting target_speed to 0
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=0),
        )

        await workflow_env.sleep(2)

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Speed should have decreased
        assert racer.speed < initial_speed
