"""Recorded two-driver collection and deterministic offline audit.

Free controls use an explicitly labeled scripted mock. Actual model runs use
unchanged native Decisions replies, without a host driving policy or retries.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import signal
import time
from contextlib import AsyncExitStack
from pathlib import Path

import httpx
from fastmcp import Client

from .bench import percentiles, tool
from .demo_mock import free_choices
from .duel import DuelSimulation
from .duel_decisions import BudgetJournal, DuelDecisionClient, DuelDriver, duel_facts
from .question_context_driver import WireCapture, _read, _write_new, encoded


def sources():
    root = Path(__file__).parent
    paths = sorted(root.glob("*.py")) + [root / "static" / "duel.html"]
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


async def collect_duel(
    *,
    url,
    routes,
    setup,
    seed,
    output,
    budget,
    free=False,
    deadline=240.0,
    label="",
    admission=None,
    pause_parent=False,
    max_decisions=1100,
    live_status_path=None,
    include_gate_geometry=False,
    added_delay_s=0.0,
    include_wheel_motion=False,
    include_control_timing=False,
    include_pedal_timing=False,
):
    if not isinstance(include_gate_geometry, bool):
        raise TypeError("Gate geometry requires an explicit boolean profile")
    if not isinstance(include_wheel_motion, bool) or not isinstance(include_control_timing, bool):
        raise TypeError("Wheel observability requires explicit boolean profiles")
    if not isinstance(include_pedal_timing, bool):
        raise TypeError("Pedal timing requires an explicit boolean profile")
    if include_pedal_timing and not include_control_timing:
        raise ValueError("Pedal timing requires declared control timing")
    if (
        isinstance(added_delay_s, bool) or not isinstance(added_delay_s, (int, float))
        or not math.isfinite(added_delay_s) or not 0 <= added_delay_s <= 2
    ):
        raise ValueError("Added response delay must be between zero and two seconds")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    config = DuelSimulation(seed=seed, **setup).config()
    racers = tuple(config["racer_ids"])
    if set(routes) != set(racers):
        raise ValueError("Routes must match every racer")
    frozen = sources()
    ledger_before = _read(budget.path)
    journal = BudgetJournal(budget, output / "budget-events.jsonl")
    seen_ids, stop, samples = set(), asyncio.Event(), {r: [] for r in racers}
    errors, pause, in_flight, max_in_flight = [], {}, set(), 0
    spectator_warnings = []
    _write_new(
        output / "collection-start.json",
        {
            "source_sha256": frozen,
            "routes": routes,
            "setup": setup,
            "seed": seed,
            "free": free,
            "budget_before": ledger_before,
            "writer_pid": os.getpid(),
            "max_decisions_per_racer": max_decisions,
            "include_gate_geometry": include_gate_geometry,
            "added_delay_s": added_delay_s,
            "include_wheel_motion": include_wheel_motion,
            "include_control_timing": include_control_timing,
            "include_pedal_timing": include_pedal_timing,
        },
    )
    async with AsyncExitStack() as stack:
        try:
            mcp = await stack.enter_async_context(Client(url, timeout=45))
            runtime = await tool(mcp, "runtime_info")
            if runtime.get("mode") != ("trio" if len(racers) == 3 else "duel") or runtime.get("backend") != "process":
                raise ValueError("A process-isolated duel runtime is required")
            captures, drivers = {}, {}
            for rid in racers:
                capture = captures[rid] = WireCapture()

                async def mock(request, rid=rid):
                    nonlocal max_in_flight
                    if rid in in_flight:
                        raise RuntimeError("Duplicate in-flight racer")
                    in_flight.add(rid)
                    max_in_flight = max(max_in_flight, len(in_flight))
                    try:
                        body = json.loads(request.content)
                        facts = {
                            h + "_facts": body["questions"][h]["instructions"]["current_facts"][h + "_facts"]
                            for h in ("wheel", "pedal")
                        }
                        wheel, pedal = free_choices(facts)
                        await asyncio.sleep(0.2)
                        return httpx.Response(
                            200,
                            json={
                                "id": f"free-{seed}-{rid}-{len(samples[rid])}",
                                "model": routes[rid]["resolved_model"],
                                "provider": routes[rid]["provider_name"],
                                "answers": {
                                    "wheel": {"type": "choice", "choice": wheel},
                                    "pedal": {"type": "choice", "choice": pedal},
                                },
                                "usage": {"input_tokens": 0, "output_tokens": 0, "cost": 0},
                            },
                        )
                    finally:
                        in_flight.remove(rid)

                http = await stack.enter_async_context(
                    httpx.AsyncClient(
                        timeout=5,
                        follow_redirects=False,
                        event_hooks=capture.hooks,
                        **({"transport": httpx.MockTransport(mock)} if free else {}),
                    )
                )
                drivers[rid] = DuelDriver(
                    racer_id=rid,
                    config=config,
                    route=routes[rid],
                    budget=journal.view(rid),
                    http=http,
                    capture=capture,
                    output=output / rid,
                    api_key="mock-duel-free-secret" if free else None,
                    admission=admission,
                    seen_ids=seen_ids,
                    include_gate_geometry=include_gate_geometry,
                    include_wheel_motion=include_wheel_motion,
                    control_timing_s=added_delay_s if include_control_timing else None,
                    include_pedal_timing=include_pedal_timing,
                )
            if sources() != frozen:
                raise RuntimeError("Source changed during preparation")
            _write_new(output / "runtime.json", runtime)
            initial = await tool(
                mcp, "start_duel", {"seed": seed, "deadline": deadline, "label": label, "race_setup": setup}
            )
            race_id = initial["race_id"]
            live_metrics = {r: {"requests": 0, "thinking": False, "last_latency_ms": None} for r in racers}
            driver_labels = {
                r: (
                    "Scripted control" if free else {"typesafe": "Jev", "openai": "OpenAI", "primeintellect": "Clef"}[routes[r]["provider"]]
                )
                + " · "
                + r
                for r in racers
            }

            def publish_live():
                if live_status_path is None:
                    return
                destination = Path(live_status_path)
                temporary = destination.with_suffix(".tmp")
                try:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    temporary.write_text(
                        json.dumps(
                            {
                                "race_id": race_id,
                                "driver_labels": driver_labels,
                                "driver_metrics": live_metrics,
                            }
                        )
                    )
                    os.replace(temporary, destination)
                except OSError as error:
                    warning = "Spectator status unavailable: " + type(error).__name__
                    if warning not in spectator_warnings:
                        spectator_warnings.append(warning)

            publish_live()

            async def spectator():
                async with httpx.AsyncClient(timeout=2) as http:
                    while not stop.is_set():
                        try:
                            await http.get(url.removesuffix("/mcp") + "/api/state")
                        except httpx.HTTPError:
                            pass
                        await asyncio.sleep(0.1)

            async def pause_once():
                if not pause_parent:
                    return
                await asyncio.sleep(5)
                pid = runtime["process_pid"]
                pause.update(parent_pid=pid, started_ns=time.monotonic_ns())
                os.kill(pid, signal.SIGSTOP)
                try:
                    await asyncio.sleep(0.35)
                finally:
                    os.kill(pid, signal.SIGCONT)
                    pause["ended_ns"] = time.monotonic_ns()

            async def drive(rid):
                observation = initial["drivers"][rid]["observation"]
                seq = 0
                try:
                    while (
                        not stop.is_set()
                        and observation["status"] == "running"
                        and not observation["finished"]
                    ):
                        if len(samples[rid]) >= max_decisions:
                            raise RuntimeError("Per-racer finite decision ceiling reached")
                        live_metrics[rid]["thinking"] = True
                        publish_live()
                        record = await drivers[rid].decide(observation)
                        live_metrics[rid].update(
                            thinking=False, requests=drivers[rid].count, last_latency_ms=record["latency_ms"]
                        )
                        publish_live()
                        if not record["ok"]:
                            raise RuntimeError("Invalid model reply: " + str(record.get("error")))
                        if added_delay_s:
                            record["delay_started_ns"] = time.monotonic_ns()
                            await asyncio.sleep(added_delay_s)
                            record["delay_ended_ns"] = time.monotonic_ns()
                            record["added_delay_s"] = added_delay_s
                        if stop.is_set():
                            samples[rid].append(
                                {**record, "applied": False, "reason": "duel_stopped_before_submission"}
                            )
                            break
                        ack = await tool(
                            mcp,
                            "drive_duel",
                            {
                                "race_id": race_id,
                                "racer_id": rid,
                                "driver_token": initial["drivers"][rid]["driver_token"],
                                "action_id": record["action"],
                                "observation_tick": observation["tick"],
                                "command_seq": seq,
                            },
                        )
                        samples[rid].append(
                            {
                                **record,
                                "command_seq": seq,
                                "observation_tick": observation["tick"],
                                "applied": ack["applied"],
                                "applied_tick": ack.get("applied_tick"),
                                "applied_ns": ack.get("applied_ns"),
                                "reason": ack.get("reason"),
                            }
                        )
                        if ack["applied"]:
                            seq += 1
                        observation = ack["observation"]
                        if not ack["applied"] and ack.get("reason") == "observation_before_rescue":
                            observation = await tool(
                                mcp, "observe_duel", {"race_id": race_id, "racer_id": rid}
                            )
                except Exception as error:  # noqa: BLE001 -- preserve both recordings and settle in-flight billing.
                    live_metrics[rid].update(thinking=False, error=type(error).__name__)
                    publish_live()
                    errors.append({"racer_id": rid, "type": type(error).__name__, "detail": str(error)})
                    stop.set()

            background = [asyncio.create_task(spectator()), asyncio.create_task(pause_once())]
            try:
                await asyncio.gather(*(drive(r) for r in racers))
            finally:
                stop.set()
                for task in background:
                    task.cancel()
                await asyncio.gather(*background, return_exceptions=True)
                race = await tool(
                    mcp,
                    "finish_duel",
                    {
                        "race_id": race_id,
                        "owner_token": initial["owner_token"],
                        "reason": "driver_error" if errors else "drivers_finished",
                    },
                )
            race["driver_labels"] = {
                r: (
                    "Scripted control" if free else {"typesafe": "Jev", "openai": "OpenAI", "primeintellect": "Clef"}[routes[r]["provider"]]
                )
                + " · "
                + r
                for r in racers
            }
            metrics = {
                r: {
                    "requests": drivers[r].count,
                    "api_latency_ms": percentiles([x["latency_ms"] for x in samples[r]]),
                    "cost_usd": sum(x["cost"] for x in samples[r]),
                    "discarded": sum(not x["applied"] for x in samples[r]),
                }
                for r in racers
            }
            race["driver_metrics"] = metrics
            _write_new(output / "race.json", race)
            _write_new(output / "decisions.json", samples)
            pause["physics_samples"] = sum(
                pause.get("started_ns", 0) < s["wall_ns"] < pause.get("ended_ns", 0) for s in race["samples"]
            )
            result = {
                "free": free,
                "errors": errors,
                "spectator_warnings": spectator_warnings,
                "summary": race["summary"],
                "timing": race["timing"],
                "metrics": metrics,
                "pause": pause,
                "max_in_flight_mock_calls": max_in_flight,
                "source_unchanged": sources() == frozen,
                "budget_before": ledger_before,
                "budget_after": journal.check(),
                "collection_complete": True,
            }
            _write_new(output / "collection.json", result)
            return result
        finally:
            journal.close()


def audit_duel(directory, *, allow_failures=False):
    directory = Path(directory)
    race = _read(directory / "race.json")
    collection = _read(directory / "collection.json")
    start = _read(directory / "collection-start.json")
    decisions = _read(directory / "decisions.json")
    sim = DuelSimulation.from_config(race["config"])
    racers = sim.racer_ids
    commands = {}
    for c in race["commands"]:
        commands.setdefault(c["applied_tick"], []).append(c)
    queries = {r: {} for r in racers}
    calls = 0
    response_ids, reservations = set(), {}
    for rid in racers:
        for path in sorted((directory / rid).glob("query-*.json")):
            query = _read(path)
            queries[rid].setdefault(query["raw_observation"]["tick"], []).append(query)

    def verify_snapshot(sample):
        nonlocal calls
        assert sim.state()["racers"] == sample["racers"], ("physics", sample["tick"])
        assert sim.leader() == sample["leader"]
        for rid in racers:
            for query in queries[rid].pop(sample["tick"], []):
                raw = query["raw_observation"]
                expected = sim.observation(rid)
                for key in expected:
                    assert raw[key] == expected[key], (rid, key, sample["tick"])
                facts = duel_facts(
                    raw, race["config"], rid,
                    include_gate_geometry=start.get("include_gate_geometry", False),
                    include_wheel_motion=start.get("include_wheel_motion", False),
                    include_pedal_timing=start.get("include_pedal_timing", False),
                    control_timing_s=(
                        start.get("added_delay_s", 0.0)
                        if start.get("include_control_timing", False) else None
                    ),
                )
                assert facts == query["facts"]
                capture = _read(directory / rid / "calls" / f"{query['index']:05d}.json")
                api = DuelDecisionClient(
                    facts=facts,
                    handling=race["config"]["handling"],
                    budget=None,
                    http_client=object(),
                    api_key="audit-duel-placeholder",
                )
                payload = {
                    "model": start["routes"][rid]["model"],
                    "state": {},
                    "questions": api.questions,
                    "provider": {"only": [start["routes"][rid]["provider"]], "allow_fallbacks": False},
                }
                assert query["payload"] == payload and capture["wire"]["saved_unmodified"]
                wire = capture["wire"]["requests"]
                assert len(wire) == 1 and wire[0]["body_utf8"].encode() == encoded(payload)
                assert wire[0]["body_sha256"] == hashlib.sha256(encoded(payload)).hexdigest()
                replies = capture["wire"]["responses"]
                record = capture["record"]
                route = start["routes"][rid]
                reservations[record["reservation_id"]] = (rid, record)
                for reply in replies:
                    assert hashlib.sha256(reply["body_utf8"].encode()).hexdigest() == reply["body_sha256"]
                if allow_failures and not record["ok"]:
                    assert not any(d["applied"] and d["query_index"] == query["index"] for d in decisions[rid])
                    calls += 1
                    continue
                assert len(replies) == 1 and replies[0]["status"] == 200
                body = replies[0]["json"]
                assert body["model"] == route["resolved_model"] and body["provider"] == route["provider_name"]
                assert record["ok"] and record["id"] == body["id"] and record["usage"] == body["usage"]
                assert isinstance(body["id"], str) and body["id"].strip() and body["id"] not in response_ids
                response_ids.add(body["id"])
                assert body["usage"]["cost"] == record["cost"] and record["cost_source"] == "reported"
                reservations[record["reservation_id"]] = (rid, record)
                choices = {h: body["answers"][h]["choice"] for h in ("wheel", "pedal")}
                assert set(body["answers"]) == {"wheel", "pedal"}
                for head in ("wheel", "pedal"):
                    assert body["answers"][head]["type"] == "choice" and not body["answers"][head].get(
                        "refusal"
                    )
                    assert choices[head] in api.component_criteria[head]
                assert record["action"] == api._component_actions[(choices["wheel"], choices["pedal"])]
                assert choices == record["component_choices"]
                calls += 1

    origin_tick = sim.tick
    for index, sample in enumerate(race["samples"]):
        assert sample["tick"] == sim.tick + (1 if index else 0)
        if index:
            for c in commands.get(sample["tick"], []):
                sim.set_control(c["racer_id"], c["action_id"])
            sim.step()
        verify_snapshot(sample)
        if sim.episode_outcome() is not None:
            assert index == len(race["samples"]) - 1, "Episode continued past its stopping condition"
    if race.get("episode") and race["reason"].startswith("episode_"):
        assert race["episode"]["outcome"] == sim.episode_outcome()
    assert all(not q for q in queries.values()), "Unmatched observation tick"
    assert (
        sim.summary() == race["summary"] and sim.contacts == race["contacts"] and sim.events == race["events"]
    )
    events = [json.loads(line) for line in (directory / "budget-events.jsonl").read_text().splitlines()]
    current = start["budget_before"]
    owners = {}
    peak = 0
    for event in events:
        assert event["before"] == current
        expected = copy_ledger(current)
        reservation = event["reservation_id"]
        rid = event["racer_id"]
        if event["kind"] == "reserve":
            assert rid not in owners.values() and len(owners) < len(racers)
            owners[reservation] = rid
            expected["requests"] += 1
            item = event["after"]["pending"][reservation]
            assert item["cost"] == event["cost"] and item["tokens"] == event["tokens"]
            assert item["model"] == event["model"] and item["provider"] == event["provider"]
            route = start["routes"][rid]
            _, record = reservations[reservation]
            maximum = int(route.get("max_completion_tokens") or route.get("context_length") or 1000000)
            assert item["tokens"] == record["input_token_ceiling"] + maximum
            assert item["cost"] == (record["input_token_ceiling"] * route["price_input_per_token"]
                                    + maximum * route["price_output_per_token"] + route.get("price_per_request", 0))
            expected["pending"][reservation] = item
        else:
            assert owners.pop(reservation) == rid
            owner, record = reservations[reservation]
            assert owner == rid
            usage = record.get("usage", {})
            assert event["cost"] == usage.get("cost")
            tokens = (usage["input_tokens"] + usage["output_tokens"]
                      if all(isinstance(usage.get(k), int) for k in ("input_tokens", "output_tokens")) else None)
            assert event["tokens"] == tokens
            item = expected["pending"].pop(reservation)
            expected["charged_usd"] += item["cost"] if event["cost"] is None else event["cost"]
            expected["charged_tokens"] += item["tokens"] if event["tokens"] is None else event["tokens"]
            if event["cost"] is None:
                expected["uncertain_requests"] += 1
            else:
                expected["reported_cost_usd"] += event["cost"]
        assert expected == event["after"]
        current = expected
        peak = max(peak, len(owners))
    assert not owners and current == collection["budget_after"]
    applied = {(r, c["command_seq"]): c for r in racers for c in decisions[r] if c["applied"]}
    assert len(applied) == len(race["commands"])
    for command in race["commands"]:
        actual = applied[(command["racer_id"], command["command_seq"])]
        assert actual["action"] == command["action_id"] and actual["applied_tick"] == command["applied_tick"]
        assert actual["applied_ns"] == command["applied_ns"]
        assert actual["response_received_ns"] <= command["queued_ns"] <= command["applied_ns"]
        if start.get("added_delay_s", 0):
            assert actual["response_received_ns"] <= actual["delay_started_ns"] <= actual["delay_ended_ns"] <= command["queued_ns"]
            assert actual["delay_ended_ns"] - actual["delay_started_ns"] >= start["added_delay_s"] * 1e9
    assert calls == sum(m["requests"] for m in collection["metrics"].values()) == len(events) // 2
    assert (
        collection["source_unchanged"] and (allow_failures or (
            race["timing"]["infrastructure_valid"] and not collection["errors"]))
    )
    sample_lateness = [
        (s["wall_ns"] - race["started_ns"]) / 1e6 - (s["tick"] - origin_tick) * 1000 / 60
        for s in race["samples"][1:]
    ]
    assert allow_failures or max(sample_lateness, default=0) <= 100
    return {
        "passed": True,
        "failure_evidence_only": allow_failures,
        "physics_frames": len(race["samples"]),
        "exact_queries": calls,
        "budget_transitions": len(events),
        "peak_pending": peak,
        "max_sample_lateness_ms": max(sample_lateness, default=0),
        "summary": race["summary"],
    }


def copy_ledger(value):
    return json.loads(json.dumps(value))
