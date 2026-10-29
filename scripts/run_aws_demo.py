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
from pathlib import Path

from demo_host import clients

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "artifacts/aws-demo-regular-release-v1"
CLOCK = "artifacts/aws-demo-ec2-clock-v1/evidence/qualification.json"
INTERFACE = "artifacts/aws-demo-ec2-regular-free-v2/trial/interface-proof.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", choices=("rehearsal", "stage"))
    args = parser.parse_args()
    plan = json.loads((ROOT / RELEASE / "release.json").read_text())
    # Both original Local Activity entries are consumed. Only the new,
    # single manually invoked regular-Activity entry may dispatch.
    if args.entry == "rehearsal":
        raise ValueError("The rehearsal is closed; only the unrun stage entry remains")
    interface_registration = json.loads(
        (ROOT / Path(INTERFACE).parent / "demo-registration.json").read_text()
    )
    if interface_registration.get("local_activities") is not False:
        raise ValueError("The exact regular-Activity Cloud interface has not passed")
    review = json.loads((ROOT / RELEASE / "qualification-review.json").read_text())
    if not (review.get("passed") and review.get("regular_activities") and review.get("budget_unchanged")):
        raise ValueError("Root must review the complete regular-Activity qualification")
    if plan.get("activity_mode") != "regular" or len(plan["entries"]) != 1:
        raise ValueError("Expected the single-entry regular-Activity release")
    identity = plan["entries"][0]
    output = "artifacts/aws-demo-regular-live-" + args.entry + "-v1"
    directory = ROOT / output
    ledger = ROOT / "artifacts/budget.json"
    writer = (ROOT / "artifacts/root-paid-writer.lock").open("a")
    fcntl.flock(writer.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
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
    script += shlex.join(command) + "\nresult=$?\n"
    script += "cp artifacts/budget.json " + shlex.quote(output + "/budget-after.json") + "\n"
    script += 'exit "$result"\n'
    path = directory / "command.sh"
    path.write_text(script)
    helper = [sys.executable, str(ROOT / "scripts/demo_host.py")]
    subprocess.run([*helper, "submit", directory.name, "--script", str(path), "--collect", RELEASE],
                   cwd=ROOT, check=True)
    host, ssm, _ = clients()
    receipt = json.loads((directory / "ssm-command.json").read_text())
    while True:
        time.sleep(15)
        result = ssm.get_command_invocation(CommandId=receipt["command"], InstanceId=host["instance"])
        status = result["Status"]
        print(json.dumps({"remote_status": status, "logical_id": identity}), flush=True)
        if status not in ("Pending", "InProgress", "Delayed"):
            break
    (directory / "observed-exit.json").write_text(json.dumps({
        "status": status, "response_code": result["ResponseCode"],
        "started": result.get("ExecutionStartDateTime"), "ended": result.get("ExecutionEndDateTime"),
    }, indent=2))
    subprocess.run([*helper, "fetch", directory.name], cwd=ROOT, check=True)
    after = (directory / "budget-after.json").read_bytes()
    state, old = json.loads(after), json.loads(before)
    if ledger.read_bytes() != before:
        raise RuntimeError("Local ledger changed despite writer lock; preserve both for root review")
    for key in ("requests", "charged_usd", "charged_tokens", "uncertain_requests"):
        if state[key] < old[key]:
            raise RuntimeError("Remote ledger regressed; preserve evidence and stop")
    for key in ("cap_usd", "max_requests", "max_tokens"):
        if state[key] != old[key]:
            raise RuntimeError("Remote budget caps changed; preserve evidence and stop")
    temporary = ledger.with_name("budget-remote-handoff.tmp")
    with temporary.open("xb") as stream:
        stream.write(after)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(ledger)
    print(json.dumps({"observed_remote_exit": result["ResponseCode"], "ledger_reconciled": True,
                      "requests": state["requests"], "charged_usd": state["charged_usd"],
                      "charged_tokens": state["charged_tokens"], "uncertainties": state["uncertain_requests"],
                      "root_audit_required_before_next_entry": True}), flush=True)
    raise SystemExit(0 if status == "Success" else 1)


if __name__ == "__main__":
    main()
