"""Submit once and inspect jobs on the dedicated MCP Kart SSM host.

Commands and collected paths must contain no credentials. Collection is explicit;
the private Temporal file is never part of an artifact upload.
"""

import argparse
import hashlib
import json
import shlex
import tarfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from botocore.config import Config

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "artifacts/aws-demo-ec2-v1/resources.json"


def clients():
    host = json.loads(HOST.read_text())
    session = boto3.Session(region_name=host["region"])
    config = Config(retries={"total_max_attempts": 1})
    return host["resources"], session.client("ssm", config=config), session.client("s3", config=config)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("submit", "status", "fetch"))
    parser.add_argument("job", help="Unique artifact directory basename")
    parser.add_argument("--script", type=Path)
    parser.add_argument("--collect", action="append", default=[])
    args = parser.parse_args()
    if not args.job.startswith("aws-demo-") or "/" in args.job:
        parser.error("Use a dedicated aws-demo- job name")
    host, ssm, s3 = clients()
    output = ROOT / "artifacts" / args.job
    receipt = output / "ssm-command.json"
    if args.mode == "submit":
        script = args.script.read_text()
        intent = output / "submission-intent.json"
        if receipt.exists() or intent.exists():
            raise ValueError("Job submission already attempted; inspect it, never resubmit")
        output.mkdir(exist_ok=True)
        paths = ["artifacts/" + args.job, *args.collect]
        for path in paths:
            if not path.startswith("artifacts/aws-demo-") or any(x in path for x in ("..", "private", "credentials")):
                raise ValueError("Only explicit non-secret demo artifacts may be collected")
        remote = "set -u\ncd /opt/mcpkart\nmkdir -p " + shlex.quote(paths[0]) + "\n"
        remote += "(\n" + script + "\n) > " + shlex.quote(paths[0] + "/job.log") + " 2>&1\n"
        remote += "result=$?\nprintf '%s\\n' \"$result\" > " + shlex.quote(paths[0] + "/exit-code") + "\n"
        archive_key = "operator/archives/" + args.job + ".tar.gz"
        archive_path = "/tmp/" + args.job + ".tar.gz"
        remote += "tar -czf " + shlex.quote(archive_path) + " -- " + shlex.join(paths) + "\n"
        remote += "aws s3 cp " + shlex.quote(archive_path) + " " + shlex.quote("s3://" + host["bucket"] + "/" + archive_key) + " --only-show-errors --region us-west-2\n"
        remote += 'exit "$result"\n'
        # Persist before the API call: a lost response must not admit a second
        # remote command, especially when that command can make paid requests.
        with intent.open("x") as stream:
            json.dump({"script_sha256": hashlib.sha256(remote.encode()).hexdigest(),
                       "collect": paths, "no_resubmit_after_unknown_outcome": True}, stream, indent=2)
        result = ssm.send_command(InstanceIds=[host["instance"]], DocumentName="AWS-RunShellScript",
                                  Parameters={"commands": [remote], "executionTimeout": ["1200"]},
                                  Comment="MCP Kart " + args.job)
        receipt.write_text(json.dumps({"command": result["Command"]["CommandId"], "collect": paths,
                                       "archive_key": archive_key}, indent=2))
        print(receipt.read_text())
    elif args.mode == "status":
        result = ssm.get_command_invocation(CommandId=json.loads(receipt.read_text())["command"], InstanceId=host["instance"])
        print(json.dumps({k: result.get(k) for k in ("Status", "ResponseCode", "ExecutionStartDateTime", "ExecutionEndDateTime", "StandardOutputContent", "StandardErrorContent")}, indent=2))
    else:
        saved = json.loads(receipt.read_text())
        status = ssm.get_command_invocation(CommandId=saved["command"], InstanceId=host["instance"])["Status"]
        if status in ("Pending", "InProgress", "Delayed"):
            raise ValueError("Wait for the terminal SSM exit before retrieving the complete archive")
        collected = saved["collect"]
        if saved.get("archive_key"):
            archive = output / "evidence.tar.gz"
            s3.download_file(host["bucket"], saved["archive_key"], str(archive))
            with tarfile.open(archive, "r:gz") as bundle:
                members = bundle.getmembers()
                for member in members:
                    if not (member.isfile() or member.isdir()) or not any(
                        (ROOT / member.name).resolve().is_relative_to((ROOT / path).resolve()) for path in collected
                    ) or not (ROOT / member.name).resolve().is_relative_to(ROOT):
                        raise ValueError("Unexpected evidence archive member")
                bundle.extractall(ROOT, filter="data")
            print(json.dumps({"downloaded_files": sum(m.isfile() for m in members), "paths": collected,
                              "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}))
            return
        downloads = []
        for path in collected:
            prefix = "operator/evidence/" + path + "/"
            for page in s3.get_paginator("list_objects_v2").paginate(Bucket=host["bucket"], Prefix=prefix):
                for item in page.get("Contents", []):
                    local = ROOT / path / item["Key"][len(prefix):]
                    if not local.resolve().is_relative_to((ROOT / path).resolve()):
                        raise ValueError("Unexpected artifact path")
                    local.parent.mkdir(parents=True, exist_ok=True)
                    downloads.append((item["Key"], local))
        def download(item):
            key, local = item
            s3.download_file(host["bucket"], key, str(local))
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(download, downloads))
        print(json.dumps({"downloaded_files": len(downloads), "paths": collected}))


if __name__ == "__main__":
    main()
