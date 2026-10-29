import json
from datetime import UTC, datetime, timedelta

import pytest

from mcpkart import demo_admission as admission


def test_hot_admission_checks_manifest_identity_without_rehashing_archive(tmp_path, monkeypatch):
    plan = {"source_sha256": {"example.py": "frozen"},
            "expires_utc": (datetime.now(UTC) + timedelta(hours=1)).isoformat()}
    path = tmp_path / "release.json"
    path.write_text(json.dumps(plan))
    guard = admission.Admission.__new__(admission.Admission)
    guard.path, guard.plan, guard.digest = path, plan, admission.release_digest(plan)
    manifest = tmp_path / "interface.json"
    manifest.write_text('{"passed":true}')
    stat = manifest.stat()
    guard.bound = {manifest: (stat.st_ino, stat.st_size, stat.st_mtime_ns)}
    monkeypatch.setattr(admission, "sources", lambda: plan["source_sha256"])
    monkeypatch.setattr(admission, "sha", lambda _: pytest.fail("Hot path must not hash large archives"))
    guard.check()
    manifest.write_text('{"passed":false}')
    with pytest.raises(RuntimeError, match="manifest changed"):
        guard.check()
