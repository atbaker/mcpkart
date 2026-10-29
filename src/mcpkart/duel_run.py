"""Run one recorded two-kart match, with free mode or explicit paid admission."""

from __future__ import annotations

import argparse
import asyncio
import fcntl
import json
from pathlib import Path

from fastmcp import Client

from .bench import tool
from .decisions import Budget, discover_routes, load_api_key
from .duel import RACERS, TRIO_RACERS, DuelSimulation
from .duel_bench import audit_duel, collect_duel, sources
from .duel_clock import mock_routes, validate_qualification
from .question_context_driver import _read, _safe, _write_new

MODELS = ("typesafe/jev-1.14", "openai/gpt-6-luna-decisions", "cloudflare/clef")
DEFAULT_REPLAY_ROOT = Path(__file__).resolve().parents[2] / "artifacts" / "two-kart-session-v1"


def existing_budget(path):
    state = _read(path)
    if state.get("schema_version") != 1 or state.get("pending"):
        raise ValueError("An existing cumulative ledger with no pending reservation is required")
    if not (
        0 <= state["charged_usd"] <= state["cap_usd"] <= 20
        and 1 <= state["max_requests"] <= 110000
        and 1 <= state["max_tokens"] <= 500000000
        and 0 <= state["requests"] <= state["max_requests"]
        and 0 <= state["charged_tokens"] <= state["max_tokens"]
    ):
        raise ValueError("Ledger exceeds the current authorized caps or is exhausted")
    if (
        state["max_requests"] - state["requests"] < 1000
        or state["max_tokens"] - state["charged_tokens"] < 5000000
    ):
        raise ValueError("The 1000-request / 5-million-token admission floor is unavailable")
    return Budget(
        path, cap_usd=state["cap_usd"], max_requests=state["max_requests"], max_tokens=state["max_tokens"]
    )


def setup(course, grid):
    sign = 1 if course == "stadium" else -1
    positions = [(0, -2 * sign), (0, 2 * sign)] if grid == "side" else [(0, -sign), (-3, sign)]
    return {
        "course": course,
        "grid": [
            {"distance_m": float(distance), "offset_m": float(offset), "heading_error_rad": 0.0}
            for distance, offset in positions
        ],
    }


async def run(args):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    source = sources()
    racers = TRIO_RACERS if len(args.models) == 3 else RACERS
    race_setup = setup(args.course, args.grid)
    if racers == TRIO_RACERS:
        sign = 1 if args.course == "stadium" else -1
        race_setup.update(racer_ids=list(racers), contact="ghost", grid=[
            {"distance_m": 0.0, "offset_m": sign * o, "heading_error_rad": 0.0}
            for o in (-4.0, 0.0, 4.0)
        ])
        if not args.free:
            raise ValueError("Paid trio admission requires the new demo qualification and registration")
    DuelSimulation(seed=args.seed, **race_setup)
    key, writer = None, None
    try:
        if args.free:
            budget = Budget(output / "mock-budget.json")
            routes = mock_routes(args.models, racers)
        else:
            if args.clock_qualification is None:
                raise ValueError("Paid mode requires --clock-qualification")
            key = load_api_key()
            writer = (Path(args.ledger).parent / "root-paid-writer.lock").open("a")
            fcntl.flock(writer.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            budget = existing_budget(args.ledger)
        async with Client(args.url, timeout=45) as mcp:
            runtime = await tool(mcp, "runtime_info")
        if not args.free:
            qualification = validate_qualification(args.clock_qualification, runtime)
            pinned = await discover_routes(models=list(dict.fromkeys(args.models)))
            by_model = {route["model"]: route for route in pinned}
            routes = {r: by_model[m] for r, m in zip(racers, args.models, strict=True)}
            files = [Path(args.clock_qualification)] + [
                Path(args.clock_qualification).parent / name for name in qualification["evidence_sha256"]
            ]
            bound = {p: (p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns) for p in files}
        else:
            bound = {}
        _write_new(
            output / "registration.json",
            {
                "scope": "One explicit match, no retries or replacement races",
                "free": args.free,
                "models": list(args.models),
                "routes": routes,
                "seed": args.seed,
                "setup": race_setup,
                "deadline_s": args.deadline,
                "max_decisions_per_racer": args.max_decisions,
                "source_sha256": source,
                "runtime": runtime,
                "budget_start": budget.summary(),
            },
        )

        def admit():
            if sources() != source:
                raise RuntimeError("Source changed before the next native request")
            for path, identity in bound.items():
                stat = path.stat()
                if (stat.st_ino, stat.st_size, stat.st_mtime_ns) != identity:
                    raise RuntimeError("Clock qualification evidence changed")

        result = await collect_duel(
            url=args.url,
            routes=routes,
            setup=race_setup,
            seed=args.seed,
            output=output / "trial",
            budget=budget,
            free=args.free,
            deadline=args.deadline,
            max_decisions=args.max_decisions,
            admission=admit,
            label="Scripted practice" if args.free else " vs ".join(args.models),
            live_status_path=args.live_status,
        )
        proof = (
            audit_duel(output / "trial")
            if not result["errors"] and result["timing"]["infrastructure_valid"]
            else None
        )
        receipt = {
            "collection_complete": True,
            "free": args.free,
            "summary": result["summary"],
            "metrics": result["metrics"],
            "errors": result["errors"],
            "spectator_warnings": result["spectator_warnings"],
            "audit": proof,
            "budget_after": budget.summary(),
        }
        _write_new(output / "receipt.json", receipt)
        print(
            json.dumps(
                {
                    "finished": result["summary"]["finished"],
                    "free": args.free,
                    "finish_times_s": result["summary"]["finish_times_s"],
                    "errors": result["errors"],
                    "audit_passed": bool(proof),
                    "recording": str(output / "trial/race.json"),
                }
            ),
            flush=True,
        )
        return 0 if proof else 1
    except BaseException as error:
        _write_new(
            output / "failure.json",
            {"error": type(error).__name__, "detail": _safe(str(error), key), "no_automatic_retry": True},
        )
        raise
    finally:
        if writer is not None:
            writer.close()


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--free", action="store_true", help="Scripted mock; no model key or paid request")
    mode.add_argument(
        "--paid", action="store_true", help="One paid match under an existing ledger and clock gate"
    )
    p.add_argument(
        "--models",
        nargs="+",
        default=("jev", "jev"),
        choices=("jev", "openai", "clef", *MODELS),
        metavar="MODEL",
    )
    p.add_argument("--url", default="http://127.0.0.1:8766/mcp")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--ledger", type=Path, default=Path("artifacts/budget.json"))
    p.add_argument("--clock-qualification", type=Path)
    p.add_argument(
        "--live-status",
        type=Path,
        default=DEFAULT_REPLAY_ROOT / "live-status.json",
        help="Use the spectator replay-root/live-status.json for live model labels",
    )
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--course", choices=("stadium", "stadium_clockwise"), default="stadium")
    p.add_argument("--grid", choices=("side", "staggered"), default="side")
    p.add_argument("--deadline", type=float, default=240.0)
    p.add_argument("--max-decisions", type=int, default=1100)
    return p


def main():
    p = parser()
    args = p.parse_args()
    if args.paid and args.clock_qualification is None:
        p.error("--paid requires --clock-qualification")
    if not 0 < args.deadline <= 600:
        p.error("Deadline must be positive and at most 600 seconds")
    if not 1 <= args.max_decisions <= 5000:
        p.error("Decision ceiling must be between 1 and 5000 per racer")
    if len(args.models) not in (2, 3):
        p.error("--models requires two or three models")
    aliases = {"jev": MODELS[0], "openai": MODELS[1], "clef": MODELS[2]}
    args.models = tuple(aliases.get(model, model) for model in args.models)
    raise SystemExit(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
