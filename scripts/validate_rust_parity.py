"""Offline parity gate for the Rust worker; no wall-clock races or model calls.

Python generates the input schedule and full precision initial conditions. The
Rust replay must match every observation, raw state, summary, rescue and config.
Discrete values are exact; floating point values use a declared absolute error
bound with no relative allowance. This does not test runtime scheduling.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcpkart.rust_runtime import simulation_fixture
from mcpkart.sim import ACTIONS, DT, Simulation, scripted_action

DEFAULT_BINARY = Path(__file__).resolve().parents[1]/"rust-race/target/release/mcpkart-race"
ABSOLUTE_TOLERANCE = 1e-8
CONTINUOUS_NUMERIC_FIELDS = frozenset({"after_s", "reset_after_s"})


@dataclass
class Comparison:
    tolerance: float = ABSOLUTE_TOLERANCE
    checks: int = 0
    float_checks: int = 0
    failures: int = 0
    maximum_absolute_error: float = 0.0
    maximum_error_path: str | None = None
    differences: list[dict] = field(default_factory=list)

    def fail(self, path: str, expected: Any, actual: Any) -> None:
        self.failures += 1
        if len(self.differences) < 20:
            self.differences.append({"path": path, "expected": expected, "actual": actual})

    def compare(self, expected: Any, actual: Any, path: str = "$") -> None:
        self.checks += 1
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                self.fail(path, "object", type(actual).__name__)
                return
            if set(expected) != set(actual):
                self.fail(path+".keys", sorted(expected), sorted(actual))
            for key in expected:
                if key in actual:
                    self.compare(expected[key], actual[key], f"{path}.{key}")
        elif isinstance(expected, (list, tuple)):
            if not isinstance(actual, (list, tuple)):
                self.fail(path, "array", type(actual).__name__)
                return
            if len(expected) != len(actual):
                self.fail(path+".length", len(expected), len(actual))
            for index, (left, right) in enumerate(zip(expected, actual)):
                self.compare(left, right, f"{path}[{index}]")
        elif isinstance(expected, float) or (
            type(expected) is int and path.rsplit(".", 1)[-1] in CONTINUOUS_NUMERIC_FIELDS
        ):
            self.float_checks += 1
            if isinstance(actual, bool) or not isinstance(actual, (float, int)) or not math.isfinite(actual):
                self.fail(path, expected, actual)
                return
            error = abs(expected-actual)
            if error > self.maximum_absolute_error:
                self.maximum_absolute_error, self.maximum_error_path = error, path
            if not math.isfinite(expected) or error > self.tolerance:
                self.fail(path, expected, actual)
        elif type(expected) is not type(actual) or expected != actual:
            self.fail(path, expected, actual)

    def result(self) -> dict:
        return {"passes": self.failures == 0, "checks": self.checks,
                "float_checks": self.float_checks, "failures": self.failures,
                "maximum_absolute_error": self.maximum_absolute_error,
                "maximum_error_path": self.maximum_error_path, "differences": self.differences}


def snapshot(sim: Simulation) -> dict:
    return {"tick": sim.tick, "observation": sim.observation(),
            "raw_state": copy.deepcopy(simulation_fixture(sim)["initial_state"])}


def fixture_case(name: str, sim: Simulation, ticks: int,
                 action: Callable[[Simulation], str | None] | None = None) -> dict:
    fixture, samples, steps = copy.deepcopy(simulation_fixture(sim)), [snapshot(sim)], []
    for _ in range(ticks):
        selected = action(sim) if action is not None else None
        if selected is not None:
            sim.set_control(selected)
            steps.append({"tick": sim.tick+1, "action_id": selected})
        sim.step()
        samples.append(snapshot(sim))
        if sim.finished:
            break
    return {"name": name,
            "input": {"fixture": fixture, "ticks": len(samples)-1, "steps": steps},
            "expected": {"samples": samples, "summary": sim.summary(), "config": sim.config(),
                         "reset_events": [event.copy() for event in sim.reset_events]}}


def place(sim: Simulation, distance: float, lateral: float = 0.0) -> None:
    x, y, heading, _ = sim.track.at(distance)
    sim.x, sim.y = x-math.sin(heading)*lateral, y+math.cos(heading)*lateral
    sim.heading = heading
    sim.vx = sim.vy = sim.yaw_rate = sim.steering = 0.0
    sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)


def held_driver(delay_ticks: int) -> Callable[[Simulation], str | None]:
    due, pending = delay_ticks, None

    def select(sim: Simulation) -> str | None:
        nonlocal due, pending
        if pending is None:
            pending = scripted_action(sim.observation())
        if sim.tick != due:
            return None
        selected = pending
        due, pending = sim.tick+delay_ticks, scripted_action(sim.observation())
        return selected

    return select


def cases():
    for seed in (0, 1, 7, 42, 2**32+1):
        yield fixture_case(f"initial-seed-{seed}", Simulation(seed=seed), 0)
    scripted = Simulation()
    yield fixture_case("scripted-three-laps", scripted, 65*60,
                       lambda sim: scripted_action(sim.observation()))
    assert scripted.finished and scripted.checkpoints_passed == 120
    for ticks in (6, 12):
        held = Simulation()
        yield fixture_case(f"held-stale-{ticks}-ticks", held, 110*60, held_driver(ticks))
        assert held.finished and not held.reset_events
    actions = list(ACTIONS)
    yield fixture_case("all-fifteen-actions", Simulation(seed=7), 900,
                       lambda sim: actions[(sim.tick//7) % len(actions)])

    rescue = Simulation()
    place(rescue, 0, -8)
    rescue.set_control("hard_left_brake")
    yield fixture_case("default-rescue-and-neutral-hold", rescue, 240)
    assert len(rescue.reset_events) == 1 and rescue.speed == 0

    strict = Simulation(reset_after_s=None)
    place(strict, 0, -8)
    yield fixture_case("disabled-rescue", strict, 240)
    assert not strict.reset_events and strict.offroad_time > 3

    departure = Simulation(reset_after_s=3*DT)
    place(departure, 18)
    departure.departure_s = .2  # Exercise wrapping one metre behind departure.
    departure.x = departure.y = 1000.0
    departure.s, departure.offset, _ = departure.track.project(departure.x, departure.y)
    departure.next_checkpoint = 17
    departure.checkpoints_passed = 16
    yield fixture_case("rescue-wrap-preserves-progress", departure, 4)
    assert departure.reset_events and departure.checkpoints_passed == 16 and departure.next_checkpoint == 17

    for name, gate, reverse, lateral, finish in (
        ("forward-gate", 1, False, 0.0, False),
        ("reverse-gate", 1, True, 0.0, False),
        ("offroad-gate", 1, False, 5.0, False),
        ("skipped-gate", 2, False, 0.0, False),
        ("ordered-finish", 0, False, 0.0, True),
    ):
        sim = Simulation(laps=1)
        x, y, heading, _ = sim.track.checkpoints[gate]
        tx, ty = math.cos(heading), math.sin(heading)
        direction = -1 if reverse else 1
        sim.x, sim.y = x-direction*.05*tx-lateral*ty, y-direction*.05*ty+lateral*tx
        sim.heading = heading if not reverse else heading+math.pi
        sim.vx, sim.vy = direction*tx*10, direction*ty*10
        sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)
        if finish:
            sim.next_checkpoint, sim.checkpoints_passed = 0, 39
        yield fixture_case(name, sim, 1)
        assert sim.checkpoints_passed == (40 if finish else 1 if name == "forward-gate" else 0)
        assert sim.finished is finish


def recorded_case(path: Path) -> tuple[dict, dict]:
    trial = json.loads(path.read_text())
    race = trial.get("race", trial)
    sim = Simulation(seed=race["seed"], laps=race["config"]["laps"],
                     reset_after_s=race["config"]["rescue"]["after_s"])
    commands = {row["applied_tick"]: row["action_id"] for row in race["commands"]}
    case = fixture_case("saved-"+path.parent.name, sim, race["samples"][-1]["tick"],
                        lambda state: commands.get(state.tick+1))
    proof = Comparison()
    proof.compare(len(race["samples"]), len(case["expected"]["samples"]), "recording.samples.length")
    for recorded, expected in zip(race["samples"], case["expected"]["samples"]):
        observation = expected["observation"]
        for key in ("tick", "kart", "progress", "control", "rescue"):
            proof.compare(recorded[key], observation[key], f"recording.tick{recorded['tick']}.{key}")
        proof.compare(recorded["time"], expected["raw_state"]["elapsed"], "recording.elapsed")
    expected_summary = case["expected"]["summary"]
    proof.compare({key: race["summary"][key] for key in expected_summary}, expected_summary, "recording.summary")
    return case, {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), **proof.result()}


def validate_case(binary: Path, case: dict, tolerance: float) -> dict:
    with tempfile.TemporaryDirectory(prefix="mcpkart-rust-parity-") as directory:
        source = Path(directory)/"fixture.json"
        source.write_text(json.dumps(case["input"], allow_nan=False))
        result = subprocess.run([str(binary), "--replay", str(source)], capture_output=True,
                                text=True, check=True, timeout=60)
    actual = json.loads(result.stdout)
    proof = Comparison(tolerance)
    proof.compare(case["expected"], actual)
    return {"name": case["name"], "ticks": case["input"]["ticks"], **proof.result()}


def run(binary: Path, output: Path, recordings: list[Path], tolerance: float) -> dict:
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError(f"Build the release Rust worker first; executable missing: {binary}")
    if output.exists():
        raise ValueError(f"Refusing to overwrite parity evidence: {output}")
    report = {"passes": False, "mode": "offline-replay", "absolute_float_tolerance": tolerance,
              "relative_float_tolerance": 0, "discrete_values": "exact value and JSON type",
              "binary": str(binary), "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "model_requests": 0, "cases": [], "recordings": []}
    try:
        for case in cases():
            report["cases"].append(validate_case(binary, case, tolerance))
        for path in recordings:
            case, recorded = recorded_case(path)
            report["recordings"].append(recorded)
            report["cases"].append(validate_case(binary, case, tolerance))
        report["passes"] = all(case["passes"] for case in report["cases"]+report["recordings"])
        return report
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path,
                        default=Path(os.environ.get("MCPKART_RUST_WORKER", DEFAULT_BINARY)))
    parser.add_argument("--output", type=Path, default=Path("artifacts/rust-clock-v1/parity.json"))
    parser.add_argument("--recording", type=Path, action="append", default=[])
    parser.add_argument("--absolute-tolerance", type=float, default=ABSOLUTE_TOLERANCE)
    args = parser.parse_args()
    if not math.isfinite(args.absolute_tolerance) or args.absolute_tolerance <= 0:
        parser.error("Absolute tolerance must be positive and finite")
    report = run(args.binary.resolve(), args.output, args.recording, args.absolute_tolerance)
    print(json.dumps({"passes": report["passes"], "cases": len(report["cases"]),
                      "checks": sum(row["checks"] for row in report["cases"]),
                      "failures": sum(row["failures"] for row in report["cases"]),
                      "output": str(args.output)}))
    raise SystemExit(0 if report["passes"] else 1)


if __name__ == "__main__":
    main()
