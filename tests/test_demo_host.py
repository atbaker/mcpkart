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
