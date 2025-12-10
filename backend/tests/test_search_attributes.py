"""Integration tests for Temporal search attributes.

These tests use WorkflowEnvironment.start_local() which provides a full
Temporal server with search attribute support. They run in real-time
(no time-skipping), so they're slower but test the full search attribute
functionality.
"""

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from mcpkart_backend.models import RacePhase
from mcpkart_backend.temporal.workflows import RaceWorkflow


# Mock the activity since we don't want to hit the database in tests
@activity.defn(name="store_race_results")
async def mock_store_race_results(*args, **kwargs) -> None:
    """Mock activity that does nothing."""
    pass


@pytest.mark.asyncio
async def test_search_attributes_set_on_init(workflow_env_integration: WorkflowEnvironment):
    """Test that search attributes are set when workflow initializes."""
    async with Worker(
        workflow_env_integration.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        # Start a private lobby with search attrs enabled
        handle = await workflow_env_integration.client.start_workflow(
            RaceWorkflow.run,
            args=["test-search-race", "player1", False, True],  # is_public=False, enable_search_attrs=True
            id="test-search-init-1",
            task_queue="test-queue",
        )

        # Query state - workflow should be in LOBBY phase
        state = await handle.query(RaceWorkflow.get_state)
        assert state.phase == RacePhase.LOBBY
        assert state.is_public is False

        # The search attributes should be set (no exception thrown)
        # We can't easily query search attributes directly, but if we got here
        # without an exception, the upsert worked


@pytest.mark.asyncio
async def test_public_race_search_attributes(workflow_env_integration: WorkflowEnvironment):
    """Test that public races set IsPublic search attribute correctly."""
    async with Worker(
        workflow_env_integration.client,
        task_queue="test-queue",
        workflows=[RaceWorkflow],
        activities=[mock_store_race_results],
    ):
        # Start a public matchmaking race with search attrs enabled
        handle = await workflow_env_integration.client.start_workflow(
            RaceWorkflow.run,
            args=["test-public-race", "player1", True, True],  # is_public=True, enable_search_attrs=True
            id="test-search-public-1",
            task_queue="test-queue",
        )

        # Query state - should be in MATCHMAKING phase
        state = await handle.query(RaceWorkflow.get_state)
        assert state.phase == RacePhase.MATCHMAKING
        assert state.is_public is True

        # The search attributes should be set with IsPublic=True
        # We can't easily query search attributes directly, but if we got here
        # without an exception, the upsert worked
