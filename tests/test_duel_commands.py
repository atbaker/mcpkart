import json
import os
from pathlib import Path

import pytest

from mcpkart import duel_clock, duel_run
from mcpkart.question_context_run import start_ticks


def ledger(tmp_path):
    path = tmp_path / "budget.json"
    state = {
        "schema_version": 1,
        "cap_usd": 20.0,
        "max_requests": 100000,
        "max_tokens": 500000000,
        "requests": 94598,
        "charged_usd": 10.983352472002839,
        "charged_tokens": 320361620,
        "reported_cost_usd": 10.922141848002797,
        "uncertain_requests": 70,
        "pending": {},
    }
    path.write_text(json.dumps(state))
    return path, state


@pytest.mark.parametrize("max_requests", [100000, 110000])
def test_paid_admission_preserves_expanded_caps_and_all_historical_charges(tmp_path, max_requests):
    path, state = ledger(tmp_path)
    state["max_requests"] = max_requests
    path.write_text(json.dumps(state))
    duel_run.existing_budget(path)
    assert json.loads(path.read_text()) == state


@pytest.mark.parametrize(
    "change",
    [
        {"pending": {"request": {"usd": 1}}},
        {"cap_usd": 21},
        {"max_requests": 110001},
        {"requests": 99500},
        {"charged_tokens": 499000000},
        {"charged_usd": 21},
    ],
)
def test_paid_admission_rejects_invalid_or_insufficient_ledger_without_reset(tmp_path, change):
    path, state = ledger(tmp_path)
    state.update(change)
    path.write_text(json.dumps(state))
    before = path.read_bytes()
    with pytest.raises(ValueError):
        duel_run.existing_budget(path)
    assert path.read_bytes() == before


def qualification(tmp_path, monkeypatch):
    runtime = {"process_pid": os.getpid(), "backend": "process", "mode": "duel"}
    source = {"engine.py": "frozen"}
    monkeypatch.setattr(duel_clock, "sources", lambda: source)
    names = ["plan.json", "long-clock.json.gz", "long-proof.json", "memory-samples.json"]
    names += [f"control-{i}/{name}.json" for i in range(4) for name in ("race", "proof")]
    evidence = {}
    for name in names:
        file = tmp_path / name
        file.parent.mkdir(exist_ok=True)
        file.write_text("saved proof")
        evidence[name] = duel_clock.sha(file)
    q = {
        "passed": True,
        "controls": 4,
        "long_clock_s": 600,
        "parent_pause_physics_samples": 21,
        "model_requests": 0,
        "budget_unchanged": True,
        "source_sha256": source,
        "runtime": runtime,
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "http_parent_start_ticks": start_ticks(os.getpid()),
        "evidence_sha256": evidence,
    }
    path = tmp_path / "qualification.json"
    path.write_text(json.dumps(q))
    return path, q, runtime


def test_clock_binding_rejects_different_server_or_modified_evidence(tmp_path, monkeypatch):
    path, q, runtime = qualification(tmp_path, monkeypatch)
    assert duel_clock.validate_qualification(path, runtime) == q
    with pytest.raises(ValueError, match="different source or server"):
        duel_clock.validate_qualification(path, {**runtime, "process_pid": -1})
    (tmp_path / "control-0/race.json").write_text("changed trace")
    with pytest.raises(ValueError, match="Clock evidence changed"):
        duel_clock.validate_qualification(path, runtime)


@pytest.mark.parametrize(
    "change",
    [
        {"evidence_sha256": {}},
        {"boot_id": "old boot"},
        {"source_sha256": {"engine.py": "changed"}},
        {"parent_pause_physics_samples": 0},
        {"model_requests": 1},
    ],
)
def test_incomplete_or_stale_clock_is_rejected(tmp_path, monkeypatch, change):
    path, q, runtime = qualification(tmp_path, monkeypatch)
    q.update(change)
    path.write_text(json.dumps(q))
    with pytest.raises(ValueError):
        duel_clock.validate_qualification(path, runtime)


def test_clock_evidence_cannot_escape_qualification_directory(tmp_path, monkeypatch):
    path, q, runtime = qualification(tmp_path / "gate", monkeypatch)
    outside = tmp_path / "outside.json"
    outside.write_text("outside")
    q["evidence_sha256"]["../outside.json"] = duel_clock.sha(outside)
    path.write_text(json.dumps(q))
    with pytest.raises(ValueError, match="Clock evidence changed"):
        duel_clock.validate_qualification(path, runtime)
