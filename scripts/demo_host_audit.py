"""Replay saved physics in its qualified Linux environment, without model calls."""

import hashlib
import json
import shlex
import subprocess
import sys
import tarfile
import time
from pathlib import Path

from demo_host import clients

from mcpkart.demo_admission import release_digest

ROOT = Path(__file__).resolve().parents[1]
AUDIT_VERSION = 2
DRIVER = '''import fcntl,json,sys
from pathlib import Path
from mcpkart.duel_bench import sources
from mcpkart.duel_clock import sha
from mcpkart.demo_admission import release_digest
here=Path(__file__).parent
sys.path.insert(0,str(here))
from audit_demo_run import audit_run
data=json.loads((here/'input.json').read_text())
directory=Path(data['directory'])
plan=json.loads(Path(data['release']).read_text())
writer=Path('artifacts/root-paid-writer.lock').open('a')
fcntl.flock(writer.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
assert release_digest(plan)==data['release_sha256']
assert sources()==plan['source_sha256']
assert json.loads(Path('artifacts/budget.json').read_text())==data['budget']
for name,digest in data['evidence_sha256'].items():
 assert sha(directory/'trial'/name)==digest, name
observed=directory/'observed-exit.json'
if observed.exists():assert json.loads(observed.read_text())==data['observed_exit']
else:
 with observed.open('x') as stream:json.dump(data['observed_exit'],stream,indent=2)
review=audit_run(directory,plan,data['budget'])
for name,digest in data['evidence_sha256'].items():
 assert sha(directory/'trial'/name)==digest, name
review.update(audit_environment='qualified-linux-container',
 evidence_manifest_sha256=sha(here/'input.json'),
 observed_ssm_command=data['observed_ssm_command'])
with (here/'review.json').open('x') as stream:json.dump(review,stream,indent=2)
print(json.dumps({'independent_linux_audit_passed':True,
 'exact_descriptive_receipts':review['exact_descriptive_receipts']}),flush=True)
'''


def audit_completed_run(directory, plan, ledger, release):
    """Submit one free audit, or reattach to its saved command after interruption."""
    directory = Path(directory)
    job = directory.name + f"-audit-v{AUDIT_VERSION}"
    output = ROOT / "artifacts" / job
    receipt = output / "ssm-command.json"
    if (output / "submission-intent.json").exists() and not receipt.exists():
        raise RuntimeError("Audit submission outcome unknown; preserve it without redispatch")
    helper = [sys.executable, str(ROOT / "scripts/demo_host.py")]
    host, ssm, s3 = clients()
    if not receipt.exists():
        output.mkdir(exist_ok=True)
        evidence = {
            str(p.relative_to(directory / "trial")): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((directory / "trial").rglob("*"))
            if p.is_file() and not p.name.endswith(("-shm", "-wal"))
        }
        data = {"directory": str(directory.relative_to(ROOT)), "release": release + "/release.json",
                "release_sha256": release_digest(plan), "budget": ledger, "evidence_sha256": evidence,
                "observed_exit": json.loads((directory / "observed-exit.json").read_text()),
                "observed_ssm_command": json.loads((directory / "ssm-command.json").read_text())["command"]}
        (output / "input.json").write_text(json.dumps(data, indent=2))
        (output / "run.py").write_text(DRIVER)
        for name in ("audit_demo_run.py", "audit_demo_wire.py"):
            (output / name).write_bytes((ROOT / "scripts" / name).read_bytes())
        archive = output / "install.tar.gz"
        with tarfile.open(archive, "w:gz") as bundle:
            for name in ("input.json", "run.py", "audit_demo_run.py", "audit_demo_wire.py"):
                bundle.add(output / name, arcname=str((output / name).relative_to(ROOT)))
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        key = "operator/audits/" + digest + ".tar.gz"
        s3.upload_file(str(archive), host["bucket"], key)
        remote_archive = "/tmp/" + job + ".tar.gz"
        script = "set -e\naws s3 cp " + shlex.quote("s3://" + host["bucket"] + "/" + key)
        script += " " + shlex.quote(remote_archive) + " --only-show-errors --region us-west-2\n"
        script += "echo " + shlex.quote(digest + "  " + remote_archive) + " | sha256sum -c -\n"
        script += "tar -xzf " + shlex.quote(remote_archive) + " -C /opt/mcpkart\n"
        script += "docker exec mcpkart-demo python " + shlex.quote(str((output / "run.py").relative_to(ROOT))) + "\n"
        (output / "command.sh").write_text(script)
        subprocess.run([*helper, "submit", job, "--script", str(output / "command.sh")], cwd=ROOT, check=True)
    saved = json.loads(receipt.read_text())
    while True:
        result = ssm.get_command_invocation(CommandId=saved["command"], InstanceId=host["instance"])
        if result["Status"] not in ("Pending", "InProgress", "Delayed"):
            break
        print(json.dumps({"independent_audit_status": result["Status"]}), flush=True)
        time.sleep(5)
    subprocess.run([*helper, "fetch", job], cwd=ROOT, check=True)
    if result["Status"] != "Success" or result["ResponseCode"] != 0:
        raise RuntimeError("Independent Linux audit failed; preserve evidence before another race")
    review = json.loads((output / "review.json").read_text())
    data = json.loads((output / "input.json").read_text())
    if (review.get("release_sha256") != release_digest(plan) or review.get("budget_after") != ledger
            or not review.get("observed_exit_and_audited")
            or review.get("audit_environment") != "qualified-linux-container"
            or review.get("evidence_manifest_sha256") != hashlib.sha256((output / "input.json").read_bytes()).hexdigest()
            or data["observed_exit"] != json.loads((directory / "observed-exit.json").read_text())
            or data["observed_ssm_command"] != json.loads((directory / "ssm-command.json").read_text())["command"]):
        raise RuntimeError("Independent audit does not match the observed race and accounting")
    for name, expected in data["evidence_sha256"].items():
        if hashlib.sha256((directory / "trial" / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("Downloaded race evidence changed after the independent audit")
    return review
