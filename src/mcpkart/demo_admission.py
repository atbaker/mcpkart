"""One frozen two-entry demo release, bound to fresh Linux and cloud evidence."""

from __future__ import annotations

import fcntl
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from .duel_bench import sources
from .duel_clock import sha, validate_qualification
from .duel_run import existing_budget
from .question_context_driver import _write_new


def release_digest(plan):
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Admission:
    def __init__(self, path, ledger, logical_id):
        self.path = Path(path)
        self.plan = json.loads(self.path.read_text())
        self.digest = release_digest(self.plan)
        self.check()
        if logical_id not in self.plan["entries"]:
            raise ValueError("Race identity is outside the finite registered release")
        self.logical_id = logical_id
        self.writer = (Path(ledger).parent / "root-paid-writer.lock").open("a")
        try:
            fcntl.flock(self.writer.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.budget = existing_budget(ledger)
            state = json.loads(Path(ledger).read_text())
            if state["uncertain_requests"] != self.plan["budget_boundary"]["uncertain_requests"]:
                raise ValueError("New uncertainty blocks any further demo admission")
            index = self.plan["entries"].index(logical_id)
            if index:
                review = json.loads((self.path.parent / (self.plan["entries"][index - 1] + "-review.json")).read_text())
                if (review.get("release_sha256") != self.digest or not review.get("observed_exit_and_audited")
                        or review.get("budget_after") != state):
                    raise ValueError("Root must observe and audit the earlier entry before another admission")
            elif state != self.plan["budget_boundary"]:
                raise ValueError("Cumulative ledger differs from the prospective registration boundary")
        except BaseException:
            self.writer.close()
            raise
        self.bound = {}

    def check(self):
        if sources() != self.plan["source_sha256"] or release_digest(json.loads(self.path.read_text())) != self.digest:
            raise RuntimeError("Frozen live release source or registration changed")
        remaining = (datetime.fromisoformat(self.plan["expires_utc"]) - datetime.now(UTC)).total_seconds()
        if remaining <= 0:
            raise RuntimeError("Live release expired")
        for path, digest in getattr(self, "bound", {}).items():
            if sha(path) != digest:
                raise RuntimeError("Bound qualification or interface evidence changed")

    def qualify(self, runtime, clock_path, interface_path, deployment_path):
        self.check()
        if (datetime.fromisoformat(self.plan["expires_utc"]) - datetime.now(UTC)).total_seconds() < 900:
            raise ValueError("The 15-minute admission floor is unavailable")
        q = validate_qualification(clock_path, runtime)
        if runtime.get("mode") != "trio" or q["controls"] != 4:
            raise ValueError("Four complete trio controls are required")
        interface = json.loads(Path(interface_path).read_text())
        if not (interface.get("passed") and interface.get("free") and interface.get("runtime") == runtime
                and interface.get("source_sha256") == sources()
                and interface.get("release_sha256") == self.digest
                and interface.get("namespace") == self.plan["namespace"]
                and interface.get("runtime_arn") == self.plan["agentcore_arn"]):
            raise ValueError("The exact Temporal Cloud / AgentCore / MCP free interface has not passed")
        deployment = json.loads(Path(deployment_path).read_text())
        if deployment.get("release_sha256") != self.digest or deployment.get("runtime_arn") != self.plan["agentcore_arn"]:
            raise ValueError("AgentCore deployment differs from the frozen release")
        # Read current configuration; an old receipt alone cannot establish the active version.
        import boto3
        from botocore.config import Config
        current = boto3.client("bedrock-agentcore-control", region_name=self.plan["region"],
                               config=Config(retries={"total_max_attempts": 1})).get_agent_runtime(
                                   agentRuntimeId=deployment["runtime_id"])
        env = current.get("environmentVariables", {})
        if current["status"] != "READY" or current["agentRuntimeVersion"] != deployment["version"] or env.get(
            "MCPKART_RELEASE_SHA256"
        ) != self.digest:
            raise ValueError("Active AgentCore release/version is not ready or changed")
        paths = [Path(clock_path), Path(interface_path), Path(deployment_path)]
        paths += [Path(clock_path).parent / name for name in q["evidence_sha256"]]
        paths += [Path(interface_path).parent / name for name in interface["evidence_sha256"]]
        self.bound = {p: sha(p) for p in paths}
        # Claim exactly once, before starting physics or performing live effects.
        _write_new(self.path.parent / (self.logical_id + "-claimed.json"), {
            "release_sha256": self.digest, "logical_id": self.logical_id,
            "runtime": runtime, "budget_before": json.loads(self.budget.path.read_text()),
            "no_retries_or_replacement": True,
        })

    def close(self):
        self.writer.close()
