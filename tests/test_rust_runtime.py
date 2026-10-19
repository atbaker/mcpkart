"""Native worker protocol and parity checks; no benchmark or model requests."""

import asyncio
import os
import time
from pathlib import Path

import pytest

from mcpkart import rust_runtime
from mcpkart.rust_runtime import RUST_CLOCK_MODE, RustRaceRuntime, simulation_fixture
from mcpkart.sim import Simulation
from scripts.validate_rust_parity import Comparison, fixture_case, place


@pytest.fixture
def rust_binary():
    default = Path(__file__).resolve().parents[1]/"rust-race/target/release/mcpkart-race"
    binary = Path(os.environ.get("MCPKART_RUST_WORKER", default)).resolve()
    if not binary.is_file() or not os.access(binary, os.X_OK):
        pytest.skip("Release Rust worker is not built; tests never build it implicitly")
    return binary


def test_parity_comparison_keeps_discrete_values_exact_and_uses_only_absolute_tolerance():
    proof = Comparison()
    proof.compare({"tick": 1, "finished": False, "x": 1e8},
                  {"tick": 1.0, "finished": 0, "x": 1e8+.001})
    assert proof.failures == 3  # A relative tolerance would hide the large-coordinate drift.
    accepted = Comparison()
    accepted.compare({"x": 2.0}, {"x": 2.0+1e-9})
    assert accepted.result()["passes"]
    missing = Comparison()
    missing.compare({"resets": [], "tick": 0}, {"tick": 0})
    assert missing.failures == 1


def test_parity_comparison_treats_rescue_seconds_as_continuous_but_not_ticks_or_booleans():
    continuous = Comparison()
    continuous.compare({"rescue": {"after_s": 3}, "initial_state": {"reset_after_s": 3}},
                       {"rescue": {"after_s": 3.0}, "initial_state": {"reset_after_s": 3.0+1e-9}})
    assert continuous.result()["passes"] and continuous.float_checks == 2
    invalid = Comparison()
    invalid.compare({"after_s": 3, "reset_after_s": 3, "tick": 3, "finished": False},
                    {"after_s": 3.001, "reset_after_s": True, "tick": 3.0, "finished": 0})
    assert invalid.failures == 4


def test_fixture_preserves_unrounded_initial_conditions_and_independent_history():
    sim = Simulation(seed=7, reset_after_s=.05)
    place(sim, 0, -8)
    initial = simulation_fixture(sim)
    assert initial["initial_state"]["x"] == sim.x
    assert initial["track"]["points"] == sim.track.points
    assert initial["track"]["width"] == sim.track.width
    assert initial["handling"]["max_speed"] == sim.handling.max_speed
    case = fixture_case("test-rescue", sim, 4)
    assert not case["input"]["fixture"]["initial_state"]["reset_events"]
    assert not case["expected"]["samples"][0]["raw_state"]["reset_events"]
    assert case["expected"]["summary"]["resets"] == 1


@pytest.mark.asyncio
async def test_rust_worker_applies_held_inputs_and_replays_samples_after_parent_block(rust_binary):
    runtime = RustRaceRuntime(binary=rust_binary)
    try:
        start_submitted = time.monotonic_ns()
        initial = await runtime.start(deadline=.2, label="Native protocol check")
        start_received = time.monotonic_ns()
        assert start_submitted <= initial["observed_ns"] <= start_received
        submitted = time.monotonic_ns()
        ack = await runtime.drive(initial["race_id"], "straight_accelerate", initial["tick"], 0)
        received = time.monotonic_ns()
        assert ack["applied"] and ack["applied_tick"] > initial["tick"]
        assert submitted <= ack["queued_ns"] <= ack["applied_ns"] <= ack["observation"]["observed_ns"] <= received
        time.sleep(.06)  # noqa: ASYNC251 — test only: the parent cannot own the Rust clock.
        observed = await runtime.observe(initial["race_id"])
        assert observed["tick"] >= ack["applied_tick"]+3
        assert observed["control"] == "straight_accelerate"
        assert observed["kart"]["speed"] > ack["observation"]["kart"]["speed"]
        with pytest.raises(ValueError, match="Stop the race"):
            await runtime.result()
        with pytest.raises(ValueError, match="out-of-order"):
            await runtime.drive(initial["race_id"], "straight_brake", observed["tick"], 0)
        result = await runtime.finish(reason="test_finished")
        assert start_submitted <= result["started_ns"] <= initial["observed_ns"] <= start_received
        assert result["runtime_info"]["engine"] == "rust"
        assert result["runtime_info"]["clock_mode"] == result["timing"]["clock_mode"] == RUST_CLOCK_MODE
        assert result["process_provenance"]["child_pid"] != os.getpid()
        assert result["process_provenance"]["child_web_modules_loaded"] == []
        assert runtime._session is None
        sim = Simulation(seed=result["seed"], laps=result["config"]["laps"],
                         reset_after_s=result["config"]["rescue"]["after_s"])
        commands = {row["applied_tick"]: row["action_id"] for row in result["commands"]}
        proof = Comparison()
        for sample in result["samples"]:
            if sample["tick"]:
                if sample["tick"] in commands:
                    sim.set_control(commands[sample["tick"]])
                sim.step()
            observation = sim.observation()
            for key in ("kart", "progress", "control", "rescue"):
                proof.compare(observation[key], sample[key], f"tick{sample['tick']}.{key}")
            proof.compare(sim.elapsed, sample["time"], f"tick{sample['tick']}.time")
        assert not proof.failures, proof.differences
        late = await runtime.drive(initial["race_id"], "hard_left_accelerate", 0, 1)
        assert not late["applied"] and late["reason"] == "race_already_ended"
        assert await runtime.finish() == result
    finally:
        await runtime.close()
        await runtime.close()


@pytest.mark.asyncio
async def test_rust_worker_rescue_rejects_old_observation_without_consuming_sequence(rust_binary, monkeypatch):
    class OffroadSimulation(Simulation):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            place(self, 0, -8)

    monkeypatch.setattr(rust_runtime, "Simulation", OffroadSimulation)
    runtime = RustRaceRuntime(binary=rust_binary)
    try:
        initial = await runtime.start(deadline=.2, reset_after_s=.05)
        await runtime.drive(initial["race_id"], "hard_left_brake", initial["tick"], 0)
        await asyncio.sleep(.065)
        rescued = await runtime.observe()
        assert rescued["rescue"]["count"] == 1
        assert rescued["kart"]["speed"] == 0 and rescued["control"] == "straight_coast"
        stale = await runtime.drive(initial["race_id"], "straight_accelerate", initial["tick"], 1)
        assert not stale["applied"] and stale["reason"] == "observation_before_rescue"
        fresh = await runtime.drive(initial["race_id"], "straight_accelerate", stale["observation"]["tick"], 1)
        assert fresh["applied"]
        result = await runtime.finish()
        assert result["rejected_commands"][0]["reason"] == "observation_before_rescue"
        assert result["reset_events"][0]["control"] == "straight_coast"
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_rust_worker_deadline_collection_and_new_race_identity(rust_binary):
    runtime = RustRaceRuntime(binary=rust_binary)
    try:
        old = await runtime.start(deadline=.04)
        await asyncio.sleep(.07)
        assert (await runtime.observe())["status"] == "failed"
        result = await runtime.result()
        assert result["reason"] == "deadline" and runtime._session is None
        new = await runtime.start(seed=1, deadline=.1)
        with pytest.raises(ValueError, match="Stale race_id"):
            await runtime.drive(old["race_id"], "straight_accelerate", old["tick"], 0)
        applied = await runtime.drive(new["race_id"], "straight_accelerate", new["tick"], 0)
        assert applied["applied"] and applied["observation"]["race_id"] == new["race_id"]
        await runtime.finish()
    finally:
        await runtime.close()
