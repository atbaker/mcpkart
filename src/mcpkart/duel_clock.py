"""Free qualification for the local Linux shared-clock duel server."""

from __future__ import annotations

import argparse
import asyncio
import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastmcp import Client

from .bench import tool
from .decisions import DEFAULT_PROVIDERS, Budget
from .duel import TRIO_RACERS, DuelSimulation
from .duel_bench import audit_duel, collect_duel, sources
from .question_context_driver import _read, _write_new
from .question_context_run import start_ticks


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mock_routes(models=("typesafe/jev-1.14", "typesafe/jev-1.14"), racers=("red", "blue")):
    return {
        rid: {
            "model": model,
            "resolved_model": model + "-mock",
            "provider": DEFAULT_PROVIDERS[model],
            "provider_name": {"typesafe": "TypeSafe", "openai": "OpenAI", "primeintellect": "Prime Intellect"}[
                DEFAULT_PROVIDERS[model]
            ],
            "price_input_per_token": 0,
            "price_output_per_token": 0,
            "price_per_request": 0,
            "context_length": 262144,
            "max_completion_tokens": 235929,
        }
        for rid, model in zip(racers, models, strict=True)
    }


def validate_qualification(path, runtime):
    path = Path(path)
    q = _read(path)
    if not (
        q.get("passed")
        and q.get("controls", 0) >= 3
        and q.get("long_clock_s", 0) >= 170.1 - 1e-6
        and q.get("parent_pause_physics_samples", 0) >= 12
        and q.get("model_requests") == 0
        and q.get("budget_unchanged")
    ):
        raise ValueError("The complete free duel clock qualification must pass")
    required = {"plan.json", "long-clock.json.gz", "long-proof.json", "memory-samples.json"}
    for index in range(q["controls"]):
        required.update((f"control-{index}/race.json", f"control-{index}/proof.json"))
    if not required.issubset(q.get("evidence_sha256", {})):
        raise ValueError("Clock qualification lacks its complete saved evidence")
    if q.get("runtime") != runtime or q.get("source_sha256") != sources():
        raise ValueError("Clock qualification belongs to a different source or server")
    if q.get("boot_id") != Path("/proc/sys/kernel/random/boot_id").read_text().strip() or q.get(
        "http_parent_start_ticks"
    ) != start_ticks(runtime["process_pid"]):
        raise ValueError("Clock qualification belongs to a different boot or server process")
    for name, digest in q.get("evidence_sha256", {}).items():
        evidence = path.parent / name
        if not evidence.resolve().is_relative_to(path.parent.resolve()) or sha(evidence) != digest:
            raise ValueError("Clock evidence changed: " + name)
    return q


def _local_server(url, runtime):
    if (
        urlparse(url).hostname not in ("127.0.0.1", "localhost", "::1")
        or runtime.get("backend") != "process"
        or runtime.get("mode") not in ("duel", "trio")
    ):
        raise ValueError("Clock qualification requires the local process-isolated duel server")
    command = Path(f"/proc/{runtime['process_pid']}/cmdline").read_bytes().split(b"\0")
    if not any(b"mcpkart.duel_web" in value for value in command):
        raise ValueError("Use the standard python -m mcpkart.duel_web server for the parent-pause check")
    if runtime.get("mode") == "trio" and b"--trio" not in command:
        raise ValueError("Trio qualification requires the standard --trio server")


def _worker_memory(parent_pid):
    result = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            args = (path / "cmdline").read_bytes().split(b"\0")
            if not any(module in args for module in (b"mcpkart.duel_worker", b"mcpkart.trio_worker")):
                continue
            fields = dict(
                line.split(":", 1) for line in (path / "status").read_text().splitlines() if ":" in line
            )
            if int(fields["PPid"]) != parent_pid:
                continue
            result.append(
                {
                    "pid": int(path.name),
                    "current_rss_kib": int(fields["VmRSS"].split()[0]),
                    "process_peak_rss_kib": int(fields["VmHWM"].split()[0]),
                }
            )
        except (OSError, KeyError, ValueError):
            continue
    return result


async def run(args):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    frozen = sources()
    ledger = Path(args.ledger)
    budget_before = sha(ledger) if ledger.exists() else None

    def check():
        if sources() != frozen:
            raise RuntimeError("Source changed during clock qualification")
        if (sha(ledger) if ledger.exists() else None) != budget_before:
            raise RuntimeError("Real model budget changed during a free qualification")

    setups = [
        {
            "course": "stadium",
            "grid": [
                {"distance_m": 0.0, "offset_m": -2.0, "heading_error_rad": 0.0},
                {"distance_m": 0.0, "offset_m": 2.0, "heading_error_rad": 0.0},
            ],
        },
        {
            "course": "stadium_clockwise",
            "grid": [
                {"distance_m": 0.0, "offset_m": 2.0, "heading_error_rad": 0.0},
                {"distance_m": 0.0, "offset_m": -2.0, "heading_error_rad": 0.0},
            ],
        },
        {
            "course": "stadium",
            "grid": [
                {"distance_m": 0.0, "offset_m": -1.0, "heading_error_rad": 0.0},
                {"distance_m": -3.0, "offset_m": 1.0, "heading_error_rad": 0.0},
            ],
        },
        {
            "course": "stadium_clockwise",
            "grid": [
                {"distance_m": -3.0, "offset_m": 1.0, "heading_error_rad": 0.0},
                {"distance_m": 0.0, "offset_m": -1.0, "heading_error_rad": 0.0},
            ],
        },
    ]
    trio = getattr(args, "trio", False)
    if trio:
        for index, setup in enumerate(setups):
            sign = -1 if setup["course"].endswith("clockwise") else 1
            setup.update(racer_ids=list(TRIO_RACERS), contact="ghost", grid=[
                {"distance_m": float(-3 * i if index >= 2 else 0),
                 "offset_m": sign * offset, "heading_error_rad": 0.0}
                for i, offset in enumerate((-4.0, 0.0, 4.0))
            ])
    async with Client(args.url, timeout=45) as mcp:
        runtime = await tool(mcp, "runtime_info")
        if runtime.get("mode") != ("trio" if trio else "duel"):
            raise ValueError("Clock qualification mode differs from the selected server")
        _local_server(args.url, runtime)
    plan = {
        "source_sha256": frozen,
        "runtime": runtime,
        "controls": 4,
        "setups": setups,
        "neutral_seconds": args.neutral_seconds,
        "model_requests": 0,
        "budget_before_sha256": budget_before,
        "created_utc": datetime.now(UTC).isoformat(),
        "helper_sha256": sha(__file__),
    }
    _write_new(output / "plan.json", plan)
    evidence = [output / "plan.json"]
    pause_samples = 0
    for index, setup in enumerate(setups):
        check()
        directory = output / f"control-{index}"
        result = await collect_duel(
            url=args.url,
            routes=mock_routes(
                ("typesafe/jev-1.14", "openai/gpt-6-luna-decisions", "cloudflare/clef"), TRIO_RACERS,
            ) if trio else mock_routes(),
            setup=setup,
            seed=301 + index,
            output=directory,
            budget=Budget(output / f"mock-budget-{index}.json"),
            free=True,
            label=f"FREE final clock control {index}",
            pause_parent=index == 1,
            admission=check,
            live_status_path=output.parent / "live-status.json",
        )
        check()
        if (
            result["errors"]
            or not result["summary"]["finished"]
            or any(r["resets"] or r["offroad_time"] for r in result["summary"]["racers"].values())
        ):
            raise RuntimeError("Free full-duel control failed; its evidence is preserved")
        proof = audit_duel(directory)
        _write_new(directory / "proof.json", proof)
        evidence.extend((directory / "proof.json", directory / "race.json"))
        pause_samples += result["pause"].get("physics_samples", 0)
        print(
            json.dumps(
                {
                    "control": index,
                    "passed": True,
                    "finish_times_s": result["summary"]["finish_times_s"],
                    "max_lateness_ms": result["timing"]["max_lateness_ms"],
                }
            ),
            flush=True,
        )
    memory = []
    check()
    async with Client(args.url, timeout=90) as mcp:
        initial = await tool(
            mcp,
            "start_duel",
            {
                "seed": 399,
                "deadline": args.neutral_seconds,
                "label": f"FREE {args.neutral_seconds:g}s neutral clock",
            },
        )
        last_memory = -30.0
        async with httpx.AsyncClient(timeout=3) as http:
            for _ in range(int(args.neutral_seconds / 0.2) + 150):
                response = await http.get(args.url.removesuffix("/mcp") + "/api/state")
                response.raise_for_status()
                state = response.json()
                elapsed = state["observation"]["time"]
                if elapsed - last_memory >= 30:
                    check()
                    sample = {"simulation_s": elapsed, "workers": _worker_memory(runtime["process_pid"])}
                    memory.append(sample)
                    last_memory = elapsed
                    print(json.dumps({"long_clock_progress": sample}), flush=True)
                if state["status"] != "running":
                    break
                await asyncio.sleep(0.2)
            else:
                raise RuntimeError("Finite neutral-clock observation limit exceeded")
        race = await tool(
            mcp, "finish_duel", {"race_id": initial["race_id"], "owner_token": initial["owner_token"]}
        )
    # Lossless masters remain available; compress this repetitive neutral trace.
    with gzip.open(output / "long-clock.json.gz", "xt", encoding="utf-8") as stream:
        json.dump(race, stream, separators=(",", ":"), allow_nan=False)
    _write_new(output / "memory-samples.json", memory)
    check()
    if race["summary"]["elapsed"] < args.neutral_seconds - 1e-6 or not race["timing"]["infrastructure_valid"]:
        raise RuntimeError("Neutral clock failed; recording is preserved")
    sim = DuelSimulation.from_config(race["config"])
    maximum_sample_late = 0.0
    for sample in race["samples"]:
        if sample["tick"]:
            sim.step()
        if sim.state()["racers"] != sample["racers"]:
            raise RuntimeError("Neutral physics replay differs")
        maximum_sample_late = max(
            maximum_sample_late, (sample["wall_ns"] - race["started_ns"]) / 1e6 - sample["tick"] * 1000 / 60
        )
    if maximum_sample_late > 100:
        raise RuntimeError("Neutral sample timing exceeds 100 ms")
    proof = {
        "passed": True,
        "exact_frames": len(race["samples"]),
        "seconds": race["summary"]["elapsed"],
        "timing": race["timing"],
        "worker_memory": race["worker_memory"],
        "max_sample_lateness_ms": maximum_sample_late,
    }
    _write_new(output / "long-proof.json", proof)
    evidence.extend(
        (output / "long-clock.json.gz", output / "long-proof.json", output / "memory-samples.json")
    )
    q = {
        "passed": True,
        "controls": 4,
        "long_clock_s": race["summary"]["elapsed"],
        "parent_pause_physics_samples": pause_samples,
        "source_sha256": frozen,
        "runtime": runtime,
        "http_parent_start_ticks": start_ticks(runtime["process_pid"]),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "model_requests": 0,
        "budget_unchanged": True,
        "evidence_sha256": {str(p.relative_to(output)): sha(p) for p in evidence},
        "created_utc": datetime.now(UTC).isoformat(),
    }
    _write_new(output / "qualification.json", q)
    print(
        json.dumps(
            {
                "complete_clock_gate": True,
                "controls": 4,
                "long_clock_s": q["long_clock_s"],
                "pause_samples": pause_samples,
                "worker_memory": race["worker_memory"],
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8766/mcp")
    parser.add_argument("--trio", action="store_true", help="Qualify four complete three-ghost-kart controls")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, default=Path("artifacts/budget.json"))
    parser.add_argument("--neutral-seconds", type=float, default=170.1)
    args = parser.parse_args()
    if not 170.1 <= args.neutral_seconds <= 600:
        parser.error("Neutral duration must be between 170.1 and 600 seconds")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
