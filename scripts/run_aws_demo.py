"""Run one registered demo entry on the already-qualified Linux server.

Refreshes only this demo's ignored AWS credential file; never restarts the server.
"""

import argparse
import json
import os
import subprocess
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]
RELEASE = "artifacts/aws-demo-live-release-v1"
CONTAINER = "mcpkart-demo-linux-20261029"


def credentials():
    frozen = boto3.Session().get_credentials().get_frozen_credentials()
    path = ROOT / "artifacts/aws-demo-linux-credentials"
    # The directory is private and ignored; credentials never enter argv or logs.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write("[default]\naws_access_key_id=" + frozen.access_key
                     + "\naws_secret_access_key=" + frozen.secret_key
                     + "\naws_session_token=" + (frozen.token or "") + "\n")
    path.chmod(0o600)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", choices=("rehearsal", "stage", "credentials"))
    args = parser.parse_args()
    credentials()
    if args.entry == "credentials":
        print("Dedicated demo credential file refreshed; no model requests")
        return
    plan = json.loads((ROOT / RELEASE / "release.json").read_text())
    identity = plan["entries"][0 if args.entry == "rehearsal" else 1]
    command = ["docker", "exec", CONTAINER, "python", "-m", "mcpkart.demo_run", "--paid", "--local",
               "--url", "http://127.0.0.1:8771/mcp", "--release", RELEASE + "/release.json",
               "--clock-qualification", "artifacts/aws-demo-linux-clock-v1/qualification.json",
               "--interface", "artifacts/aws-demo-cloud-interface-v1/trial/interface-proof.json",
               "--deployment", RELEASE + "/deployment.json", "--agentcore-arn", plan["agentcore_arn"],
               "--output", "artifacts/aws-demo-live-" + args.entry + "-v1/trial", "--race-id", identity,
               "--live-status", "artifacts/aws-demo-free-v1/live-status.json"]
    raise SystemExit(subprocess.call(command, cwd=ROOT))


if __name__ == "__main__":
    main()
