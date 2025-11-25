"""Pytest fixtures for MCP Kart tests."""

import pytest
from temporalio.testing import WorkflowEnvironment


@pytest.fixture
async def workflow_env():
    """Create a time-skipping test environment.

    This environment automatically fast-forwards through sleep() calls,
    allowing us to test 3-minute races in milliseconds.
    """
    async with await WorkflowEnvironment.start_time_skipping() as env:
        yield env
