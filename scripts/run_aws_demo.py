"""Run one registered race on EC2, locking and reconciling the local ledger."""

import argparse
import fcntl
import hashlib
import json
import os
import shlex
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from demo_host import clients

from mcpkart.demo_admission import release_digest

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "artifacts/aws-demo-encore-release-20261110-v1"
CLOCK = "artifacts/aws-demo-encore-clock-20261110-v1/clock/qualification.json"
INTERFACE = "artifacts/aws-demo-encore-cloud-free-20261110-v1/trial/interface-proof.json"


def reject_existing_attempt(directory, release, identity):
    claim = release / f"{identity}-claimed.json"
    if not directory.exists() and not claim.exists():
        return
    detail = "A prior attempt exists; its submission must not be retried."
    try:
        saved = json.loads((directory / "observed-exit.json").read_text())
        detail = (f"Saved AWS result: {saved['status']}, exit {saved['response_code']}, "
                  f"ended {saved['ended']}.")
    except (OSError, ValueError, KeyError, TypeError):
        pass
    raise SystemExit(
        f"Stage entry {identity} has already been attempted or claimed.\n"
        f"{detail}\nEvidence: {directory}\n"
        "No new AWS command was sent. Preserve this directory and the release claim. "
        "Another live race requires a newly authorized, reviewed entry."
    )


def next_manual_entry(plan):
    for identity in plan["entries"]:
        output = "artifacts/aws-demo-live-" + identity
        directory = ROOT / output
        claim = ROOT / RELEASE / (identity + "-claimed.json")
        if directory.exists() or claim.exists():
            if not (ROOT / RELEASE / (identity + "-review.json")).exists():
                raise SystemExit(f"Previous race {identity} needs its exit/ledger reconciled; no duplicate submitted.")
            continue
        return identity, output, directory
    raise SystemExit("Today's manual demo session has no unused race identities left.")


def pending_manual_entry(plan):
    for identity in plan["entries"]:
        directory = ROOT / ("artifacts/aws-demo-live-" + identity)
        release = ROOT / RELEASE
        if (directory.exists() or (release / (identity + "-claimed.json")).exists()) and not (
            release / (identity + "-review.json")
        ).exists():
            return directory
    return None


def reconcile_ledger(directory, ledger):
    transfer = json.loads((directory / "ledger-transfer.json").read_text())
    after = (directory / "budget-after.json").read_bytes()
    state, old = json.loads(after), transfer["budget_before"]
    for key in ("requests", "charged_usd", "charged_tokens", "uncertain_requests", "reported_cost_usd"):
        if state[key] < old[key]:
            raise RuntimeError("Remote ledger regressed; preserve evidence and stop")
    for key in ("cap_usd", "max_requests", "max_tokens"):
        if state[key] != old[key]:
            raise RuntimeError("Remote budget metadata changed; preserve evidence and stop")
    current = ledger.read_bytes()
    if json.loads(current) == state:
        return state  # Interrupted after the atomic handoff: do not charge twice.
    if hashlib.sha256(current).hexdigest() != transfer["local_before_sha256"]:
        raise RuntimeError("Local ledger differs from both saved boundaries; preserve both and stop")
    temporary = ledger.with_name("budget-remote-handoff.tmp")
    # A leftover temporary file has no authority over either saved boundary.
    with temporary.open("wb") as stream:
        stream.write(after)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(ledger)
    return state


def finish_existing_run(directory, plan, ledger):
    """Watch/fetch the original SSM command; this function cannot submit a race."""
    receipt_path = directory / "ssm-command.json"
    if not receipt_path.exists():
        raise SystemExit(f"No saved SSM receipt in {directory}; submission outcome needs inspection. Nothing resubmitted.")
    host, ssm, _ = clients()
    receipt = json.loads(receipt_path.read_text())
    identity = json.loads((directory / "ledger-transfer.json").read_text())["logical_id"]
    while True:
        result = ssm.get_command_invocation(CommandId=receipt["command"], InstanceId=host["instance"])
        status = result["Status"]
        print(json.dumps({"remote_status": status, "logical_id": identity}), flush=True)
        if status not in ("Pending", "InProgress", "Delayed"):
            break
        time.sleep(15)
    observed = {"status": status, "response_code": result["ResponseCode"],
                "started": result.get("ExecutionStartDateTime"), "ended": result.get("ExecutionEndDateTime")}
    (directory / "observed-exit.json").write_text(json.dumps(observed, indent=2))
    helper = [sys.executable, str(ROOT / "scripts/demo_host.py")]
    subprocess.run([*helper, "fetch", directory.name], cwd=ROOT, check=True)
    state = reconcile_ledger(directory, ledger)
    if plan.get("manual_invocations_only"):
        completed = json.loads((directory / "trial/collection.json").read_text())
        if (result["ResponseCode"] != 0 or completed["budget_after"] != state or state["pending"]
                or not completed.get("collection_complete") or not completed.get("source_unchanged")
                or any(e["type"] != "provider_error" for e in completed["errors"])):
            raise RuntimeError("Race evidence is incomplete; preserve it before starting another race")
        if plan.get("user_waived_new_audit"):
            reviewed = {"release_sha256": release_digest(plan), "observed_exit_and_reconciled": True,
                        "only_provider_errors_or_none": True, "budget_after": state,
                        "user_waived_new_audit": True}
        else:
            from demo_host_audit import audit_completed_run
            reviewed = audit_completed_run(directory, plan, state, RELEASE)
        review_path = ROOT / RELEASE / (identity + "-review.json")
        if review_path.exists():
            if json.loads(review_path.read_text()) != reviewed:
                raise RuntimeError("Existing review differs; refusing to overwrite it")
        else:
            with review_path.open("x") as stream:
                json.dump(reviewed, stream, indent=2)
    print(json.dumps({"observed_remote_exit": result["ResponseCode"], "ledger_reconciled": True,
                      "requests": state["requests"], "charged_usd": state["charged_usd"],
                      "charged_tokens": state["charged_tokens"], "uncertainties": state["uncertain_requests"]}), flush=True)
    return 0 if status == "Success" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", choices=("race", "resume", "rehearsal", "stage"))
    args = parser.parse_args()
    plan = json.loads((ROOT / RELEASE / "release.json").read_text())
    # Each invocation uses a fresh identity from the current dated release.
    if args.entry == "rehearsal":
        raise ValueError("The rehearsal is closed; only the unrun stage entry remains")
    interface_registration = json.loads(
        (ROOT / Path(INTERFACE).parent / "demo-registration.json").read_text()
    )
    if interface_registration.get("local_activities") is not False:
        raise ValueError("The exact regular-Activity Cloud interface has not passed")
    review = json.loads((ROOT / RELEASE / "qualification-review.json").read_text())
    if not (review.get("passed") and review.get("regular_activities") and review.get("budget_unchanged") and review.get("descriptive_step_results")):
        raise ValueError("Root must review the complete regular-Activity qualification")
    repeatable = plan.get("manual_invocations_only") is True
    if plan.get("activity_mode") != "regular" or not plan["entries"] or (not repeatable and len(plan["entries"]) != 1):
        raise ValueError("Expected an authorized regular-Activity release")
    identity = plan["entries"][0]
    output = "artifacts/aws-demo-regular-live-" + args.entry + "-v1"
    directory = ROOT / output
    ledger = ROOT / "artifacts/budget.json"
    writer = (ROOT / "artifacts/root-paid-writer.lock").open("a")
    fcntl.flock(writer.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    if repeatable:
        pending = pending_manual_entry(plan)
        if pending:
            print(f"Recovering the existing AWS job in {pending.name}; no race resubmitted.", flush=True)
            code = finish_existing_run(pending, plan, ledger)
            if args.entry == "resume" or code:
                return code
        elif args.entry == "resume":
            print("No interrupted race needs recovery. Run 'race' to start a new one.")
            return 0
        identity, output, directory = next_manual_entry(plan)
    reject_existing_attempt(directory, ROOT / RELEASE, identity)
    if (datetime.fromisoformat(plan["expires_utc"]) - datetime.now(UTC)).total_seconds() < 900:
        raise SystemExit("Demo session expired or has less than 15 minutes remaining. No AWS command was sent.")
    before = ledger.read_bytes()
    directory.mkdir(exist_ok=False)  # Unknown submissions cannot be retried.
    (directory / "ledger-transfer.json").write_text(json.dumps({
        "local_before_sha256": hashlib.sha256(before).hexdigest(),
        "budget_before": json.loads(before), "logical_id": identity,
        "local_writer_locked": True, "no_retry": True,
    }, indent=2))
    bootstrap = ("import json,os,runpy,sys;"
                 "os.environ.update(json.load(open('artifacts/aws-demo-temporal-private.json')));"
                 "sys.argv=['mcpkart.demo_run',*sys.argv[1:]];"
                 "runpy.run_module('mcpkart.demo_run',run_name='__main__')")
    command = ["docker", "exec", "mcpkart-demo", "python", "-c", bootstrap,
               "--paid", "--retire-provider-errors", "--url", "http://127.0.0.1:8771/mcp",
               "--release", RELEASE + "/release.json", "--clock-qualification", CLOCK,
               "--interface", INTERFACE, "--deployment", RELEASE + "/deployment.json",
               "--agentcore-arn", plan["agentcore_arn"], "--output", output + "/trial",
               "--race-id", identity, "--live-status", "artifacts/aws-demo-free-v1/live-status.json"]
    check = ("import hashlib;assert hashlib.sha256(open('artifacts/budget.json','rb').read()).hexdigest()=="
             + repr(hashlib.sha256(before).hexdigest()))
    script = "set -e\ndocker exec mcpkart-demo python -c " + shlex.quote(check) + "\nset +e\n"
    if repeatable and plan["entries"].index(identity):
        previous = plan["entries"][plan["entries"].index(identity) - 1]
        review_path = ROOT / RELEASE / (previous + "-review.json")
        payload = review_path.read_text()
        copy_review = ("import json;from pathlib import Path;p=Path(" + repr(str(review_path.relative_to(ROOT)))
                       + ");v=" + repr(payload) + ";assert not p.exists() or json.loads(p.read_text())==json.loads(v);"
                       "p.exists() or p.write_text(v)")
        script = "set -e\npython3 -c " + shlex.quote(copy_review) + "\n" + script
    script += shlex.join(command) + "\nresult=$?\n"
    script += "cp artifacts/budget.json " + shlex.quote(output + "/budget-after.json") + "\n"
    script += 'exit "$result"\n'
    path = directory / "command.sh"
    path.write_text(script)
    helper = [sys.executable, str(ROOT / "scripts/demo_host.py")]
    subprocess.run([*helper, "submit", directory.name, "--script", str(path), "--collect", RELEASE],
                   cwd=ROOT, check=True)
    return finish_existing_run(directory, plan, ledger)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nLocal watcher stopped; an already-submitted AWS race continues.\n"
              "Recover it with: .venv/bin/python scripts/run_aws_demo.py resume", file=sys.stderr)
        raise SystemExit(130) from None
