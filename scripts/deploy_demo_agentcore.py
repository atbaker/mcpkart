"""Prepare/deploy only this branch's dedicated mock Runtime in the AWS sandbox.

The execution role has no Bedrock inference or secret-read permissions. Deployment
does not enable model calls. The receipt names every resource created here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import boto3
from botocore.config import Config

PREFIX = "mcpkart-aws-demo-20261029"
RUNTIME_NAME = PREFIX.replace("-", "_")
ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)


def prepare(output):
    output.mkdir(parents=True, exist_ok=False)
    requirements = subprocess.check_output([
        "uv", "export", "--locked", "--extra", "demo", "--no-dev", "--no-emit-project",
        "--format", "requirements-txt", "--no-hashes", "--python", sys.executable,
    ], cwd=ROOT, env={**os.environ, "UV_CACHE_DIR": "/tmp/mcpkart-uv-cache"})
    (output / "requirements.txt").write_bytes(requirements)
    package = output / "package"
    subprocess.run([
        "uv", "pip", "install", "--python-platform", "aarch64-manylinux2014",
        "--python-version", "3.12", "--only-binary", ":all:",
        "--target", str(package), "-c", str(output / "requirements.txt"), "bedrock-agentcore",
    ], check=True, cwd=ROOT, env={**os.environ, "UV_CACHE_DIR": "/tmp/mcpkart-uv-cache"})
    archive = output / "deployment.zip"
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as target:
        for path in sorted(package.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                target.write(path, path.relative_to(package))
        for name in ("__init__.py", "demo_agentcore.py", "demo_contract.py", "demo_mock.py"):
            path = ROOT / "src" / "mcpkart" / name
            target.write(path, path.relative_to(ROOT / "src"))
        target.writestr("main.py", "from mcpkart.demo_agentcore import app\napp.run()\n")
    with zipfile.ZipFile(archive) as target:
        assert target.testzip() is None
    write(output / "package.json", {
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "bytes": archive.stat().st_size, "runtime": "PYTHON_3_12", "architecture": "linux-arm64",
        "model_requests_enabled": False,
    })
    print(json.dumps({"prepared": str(archive), "bytes": archive.stat().st_size}), flush=True)


def deploy(output, region, expected_account):
    # No retries on resource creation; retain a progress receipt after each mutation.
    cfg = Config(retries={"total_max_attempts": 1})
    session = boto3.Session(region_name=region)
    identity = session.client("sts", config=cfg).get_caller_identity()
    if identity["Account"] != expected_account:
        raise ValueError("AWS account differs from the explicitly selected sandbox")
    control = session.client("bedrock-agentcore-control", config=cfg)
    existing = control.get_paginator("list_agent_runtimes").paginate()
    if any(r["agentRuntimeName"] == RUNTIME_NAME for page in existing for r in page["agentRuntimes"]):
        raise ValueError("Dedicated runtime already exists; refusing to overwrite it")
    receipt = output / "aws-resources.json"
    if receipt.exists():
        raise ValueError("A deployment receipt exists; inspect it rather than repeating resource creation")
    state = {"account": expected_account, "region": region, "prefix": PREFIX,
             "model_requests_enabled": False, "resources": {}}
    write(receipt, state)

    def save(kind, value):
        state["resources"][kind] = value
        temporary = receipt.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2))
        temporary.replace(receipt)

    bucket = f"{PREFIX}-{expected_account}-{region}"
    s3 = session.client("s3", config=cfg)
    s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": region})
    save("bucket", bucket)
    s3.put_public_access_block(Bucket=bucket, PublicAccessBlockConfiguration={
        "BlockPublicAcls": True, "IgnorePublicAcls": True,
        "BlockPublicPolicy": True, "RestrictPublicBuckets": True,
    })
    s3.put_bucket_tagging(Bucket=bucket, Tagging={"TagSet": [
        {"Key": "Project", "Value": "MCPKart"}, {"Key": "DemoDate", "Value": "2026-10-29"},
    ]})
    archive = output / "deployment.zip"
    key = hashlib.sha256(archive.read_bytes()).hexdigest() + "/deployment.zip"
    s3.upload_file(str(archive), bucket, key)
    save("code_key", key)

    iam = session.client("iam", config=cfg)
    role_name = PREFIX + "-runtime"
    role = iam.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps({
        "Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "sts:AssumeRole",
        "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
        "Condition": {"StringEquals": {"aws:SourceAccount": expected_account},
                      "ArnLike": {"aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{expected_account}:*"}}}],
    }), Tags=[{"Key": "Project", "Value": "MCPKart"}])["Role"]
    save("role", role["Arn"])
    iam.put_role_policy(RoleName=role_name, PolicyName=PREFIX, PolicyDocument=json.dumps({
        "Version": "2012-10-17", "Statement": [
            {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": f"arn:aws:s3:::{bucket}/{key}"},
            {"Effect": "Allow", "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
             "Resource": f"arn:aws:logs:{region}:{expected_account}:log-group:/aws/bedrock-agentcore/runtimes/{RUNTIME_NAME}*"},
        ],
    }))
    # IAM propagation only; no model or Runtime invocation is retried.
    time.sleep(10)
    result = control.create_agent_runtime(
        agentRuntimeName=RUNTIME_NAME, roleArn=role["Arn"],
        agentRuntimeArtifact={"codeConfiguration": {
            "code": {"s3": {"bucket": bucket, "prefix": key}},
            "runtime": "PYTHON_3_12", "entryPoint": ["main.py"],
        }}, networkConfiguration={"networkMode": "PUBLIC"},
        lifecycleConfiguration={"idleRuntimeSessionTimeout": 300, "maxLifetime": 1800},
        description="MCP Kart three-kart transport rehearsal; scripted mocks only",
        tags={"Project": "MCPKart", "DemoDate": "2026-10-29"},
    )
    save("runtime", result["agentRuntimeArn"])
    save("runtime_id", result["agentRuntimeId"])
    print(json.dumps(state), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--deploy", action="store_true", help="Create only dedicated mock resources")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--expected-account")
    args = parser.parse_args()
    if args.deploy:
        if not args.expected_account or args.region != "us-west-2":
            parser.error("Deployment requires --expected-account and the selected us-west-2 sandbox")
        deploy(args.output.resolve(), args.region, args.expected_account)
    else:
        prepare(args.output.resolve())


if __name__ == "__main__":
    main()
