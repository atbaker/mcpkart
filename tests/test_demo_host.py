"""Operator dispatch must remain one-shot even if SSM loses its response."""

import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("boto3")

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_host():
    spec = importlib.util.spec_from_file_location("demo_host_test", SCRIPTS / "demo_host.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unknown_ssm_submission_is_never_redispatched(tmp_path, monkeypatch):
    host = load_host()
    script = tmp_path / "free-command.sh"
    script.write_text("true\n")
    attempts = []

    class SSM:
        def send_command(self, **kwargs):
            attempts.append(kwargs)
            raise TimeoutError("response lost after possible acceptance")

    monkeypatch.setattr(host, "ROOT", tmp_path)
    monkeypatch.setattr(host, "clients", lambda: ({"instance": "own-instance", "bucket": "own-bucket"}, SSM(), None))
    monkeypatch.setattr(sys, "argv", ["demo_host.py", "submit", "aws-demo-unknown", "--script", str(script)])
    (tmp_path / "artifacts").mkdir()
    with pytest.raises(TimeoutError):
        host.main()
    assert (tmp_path / "artifacts/aws-demo-unknown/submission-intent.json").is_file()
    with pytest.raises(ValueError, match="never resubmit"):
        host.main()
    assert len(attempts) == 1


def test_private_artifacts_are_rejected_before_ssm_dispatch(tmp_path, monkeypatch):
    host = load_host()
    script = tmp_path / "free-command.sh"
    script.write_text("true\n")

    class SSM:
        def send_command(self, **kwargs):
            pytest.fail("Private evidence must never be submitted")

    monkeypatch.setattr(host, "ROOT", tmp_path)
    monkeypatch.setattr(host, "clients", lambda: ({"instance": "own", "bucket": "own"}, SSM(), None))
    monkeypatch.setattr(sys, "argv", ["demo_host.py", "submit", "aws-demo-invalid",
                                     "--script", str(script), "--collect",
                                     "artifacts/aws-demo-temporal-private.json"])
    (tmp_path / "artifacts").mkdir()
    with pytest.raises(ValueError, match="non-secret"):
        host.main()


def test_fetch_rejects_archive_escape_from_collected_directory(tmp_path, monkeypatch):
    import io
    import json
    import tarfile

    host = load_host()
    output = tmp_path / "artifacts/aws-demo-archive"
    output.mkdir(parents=True)
    (output / "ssm-command.json").write_text(json.dumps({
        "command": "already-finished", "collect": ["artifacts/aws-demo-archive"], "archive_key": "own/archive",
    }))

    class SSM:
        def get_command_invocation(self, **kwargs):
            return {"Status": "Success"}

    class S3:
        def download_file(self, bucket, key, destination):
            with tarfile.open(destination, "w:gz") as bundle:
                member = tarfile.TarInfo("artifacts/aws-demo-archive/../budget.json")
                member.size = 2
                bundle.addfile(member, io.BytesIO(b"{}"))

    monkeypatch.setattr(host, "ROOT", tmp_path)
    monkeypatch.setattr(host, "clients", lambda: ({"instance": "own", "bucket": "own"}, SSM(), S3()))
    monkeypatch.setattr(sys, "argv", ["demo_host.py", "fetch", "aws-demo-archive"])
    with pytest.raises(ValueError, match="Unexpected evidence"):
        host.main()
    assert not (tmp_path / "artifacts/budget.json").exists()


def load_operator(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("demo_operator_test", SCRIPTS / "run_aws_demo.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def operator_fixture(tmp_path, monkeypatch, local):
    import json

    operator = load_operator(monkeypatch)
    monkeypatch.setattr(operator, "ROOT", tmp_path)
    release = tmp_path / operator.RELEASE
    release.mkdir(parents=True)
    (release / "release.json").write_text(json.dumps({
        "entries": ["unrun-stage"], "agentcore_arn": "own-runtime", "activity_mode": "regular",
        "expires_utc": "2099-01-01T00:00:00+00:00",
    }))
    (release / "qualification-review.json").write_text(json.dumps({
        "passed": True, "regular_activities": True, "budget_unchanged": True, "descriptive_step_results": True,
    }))
    interface = tmp_path / Path(operator.INTERFACE).parent
    interface.mkdir(parents=True)
    (interface / "demo-registration.json").write_text(json.dumps({"local_activities": local}))
    (tmp_path / "artifacts/budget.json").write_text("{}")
    monkeypatch.setattr(sys, "argv", ["run_aws_demo.py", "stage"])
    return operator


def test_operator_rejects_local_activity_qualification_for_regular_stage(tmp_path, monkeypatch):
    operator = operator_fixture(tmp_path, monkeypatch, True)
    with pytest.raises(ValueError, match="regular-Activity"):
        operator.main()
    assert not (tmp_path / "artifacts/aws-demo-regular-live-stage-v1").exists()


def test_operator_submits_regular_stage_without_local_flag(tmp_path, monkeypatch):
    operator = operator_fixture(tmp_path, monkeypatch, False)

    class SubmissionInspected(Exception):
        pass

    def inspect_submission(command, **kwargs):
        script = (tmp_path / "artifacts/aws-demo-regular-live-stage-v1/command.sh").read_text()
        assert "--paid --retire-provider-errors" in script
        assert "--local" not in script
        assert "--race-id unrun-stage" in script
        raise SubmissionInspected

    monkeypatch.setattr(operator.subprocess, "run", inspect_submission)
    with pytest.raises(SubmissionInspected):
        operator.main()


@pytest.mark.parametrize("saved_exit", [None, {"status": "Success", "response_code": 0, "ended": "2026-10-30T00:22:28Z"}])
def test_operator_reports_existing_attempt_without_redispatch(tmp_path, monkeypatch, saved_exit):
    import json

    operator = operator_fixture(tmp_path, monkeypatch, False)
    directory = tmp_path / "artifacts/aws-demo-regular-live-stage-v1"
    directory.mkdir()
    evidence = directory / "submission-intent.json"
    evidence.write_text('{"preserve":true}')
    if saved_exit:
        (directory / "observed-exit.json").write_text(json.dumps(saved_exit))
    monkeypatch.setattr(operator.subprocess, "run", lambda *a, **kw: pytest.fail("Must not redispatch"))
    monkeypatch.setattr(operator, "clients", lambda: pytest.fail("Must not contact AWS"))
    with pytest.raises(SystemExit, match="already been attempted or claimed") as result:
        operator.main()
    assert "No new AWS command was sent" in str(result.value)
    if saved_exit:
        assert "Success, exit 0" in str(result.value)
    assert evidence.read_text() == '{"preserve":true}'
    assert (tmp_path / "artifacts/budget.json").read_text() == "{}"


def test_operator_rejects_claim_even_if_output_directory_is_missing(tmp_path, monkeypatch):
    operator = operator_fixture(tmp_path, monkeypatch, False)
    claim = tmp_path / operator.RELEASE / "unrun-stage-claimed.json"
    claim.write_text("{}")
    monkeypatch.setattr(operator.subprocess, "run", lambda *a, **kw: pytest.fail("Must not redispatch"))
    with pytest.raises(SystemExit, match="already been attempted or claimed"):
        operator.main()
    assert claim.read_text() == "{}"
    assert not (tmp_path / "artifacts/aws-demo-regular-live-stage-v1").exists()


def test_manual_command_allocates_next_race_and_preserves_previous(tmp_path, monkeypatch):
    operator = operator_fixture(tmp_path, monkeypatch, False)
    plan = {"entries": ["mcpkart-demo-first", "mcpkart-demo-second"]}
    identity, _output, first = operator.next_manual_entry(plan)
    assert identity == "mcpkart-demo-first"
    first.mkdir()
    (first / "ledger-transfer.json").write_text("preserved")
    with pytest.raises(SystemExit, match="exit/ledger reconciled"):
        operator.next_manual_entry(plan)
    (tmp_path / operator.RELEASE / (identity + "-review.json")).write_text("{}")
    identity, _output, second = operator.next_manual_entry(plan)
    assert identity == "mcpkart-demo-second" and first != second and not second.exists()
    assert (first / "ledger-transfer.json").read_text() == "preserved"


def test_interrupted_ledger_handoff_is_idempotent_and_rejects_unrelated_state(tmp_path, monkeypatch):
    import hashlib
    import json

    operator = load_operator(monkeypatch)
    directory = tmp_path / "race"
    directory.mkdir()
    ledger = tmp_path / "budget.json"
    before = {"requests": 10, "charged_usd": 1, "charged_tokens": 100, "uncertain_requests": 2,
              "reported_cost_usd": .8, "cap_usd": 20, "max_requests": 100, "max_tokens": 1000}
    initial = json.dumps(before).encode()
    ledger.write_bytes(initial)
    after = {**before, "requests": 12, "charged_usd": 1.2, "charged_tokens": 120, "reported_cost_usd": 1}
    (directory / "ledger-transfer.json").write_text(json.dumps({
        "budget_before": before, "local_before_sha256": hashlib.sha256(initial).hexdigest(),
    }))
    (directory / "budget-after.json").write_text(json.dumps(after))
    assert operator.reconcile_ledger(directory, ledger) == after
    assert operator.reconcile_ledger(directory, ledger) == after
    ledger.write_text(json.dumps({**after, "requests": 13}))
    with pytest.raises(RuntimeError, match="differs from both saved boundaries"):
        operator.reconcile_ledger(directory, ledger)
    assert json.loads(ledger.read_text())["requests"] == 13


def test_resume_recovers_existing_job_without_submitting_a_new_race(tmp_path, monkeypatch):
    import json

    operator = operator_fixture(tmp_path, monkeypatch, False)
    path = tmp_path / operator.RELEASE / "release.json"
    plan = json.loads(path.read_text())
    plan["manual_invocations_only"] = True
    path.write_text(json.dumps(plan))
    pending = tmp_path / "artifacts/aws-demo-live-unrun-stage"
    pending.mkdir()
    calls = []
    monkeypatch.setattr(operator, "finish_existing_run", lambda directory, *_: calls.append(directory) or 0)
    monkeypatch.setattr(operator.subprocess, "run", lambda *a, **kw: pytest.fail("Resume must never submit"))
    monkeypatch.setattr(sys, "argv", ["run_aws_demo.py", "resume"])
    assert operator.main() == 0
    assert calls == [pending]


def test_expired_demo_is_rejected_before_allocating_or_submitting(tmp_path, monkeypatch):
    import json

    operator = operator_fixture(tmp_path, monkeypatch, False)
    path = tmp_path / operator.RELEASE / "release.json"
    plan = json.loads(path.read_text())
    plan["expires_utc"] = "2026-01-01T00:00:00+00:00"
    path.write_text(json.dumps(plan))
    monkeypatch.setattr(operator.subprocess, "run", lambda *a, **kw: pytest.fail("No expired dispatch"))
    with pytest.raises(SystemExit, match="less than 15 minutes"):
        operator.main()
    assert not (tmp_path / "artifacts/aws-demo-regular-live-stage-v1").exists()


@pytest.mark.parametrize("audit_fails", [False, True])
def test_new_manual_session_requires_outcome_audit_before_next_entry(tmp_path, monkeypatch, audit_fails):
    import hashlib
    import json

    operator = operator_fixture(tmp_path, monkeypatch, False)
    import demo_host_audit
    plan = {"manual_invocations_only": True, "user_waived_new_audit": False}
    state = {"requests": 10, "charged_usd": 1, "charged_tokens": 100, "uncertain_requests": 2,
             "reported_cost_usd": .8, "cap_usd": 20, "max_requests": 100, "max_tokens": 1000,
             "pending": {}}
    ledger = tmp_path / "artifacts/budget.json"
    ledger.write_text(json.dumps(state))
    directory = tmp_path / "artifacts/aws-demo-live-first"
    (directory / "trial").mkdir(parents=True)
    (directory / "ssm-command.json").write_text('{"command":"already-submitted"}')
    (directory / "budget-after.json").write_bytes(ledger.read_bytes())
    (directory / "ledger-transfer.json").write_text(json.dumps({
        "logical_id": "first", "budget_before": state,
        "local_before_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
    }))
    (directory / "trial/collection.json").write_text(json.dumps({
        "budget_after": state, "collection_complete": True, "source_unchanged": True, "errors": [],
    }))

    class SSM:
        def get_command_invocation(self, **kwargs):
            return {"Status": "Success", "ResponseCode": 0}

    monkeypatch.setattr(operator, "clients", lambda: ({"instance": "own"}, SSM(), None))
    monkeypatch.setattr(operator.subprocess, "run", lambda *a, **kw: None)
    calls = []

    def audit(path, registration, budget, release):
        assert release == operator.RELEASE
        calls.append((path, registration, budget))
        if audit_fails:
            raise ValueError("Physics evidence did not pass")
        return {"observed_exit_and_audited": True, "budget_after": budget}

    monkeypatch.setattr(demo_host_audit, "audit_completed_run", audit)
    review = tmp_path / operator.RELEASE / "first-review.json"
    if audit_fails:
        with pytest.raises(ValueError, match="Physics evidence"):
            operator.finish_existing_run(directory, plan, ledger)
        assert not review.exists()
    else:
        assert operator.finish_existing_run(directory, plan, ledger) == 0
        assert json.loads(review.read_text())["observed_exit_and_audited"] is True
    assert calls == [(directory, plan, state)]
