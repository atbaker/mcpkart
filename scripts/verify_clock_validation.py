"""Verify saved free-clock gates and final worker identity without starting work."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from mcpkart.bench import fingerprint

CLOCK_MODES = {"python": "fixed_step_wall_clock", "rust": "rust_fixed_step_wall_clock"}
LIMITS = {"max_lateness": 100, "p95_lateness": 25, "absolute_drift": 100}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_race(race: dict, expected_info: dict, engine: str, label: str) -> None:
    mode = CLOCK_MODES[engine]
    module = "mcpkart.physics_worker" if engine == "python" else "mcpkart-rust-worker"
    for info in (expected_info, race["runtime_info"]):
        require(info["backend"] == "process" and info.get("engine", "python") == engine,
                f"{label}: wrong engine/backend")
        require(info["clock_mode"] == mode and info["physics_hz"] == 60,
                f"{label}: wrong clock mode/frequency")
        require(info["watchdog_enabled"] is False, f"{label}: watchdog enabled")
        require(info["process_pid"] == expected_info["process_pid"] > 1,
                f"{label}: HTTP parent identity changed")
    provenance, timing = race["process_provenance"], race["timing"]
    require(provenance["worker_module"] == module and provenance["child_clock_mode"] == mode,
            f"{label}: wrong final worker provenance")
    require(provenance["child_web_modules_loaded"] == [], f"{label}: web modules in physics child")
    require(provenance["parent_pid"] == expected_info["process_pid"]
            and provenance["child_pid"] > 1 and provenance["child_pid"] != provenance["parent_pid"],
            f"{label}: physics did not run in a distinct child")
    require(timing["process_provenance"] == provenance, f"{label}: timing provenance mismatch")
    require(timing["clock_mode"] == mode and timing["backend"] == "process"
            and timing["physics_hz"] == 60, f"{label}: wrong final timing clock")
    require(timing["validity_limits_ms"] == LIMITS, f"{label}: timing limits changed")
    require(timing["infrastructure_valid"] and race["realtime_valid"], f"{label}: timing gate failed")
    for key, limit in (("max_lateness_ms", 100), ("p95_lateness_ms", 25), ("drift_ms", 100)):
        require(math.isfinite(timing[key]) and abs(timing[key]) <= limit,
                f"{label}: {key} exceeds timing limit")


def verify(directory: Path, engine: str = "python") -> dict:
    require(engine in CLOCK_MODES, "Unknown engine")
    controls = json.loads((directory / "controls/validation.json").read_text())
    require(controls["passes"] and controls["source_unchanged"] and controls["model_requests"] == 0,
            "Scripted controls did not pass")
    require(len(controls["controls"]) == controls["required_consecutive_controls"] == 3,
            "Exactly three consecutive controls are required")
    require(controls["expected_clock_mode"] == CLOCK_MODES[engine], "Control clock mode changed")
    require(controls["validity_limits_ms"] == LIMITS, "Control timing limits changed")
    source = fingerprint()
    for index, row in enumerate(controls["controls"], 1):
        label = f"Control {index}"
        trial = json.loads((directory / f"controls/run-{index:02d}/scripted-live.json").read_text())
        race = trial["race"]
        require(row["passes"] and row["spectator_polls"] > 0, f"{label}: control gate failed")
        require(trial["fingerprint"] == row["fingerprint"] == source, f"{label}: source changed")
        require(not trial["runtime_mismatches"] and trial["collection_complete"],
                f"{label}: recording incomplete or runtime changed")
        require(race["summary"]["finished"] and race["summary"]["checkpoints_passed"] == 120,
                f"{label}: three-lap race did not finish")
        verify_race(race, controls["runtime_info"], engine, label)
        if index == 2:
            pause = row["parent_pause"]
            require(pause["race_id"] == race["race_id"]
                    and pause["parent_pid"] == controls["runtime_info"]["process_pid"],
                    "Parent pause targeted the wrong race or process")
            require(pause["signals"] == ["SIGSTOP", "SIGCONT"]
                    and abs(pause["requested_duration_s"] - .35) < 1e-6,
                    "Declared parent pause changed")
            samples = [sample for sample in race["samples"]
                       if pause["started_ns"] <= sample["wall_ns"] <= pause["ended_ns"]]
            require(len(samples) == pause["physics_samples_during_parent_pause"] >= 12,
                    "Insufficient actual child samples during parent pause")
    long = json.loads((directory / "long-clock.json").read_text())
    require(long["passes"] and long["model_requests"] == 0 and long["fingerprint"] == source,
            "Long clock check failed or source changed")
    require(not long["runtime_mismatches"] and long["trial_error"] is None
            and long["collection_error"] is None, "Long clock recording incomplete or runtime changed")
    require(abs(long["required_duration_s"] - 170.1) < 1e-6
            and long["race"]["reason"] == "deadline"
            and long["race"]["summary"]["elapsed"] >= 170.1 - 1e-6,
            "Full 170.1 second clock check required")
    verify_race(long["race"], long["runtime_info"], engine, "Long clock")
    return {"passes": True, "engine": engine, "clock_mode": CLOCK_MODES[engine],
            "controls": 3, "long_clock_s": long["race"]["summary"]["elapsed"],
            "fingerprint": source, "model_requests": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--engine", choices=tuple(CLOCK_MODES), default="python")
    args = parser.parse_args()
    try:
        result = verify(args.directory, args.engine)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"passes": False, "error": str(error)}))
        raise SystemExit(1) from error
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
