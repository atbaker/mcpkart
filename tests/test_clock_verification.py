import copy
import json
import sys

import pytest

from scripts import verify_clock_validation as verifier


@pytest.fixture
def saved_batch(tmp_path, monkeypatch):
    monkeypatch.setattr(verifier, "fingerprint", lambda: "frozen-source")
    info = {"backend": "process", "clock_mode": "fixed_step_wall_clock", "physics_hz": 60,
            "watchdog_enabled": False, "process_pid": 42}
    provenance = {"worker_module": "mcpkart.physics_worker", "child_clock_mode": "fixed_step_wall_clock",
                  "child_web_modules_loaded": [], "parent_pid": 42, "child_pid": 43}
    timing = {"clock_mode": "fixed_step_wall_clock", "backend": "process", "physics_hz": 60,
              "process_provenance": provenance, "validity_limits_ms": verifier.LIMITS,
              "infrastructure_valid": True, "max_lateness_ms": 2, "p95_lateness_ms": 1, "drift_ms": .5}
    race = {"race_id": "race", "runtime_info": info, "process_provenance": provenance,
            "timing": timing, "realtime_valid": True, "reason": "finished",
            "summary": {"finished": True, "checkpoints_passed": 120, "elapsed": 56.7},
            "samples": [{"wall_ns": tick} for tick in range(1000, 1012)]}
    rows = []
    for index in range(1, 4):
        path = tmp_path / f"controls/run-{index:02d}/scripted-live.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"fingerprint": "frozen-source", "runtime_mismatches": [],
                                    "collection_complete": True, "race": copy.deepcopy(race)}))
        row = {"passes": True, "spectator_polls": 2, "fingerprint": "frozen-source"}
        if index == 2:
            row["parent_pause"] = {"race_id": "race", "parent_pid": 42, "signals": ["SIGSTOP", "SIGCONT"],
                                   "requested_duration_s": .35, "started_ns": 1000, "ended_ns": 1011,
                                   "physics_samples_during_parent_pause": 12}
        rows.append(row)
    (tmp_path / "controls/validation.json").write_text(json.dumps({
        "passes": True, "source_unchanged": True, "model_requests": 0, "controls": rows,
        "required_consecutive_controls": 3, "expected_clock_mode": "fixed_step_wall_clock",
        "validity_limits_ms": verifier.LIMITS, "runtime_info": info}))
    race["summary"]["elapsed"] = 170.1
    race["reason"] = "deadline"
    (tmp_path / "long-clock.json").write_text(json.dumps({
        "passes": True, "model_requests": 0, "fingerprint": "frozen-source", "runtime_mismatches": [],
        "trial_error": None, "collection_error": None, "required_duration_s": 170.1,
        "race": race, "runtime_info": info}))
    return tmp_path


def test_complete_saved_python_gate_passes(saved_batch):
    assert verifier.verify(saved_batch)["passes"]


@pytest.mark.parametrize("failure", ["rust_child", "same_process", "slow_clock", "changed_source",
                                     "short_clock", "missing_pause_samples", "failed_control"])
def test_summary_pass_cannot_hide_invalid_final_recording(saved_batch, failure):
    path = saved_batch / "long-clock.json"
    record = json.loads(path.read_text())
    if failure == "rust_child":
        record["race"]["process_provenance"]["worker_module"] = "mcpkart-rust-worker"
    elif failure == "same_process":
        record["race"]["process_provenance"]["child_pid"] = 42
    elif failure == "slow_clock":
        record["race"]["timing"]["max_lateness_ms"] = 101
    elif failure == "changed_source":
        record["fingerprint"] = "other-source"
    elif failure == "short_clock":
        record["race"]["summary"]["elapsed"] = 60
    elif failure == "missing_pause_samples":
        path = saved_batch / "controls/run-02/scripted-live.json"
        record = json.loads(path.read_text())
        record["race"]["samples"].pop()
    else:
        path = saved_batch / "controls/validation.json"
        record = json.loads(path.read_text())
        record["controls"][2]["passes"] = False
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        verifier.verify(saved_batch)


def test_cli_failed_gate_exits_nonzero(saved_batch, monkeypatch, capsys):
    (saved_batch / "long-clock.json").unlink()
    monkeypatch.setattr(sys, "argv", ["verify_clock_validation.py", "--directory", str(saved_batch)])
    with pytest.raises(SystemExit) as error:
        verifier.main()
    assert error.value.code == 1
    assert json.loads(capsys.readouterr().out)["passes"] is False
