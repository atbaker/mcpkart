"""Stop only AgentCore mock sessions named in this demo's saved wire evidence."""

import argparse
import json
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording_directory", type=Path)
    parser.add_argument("--region", default="us-west-2")
    args = parser.parse_args()
    sessions = set()
    for path in args.recording_directory.rglob("agentcore-wire/*.json"):
        evidence = json.loads(path.read_text())
        arn = evidence["runtime_arn"]
        if ":runtime/mcpkart_aws_demo_20261029-" not in arn:
            raise ValueError("Evidence does not belong to the dedicated MCP Kart runtime")
        sessions.add((arn, evidence["session_id"]))
    if not sessions:
        raise ValueError("No recorded demo sessions were found")
    client = boto3.client("bedrock-agentcore", region_name=args.region,
                          config=Config(retries={"total_max_attempts": 1}))
    for arn, session in sorted(sessions):
        try:
            result = client.stop_runtime_session(agentRuntimeArn=arn, runtimeSessionId=session)
            status = {"http_status": result["ResponseMetadata"]["HTTPStatusCode"]}
        except ClientError as error:
            if error.response["Error"]["Code"] != "ResourceNotFoundException":
                raise
            status = {"already_ended": True}
        print(json.dumps({"session_id": session, **status}))


if __name__ == "__main__":
    main()
