"""Tests for the RaceWorkflow."""

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from mcpkart_backend.models import PlayerInput, RacePhase
from mcpkart_backend.temporal.workflows import RaceWorkflow


# Mock the activity since we don't want to hit the database in tests
@activity.defn(name="store_race_results")
async def mock_store_race_results(*args, **kwargs) -> None:
    """Mock activity that does nothing."""
    pass


async def start_race_for_testing(handle, workflow_env, creator_id: str = "player1"):
    """Helper to transition from LOBBY -> PLANNING -> RACING for tests."""
    # Start the race (transitions to PLANNING)
    await handle.execute_update(RaceWorkflow.start_race, creator_id)
    # Wait for planning phase to complete (60 seconds)
    await workflow_env.sleep(61)


@pytest.mark.asyncio
async def test_race_initializes_correctly(workflow_env: WorkflowEnvironment):
    """Test that a race initializes with correct state in LOBBY phase."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", "player1", False, "test-client", 8, False],  # race_id, creator_id, is_public, enable_search_attrs
            id="test-init-1",
            task_queue="test-queue",
        )

        # Query state immediately - should be in LOBBY phase
        state = await handle.query(RaceWorkflow.get_state)

        assert state.race_id == "test-race"
        assert state.phase == RacePhase.LOBBY
        assert state.creator_id == "player1"
        assert "player1" in state.racers
        assert state.track.total_tiles == 44
        assert state.laps_required == 3


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
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-accel-1",
            task_queue="test-queue",
        )

        # Start the race first
        await start_race_for_testing(handle, workflow_env)

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
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-crash-1",
            task_queue="test-queue",
        )

        # Start the race first
        await start_race_for_testing(handle, workflow_env)

        # Set target speed to max and let racer hit the first turn (tile 7)
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=3),
        )

        # At speed 3, racer moves 3 subunits per tick
        # Tile 7 is the first turn. Tiles 0-6 are straight (7 tiles * 3 subunits = 21 subunits)
        # At speed 3: need ~8 ticks to reach tile 7
        await workflow_env.sleep(11)

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
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-safe-turn-1",
            task_queue="test-queue",
        )

        # Start the race first
        await start_race_for_testing(handle, workflow_env)

        # Set target speed to 1 (safe for turns)
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=1),
        )

        # Wait long enough to pass the first turn (tile 7)
        # At speed 1: need to cross 8 tiles * 3 subunits = 24 subunits
        # At 1 subunit/tick: need ~25 ticks
        await workflow_env.sleep(28)

        state = await handle.query(RaceWorkflow.get_state)
        racer = state.racers["player1"]

        # Should have passed the turn without crashing
        assert racer.tile_index >= 8  # Past the first turn
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
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-drift-enable-1",
            task_queue="test-queue",
        )

        # Start the race first
        await start_race_for_testing(handle, workflow_env)

        # First move racer to drift zone (tiles 4-6) before turn at tile 7
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

        # Drift should be enabled (we're in drift zone for tile 7)
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
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-item-1",
            task_queue="test-queue",
        )

        # Start the race first
        await start_race_for_testing(handle, workflow_env)

        # Go at speed 1 to safely navigate to tile 11 (first item box)
        await handle.execute_update(
            RaceWorkflow.apply_input,
            PlayerInput(player_id="player1", target_speed=1),
        )

        # Wait to reach tile 11 (need to cross ~12 tiles * 3 subunits = 36+ ticks at speed 1)
        await workflow_env.sleep(38)

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
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-boost-1",
            task_queue="test-queue",
        )

        # Start the race first
        await start_race_for_testing(handle, workflow_env)

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
async def test_input_update_changes_controls_during_planning(workflow_env: WorkflowEnvironment):
    """Test that sending input updates racer controls during PLANNING phase."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-input-1",
            task_queue="test-queue",
        )

        # Ensure workflow is running before calling update
        await handle.query(RaceWorkflow.get_state)

        # Start the race (puts us in PLANNING phase)
        await handle.execute_update(RaceWorkflow.start_race, "player1")

        # Check initial controls
        state = await handle.query(RaceWorkflow.get_state)
        assert state.phase == RacePhase.PLANNING
        racer = state.racers["player1"]
        assert racer.controls.target_speed == 0

        # Update controls during planning
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
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-complete-1",
            task_queue="test-queue",
        )

        # Ensure workflow is running before calling update
        await handle.query(RaceWorkflow.get_state)

        # Start the race
        await handle.execute_update(RaceWorkflow.start_race, "player1")

        # Wait for planning (30s) + max ticks (600 ticks)
        result = await handle.result()

        assert result.is_finished
        assert result.phase == RacePhase.FINISHED
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
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-brake-1",
            task_queue="test-queue",
        )

        # Start the race first
        await start_race_for_testing(handle, workflow_env)

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


@pytest.mark.asyncio
async def test_join_lobby(workflow_env: WorkflowEnvironment):
    """Test that players can join a lobby."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", "host", False, "test-client", 8, False],
            id="test-join-lobby-1",
            task_queue="test-queue",
        )

        # Initial state should have host
        state = await handle.query(RaceWorkflow.get_state)
        assert state.phase == RacePhase.LOBBY
        assert len(state.racers) == 1
        assert "host" in state.racers

        # Join as player2
        state = await handle.execute_update(RaceWorkflow.join_lobby, "player2")
        assert len(state.racers) == 2
        assert "player2" in state.racers

        # Join as player3
        state = await handle.execute_update(RaceWorkflow.join_lobby, "player3")
        assert len(state.racers) == 3
        assert "player3" in state.racers


@pytest.mark.asyncio
async def test_only_creator_can_start_race(workflow_env: WorkflowEnvironment):
    """Test that only the lobby creator can start the race."""
    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", "host", False, "test-client", 8, False],
            id="test-start-auth-1",
            task_queue="test-queue",
        )

        # Join as player2
        await handle.execute_update(RaceWorkflow.join_lobby, "player2")

        # player2 should not be able to start - test the error
        try:
            await handle.execute_update(RaceWorkflow.start_race, "player2")
            pytest.fail("Expected exception when non-creator tries to start")
        except Exception as e:
            # The error message is in the cause chain
            assert "Only the lobby creator" in str(e.__cause__)

        # host should be able to start
        state = await handle.execute_update(RaceWorkflow.start_race, "host")
        assert state.phase == RacePhase.PLANNING


# Storage for captured activity data in replay tests
_captured_data: dict = {}


def make_capturing_activity():
    """Create a fresh capturing activity for each test."""
    @activity.defn(name="store_race_results")
    async def mock_store_race_results_capturing(*args, **kwargs) -> None:
        """Mock activity that captures racer_history for testing.

        Activity args: race_id, started_at, finished_at, current_tick, max_ticks,
        laps_required, is_public, standings, racer_states, events, racer_history
        """
        # racer_history is the 11th positional argument (index 10)
        if len(args) >= 11:
            _captured_data["racer_history"] = args[10]
    return mock_store_race_results_capturing


@pytest.mark.asyncio
async def test_racer_history_captured_during_race(workflow_env: WorkflowEnvironment):
    """Test that racer_history is populated with tick snapshots after race completes."""
    _captured_data.clear()

    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[make_capturing_activity()],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-replay-history-1",
            task_queue="test-queue",
        )

        # Start the race (transitions to PLANNING, then RACING)
        await handle.execute_update(RaceWorkflow.start_race, "player1")

        # Wait for race to complete (time-skipping handles the 600+ seconds)
        result = await handle.result()

        # Verify race completed
        assert result.phase == RacePhase.FINISHED

        # Verify racer_history was captured
        racer_history = _captured_data.get("racer_history")
        assert racer_history is not None
        assert "tick_count" in racer_history
        assert "ticks" in racer_history
        assert racer_history["tick_count"] > 0
        assert len(racer_history["ticks"]) == racer_history["tick_count"]


@pytest.mark.asyncio
async def test_racer_history_contains_all_racers(workflow_env: WorkflowEnvironment):
    """Test that each tick snapshot contains entries for all racers."""
    _captured_data.clear()

    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[make_capturing_activity()],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-replay-racers-1",
            task_queue="test-queue",
        )

        # Add a second player
        await handle.execute_update(RaceWorkflow.join_lobby, "player2")

        # Start the race and wait for completion
        await handle.execute_update(RaceWorkflow.start_race, "player1")
        result = await handle.result()

        assert result.phase == RacePhase.FINISHED

        # Verify each tick snapshot has both racers
        racer_history = _captured_data.get("racer_history")
        assert racer_history is not None
        for tick_snapshot in racer_history["ticks"]:
            assert "tick" in tick_snapshot
            assert "racers" in tick_snapshot
            assert "player1" in tick_snapshot["racers"]
            assert "player2" in tick_snapshot["racers"]

            # Verify racer snapshot structure
            for player_id, racer_data in tick_snapshot["racers"].items():
                assert "tile" in racer_data
                assert "subunit" in racer_data
                assert "speed" in racer_data
                assert "lap" in racer_data
                assert "status" in racer_data


@pytest.mark.asyncio
async def test_racer_history_tick_order(workflow_env: WorkflowEnvironment):
    """Test that ticks are sequential starting from 0."""
    _captured_data.clear()

    async with Worker(
        workflow_env.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[make_capturing_activity()],
    ):
        handle = await workflow_env.client.start_workflow(
            RaceWorkflow.run,
            args=["test-race", "player1", False, "test-client", 8, False],
            id="test-replay-order-1",
            task_queue="test-queue",
        )

        # Start the race and wait for completion
        await handle.execute_update(RaceWorkflow.start_race, "player1")
        result = await handle.result()

        assert result.phase == RacePhase.FINISHED

        # Verify ticks are sequential starting from 0
        racer_history = _captured_data.get("racer_history")
        assert racer_history is not None
        ticks = racer_history["ticks"]
        assert ticks[0]["tick"] == 0  # First snapshot is tick 0 (initial state)

        # Verify sequential ordering
        for i, tick_snapshot in enumerate(ticks):
            assert tick_snapshot["tick"] == i
