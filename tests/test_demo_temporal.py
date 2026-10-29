"""Real Temporal tests, opt-in because they launch a local development server."""

import asyncio
import os
import shutil
from datetime import timedelta

import pytest

pytest.importorskip("temporalio")

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import UnsandboxedWorkflowRunner, Worker

from mcpkart.demo_broker import DemoBroker
from mcpkart.demo_run import BrokerActivities
from mcpkart.demo_workflows import KartDriverWorkflow, KartRaceWorkflow
from mcpkart.duel_web import create_app

pytestmark = pytest.mark.skipif(
    os.getenv("MCPKART_TEMPORAL_TESTS") != "1" or not shutil.which("temporal"),
    reason="Set MCPKART_TEMPORAL_TESTS=1 to run the installed Temporal dev server",
)


@pytest.mark.parametrize("local", [False, True])
async def test_actual_temporal_concurrent_children_and_mcp_recording(tmp_path, local):
    app = create_app(trio=True, replay_root=tmp_path)
    try:
        async with await WorkflowEnvironment.start_local(
            dev_server_existing_path=shutil.which("temporal"),
        ) as env, DemoBroker(
            url=app.state.mcp_server, output=tmp_path / "trial", logical_id="mcpkart-temporal-test",
            deadline=1.5, mock_delay=.05,
        ) as broker:
            activities = BrokerActivities(broker)
            async with Worker(env.client, task_queue="mcpkart-test",
                              workflows=[KartRaceWorkflow, KartDriverWorkflow],
                              activities=[activities.start, activities.step, activities.finish]):
                result = await asyncio.wait_for(env.client.execute_workflow(
                    KartRaceWorkflow.run, {"local": local, "max_decisions": 1100},
                    id="mcpkart-test", task_queue="mcpkart-test",
                ), 45)
                assert result["audit"]["passed"]
                assert all(result["audit"]["summary"]["racers"][r] for r in ("red", "blue", "green"))
                assert result["audit"]["exact_queries"] >= 3
    finally:
        await app.state.race_runtime.close()


@workflow.defn(sandboxed=False)
class MarkerFailureWorkflow:
    # Fault injection only: fail once after the Local Activity returns and before
    # the task's marker can be persisted. Do not use shared state in real workflows.
    fail_once = True

    @workflow.run
    async def run(self):
        result = await workflow.execute_local_activity(
            "receipt_probe", schedule_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )
        if MarkerFailureWorkflow.fail_once:
            MarkerFailureWorkflow.fail_once = False
            raise RuntimeError("Injected workflow-task failure before marker persistence")
        return result


async def test_worker_task_replay_reexecutes_local_wrapper_without_second_model_request(tmp_path):
    app = create_app(trio=True, replay_root=tmp_path)
    attempts = []
    MarkerFailureWorkflow.fail_once = True
    try:
        async with await WorkflowEnvironment.start_local(
            dev_server_existing_path=shutil.which("temporal"),
        ) as env, DemoBroker(url=app.state.mcp_server, output=tmp_path / "trial",
                             logical_id="mcpkart-marker-test", deadline=30, mock_delay=.01) as broker:
            await broker.start()

            @activity.defn(name="receipt_probe")
            async def probe():
                attempts.append(1)
                return await broker.step("red", 0)

            async with Worker(env.client, task_queue="mcpkart-marker", workflows=[MarkerFailureWorkflow],
                              activities=[probe], workflow_runner=UnsandboxedWorkflowRunner()):
                result = await asyncio.wait_for(env.client.execute_workflow(
                    MarkerFailureWorkflow.run, id="mcpkart-marker", task_queue="mcpkart-marker",
                ), 45)
                assert result["applied"]
                assert len(attempts) >= 2
                assert broker.drivers["red"].count == 1
                assert len(broker.samples["red"]) == 1
    finally:
        await app.state.race_runtime.close()
