"""One frozen two-entry demo release, bound to fresh Linux and cloud evidence."""

from __future__ import annotations

import fcntl
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from .decisions import Budget
from .duel_bench import sources
from .duel_clock import sha, validate_qualification
from .duel_run import existing_budget
from .question_context_driver import _write_new
from .question_context_run import start_ticks


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
            state = json.loads(Path(ledger).read_text())
            if self.plan.get("manual_invocations_only") and self.plan.get("budget_limits_enforced") is False:
                if state.get("schema_version") != 1 or state.get("pending"):
                    raise ValueError("An intact cumulative ledger without pending reservations is required")
                self.budget = Budget(ledger, cap_usd=state["cap_usd"], max_requests=state["max_requests"],
                                     max_tokens=state["max_tokens"], enforce_limits=False)
            else:
                self.budget = existing_budget(ledger)
            index = self.plan["entries"].index(logical_id)
            if index:
                review = json.loads((self.path.parent / (self.plan["entries"][index - 1] + "-review.json")).read_text())
                reviewed_provider_uncertainty = (
                    self.plan.get("provider_error_policy") == "retire"
                    and self.plan.get("allow_fully_reserved_provider_dnfs_after_root_review") is True
                    and review.get("only_provider_errors_or_none") is True
                )
                if state["uncertain_requests"] != self.plan["budget_boundary"]["uncertain_requests"] and not reviewed_provider_uncertainty:
                    raise ValueError("Unreviewed uncertainty blocks further admission")
                reviewed = review.get("observed_exit_and_audited") or (
                    self.plan.get("manual_invocations_only") and self.plan.get("user_waived_new_audit")
                    and review.get("observed_exit_and_reconciled")
                )
                if (review.get("release_sha256") != self.digest or not reviewed
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
        for path, identity in getattr(self, "bound", {}).items():
            stat = path.stat()
            if (stat.st_ino, stat.st_size, stat.st_mtime_ns) != identity:
                raise RuntimeError("Bound qualification or interface manifest changed")

    def qualify(self, runtime, clock_path, interface_path, deployment_path):
        self.check()
        if (datetime.fromisoformat(self.plan["expires_utc"]) - datetime.now(UTC)).total_seconds() < 900:
            raise ValueError("The 15-minute admission floor is unavailable")
        if self.plan.get("manual_invocations_only") and self.plan.get("user_waived_new_audit"):
            self.qualify_manual(runtime, clock_path, interface_path, deployment_path)
            return
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
        # Verify all payload hashes once before the physics epoch. The hot path
        # checks the three frozen manifests, never rehashes recording archives.
        for name, expected in interface["evidence_sha256"].items():
            payload = Path(interface_path).parent / name
            if not payload.resolve().is_relative_to(Path(interface_path).parent.resolve()) or sha(payload) != expected:
                raise ValueError("Cloud interface payload changed: " + name)
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
        self.bound = {}
        for path in paths:
            stat = path.stat()
            self.bound[path] = (stat.st_ino, stat.st_size, stat.st_mtime_ns)
        # Claim exactly once, before starting physics or performing live effects.
        _write_new(self.path.parent / (self.logical_id + "-claimed.json"), {
            "release_sha256": self.digest, "logical_id": self.logical_id,
            "runtime": runtime, "budget_before": json.loads(self.budget.path.read_text()),
            "no_retries_or_replacement": True,
        })

    def close(self):
        self.writer.close()

    def qualify_manual(self, runtime, clock_path, interface_path, deployment_path):
        """User waived a new audit; retain the previously qualified physics/server.

        This is explicitly reuse, not a claim that new timing measurements or
        new Cloud mock calls occurred. Only accounting/admission code differs.
        """
        previous = self.plan["prior_qualified_sources"]
        changed = {name for name in previous if previous[name] != self.plan["source_sha256"].get(name)}
        if changed - {"decisions.py", "demo_admission.py"} or set(previous) != set(self.plan["source_sha256"]):
            raise ValueError("Manual session changed previously qualified game/controller source")
        q, interface = json.loads(Path(clock_path).read_text()), json.loads(Path(interface_path).read_text())
        if (sha(clock_path) != self.plan["reused_clock_sha256"]
                or sha(interface_path) != self.plan["reused_interface_sha256"]
                or not q.get("passed") or q.get("controls") != 4
                or q.get("runtime") != runtime or q.get("source_sha256") != previous
                or q.get("boot_id") != Path("/proc/sys/kernel/random/boot_id").read_text().strip()
                or q.get("http_parent_start_ticks") != start_ticks(runtime["process_pid"])
                or not interface.get("passed") or not interface.get("free")
                or interface.get("runtime") != runtime or interface.get("source_sha256") != previous
                or interface.get("namespace") != self.plan["namespace"]
                or interface.get("runtime_arn") != self.plan["agentcore_arn"]):
            raise ValueError("The previously qualified server or its manifests changed")
        deployment = json.loads(Path(deployment_path).read_text())
        import boto3
        from botocore.config import Config
        current = boto3.client("bedrock-agentcore-control", region_name=self.plan["region"],
                               config=Config(retries={"total_max_attempts": 1})).get_agent_runtime(
                                   agentRuntimeId=deployment["runtime_id"])
        if (deployment["release_sha256"] != self.digest
                or deployment["runtime_arn"] != self.plan["agentcore_arn"]
                or current["status"] != "READY" or current["agentRuntimeVersion"] != deployment["version"]
                or current.get("environmentVariables", {}).get("MCPKART_RELEASE_SHA256") != self.digest):
            raise ValueError("The manual-session AgentCore runtime is not ready")
        for path in map(Path, (clock_path, interface_path, deployment_path)):
            stat = path.stat()
            self.bound[path] = (stat.st_ino, stat.st_size, stat.st_mtime_ns)
        _write_new(self.path.parent / (self.logical_id + "-claimed.json"), {
            "release_sha256": self.digest, "logical_id": self.logical_id, "runtime": runtime,
            "budget_before": json.loads(self.budget.path.read_text()),
            "no_retries_or_replacement": True, "user_waived_new_audit": True,
            "reused_qualification_not_new_measurements": True,
        })
