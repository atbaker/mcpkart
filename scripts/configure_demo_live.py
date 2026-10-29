"""Freeze tonight's two-entry release and update only our dedicated demo Runtime."""

import argparse
import hashlib
import json
from pathlib import Path

import boto3
from botocore.config import Config
from deploy_demo_agentcore import PREFIX, ROOT, prepare, write
from dotenv import dotenv_values

from mcpkart.demo_admission import release_digest
from mcpkart.demo_contract import MODELS
from mcpkart.duel import TRIO_RACERS
from mcpkart.duel_bench import sources


def freeze(output, resources, routes):
    output.mkdir(parents=True, exist_ok=False)
    state = json.loads(resources.read_text())
    discovered = json.loads(routes.read_text())
    by_model = {r["model"]: r for r in discovered}
    plan = {
        "study": "0087", "scope": "One rehearsal and one manually admitted stage race; no retries or replacements",
        "entries": ["mcpkart-aws-demo-rehearsal-20261029", "mcpkart-aws-demo-stage-20261029"],
        "namespace": "mcpkart-dev.iuiaz", "region": "us-west-2",
        "agentcore_arn": state["resources"]["runtime"],
        "expires_utc": "2026-10-30T07:00:00+00:00", "deadline_s": 180, "max_decisions": 1100,
        "models": list(MODELS), "routes": {r: by_model[m] for r, m in zip(TRIO_RACERS, MODELS, strict=True)},
        "source_sha256": sources(), "budget_boundary": json.loads((ROOT / "artifacts/budget.json").read_text()),
        "setup": {"seed": 0, "racer_ids": list(TRIO_RACERS), "contact": "ghost"},
        "profiles": {"geometry": False, "motion": False, "timing_facts": False, "prompt": "goal-only"},
        "gate": "Four complete trio controls, parent pause, 170.1s neutral; exact cloud mock interface",
        "root_review_between_entries": True,
    }
    write(output / "release.json", plan)
    print(json.dumps({"release_sha256": release_digest(plan), "model_calls": 0}), flush=True)


def update(output, resources, package):
    plan = json.loads((output / "release.json").read_text())
    digest = release_digest(plan)
    if plan["source_sha256"] != sources():
        raise ValueError("Source changed after release freeze")
    state = json.loads(resources.read_text())
    own = state["resources"]
    if state["prefix"] != PREFIX or state["region"] != plan["region"] or own["runtime"] != plan["agentcore_arn"]:
        raise ValueError("Only this chat's dedicated Runtime can be updated")
    cfg = Config(retries={"total_max_attempts": 1})
    session = boto3.Session(region_name=plan["region"])
    if session.client("sts", config=cfg).get_caller_identity()["Account"] != state["account"]:
        raise ValueError("Wrong AWS sandbox")
    secrets = session.client("secretsmanager", config=cfg)
    name = PREFIX + "/openrouter"
    try:
        secret_arn = secrets.describe_secret(SecretId=name)["ARN"]
    except secrets.exceptions.ResourceNotFoundException:
        credential = dotenv_values(ROOT / ".env").get("OPENROUTER_API_KEY")
        if not credential:
            raise ValueError("OPENROUTER_API_KEY is missing from the private .env")
        secret_arn = secrets.create_secret(Name=name, SecretString=credential,
                                           Tags=[{"Key": "Project", "Value": "MCPKart"}])["ARN"]
    # Receipt contains only the ARN, never the secret value.
    write(output / "secret-resource.json", {"secret_arn": secret_arn})
    archive = package / "deployment.zip"
    key = hashlib.sha256(archive.read_bytes()).hexdigest() + "/deployment.zip"
    session.client("s3", config=cfg).upload_file(str(archive), own["bucket"], key)
    iam = session.client("iam", config=cfg)
    role_name = own["role"].rsplit("/", 1)[-1]
    if role_name != PREFIX + "-runtime":
        raise ValueError("Unexpected role identity")
    policy = iam.get_role_policy(RoleName=role_name, PolicyName=PREFIX)["PolicyDocument"]
    policy["Statement"].append({"Effect": "Allow", "Action": "s3:GetObject",
                                 "Resource": f"arn:aws:s3:::{own['bucket']}/{key}"})
    policy["Statement"].append({"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": secret_arn})
    iam.put_role_policy(RoleName=role_name, PolicyName=PREFIX, PolicyDocument=json.dumps(policy))
    control = session.client("bedrock-agentcore-control", config=cfg)
    current = control.get_agent_runtime(agentRuntimeId=own["runtime_id"])
    result = control.update_agent_runtime(
        agentRuntimeId=own["runtime_id"], roleArn=own["role"],
        agentRuntimeArtifact={"codeConfiguration": {"code": {"s3": {"bucket": own["bucket"], "prefix": key}},
                                                   "runtime": "PYTHON_3_12", "entryPoint": ["main.py"]}},
        networkConfiguration=current["networkConfiguration"],
        lifecycleConfiguration={"idleRuntimeSessionTimeout": 300, "maxLifetime": 1800},
        environmentVariables={"MCPKART_RELEASE_SHA256": digest,
                              "MCPKART_EXPIRES_UTC": plan["expires_utc"],
                              "MCPKART_OPENROUTER_SECRET_ARN": secret_arn},
        description="MCP Kart finite 2026-10-29 demo; OpenRouter Decisions via IAM-authenticated AgentCore",
    )
    write(output / "deployment.json", {"release_sha256": digest, "runtime_arn": own["runtime"],
                                       "runtime_id": own["runtime_id"], "version": result["agentRuntimeVersion"],
                                       "code_sha256": key.split("/")[0], "secret_arn": secret_arn})
    print(json.dumps({"runtime_id": own["runtime_id"], "version": result["agentRuntimeVersion"],
                      "status": result["status"], "model_calls": 0}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "package", "update"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resources", type=Path, default=ROOT / "artifacts/aws-demo-package-v3/aws-resources.json")
    parser.add_argument("--routes", type=Path, default=ROOT / "artifacts/aws-demo-live-readiness-v1/routes.json")
    parser.add_argument("--package", type=Path)
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze(args.output, args.resources, args.routes)
    elif args.mode == "package":
        prepare(args.output)
    else:
        update(args.output, args.resources, args.package)


if __name__ == "__main__":
    main()
