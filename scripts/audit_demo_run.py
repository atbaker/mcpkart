"""Independently audit a completed demo before admitting another manual race."""

import base64
import json
import sqlite3
from pathlib import Path

from audit_demo_wire import audit as audit_wire

from mcpkart.demo_admission import release_digest
from mcpkart.demo_broker import DemoBroker
from mcpkart.duel_bench import audit_duel


def read(path):
    return json.loads(Path(path).read_text())


def acknowledgement_from_sample(sample, rid, record):
    # Native observations round world time to four decimals; the master frame
    # retains the accumulated floating-point time. Preserve that exact contract.
    return {"observation": {**sample["racers"][rid], "time": round(sample["time"], 4)},
            "applied": record["applied"], "reason": record.get("reason"),
            "applied_tick": record.get("applied_tick")}


def audit_run(directory, plan, ledger):
    directory = Path(directory)
    observed = read(directory / "observed-exit.json")
    if observed["status"] != "Success" or observed["response_code"] != 0:
        raise ValueError("The previous AWS process did not exit successfully; inspect its evidence")
    trial = directory / "trial"
    collection, start = read(trial / "collection.json"), read(trial / "collection-start.json")
    registration = read(trial / "demo-registration.json")
    if (not collection["collection_complete"] or not collection["source_unchanged"]
            or start["source_sha256"] != plan["source_sha256"]
            or registration["release_sha256"] != release_digest(plan)
            or registration["local_activities"] is not False
            or not registration["model_requests_enabled"]):
        raise ValueError("Previous race does not match its frozen regular-Activity release")
    if collection["budget_after"] != ledger or read(directory / "budget-after.json") != ledger or ledger["pending"]:
        raise ValueError("The complete previous cumulative ledger has not been reconciled")
    errors = collection["errors"]
    if any(error["type"] != "provider_error" for error in errors):
        raise ValueError("Previous race has an unreviewed execution failure")
    physics = audit_duel(trial, allow_failures=bool(errors))
    race = read(trial / "race.json")
    if not race["timing"]["infrastructure_valid"] or physics["max_sample_lateness_ms"] > 100:
        raise ValueError("Previous race failed its timing checks")
    wire = audit_wire(trial)
    if physics["exact_queries"] != wire["native_calls"]:
        raise ValueError("Native call count differs between independent audits")
    samples = {sample["tick"]: sample for sample in race["samples"]}
    decisions = read(trial / "decisions.json")
    broker = DemoBroker.__new__(DemoBroker)
    broker.config, broker.routes = race["config"], start["routes"]
    database = sqlite3.connect(f"file:{trial / 'receipts.sqlite3'}?mode=ro", uri=True)
    try:
        rows = database.execute("SELECT identity,state,receipt FROM operations").fetchall()
    finally:
        database.close()
    receipts = {}
    for identity, status, body in rows:
        if status != "done":
            raise ValueError("An earlier broker operation has an unknown outcome")
        receipts[identity] = json.loads(body)
    completed_steps = {}
    for rid in ("red", "blue", "green"):
        events = read(trial / f"temporal-history-{rid}.json")["events"]
        scheduled = {}
        if events[-1]["eventType"] != "EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED":
            raise ValueError("A driver workflow did not complete")
        for event in events:
            if event["eventType"].endswith(("FAILED", "TIMED_OUT")):
                raise ValueError("A Temporal event failed or timed out")
            if event["eventType"] == "EVENT_TYPE_ACTIVITY_TASK_SCHEDULED":
                scheduled[event["eventId"]] = event["activityTaskScheduledEventAttributes"]["activityId"]
            if event["eventType"] == "EVENT_TYPE_ACTIVITY_TASK_COMPLETED":
                attrs = event["activityTaskCompletedEventAttributes"]
                activity_id = scheduled[attrs["scheduledEventId"]]
                payload = attrs["result"]["payloads"][0]
                completed_steps[activity_id] = json.loads(base64.b64decode(payload["data"]))
        for seq, record in enumerate(decisions[rid]):
            query = read(trial / rid / f"query-{seq:05d}.json")
            identity = f"{registration['logical_id']}:{rid}:{seq}"
            receipt = receipts[identity]
            game = receipt["game_acknowledgement"]
            ack = None
            if "state_when_acknowledged" in game:
                tick = round(game["state_when_acknowledged"]["simulation_time_s"] * 60)
                sample = samples[tick]
                ack = acknowledgement_from_sample(sample, rid, record)
            expected = broker.describe_step(rid, seq, query["raw_observation"], record,
                                            ack=ack, reason=game.get("reason"))
            if any(receipt[key] != value for key, value in expected.items()):
                raise ValueError("Descriptive result differs from the actual model or physics evidence")
            if completed_steps[f"{rid}-decision-{seq + 1:04d}"] != receipt:
                raise ValueError("Temporal result differs from the durable broker receipt")
    parent = read(trial / "temporal-history.json")["events"]
    if parent[-1]["eventType"] != "EVENT_TYPE_WORKFLOW_EXECUTION_COMPLETED" or any(
        event["eventType"].endswith(("FAILED", "TIMED_OUT")) for event in parent
    ):
        raise ValueError("The parent workflow did not complete cleanly")
    return {"release_sha256": release_digest(plan), "observed_exit_and_audited": True,
            "budget_after": ledger, "only_provider_errors_or_none": True,
            "physics_audit": physics, "wire_audit": wire,
            "exact_descriptive_receipts": physics["exact_queries"],
            "audit_authority": "User-authorized automatic review between manual demo starts"}
