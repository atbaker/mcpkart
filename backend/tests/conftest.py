"""Pytest fixtures for MCP Kart tests."""

import pytest
from temporalio.testing import WorkflowEnvironment

from mcpkart_backend.temporal.search_attributes import IS_PUBLIC, PHASE, RACER_COUNT


@pytest.fixture
async def workflow_env():
    """Time-skipping test environment (fast, no search attributes).

    Use for testing game logic: movement, crashes, turns, items, etc.
    Search attribute upserts must be disabled via enable_search_attrs=False
    because the time-skipping server doesn't support them.
    """
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env


@pytest.fixture
async def workflow_env_integration():
    """Local Temporal server with full features (slower, has search attributes).

    Use for testing search attributes, visibility queries, matchmaking filters.
    Runs in real-time (no time-skipping).
    """
    async with await WorkflowEnvironment.start_local(
        search_attributes=[IS_PUBLIC, PHASE, RACER_COUNT],
        dev_server_extra_args=[
            "--dynamic-config-value",
            "system.forceSearchAttributesCacheRefreshOnRead=true",
        ],
    ) as env:
        yield env
