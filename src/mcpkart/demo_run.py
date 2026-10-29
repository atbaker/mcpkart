"""One finite three-kart race via conventional Temporal workers, AgentCore and MCP."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import timedelta
from pathlib import Path

from dotenv import dotenv_values
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from .demo_admission import Admission, release_digest
from .demo_broker import DemoBroker
from .demo_workflows import KartDriverWorkflow, KartRaceWorkflow
from .duel_clock import sha


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


def temporal_settings(env_path=None):
    path = env_path or Path(__file__).resolve().parents[2] / ".env"
    values = dotenv_values(path)
    namespace = os.environ.get("TEMPORAL_NAMESPACE", values.get("TEMPORAL_NAMESPACE")) or "default"
    address = os.environ.get("TEMPORAL_ADDRESS", values.get("TEMPORAL_ADDRESS"))
    # Local development overrides must never inherit a Cloud key from .env.
    file_key = values.get("TEMPORAL_API_KEY") if namespace == values.get("TEMPORAL_NAMESPACE") else None
    key = os.environ.get("TEMPORAL_API_KEY", file_key if namespace != "default" else None)
    if namespace != "default" and not key:
        raise ValueError("Configure TEMPORAL_API_KEY in the repo-root .env or environment")
    if namespace != "default" and not address:
        raise ValueError("Copy TEMPORAL_ADDRESS from the namespace connection settings into .env")
    return {"target_host": address or "localhost:7233", "namespace": namespace,
            "api_key": key or None, "tls": bool(key)}


async def connect():
    return await Client.connect(**temporal_settings())


async def run(args):
    client = await connect()
    admission = Admission(args.release, args.ledger, args.race_id) if args.paid else None
    plan = json.loads(Path(args.release).read_text()) if args.release else None
    digest = release_digest(plan) if plan else None
    if plan and (client.namespace != plan["namespace"] or args.agentcore_arn != plan["agentcore_arn"]):
        if admission:
            admission.close()
        raise ValueError("Temporal namespace or Runtime differs from the frozen demo release")
    factory = None
    if args.agentcore_arn:
        from .demo_transport import AgentCoreTransport
        factory = lambda rid: AgentCoreTransport(
            args.agentcore_arn, args.region, rid, args.race_id,
            evidence_path=Path(args.output) / rid / "agentcore-wire", paid=args.paid, release_sha256=digest,
        )
    try:
        async with DemoBroker(
            url=args.url, output=args.output, logical_id=args.race_id, deadline=args.deadline,
            max_decisions=args.max_decisions, transport_factory=factory,
            live_status_path=args.live_status, paid=args.paid, admission=admission,
            retire_provider_errors=args.retire_provider_errors,
            clock_path=args.clock_qualification, interface_path=args.interface, deployment_path=args.deployment,
        ) as broker:
            (Path(args.output) / "demo-registration.json").write_text(json.dumps({
                "free": not args.paid, "logical_id": args.race_id, "temporal_namespace": client.namespace,
                "task_queue": args.race_id, "local_activities": args.local,
                "agentcore_runtime_arn": args.agentcore_arn, "region": args.region,
                "max_decisions_per_racer": args.max_decisions, "deadline_s": args.deadline,
                "models": broker.routes, "model_requests_enabled": args.paid,
                "retire_provider_errors": args.retire_provider_errors, "release_sha256": digest,
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
                if not args.paid and plan and receipt.get("audit"):
                    output = Path(args.output)
                    evidence = {str(p.relative_to(output)): sha(p) for p in output.rglob("*")
                                if p.is_file() and p.suffix != ".sqlite3" and "sqlite3-" not in p.name}
                    (output / "interface-proof.json").write_text(json.dumps({
                        "passed": True, "free": True, "runtime": broker.runtime,
                        "source_sha256": broker.frozen, "release_sha256": digest,
                        "namespace": client.namespace, "runtime_arn": args.agentcore_arn,
                        "evidence_sha256": evidence, "model_requests": 0,
                    }, indent=2))
                print(json.dumps(receipt), flush=True)
                return 0 if receipt.get("audit") else 1
    finally:
        if admission:
            admission.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--free", action="store_true", help="Scripted mocks; no model calls")
    mode.add_argument("--paid", action="store_true", help="One registered live race; never retries")
    parser.add_argument("--retire-provider-errors", action="store_true",
                        help="Mark provider failure DNF and let other karts finish; never retries")
    parser.add_argument("--release", help="Prospective finite demo release JSON")
    parser.add_argument("--ledger", default="artifacts/budget.json")
    parser.add_argument("--clock-qualification")
    parser.add_argument("--interface", help="Audited exact cloud mock interface proof")
    parser.add_argument("--deployment", help="Dedicated live-capable AgentCore deployment receipt")
    parser.add_argument("--url", default="http://127.0.0.1:8771/mcp")
    parser.add_argument("--output", required=True)
    parser.add_argument("--race-id", required=True, help="Unique mcpkart- ID; also isolates the task queue")
    parser.add_argument("--deadline", type=float, default=180)
    parser.add_argument("--max-decisions", type=int, default=1100)
    parser.add_argument("--local", action="store_true", help="Local Activities with durable broker receipts")
    parser.add_argument("--agentcore-arn", help="Optional deployed AgentCore mock adapter")
    parser.add_argument("--live-status", help="Spectator replay-root/live-status.json if output has another parent")
    parser.add_argument("--region", default="us-west-2")
    args = parser.parse_args()
    if args.paid and not all((args.release, args.clock_qualification, args.interface, args.deployment, args.agentcore_arn)):
        parser.error("Live mode requires release, clock qualification, interface, deployment and AgentCore ARN")
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
