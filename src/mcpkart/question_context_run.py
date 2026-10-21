"""Run one experimental Jev stadium race with recorded native decisions.

    python -m mcpkart.question_context_run --help

The spectator/MCP server must already be running on this machine. This command
does not change its defaults or handling, create a new budget, or retry a race.
"""

from __future__ import annotations

import argparse
import asyncio
import fcntl
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx
from fastmcp import Client

from . import bench
from .decisions import Budget, discover_routes
from .question_context import INSTRUCTION_STYLE, PromptDomainError
from .question_context_driver import QuestionContextDriver, WireCapture, _write_new
from .sim import Simulation


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def start_ticks(pid):
    return int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])


def controller_sources():
    root = Path(__file__).parent
    return {str(root / name): sha(root / name) for name in (
        "question_context.py", "question_context_driver.py", "question_context_run.py",
    )}


def existing_budget(path):
    """Preserve saved authorizations instead of clamping an expanded token cap."""
    state = read(path)
    if state.get("schema_version") != 1 or state.get("pending") != {}:
        raise ValueError("A valid existing shared ledger with no pending POST is required")
    if not 0 <= state["charged_usd"] <= state["cap_usd"] <= 10:
        raise ValueError("Invalid or exhausted shared financial authorization")
    return Budget(path, cap_usd=state["cap_usd"], max_requests=state["max_requests"],
                  max_tokens=state["max_tokens"])


def qualify_clock(path, runtime):
    """Bind the complete engine clock gate to this boot, server and source."""
    path = Path(path)
    q = read(path)
    if not (q.get("passed") and q.get("controls", 0) >= 3
            and q.get("parent_pause_physics_samples", 0) > 0
            and q.get("long_clock_s", 0) >= 170.1 - 1e-6
            and q.get("model_requests") == 0 and q.get("budget_unchanged")):
        raise ValueError("The complete free engine clock qualification must pass")
    expected = {"backend": "process", "protocol_version": 1, "watchdog_enabled": False,
                "clock_mode": "fixed_step_wall_clock", "physics_hz": 60,
                "process_pid": q["http_parent_pid"]}
    if runtime != expected:
        raise ValueError("Server runtime differs from its clock qualification")
    if (q["boot_id"] != Path("/proc/sys/kernel/random/boot_id").read_text().strip()
            or q["http_parent_start_ticks"] != start_ticks(q["http_parent_pid"])
            or q["source_fingerprint"] != bench.fingerprint()):
        raise ValueError("Clock qualification belongs to a different source, boot or server")
    for name, digest in q["evidence_sha256"].items():
        if sha(path.parent / name) != digest:
            raise ValueError("Clock qualification evidence changed: " + name)
    return q


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", default="http://127.0.0.1:8765/mcp")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--course", choices=("stadium", "stadium_clockwise"), default="stadium")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--ledger", type=Path, default=Path("artifacts/budget.json"))
    p.add_argument("--clock-qualification", type=Path, required=True)
    p.add_argument("--max-decisions", type=int, default=800)
    p.add_argument("--stop-at", help="Optional absolute ISO8601 deadline, including timezone")
    return p


async def run(args, deadline):
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise ValueError("Configure OPENROUTER_API_KEY before running a model race")
    setup = {"course": args.course, "road_width": 24, "max_speed": 12,
             "max_steering_angle": .12}
    config = Simulation(reset_after_s=3, **setup).config()
    reference = bench.reference_trial(args.seed, race_setup=setup)
    if not reference["finished"] or reference["summary"]["resets"]:
        raise ValueError("The deterministic reference did not finish cleanly")
    source = bench.fingerprint()
    controllers = controller_sources()
    async with Client(args.url, timeout=45) as mcp:
        runtime = await bench.read_runtime_info(mcp)
        qualification = qualify_clock(args.clock_qualification, runtime)
        bound_paths = [args.clock_qualification]
        bound_paths += [args.clock_qualification.parent / name
                        for name in qualification["evidence_sha256"]]
        def identity(path):
            s = path.stat()
            return s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns
        bound = {path: identity(path) for path in bound_paths}
        budget = existing_budget(args.ledger)
        before = read(args.ledger)
        if (before["max_requests"] - before["requests"] < 1000
                or before["max_tokens"] - before["charged_tokens"] < 5_000_000):
            raise ValueError("The unchanged live admission floor is not met")
        if deadline and (deadline - datetime.now(UTC)).total_seconds() < 900:
            raise ValueError("Fewer than fifteen minutes remain for live admission")
        args.output.mkdir(parents=True, exist_ok=False)
        writer = {"pid": os.getpid(), "process_start_ticks": start_ticks(os.getpid()),
                  "parent_pid": os.getppid(), "parent_start_ticks": start_ticks(os.getppid()),
                  "boot_id": qualification["boot_id"], "started_utc": datetime.now(UTC).isoformat(),
                  "mode": "single_race_cli"}
        _write_new(args.output / "collection-start.json", {
            "writer": writer, "budget_before": before, "source_fingerprint": source,
            "controller_sources_sha256": controllers, "runtime_info": runtime,
            "clock_qualification_sha256": sha(args.clock_qualification),
            "seed": args.seed, "race_setup": setup, "reference_s": reference["elapsed"],
            "single_race": True, "automatic_retries": 0, "provider_fallbacks": False,
        })
        capture, driver, quality_stop, error = WireCapture(), None, False, None
        try:
            async with httpx.AsyncClient(timeout=5, follow_redirects=False,
                                         event_hooks=capture.hooks) as http:
                routes = await discover_routes(http, models=["typesafe/jev-1.14"])
                if len(routes) != 1 or routes[0]["model"] != "typesafe/jev-1.14":
                    raise ValueError("Exactly one pinned Jev route is required")
                route = routes[0]
                _write_new(args.output / "route.json", route)
                def admission():
                    if deadline and datetime.now(UTC) >= deadline:
                        raise RuntimeError("Absolute collection deadline reached before POST")
                    if driver.count >= args.max_decisions:
                        raise RuntimeError("Single-race decision ceiling reached before POST")
                    if source != bench.fingerprint() or controllers != controller_sources():
                        raise RuntimeError("Engine or controller source changed before POST")
                    if any(identity(path) != value for path, value in bound.items()):
                        raise RuntimeError("Clock qualification evidence changed before POST")
                    if (qualification["http_parent_start_ticks"]
                            != start_ticks(qualification["http_parent_pid"])):
                        raise RuntimeError("Qualified server process changed before POST")
                driver = QuestionContextDriver(
                    budget=budget, http=http, capture=capture, route=route, config=config,
                    output=args.output, admission=admission,
                )
                trial = await bench.run_trial(
                    mcp, driver, route, args.seed, reference["elapsed"], args.output / "trial.json",
                    telemetry="raw", control_language="geometry", instruction_style=INSTRUCTION_STYLE,
                    runtime_info=runtime, race_setup=setup, stop_on_first_error=True,
                )
                if trial["metrics"]["request_errors"] or not trial["metrics"]["realtime_valid"]:
                    raise RuntimeError("Race retained after an endpoint or runtime validation failure")
        except PromptDomainError as caught:
            quality_stop, error = True, caught
        except BaseException as caught:
            error = caught
            raise
        finally:
            _write_new(args.output / "collection-ended.json", {
                "writer": writer, "budget_before": before, "budget_after": read(args.ledger),
                "requests": driver.count if driver else 0, "quality_domain_stop": quality_stop,
                "error": bench.failure_detail(error, driver.api_key if driver else None) if error else None,
                "ended_utc": datetime.now(UTC).isoformat(), "no_additional_race_admitted": True,
                "controller_sources_sha256": controllers, "source_fingerprint": source,
            })


def main():
    args = parser().parse_args()
    if args.max_decisions < 1:
        raise ValueError("max-decisions must be positive")
    if args.stop_at:
        deadline = datetime.fromisoformat(args.stop_at)
        if deadline.tzinfo is None:
            raise ValueError("stop-at must include a timezone")
    else:
        deadline = None
    lock_path = args.ledger.parent / "root-paid-writer.lock"
    with lock_path.open("a") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        asyncio.run(run(args, deadline))


if __name__ == "__main__":
    main()
