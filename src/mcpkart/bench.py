"""Reference calibration, real MCP driving trials, and reproducible result files."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import math
import statistics
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastmcp import Client

from .decisions import CONTROL_LANGUAGES, INSTRUCTION_STYLES
from .observations import ObservationHistory
from .sim import ACTIONS, DT, Simulation, scripted_action
from .telemetry import VARIANTS, represent

RESET_AFTER_S: float | None = 3.0
POC_MODELS = "typesafe/jev-1.14"
RUNTIME_IDENTITY_FIELDS = ("backend", "protocol_version", "watchdog_enabled", "clock_mode", "physics_hz")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def percentiles(values: list[float]) -> dict[str, float | int | None]:
    """Descriptive sample quantiles, not a claim about the population tail."""
    if not values:
        return {"n": 0, "p50": None, "p95": None, "p99": None, "max": None}
    ordered = sorted(values)

    def quantile(fraction: float) -> float:
        index = (len(ordered) - 1) * fraction
        lo = math.floor(index)
        return ordered[lo] + (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo]) * (index - lo)

    return {
        "n": len(values),
        "p50": quantile(0.5),
        "p95": quantile(0.95),
        "p99": quantile(0.99) if len(values) >= 1000 else None,
        "max": max(values),
    }


def fingerprint() -> str:
    source = Path(__file__).parent
    digest = hashlib.sha256()
    for name in (
        "sim.py",
        "decisions.py",
        "runtime.py",
        "process_runtime.py",
        "physics_worker.py",
        "rust_runtime.py",
        "web.py",
        "bench.py",
        "telemetry.py",
        "observations.py",
    ):
        path = source / name
        digest.update(name.encode())
        if path.exists():
            digest.update(path.read_bytes())
    rust = source.parents[1]/"rust-race"
    for path in sorted([rust/"Cargo.toml", rust/"Cargo.lock", *(rust/"src").glob("*.rs")]):
        if path.is_file():
            digest.update(path.relative_to(rust).as_posix().encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


@lru_cache(maxsize=1)
def simulation_contract() -> dict:
    return Simulation(reset_after_s=RESET_AFTER_S).config()


def driving_evidence(observation: dict, variant: str = "raw", *, context: dict | None = None) -> dict:
    """Same factual control/geometry contract for every compared model."""
    evidence = {
        k: v for k, v in observation.items() if k not in {"race_id", "observed_ns", "captured_ns", "status"}
    }
    evidence["units"] = (
        "Metres, seconds, radians. Positive steering/yaw turns LEFT. "
        "Lookahead x is forward and y is left, relative to the kart heading; points are road centreline. "
        "Curvature is radians/metre. Offset is positive left of road centre; road half-width=width/2. "
        "Heading_error=road heading minus kart heading, positive means road faces left of kart."
    )
    contract = simulation_contract()
    evidence["handling"] = contract["handling"]
    gate = contract["track"]["checkpoints"][observation["progress"]["checkpoint"]]
    kart = observation["kart"]
    dx, dy = gate["x"] - kart["x"], gate["y"] - kart["y"]
    c, s = math.cos(kart["heading"]), math.sin(kart["heading"])
    evidence["next_checkpoint"] = {
        "x": round(gate["x"], 3),
        "y": round(gate["y"], 3),
        "ego_x": round(c * dx + s * dy, 3),
        "ego_y": round(-s * dx + c * dy, 3),
        "forward_heading": round(gate["heading"], 5),
    }
    return represent(evidence, contract, variant, context=context)


def reference_trial(seed: int, delay: float = 0, deadline: float = 180) -> dict:
    sim = Simulation(seed=seed, laps=3, reset_after_s=RESET_AFTER_S)
    pending: tuple[float, str, int] | None = None
    ages: list[float] = []
    intervals: list[float] = []
    previous_application_tick: int | None = None
    discarded = 0
    last_observation = sim.observation()
    while not sim.finished and sim.elapsed < deadline:
        if pending is None:
            pending = (sim.elapsed + delay, scripted_action(last_observation), last_observation["tick"])
        if sim.elapsed + 1e-9 >= pending[0]:
            if sim.last_reset_tick is not None and pending[2] < sim.last_reset_tick:
                discarded += 1
                pending = None
                last_observation = sim.observation()
                continue
            sim.set_control(pending[1])
            application_tick = sim.tick + 1
            ages.append((application_tick - pending[2]) * DT * 1000)
            if previous_application_tick is not None:
                intervals.append((application_tick - previous_application_tick) * DT * 1000)
            previous_application_tick = application_tick
            pending = None
        sim.step()
        if pending is None:
            last_observation = sim.observation()
    return {
        "seed": seed,
        "delay_s": delay,
        "finished": sim.finished,
        "elapsed": sim.elapsed,
        "summary": sim.summary(),
        "config": sim.config(),
        "discarded_after_rescue": discarded,
        "observation_age_ms": percentiles(ages),
        "action_interval_ms": percentiles(intervals),
    }


def make_reference(seeds: int, delays: list[float], output: Path) -> dict:
    rows = []
    for delay in delays:
        for seed in range(seeds):
            result = reference_trial(seed, delay)
            rows.append(result)
            print(json.dumps({k: result[k] for k in ("seed", "delay_s", "finished", "elapsed")}), flush=True)
    reference = {
        "created_at": time.time(),
        "fingerprint": fingerprint(),
        "dt": DT,
        "actions": ACTIONS,
        "trials": rows,
    }
    write_json(output, reference)
    return reference


async def tool(client: Client, name: str, arguments: dict | None = None) -> dict:
    result = await client.call_tool(name, arguments or {})
    data = result.data if isinstance(result.data, dict) else result.structured_content
    if not isinstance(data, dict):
        raise TypeError(f"MCP {name} did not return structured data")
    return data


def runtime_identity(info: dict) -> dict:
    """Stable runtime contract; worker/parent PIDs and timestamps are diagnostic."""
    if not isinstance(info, dict) or any(key not in info for key in RUNTIME_IDENTITY_FIELDS):
        raise ValueError("Runtime provenance is missing required runtime_info fields")
    if info["backend"] not in {"process", "event_loop"}:
        raise ValueError("Unsupported runtime backend")
    if (
        not isinstance(info["protocol_version"], int)
        or isinstance(info["protocol_version"], bool)
        or info["protocol_version"] != 1
    ):
        raise ValueError("Unsupported runtime protocol version")
    if (
        not isinstance(info["watchdog_enabled"], bool)
        or not isinstance(info["clock_mode"], str)
        or not info["clock_mode"]
    ):
        raise ValueError("Invalid runtime watchdog or clock mode")
    frequency = info["physics_hz"]
    if (
        isinstance(frequency, bool)
        or not isinstance(frequency, (int, float))
        or not math.isfinite(frequency)
        or frequency <= 0
    ):
        raise ValueError("Invalid runtime physics frequency")
    return {key: copy.deepcopy(info[key]) for key in RUNTIME_IDENTITY_FIELDS}


async def read_runtime_info(mcp: Client) -> dict:
    """Require the current server contract, with no fallback to an older server."""
    info = await tool(mcp, "runtime_info")
    runtime_identity(info)
    return copy.deepcopy(info)


def runtime_mismatches(race: dict, expected: dict) -> list[str]:
    """Check final child provenance where the server supplies it."""
    identity = runtime_identity(expected)
    if not isinstance(race, dict):
        return ["race is not an object"]
    mismatches = []
    for location, actual in (
        ("race", race),
        ("race.runtime_info", race.get("runtime_info", {})),
        ("race.timing", race.get("timing", {})),
    ):
        if not isinstance(actual, dict):
            mismatches.append(f"{location} is not an object")
            continue
        for key in RUNTIME_IDENTITY_FIELDS:
            if key in actual and actual[key] != identity[key]:
                mismatches.append(f"{location}.{key} differs from runtime_info")
    return mismatches


def compact_stdout(value: Any) -> Any:
    """Keep scalar diagnostics and event counts; full event arrays stay on disk."""
    if isinstance(value, dict):
        return {
            f"{key}_items_retained" if isinstance(item, (list, tuple)) else key: len(item)
            if isinstance(item, (list, tuple))
            else compact_stdout(item)
            for key, item in value.items()
        }
    if isinstance(value, str):
        return value[:250]
    return value


def trial_done_event(report: dict, output: Path) -> dict:
    return {
        "event": "trial_done",
        "model": report["model"],
        "seed": report["seed"],
        "output": str(output),
        "collection_complete": report.get("collection_complete", True),
        "runtime_info": runtime_identity(report["runtime_info"]),
        **compact_stdout(report["metrics"]),
    }


def failure_detail(error: BaseException, secret: str | None = None) -> dict:
    message = str(error)
    if isinstance(secret, str) and secret:
        message = message.replace(secret, "[REDACTED]")
    return {"type": type(error).__name__, "message": message[:250]}


def incomplete_metrics(requests: list[dict], baseline: float, runtime_info: dict) -> dict:
    """Only locally known request facts; an absent final race has no final clock."""
    return {
        "finished": None,
        "realtime_valid": False,
        "elapsed": None,
        "reference_s": baseline,
        "time_ratio": None,
        "rescues": None,
        "request_count": len(requests),
        "request_errors": sum(not record["ok"] for record in requests),
        "api_latency_ms": percentiles([record["latency_ms"] for record in requests]),
        "observation_age_ms": percentiles(
            [record["observation_age_ms"] for record in requests if "observation_age_ms" in record]
        ),
        "cost_usd": sum(record.get("cost", 0) or 0 for record in requests),
        "runtime_backend": runtime_identity(runtime_info)["backend"],
        "runtime_consistent": None,
    }


def reference_durations(path: Path) -> dict[int, float]:
    reference = json.loads(path.read_text())
    current_config = Simulation(reset_after_s=RESET_AFTER_S).config()
    if any(row["config"] != current_config for row in reference["trials"]):
        raise ValueError(
            "Reference track/handling differs from current physics; recalibrate before comparing"
        )
    rows = {
        int(row["seed"]): float(row["elapsed"])
        for row in reference["trials"]
        if row["delay_s"] == 0 and row["finished"]
    }
    if not rows:
        raise RuntimeError("A successful offline reference is required before model trials")
    return rows


def summarize_trial(result: dict, requests: list[dict], baseline: float) -> dict:
    summary = dict(result.get("summary", {}))
    finished = bool(summary.get("finished", result.get("finished", False)))
    elapsed = float(summary.get("elapsed", result.get("elapsed", 0)))
    timing = result.get("timing", {})
    valid = bool(timing.get("infrastructure_valid", summary.get("realtime_valid", False)))
    return {
        "finished": finished,
        "realtime_valid": valid,
        "elapsed": elapsed,
        "reference_s": baseline,
        "time_ratio": elapsed / baseline if finished else None,
        "offtrack_time": summary.get("offtrack_time", summary.get("offroad_time")),
        "rescues": summary.get("resets", 0),
        "rescue_after_s": result.get("config", {}).get("rescue", {}).get("after_s"),
        "discarded_commands": sum(r.get("applied") is False for r in requests),
        "request_count": len(requests),
        "request_errors": sum(not r["ok"] for r in requests),
        "api_latency_ms": percentiles([r["latency_ms"] for r in requests]),
        "observation_age_ms": percentiles(
            [r["observation_age_ms"] for r in requests if "observation_age_ms" in r]
        ),
        "cost_usd": sum(r.get("cost", 0) or 0 for r in requests),
        "timing": timing,
    }


def validate_resume(
    report: dict,
    *,
    route: dict,
    seed: int,
    baseline: float,
    telemetry: str,
    control_language: str,
    instruction_style: str,
    instructions: str | None = None,
    action_criteria: dict | None = None,
    runtime_info: dict | None = None,
) -> None:
    """Require the saved trial to belong to this exact experiment configuration.

    Catalog observation times and unused catalog metadata may change. The pinned
    route's request identity, accepted response identities, limits, and prices
    remain part of the comparison even when source files have not changed.
    """
    if report.get("fingerprint") != fingerprint():
        raise ValueError("Cannot resume results after source configuration changed")
    if report.get("collection_complete") is False:
        raise ValueError("Cannot resume an incompletely collected trial; retain its evidence separately")
    if runtime_info is None:
        raise ValueError("Cannot resume results without current runtime_info provenance")
    if runtime_identity(report.get("runtime_info")) != runtime_identity(runtime_info):
        raise ValueError("Cannot resume results with a different runtime backend or mode")
    if runtime_mismatches(report.get("race", {}), runtime_info):
        raise ValueError("Cannot resume results with inconsistent final runtime provenance")
    if report.get("model") != route.get("model") or report.get("seed") != seed:
        raise ValueError("Cannot resume results for a different model or seed")
    if report.get("telemetry", "raw") != telemetry:
        raise ValueError("Cannot mix telemetry variants in one result directory")
    if report.get("control_language", "numeric") != control_language:
        raise ValueError("Cannot mix control descriptions in one result directory")
    if report.get("instruction_style", "original") != instruction_style:
        raise ValueError("Cannot mix question wording in one result directory")
    race = report.get("race", {})
    if race.get("config") != Simulation(reset_after_s=RESET_AFTER_S).config():
        raise ValueError("Cannot resume results with different simulation or rescue configuration")
    if report.get("metrics", {}).get("reference_s") != baseline:
        raise ValueError("Cannot resume results with a different paired reference duration")
    if race.get("deadline") != baseline * 3:
        raise ValueError("Cannot resume results with a different trial deadline")
    route_keys = (
        "model",
        "provider",
        "provider_name",
        "resolved_model",
        "endpoint_name",
        "price_input_per_token",
        "price_output_per_token",
        "price_per_request",
        "context_length",
        "max_prompt_tokens",
        "max_completion_tokens",
        "canonical_version_pinned",
    )
    saved_route = report.get("route", {})
    if any(saved_route.get(key) != route.get(key) for key in route_keys):
        raise ValueError("Cannot resume results with a different pinned route")
    if (
        instructions is not None
        and report.get("instructions") is not None
        and report["instructions"] != instructions
    ):
        raise ValueError("Cannot resume results with different exact instructions")
    if (
        action_criteria is not None
        and report.get("action_criteria") is not None
        and report["action_criteria"] != action_criteria
    ):
        raise ValueError("Cannot resume results with different exact action criteria")


async def run_trial(
    mcp: Client,
    decisions: Any,
    route: dict,
    seed: int,
    baseline: float,
    output: Path,
    telemetry: str = "raw",
    control_language: str = "numeric",
    instruction_style: str = "original",
    *,
    runtime_info: dict | None = None,
) -> dict:
    model = route["model"]
    source_fingerprint = fingerprint()
    instructions = getattr(decisions, "instructions", None)
    action_criteria = copy.deepcopy(getattr(decisions, "criteria", None))
    runtime_info = copy.deepcopy(runtime_info) if runtime_info is not None else await read_runtime_info(mcp)
    runtime_identity(runtime_info)
    observation = await tool(
        mcp,
        "start_race",
        {
            "seed": seed,
            "deadline": baseline * 3,
            "label": f"{model}"
            + (" / explicit controls" if control_language == "explicit" else "")
            + (f" / {instruction_style}" if instruction_style != "original" else "")
            + f" [telemetry={telemetry}]",
            "reset_after_s": RESET_AFTER_S,
        },
    )
    requests: list[dict] = []
    history = ObservationHistory() if telemetry == "road_history" else None
    commands = 0
    last_progress = time.monotonic()
    reason = "completed"
    trial_error: BaseException | None = None
    try:
        while observation.get("status", "running") == "running" and not observation.get("finished"):
            # The model sees racing evidence rather than local RPC identity/timestamps.
            context = history.observe(observation) if history is not None else None
            evidence = driving_evidence(observation, telemetry, context=context)
            record = await decisions.decide(route, evidence)
            record["observation"] = evidence
            record["observation_tick"] = observation["tick"]
            record["observed_ns"] = observation["observed_ns"]
            requests.append(record)
            if record["ok"]:
                commands += 1
                mcp_started = time.monotonic_ns()
                ack = await tool(
                    mcp,
                    "drive",
                    {
                        "race_id": observation["race_id"],
                        "action_id": record["action"],
                        "observation_tick": observation["tick"],
                        "command_seq": commands,
                    },
                )
                record["mcp_roundtrip_ms"] = (time.monotonic_ns() - mcp_started) / 1e6
                record["applied"] = ack.get("applied", True)
                record["command_reason"] = ack.get("reason")
                record["reset_during_step"] = ack.get("reset_during_step", False)
                if ack.get("applied_ns") is not None:
                    record["applied_ns"] = ack["applied_ns"]
                    record["observation_age_ms"] = (ack["applied_ns"] - record["observed_ns"]) / 1e6
                observation = ack["observation"]
            else:
                observation = await tool(mcp, "observe")
            if time.monotonic() - last_progress >= 5:
                print(
                    json.dumps(
                        {
                            "event": "driving",
                            "model": model,
                            "seed": seed,
                            "racing_s": observation.get("time"),
                            "requests": len(requests),
                            "last_latency_ms": record["latency_ms"],
                        }
                    ),
                    flush=True,
                )
                last_progress = time.monotonic()
            if len(requests) >= 3 and all(not r["ok"] for r in requests[-3:]):
                reason = "three_consecutive_endpoint_errors"
                break
    except BaseException as error:
        reason = "interrupted"
        trial_error = error
        raise
    finally:
        collection_error: BaseException | None = None
        try:
            result = await tool(mcp, "finish_race", {"reason": reason})
        except BaseException as error:  # noqa: BLE001 - Re-raised after preserving evidence below.
            collection_error = error
            result = None
        if collection_error is not None:
            mismatches = []
            metrics = incomplete_metrics(requests, baseline, runtime_info)
        else:
            mismatches = runtime_mismatches(result, runtime_info)
            metrics = summarize_trial(result, requests, baseline)
            actual_info, actual_timing = result.get("runtime_info"), result.get("timing")
            metrics["runtime_backend"] = (
                (actual_info.get("backend") if isinstance(actual_info, dict) else None)
                or (actual_timing.get("backend") if isinstance(actual_timing, dict) else None)
                or result.get("backend", runtime_identity(runtime_info)["backend"])
            )
            metrics["runtime_consistent"] = not mismatches
            if mismatches:
                metrics["realtime_valid"] = False
        report = {
            "model": model,
            "route": route,
            "seed": seed,
            "fingerprint": source_fingerprint,
            "runtime_info": runtime_info,
            "runtime_mismatches": mismatches,
            "telemetry": telemetry,
            "control_language": control_language,
            "instruction_style": instruction_style,
            "instructions": instructions,
            "action_criteria": action_criteria,
            "requests": requests,
            "race": result,
            "collection_complete": collection_error is None,
            "metrics": metrics,
        }
        secret = getattr(decisions, "api_key", None)
        if trial_error is not None:
            report["trial_error"] = failure_detail(trial_error, secret)
        if collection_error is not None:
            report.update(
                status="incomplete",
                collection_error=failure_detail(collection_error, secret),
                last_observation=copy.deepcopy(observation),
            )
        write_json(output, report)
        print(json.dumps(trial_done_event(report, output)), flush=True)
        if collection_error is not None and trial_error is None:
            raise collection_error
    return report


def summarize_batch(reports: list[dict], required_trials: int = 10) -> dict:
    models = sorted({r["model"] for r in reports})
    rows = []
    for model in models:
        trials = [r for r in reports if r["model"] == model]
        incomplete = [r for r in trials if r.get("collection_complete") is False]
        completed = [r for r in trials if r["metrics"]["finished"] and r["metrics"]["realtime_valid"]]
        unrescued = [r for r in completed if not r["metrics"].get("rescues", 0)]
        ratios = [r["metrics"]["time_ratio"] for r in completed]
        strict_ratios = [r["metrics"]["time_ratio"] for r in unrescued]
        median = statistics.median(ratios) if ratios else None
        strict_median = statistics.median(strict_ratios) if strict_ratios else None
        full = len(trials) == required_trials and not incomplete
        known_rescues = sum(r["metrics"].get("rescues", 0) or 0 for r in trials)
        rows.append(
            {
                "model": model,
                "trials": len(trials),
                "incomplete_trials": len(incomplete),
                "completed": len(completed),
                "completed_without_rescue": len(unrescued),
                "total_rescues": None if incomplete else known_rescues,
                "known_rescues": known_rescues,
                "rescue_after_s": trials[0]["metrics"].get("rescue_after_s"),
                "strict_passes": bool(
                    full and len(unrescued) >= 8 and strict_median is not None and strict_median <= 2
                ),
                "median_completed_time_ratio": median,
                "complete_batch": full,
                "completion_target_ruled_out": len(completed)
                + len(incomplete)
                + max(0, required_trials - len(trials))
                < 8,
                "passes": bool(full and len(completed) >= 8 and median is not None and median <= 2),
                "cost_usd": sum(r["metrics"]["cost_usd"] for r in trials),
            }
        )
    return {"models": rows, "required_trials": required_trials}


async def remote_command(args: argparse.Namespace) -> None:
    from .decisions import Budget, BudgetExceeded, DecisionClient, discover_routes

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    if args.command == "live-reference":

        class ScriptedDriver:
            async def decide(self, route: dict, observation: dict) -> dict:
                started = time.monotonic_ns()
                action = scripted_action(observation)
                ended = time.monotonic_ns()
                return {
                    "ok": True,
                    "action": action,
                    "request_started_ns": started,
                    "response_received_ns": ended,
                    "latency_ms": (ended - started) / 1e6,
                    "cost": 0.0,
                    "model": "scripted/reference",
                    "provider": "local",
                    "error": None,
                }

        baselines = reference_durations(Path(args.reference))
        async with Client(args.url, timeout=30) as mcp:
            runtime_info = await read_runtime_info(mcp)
            await run_trial(
                mcp,
                ScriptedDriver(),
                {"model": "scripted/reference", "provider": "local"},
                0,
                baselines[0],
                output / "scripted-live.json",
                runtime_info=runtime_info,
            )
        return
    routes_path = output / "routes.json"
    if routes_path.exists():
        routes = json.loads(routes_path.read_text())
    else:
        routes = (
            await discover_routes(models=args.models.split(",")) if args.models else await discover_routes()
        )
        write_json(routes_path, routes)
    if args.models:
        requested = set(args.models.split(","))
        routes = [r for r in routes if r["model"] in requested]
        if not routes:
            raise ValueError("No requested models found in pinned routes")
    if args.command == "routes":
        print(
            json.dumps(
                [
                    {k: r[k] for k in ("model", "resolved_model", "provider", "price_input_per_token")}
                    for r in routes
                ],
                indent=2,
            )
        )
        return
    budget = Budget(path=Path("artifacts/budget.json"), cap_usd=10)
    print(json.dumps({"event": "budget", **budget.summary()}), flush=True)
    async with DecisionClient(
        budget=budget,
        actions=ACTIONS,
        control_language=args.control_language,
        instruction_style=args.instruction_style,
    ) as decisions:
        if args.command == "latency":
            measurements = []
            try:
                for sample in range(args.samples):
                    sim = Simulation(seed=sample, reset_after_s=RESET_AFTER_S)
                    for _ in range(round((0.5 + sample * 0.67) / DT)):
                        sim.set_control(scripted_action(sim.observation()))
                        sim.step()
                    for route in routes:
                        evidence = driving_evidence(sim.observation(), args.telemetry)
                        record = await decisions.decide(route, evidence)
                        record["observation"] = evidence
                        record["fingerprint"] = fingerprint()
                        record["sample"] = sample
                        record["telemetry"] = args.telemetry
                        record["warmup"] = sample == 0
                        measurements.append(record)
                        write_json(output / "latency.json", measurements)
                        print(
                            json.dumps(
                                {
                                    "model": route["model"],
                                    "sample": sample,
                                    "ok": record["ok"],
                                    "latency_ms": record["latency_ms"],
                                    "error": record.get("error"),
                                    "error_detail": record.get("error_detail"),
                                }
                            ),
                            flush=True,
                        )
                        if not record["ok"] and sample == 0:
                            raise RuntimeError(
                                f"Endpoint smoke test failed for {route['model']}: {record['error']}"
                            )
            finally:
                write_json(output / "latency.json", measurements)
        else:
            baselines = reference_durations(Path(args.reference))
            reports = []
            active_path = None
            active_attempt = False
            trials = 1 if args.command == "screen" else args.trials
            try:
                async with Client(args.url, timeout=30) as mcp:
                    runtime_info = await read_runtime_info(mcp)
                    for seed in range(trials):
                        if seed not in baselines:
                            raise ValueError(f"Missing paired scripted baseline for seed {seed}")
                        for index in range(len(routes)):
                            route = routes[(index + seed) % len(routes)]
                            previous = [r for r in reports if r["model"] == route["model"]]
                            failures = sum(
                                not (r["metrics"]["finished"] and r["metrics"]["realtime_valid"])
                                for r in previous
                            )
                            if args.stop_when_target_impossible and failures > 2:
                                continue
                            name = route["model"].replace("/", "--")
                            path = output / f"{name}--seed-{seed}.json"
                            if path.exists():
                                report = json.loads(path.read_text())
                                validate_resume(
                                    report,
                                    route=route,
                                    seed=seed,
                                    baseline=baselines[seed],
                                    telemetry=args.telemetry,
                                    control_language=args.control_language,
                                    instruction_style=args.instruction_style,
                                    instructions=decisions.instructions,
                                    action_criteria=decisions.criteria,
                                    runtime_info=runtime_info,
                                )
                            else:
                                active_path = path
                                active_attempt = True
                                report = await run_trial(
                                    mcp,
                                    decisions,
                                    route,
                                    seed,
                                    baselines[seed],
                                    path,
                                    telemetry=args.telemetry,
                                    control_language=args.control_language,
                                    instruction_style=args.instruction_style,
                                    runtime_info=runtime_info,
                                )
                            reports.append(report)
                            active_attempt = False
                            write_json(
                                output / "summary.json",
                                {**summarize_batch(reports), "budget": budget.summary()},
                            )
            except BudgetExceeded:
                print("Budget exhausted; comparison is incomplete.", flush=True)
            finally:
                # Persist the attempted trial in the summary before propagating
                # a worker/transport error, as well as on a budget interruption.
                if active_attempt and active_path is not None and active_path.exists():
                    reports.append(json.loads(active_path.read_text()))
                write_json(output / "summary.json", {**summarize_batch(reports), "budget": budget.summary()})
        write_json(output / "budget-summary.json", budget.summary())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    reference = sub.add_parser(
        "reference", help="Calibrate scripted driving and injected decision delays offline"
    )
    reference.add_argument("--seeds", type=int, default=10)
    reference.add_argument("--delays", default="0,0.1,0.2,0.35,0.5")
    reference.add_argument("--output", default="artifacts/reference.json")
    reference.add_argument(
        "--reset-after-seconds", type=float, default=3, help="Continuous off-road timeout; 0 disables rescue"
    )
    for command in ("routes", "latency", "screen", "compare", "live-reference"):
        child = sub.add_parser(command)
        child.add_argument("--output", default="artifacts/pilot")
        child.add_argument(
            "--models",
            default=POC_MODELS,
            help="Comma-separated exact model aliases; the initial PoC defaults to Jev",
        )
        child.add_argument(
            "--telemetry",
            choices=VARIANTS,
            default="raw" if command == "live-reference" else "road_physics",
            help="Factual telemetry representation; use a new result directory for each",
        )
        child.add_argument(
            "--control-language",
            choices=CONTROL_LANGUAGES,
            default="numeric",
            help="Descriptions of the same physical actions; numeric preserves the original wording",
        )
        child.add_argument(
            "--instruction-style",
            choices=INSTRUCTION_STYLES,
            default="original",
            help="Question wording; original preserves the first experiment instructions",
        )
        child.add_argument("--url", default="http://127.0.0.1:8765/mcp")
        child.add_argument("--reference", default="artifacts/reference.json")
        child.add_argument("--samples", type=int, default=20)
        child.add_argument("--trials", type=int, default=10)
        child.add_argument(
            "--stop-when-target-impossible",
            action="store_true",
            help="Stop a model after three failed trials rule out eight completions out of ten",
        )
        child.add_argument(
            "--reset-after-seconds",
            type=float,
            default=3,
            help="Continuous off-road timeout; 0 disables rescue",
        )
    args = parser.parse_args()
    if not math.isfinite(args.reset_after_seconds) or args.reset_after_seconds < 0:
        parser.error("--reset-after-seconds must be finite and nonnegative")
    global RESET_AFTER_S
    RESET_AFTER_S = args.reset_after_seconds or None
    simulation_contract.cache_clear()
    if args.command == "reference":
        make_reference(args.seeds, [float(x) for x in args.delays.split(",")], Path(args.output))
    else:
        try:
            asyncio.run(remote_command(args))
        except KeyboardInterrupt:
            print(
                "Interrupted; available trial recordings and budget reservations are preserved.", flush=True
            )
            raise SystemExit(130) from None


if __name__ == "__main__":
    main()
