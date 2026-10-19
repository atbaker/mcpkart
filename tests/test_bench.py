import argparse
import asyncio
import copy
import json
import math
from typing import ClassVar

import pytest

from mcpkart.bench import percentiles, reference_trial, summarize_batch

RUNTIME_INFO = {
    "backend": "process",
    "protocol_version": 1,
    "watchdog_enabled": True,
    "clock_mode": "fixed_step_wall_clock",
    "physics_hz": 60,
}


def report(finished=True, valid=True, ratio=1.5):
    return {
        "model": "test/model",
        "metrics": {
            "finished": finished,
            "realtime_valid": valid,
            "time_ratio": ratio if finished else None,
            "cost_usd": 0.01,
        },
    }


def test_passing_batch_preserves_failure_denominator_and_rejects_partial_samples():
    rows = [report() for _ in range(8)] + [report(finished=False), report(valid=False)]
    summary = summarize_batch(rows)["models"][0]
    assert summary["completed"] == 8 and summary["trials"] == 10
    assert summary["passes"]
    assert not summarize_batch(rows[:8])["models"][0]["passes"]
    assert not summarize_batch([report(ratio=2.1) for _ in range(10)])["models"][0]["passes"]


def test_small_latency_samples_do_not_claim_a_p99():
    assert percentiles([100, 200, 300])["p99"] is None
    assert percentiles([100, 200, 300])["p50"] == 200


def test_injected_delay_includes_physics_application_boundary():
    result = reference_trial(seed=0, delay=0.2, deadline=0.5)
    assert result["observation_age_ms"]["n"] == 2
    assert math.isclose(result["observation_age_ms"]["p50"], 200 + 1000 / 60)
    assert math.isclose(result["action_interval_ms"]["p50"], 200 + 1000 / 60)


def test_assisted_completions_do_not_count_as_unassisted_passes():
    trials = [report() for _ in range(10)]
    for trial in trials:
        trial["metrics"].update(rescues=2, rescue_after_s=3)
    result = summarize_batch(trials)["models"][0]
    assert result["passes"] and not result["strict_passes"]
    assert result["completed_without_rescue"] == 0
    assert result["total_rescues"] == 20


def test_three_failures_rule_out_eight_of_ten_without_claiming_ten_observations():
    result = summarize_batch([report(finished=False) for _ in range(3)])["models"][0]
    assert result["trials"] == 3 and not result["complete_batch"]
    assert result["completion_target_ruled_out"] and not result["passes"]
    result = summarize_batch([report(), report(finished=False), report(finished=False)])["models"][0]
    assert not result["completion_target_ruled_out"]


@pytest.mark.asyncio
async def test_trial_records_starting_source_even_when_files_change_during_a_request(monkeypatch, tmp_path):
    from mcpkart import bench
    from mcpkart.sim import Simulation

    versions = iter(["source-at-start", "source-at-end"])
    monkeypatch.setattr(bench, "fingerprint", lambda: next(versions))
    initial = {**Simulation().observation(), "observed_ns": 1, "race_id": "test", "status": "running"}

    async def fake_tool(client, name, arguments=None):
        if name == "runtime_info":
            return copy.deepcopy(RUNTIME_INFO)
        if name == "start_race":
            assert "telemetry=road" in arguments["label"]
            return initial
        if name == "observe":
            return {**initial, "finished": True}
        return {"summary": {"finished": False, "elapsed": 0.1}}

    class Driver:
        instructions = "Exact starting instruction text"
        criteria: ClassVar[dict[str, str]] = {"straight_accelerate": "Exact starting action description"}

        async def decide(self, route, evidence):
            assert "road" in evidence and "track" not in evidence
            return {"ok": False, "latency_ms": 10, "cost": 0}

    monkeypatch.setattr(bench, "tool", fake_tool)
    result = await bench.run_trial(
        None, Driver(), {"model": "test/model"}, 0, 56.7, tmp_path / "trial.json", telemetry="road"
    )
    assert result["fingerprint"] == "source-at-start"
    assert result["telemetry"] == "road"
    assert result["instructions"] == Driver.instructions
    assert result["action_criteria"] == Driver.criteria


@pytest.fixture
def resumable_trial(monkeypatch):
    from mcpkart import bench
    from mcpkart.sim import Simulation

    monkeypatch.setattr(bench, "fingerprint", lambda: "frozen-source")
    route = {
        "model": "test/model",
        "provider": "pinned",
        "provider_name": "Pinned",
        "resolved_model": "test/canonical",
        "endpoint_name": "Pinned endpoint",
        "price_input_per_token": 0.00001,
        "price_output_per_token": 0,
        "price_per_request": 0,
        "context_length": 10000,
        "max_prompt_tokens": 9000,
        "max_completion_tokens": 1,
        "canonical_version_pinned": False,
        "catalog_observed_at": "old catalog timestamp",
    }
    arguments = {
        "route": route,
        "seed": 0,
        "baseline": 56.7,
        "telemetry": "compact",
        "control_language": "explicit",
        "instruction_style": "driving_guide",
        "instructions": "Exact saved guide",
        "action_criteria": {"straight_accelerate": "Accelerate"},
        "runtime_info": copy.deepcopy(RUNTIME_INFO),
    }
    saved = {
        "fingerprint": "frozen-source",
        "model": route["model"],
        "seed": 0,
        "route": copy.deepcopy(route),
        "telemetry": "compact",
        "control_language": "explicit",
        "instruction_style": "driving_guide",
        "instructions": arguments["instructions"],
        "action_criteria": copy.deepcopy(arguments["action_criteria"]),
        "runtime_info": copy.deepcopy(RUNTIME_INFO),
        "race": {"config": Simulation(reset_after_s=bench.RESET_AFTER_S).config(), "deadline": 56.7 * 3},
        "metrics": {"reference_s": 56.7},
    }
    return saved, arguments


def test_resume_accepts_identical_experiment_and_ignores_unused_catalog_metadata(resumable_trial):
    from mcpkart.bench import validate_resume

    saved, arguments = resumable_trial
    validate_resume(saved, **arguments)
    arguments["route"]["catalog_observed_at"] = "new catalog timestamp"
    arguments["route"]["catalog_entry"] = {"irrelevant_display_name": "Updated"}
    validate_resume(saved, **arguments)


@pytest.mark.parametrize(
    "path,value,message",
    [
        (("race", "config", "handling", "max_speed"), 99, "simulation or rescue"),
        (("race", "config", "rescue", "after_s"), None, "simulation or rescue"),
        (("race", "config", "track", "width"), 10, "simulation or rescue"),
        (("metrics", "reference_s"), 57, "paired reference duration"),
        (("race", "deadline"), 171, "trial deadline"),
        (("route", "provider"), "other", "pinned route"),
        (("route", "resolved_model"), "test/new-canonical", "pinned route"),
        (("route", "price_input_per_token"), 0.00002, "pinned route"),
        (("instructions",), "A changed guide", "exact instructions"),
        (("action_criteria", "straight_accelerate"), "Changed description", "exact action criteria"),
        (("fingerprint",), "new-source", "source configuration"),
    ],
)
def test_resume_rejects_experiment_changes_even_when_source_is_unchanged(
    resumable_trial, path, value, message
):
    from mcpkart.bench import validate_resume

    saved, arguments = resumable_trial
    parent = saved
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    with pytest.raises(ValueError, match=message):
        validate_resume(saved, **arguments)


@pytest.mark.asyncio
async def test_live_history_uses_only_prior_driver_observations_and_clears_after_rescue(
    monkeypatch, tmp_path
):
    from mcpkart import bench
    from mcpkart.sim import Simulation

    frames = []
    for tick in (0, 12, 24, 36):
        raw = Simulation().observation()
        raw.update(
            tick=tick,
            time=tick / 60,
            observed_ns=tick + 1,
            race_id="history-test",
            status="running" if tick < 36 else "finished",
        )
        if tick >= 24:
            raw["rescue"].update(count=1, last_reset_tick=24)
            raw["progress"]["resets"] = 1
        frames.append(raw)
    replies = iter(frames[1:])
    seen = []

    async def fake_tool(client, name, arguments=None):
        if name == "runtime_info":
            return copy.deepcopy(RUNTIME_INFO)
        if name == "start_race":
            return frames[0]
        if name == "drive":
            return {"observation": next(replies), "applied": True}
        return {"summary": {"finished": False, "elapsed": 0.6}}

    class Driver:
        async def decide(self, route, evidence):
            seen.append(copy.deepcopy(evidence))
            return {"ok": True, "action": "straight_accelerate", "latency_ms": 10, "cost": 0}

    monkeypatch.setattr(bench, "tool", fake_tool)
    report = await bench.run_trial(
        None, Driver(), {"model": "test/model"}, 0, 56.7, tmp_path / "history.json", telemetry="road_history"
    )
    samples = [item["history"]["recent_motion"]["samples"] for item in seen]
    assert [sample["tick"] for sample in samples[1]] == [0]
    assert samples[0] == samples[2] == []
    assert all(
        sample["tick"] < item["tick"]
        for item in seen
        for sample in item["history"]["recent_motion"]["samples"]
    )
    assert report["requests"][1]["observation"]["history"] == seen[1]["history"]


def test_resume_rejects_new_rescue_cli_setting_and_unverifiable_old_configuration(
    resumable_trial, monkeypatch
):
    from mcpkart import bench

    saved, arguments = resumable_trial
    monkeypatch.setattr(bench, "RESET_AFTER_S", None)
    with pytest.raises(ValueError, match="simulation or rescue"):
        bench.validate_resume(saved, **arguments)
    saved["race"].pop("config")
    with pytest.raises(ValueError, match="simulation or rescue"):
        bench.validate_resume(saved, **arguments)


@pytest.mark.parametrize(
    "field,value",
    [
        ("backend", "event_loop"),
        ("watchdog_enabled", False),
        ("clock_mode", "manual_clock"),
        ("physics_hz", 30),
        ("protocol_version", 2),
    ],
)
def test_resume_rejects_runtime_changes_even_with_identical_source(resumable_trial, field, value):
    from mcpkart.bench import validate_resume

    saved, arguments = resumable_trial
    arguments["runtime_info"][field] = value
    with pytest.raises(ValueError, match="runtime"):
        validate_resume(saved, **arguments)


def test_resume_runtime_guard_requires_current_and_saved_provenance_but_ignores_pids(resumable_trial):
    from mcpkart.bench import validate_resume

    saved, arguments = resumable_trial
    saved["runtime_info"].update(worker_pid=123, parent_pid=124, observed_at="previous")
    arguments["runtime_info"].update(worker_pid=456, parent_pid=457, observed_at="current")
    validate_resume(saved, **arguments)
    saved["runtime_info"].pop("clock_mode")
    with pytest.raises(ValueError, match="runtime_info fields"):
        validate_resume(saved, **arguments)
    saved["runtime_info"] = copy.deepcopy(RUNTIME_INFO)
    arguments.pop("runtime_info")
    with pytest.raises(ValueError, match="without current runtime_info"):
        validate_resume(saved, **arguments)


def test_resume_checks_child_backend_evidence_independently_of_saved_preflight(resumable_trial):
    from mcpkart.bench import validate_resume

    saved, arguments = resumable_trial
    saved["race"]["runtime_info"] = {**RUNTIME_INFO, "worker_pid": 999}
    saved["race"]["timing"] = {"backend": "process"}
    validate_resume(saved, **arguments)
    saved["race"]["timing"]["backend"] = "event_loop"
    with pytest.raises(ValueError, match="inconsistent final runtime provenance"):
        validate_resume(saved, **arguments)


@pytest.mark.parametrize("module", ["process_runtime.py", "physics_worker.py"])
def test_process_runtime_source_is_part_of_benchmark_fingerprint(monkeypatch, tmp_path, module):
    from mcpkart import bench

    monkeypatch.setattr(bench, "__file__", str(tmp_path / "bench.py"))
    process = tmp_path / module
    process.write_text("process implementation v1\n")
    first = bench.fingerprint()
    process.write_text("process implementation v2\n")
    assert bench.fingerprint() != first


@pytest.mark.asyncio
async def test_runtime_preflight_is_required_before_start_and_never_falls_back(monkeypatch, tmp_path):
    from mcpkart import bench

    calls = []

    async def fake_tool(client, name, arguments=None):
        calls.append(name)
        assert name == "runtime_info"
        return {"backend": "process"}  # An old or incompatible server cannot be inferred safely.

    monkeypatch.setattr(bench, "tool", fake_tool)
    with pytest.raises(ValueError, match="runtime_info fields"):
        await bench.run_trial(
            None, object(), {"model": "scripted/reference"}, 0, 56.7, tmp_path / "trial.json"
        )
    assert calls == ["runtime_info"]
    assert not (tmp_path / "trial.json").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize("actual_backend", ["process", "event_loop"])
async def test_trial_keeps_full_backend_diagnostics_on_disk_with_compact_stdout(
    monkeypatch,
    tmp_path,
    capsys,
    actual_backend,
):
    from mcpkart import bench
    from mcpkart.sim import Simulation

    calls = []
    child_info = {**RUNTIME_INFO, "backend": actual_backend, "worker_pid": 789, "parent_pid": 456}
    events = [{"tick": i, "lateness_ms": 101, "details": "unique-diagnostic-event"} for i in range(250)]
    race = {
        "summary": {"finished": True, "elapsed": 56.7},
        "runtime_info": child_info,
        "timing": {
            "backend": actual_backend,
            "infrastructure_valid": True,
            "lateness_events": events,
            "nested": {"worker_events": events},
        },
    }
    initial = {**Simulation().observation(), "status": "completed", "finished": True}

    async def fake_tool(client, name, arguments=None):
        calls.append(name)
        if name == "runtime_info":
            return copy.deepcopy(RUNTIME_INFO)
        if name == "start_race":
            return initial
        assert name == "finish_race"
        return copy.deepcopy(race)

    monkeypatch.setattr(bench, "tool", fake_tool)
    info = await bench.read_runtime_info(None)
    path = tmp_path / "trial.json"
    report = await bench.run_trial(
        None, object(), {"model": "scripted/reference"}, 0, 56.7, path, runtime_info=info
    )
    assert calls == ["runtime_info", "start_race", "finish_race"]  # Passed preflight is reused.
    saved = json.loads(path.read_text())
    assert saved["runtime_info"] == info
    assert saved["race"]["runtime_info"] == child_info
    assert saved["race"]["timing"]["lateness_events"] == events
    assert saved["metrics"]["timing"]["nested"]["worker_events"] == events
    text = capsys.readouterr().out
    assert "unique-diagnostic-event" not in text
    assert len(text) < 2000
    event = json.loads(text)
    assert event["event"] == "trial_done"
    assert event["timing"]["lateness_events_items_retained"] == 250
    assert event["timing"]["nested"]["worker_events_items_retained"] == 250
    assert report["metrics"]["runtime_consistent"] is (actual_backend == "process")
    assert report["metrics"]["realtime_valid"] is (actual_backend == "process")
    assert report["metrics"]["runtime_backend"] == actual_backend


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [RuntimeError, asyncio.CancelledError])
async def test_failed_collection_preserves_paid_evidence_and_original_worker_failure(
    monkeypatch,
    tmp_path,
    error_type,
):
    from mcpkart import bench
    from mcpkart.sim import Simulation

    original = error_type("worker died after decision fake-test-secret")
    collection = ConnectionError("collection unavailable fake-test-secret")
    initial = {**Simulation().observation(), "observed_ns": 10, "race_id": "dead-worker", "status": "running"}
    calls = []

    async def fake_tool(client, name, arguments=None):
        calls.append(name)
        if name == "start_race":
            return copy.deepcopy(initial)
        if name == "drive":
            raise original
        assert name == "finish_race"
        raise collection

    class Driver:
        api_key = "fake-test-secret"

        async def decide(self, route, observation):
            return {"ok": True, "action": "straight_accelerate", "latency_ms": 23, "cost": 0.0001}

    monkeypatch.setattr(bench, "tool", fake_tool)
    path = tmp_path / "incomplete.json"
    with pytest.raises(error_type) as caught:
        await bench.run_trial(
            None, Driver(), {"model": "test/model"}, 0, 56.7, path, runtime_info=RUNTIME_INFO
        )
    assert caught.value is original  # Cleanup failure must not replace the original failure.
    assert calls == ["start_race", "drive", "finish_race"]
    saved = json.loads(path.read_text())
    assert saved["status"] == "incomplete" and saved["collection_complete"] is False
    assert saved["runtime_info"] == RUNTIME_INFO
    assert saved["race"] is None
    assert saved["last_observation"] == initial
    assert len(saved["requests"]) == 1 and saved["requests"][0]["cost"] == 0.0001
    assert "applied" not in saved["requests"][0]  # A disconnected command's outcome is unknown.
    assert saved["metrics"]["cost_usd"] == 0.0001
    assert saved["metrics"]["finished"] is saved["metrics"]["elapsed"] is None
    assert saved["metrics"]["realtime_valid"] is False
    assert saved["collection_error"]["type"] == "ConnectionError"
    assert saved["trial_error"]["type"] == error_type.__name__
    assert "fake-test-secret" not in path.read_text()
    assert "samples" not in saved and "commands" not in saved


@pytest.mark.asyncio
async def test_collection_failure_alone_is_persisted_then_raised(monkeypatch, tmp_path):
    from mcpkart import bench
    from mcpkart.sim import Simulation

    original = ConnectionError("final record disconnected")
    initial = {**Simulation().observation(), "status": "completed", "finished": True}

    async def fake_tool(client, name, arguments=None):
        if name == "start_race":
            return initial
        assert name == "finish_race"
        raise original

    monkeypatch.setattr(bench, "tool", fake_tool)
    path = tmp_path / "incomplete.json"
    with pytest.raises(ConnectionError) as caught:
        await bench.run_trial(
            None, object(), {"model": "scripted/reference"}, 0, 56.7, path, runtime_info=RUNTIME_INFO
        )
    assert caught.value is original
    saved = json.loads(path.read_text())
    assert saved["race"] is None and saved["last_observation"] == initial
    assert saved["metrics"]["finished"] is None  # The last observation is not a final collected result.


def test_incomplete_collection_cannot_resume_or_turn_a_partial_batch_into_a_pass(resumable_trial):
    from mcpkart.bench import validate_resume

    saved, arguments = resumable_trial
    saved["collection_complete"] = False
    saved["race"] = None
    with pytest.raises(ValueError, match="incompletely collected"):
        validate_resume(saved, **arguments)
    rows = [report() for _ in range(8)]
    rows.extend(
        {
            "model": "test/model",
            "collection_complete": False,
            "metrics": {
                "finished": None,
                "realtime_valid": False,
                "elapsed": None,
                "time_ratio": None,
                "rescues": None,
                "cost_usd": 0.001,
            },
        }
        for _ in range(2)
    )
    summary = summarize_batch(rows)["models"][0]
    assert summary["trials"] == 10 and summary["incomplete_trials"] == 2
    assert summary["completed"] == 8
    assert summary["complete_batch"] is summary["passes"] is summary["strict_passes"] is False
    assert summary["total_rescues"] is None


@pytest.mark.asyncio
async def test_comparison_stops_and_saves_incomplete_attempt_in_summary(monkeypatch, tmp_path):
    from mcpkart import bench, decisions
    from mcpkart.sim import Simulation

    original = RuntimeError("worker died")
    starts = []
    initial = {**Simulation().observation(), "status": "running", "race_id": "dead", "observed_ns": 100}
    (tmp_path / "routes.json").write_text(json.dumps([{"model": "test/model", "provider": "pinned"}]))

    async def fake_tool(client, name, arguments=None):
        if name == "runtime_info":
            return RUNTIME_INFO
        if name == "start_race":
            starts.append(arguments["seed"])
            return initial
        if name == "drive":
            raise original
        assert name == "finish_race"
        raise ConnectionError("collection failed")

    class FakeContext:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class Driver(FakeContext):
        instructions = "test"
        criteria: ClassVar[dict] = {}

        async def decide(self, route, observation):
            return {"ok": True, "action": "straight_accelerate", "latency_ms": 20, "cost": 0.001}

    class FakeBudget:
        def __init__(self, *args, **kwargs):
            pass

        def summary(self):
            return {"cap_usd": 10, "charged_usd": 0.001}

    monkeypatch.setattr(bench, "tool", fake_tool)
    monkeypatch.setattr(bench, "Client", FakeContext)
    monkeypatch.setattr(bench, "reference_durations", lambda path: {0: 56.7, 1: 56.7})
    monkeypatch.setattr(decisions, "DecisionClient", Driver)
    monkeypatch.setattr(decisions, "Budget", FakeBudget)
    args = argparse.Namespace(
        command="compare",
        output=str(tmp_path),
        models="test/model",
        control_language="numeric",
        instruction_style="original",
        url="fake://local",
        reference="unused",
        trials=2,
        telemetry="raw",
        stop_when_target_impossible=False,
    )
    with pytest.raises(RuntimeError) as caught:
        await bench.remote_command(args)
    assert caught.value is original and starts == [0]
    summary = json.loads((tmp_path / "summary.json").read_text())["models"][0]
    assert summary["trials"] == summary["incomplete_trials"] == 1
    assert summary["complete_batch"] is summary["passes"] is False
    assert summary["total_rescues"] is None
