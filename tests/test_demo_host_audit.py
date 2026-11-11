"""Audit recovery must never redispatch or approve different race evidence."""

import hashlib
import json
import sys
from pathlib import Path

import pytest


def helper(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import demo_host_audit
    monkeypatch.setattr(demo_host_audit, "ROOT", tmp_path)
    return demo_host_audit


def test_unknown_audit_submission_stops_before_contacting_aws(tmp_path, monkeypatch):
    module = helper(tmp_path, monkeypatch)
    race = tmp_path / "artifacts/aws-demo-live-first"
    audit = tmp_path / f"artifacts/aws-demo-live-first-audit-v{module.AUDIT_VERSION}"
    audit.mkdir(parents=True)
    (audit / "submission-intent.json").write_text("{}")
    monkeypatch.setattr(module, "clients", lambda: pytest.fail("Unknown submission cannot redispatch"))
    with pytest.raises(RuntimeError, match="outcome unknown"):
        module.audit_completed_run(race, {}, {}, "own-release")


@pytest.mark.parametrize("changed", [False, True])
def test_completed_audit_is_reused_only_for_exact_downloaded_evidence(tmp_path, monkeypatch, changed):
    module = helper(tmp_path, monkeypatch)
    race = tmp_path / "artifacts/aws-demo-live-first"
    (race / "trial").mkdir(parents=True)
    observed = {"status": "Success", "response_code": 0}
    (race / "observed-exit.json").write_text(json.dumps(observed))
    (race / "ssm-command.json").write_text('{"command":"original-race"}')
    payload = b'{"real_saved_evidence":true}'
    (race / "trial/race.json").write_bytes(payload if not changed else b'{"altered":true}')
    audit = tmp_path / f"artifacts/aws-demo-live-first-audit-v{module.AUDIT_VERSION}"
    audit.mkdir()
    (audit / "ssm-command.json").write_text('{"command":"original-audit"}')
    plan, ledger = {"frozen": True}, {"requests": 50}
    data = {"evidence_sha256": {"race.json": hashlib.sha256(payload).hexdigest()},
            "observed_exit": observed, "observed_ssm_command": "original-race"}
    (audit / "input.json").write_text(json.dumps(data))
    review = {"release_sha256": module.release_digest(plan), "budget_after": ledger,
              "observed_exit_and_audited": True, "audit_environment": "qualified-linux-container",
              "evidence_manifest_sha256": hashlib.sha256((audit / "input.json").read_bytes()).hexdigest()}
    (audit / "review.json").write_text(json.dumps(review))

    class SSM:
        def get_command_invocation(self, **kwargs):
            assert kwargs["CommandId"] == "original-audit"
            return {"Status": "Success", "ResponseCode": 0}

    monkeypatch.setattr(module, "clients", lambda: ({"instance": "own"}, SSM(), None))
    commands = []
    monkeypatch.setattr(module.subprocess, "run", lambda command, **kw: commands.append(command))
    if changed:
        with pytest.raises(RuntimeError, match="evidence changed"):
            module.audit_completed_run(race, plan, ledger, "own-release")
    else:
        assert module.audit_completed_run(race, plan, ledger, "own-release") == review
    assert commands == [[sys.executable, str(tmp_path / "scripts/demo_host.py"), "fetch", audit.name]]


def test_audit_acknowledgement_matches_native_observation_time(tmp_path, monkeypatch):
    helper(tmp_path, monkeypatch)
    from audit_demo_run import acknowledgement_from_sample

    from mcpkart.duel import TRIO_RACERS, DuelSimulation

    sim = DuelSimulation(racer_ids=TRIO_RACERS, contact="ghost")
    for _ in range(63):
        sim.step()
    sample = sim.state()
    observed = sim.observation("red")
    assert sample["time"] != observed["time"]  # Exact master and native API formats differ.
    ack = acknowledgement_from_sample(sample, "red", {"applied": True, "applied_tick": 63})
    assert ack["observation"]["time"] == observed["time"]
    for key in ("kart", "track", "progress", "rescue", "finished"):
        assert ack["observation"][key] == observed[key]
