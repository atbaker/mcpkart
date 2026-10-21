"""Saved authorization and runtime qualification must survive the opt-in CLI."""
import json
from pathlib import Path

import pytest

from mcpkart.decisions import Budget
from mcpkart.question_context_run import existing_budget, qualify_clock, sha


def test_existing_expanded_token_authorization_is_preserved(tmp_path):
    path = tmp_path / 'budget.json'
    Budget(path, max_requests=75000, max_tokens=500000000)
    state = json.loads(path.read_text())
    state.update(requests=68450, charged_tokens=261631856, charged_usd=8.25,
                 reported_cost_usd=8.19, uncertain_requests=69)
    path.write_text(json.dumps(state))
    reopened = existing_budget(path)
    actual = json.loads(reopened.path.read_text())
    assert actual == state


def test_pending_ledger_is_rejected_without_a_write(tmp_path):
    path = tmp_path / 'budget.json'
    Budget(path, max_tokens=500000000)
    state = json.loads(path.read_text())
    state['pending'] = {'unfinished': {'cost': .01, 'tokens': 252313}}
    path.write_text(json.dumps(state));before = path.read_bytes()
    with pytest.raises(ValueError, match='no pending'):
        existing_budget(path)
    assert path.read_bytes() == before


def clock_fixture(tmp_path, monkeypatch):
    from mcpkart import question_context_run as cli
    evidence = tmp_path / 'free-evidence.json';evidence.write_text('{}')
    runtime = {'backend': 'process', 'protocol_version': 1, 'watchdog_enabled': False,
               'clock_mode': 'fixed_step_wall_clock', 'physics_hz': 60, 'process_pid': 999}
    q = {'passed': True, 'controls': 3, 'parent_pause_physics_samples': 21,
         'long_clock_s': 170.1, 'model_requests': 0, 'budget_unchanged': True,
         'http_parent_pid': 999, 'http_parent_start_ticks': 123,
         'source_fingerprint': 'source-test',
         'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
         'evidence_sha256': {'free-evidence.json': sha(evidence)}}
    path = tmp_path / 'qualification.json';path.write_text(json.dumps(q))
    monkeypatch.setattr(cli, 'start_ticks', lambda pid: 123)
    monkeypatch.setattr(cli.bench, 'fingerprint', lambda: 'source-test')
    return path, runtime, evidence


def test_changed_clock_evidence_is_rejected(tmp_path, monkeypatch):
    path, runtime, evidence = clock_fixture(tmp_path, monkeypatch)
    assert qualify_clock(path, runtime)['passed']
    evidence.write_text('{"changed":true}')
    with pytest.raises(ValueError, match='evidence changed'):
        qualify_clock(path, runtime)


def test_different_runtime_cannot_reuse_clock_qualification(tmp_path, monkeypatch):
    path, runtime, _ = clock_fixture(tmp_path, monkeypatch)
    runtime['process_pid'] = 998
    with pytest.raises(ValueError, match='runtime differs'):
        qualify_clock(path, runtime)
