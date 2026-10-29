"""One finite free three-kart race via conventional Temporal workers and MCP."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import timedelta
from pathlib import Path

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from .demo_broker import DemoBroker
from .demo_workflows import KartDriverWorkflow, KartRaceWorkflow


class BrokerActivities:
    def __init__(self, broker):
        self.broker = broker

    @activity.defn(name="kart_start")
    async def start(self) -> dict:
        return await self.broker.start()

    @activity.defn(name="kart_step")
    async def step(self, request: dict) -> dict:
        return await self.broker.step(request["racer_id"], request["seq"])

    @activity.defn(name="kart_finish")
    async def finish(self) -> dict:
        return await self.broker.finish()


async def connect():
    key = os.environ.get("TEMPORAL_API_KEY")
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    if namespace != "default" and not key:
        raise ValueError("Configure the namespace's Temporal API key in the environment")
    return await Client.connect(address, namespace=namespace, api_key=key, tls=bool(key))


async def run(args):
    client = await connect()
    factory = None
    if args.agentcore_arn:
        from .demo_transport import AgentCoreTransport
        factory = lambda rid: AgentCoreTransport(
            args.agentcore_arn, args.region, rid, args.race_id,
            evidence_path=Path(args.output) / rid / "agentcore-wire",
        )
    async with DemoBroker(
        url=args.url, output=args.output, logical_id=args.race_id, deadline=args.deadline,
        max_decisions=args.max_decisions, transport_factory=factory,
        live_status_path=args.live_status,
    ) as broker:
        (Path(args.output) / "demo-registration.json").write_text(json.dumps({
            "free": True, "logical_id": args.race_id, "temporal_namespace": client.namespace,
            "task_queue": args.race_id, "local_activities": args.local,
            "agentcore_runtime_arn": args.agentcore_arn, "region": args.region,
            "max_decisions_per_racer": args.max_decisions, "deadline_s": args.deadline,
            "models": broker.routes, "model_requests_enabled": False,
        }, indent=2))
        activities = BrokerActivities(broker)
        async with Worker(
            client, task_queue=args.race_id, workflows=[KartRaceWorkflow, KartDriverWorkflow],
            activities=[activities.start, activities.step, activities.finish],
            max_concurrent_activities=8, max_concurrent_local_activities=8,
            graceful_shutdown_timeout=timedelta(seconds=30),
        ):
            receipt = await client.execute_workflow(
                KartRaceWorkflow.run, {"max_decisions": args.max_decisions, "local": args.local},
                id=args.race_id, task_queue=args.race_id,
                execution_timeout=timedelta(seconds=args.deadline + 180),
            )
            handle = client.get_workflow_handle(args.race_id)
            history = await handle.fetch_history()
            Path(args.output, "temporal-history.json").write_text(history.to_json())
            for rid in ("red", "blue", "green"):
                child = client.get_workflow_handle(args.race_id + "-" + rid)
                child_history = await child.fetch_history()
                Path(args.output, f"temporal-history-{rid}.json").write_text(child_history.to_json())
            print(json.dumps(receipt), flush=True)
            return 0 if receipt.get("audit") else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--free", action="store_true", required=True, help="Scripted mocks; no model calls")
    parser.add_argument("--url", default="http://127.0.0.1:8771/mcp")
    parser.add_argument("--output", required=True)
    parser.add_argument("--race-id", required=True, help="Unique mcpkart- ID; also isolates the task queue")
    parser.add_argument("--deadline", type=float, default=180)
    parser.add_argument("--max-decisions", type=int, default=1100)
    parser.add_argument("--local", action="store_true", help="Local Activities with durable broker receipts")
    parser.add_argument("--agentcore-arn", help="Optional deployed AgentCore mock adapter")
    parser.add_argument("--live-status", help="Spectator replay-root/live-status.json if output has another parent")
    parser.add_argument("--region", default="us-west-2")
    raise SystemExit(asyncio.run(run(parser.parse_args())))


if __name__ == "__main__":
    main()
