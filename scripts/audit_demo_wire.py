"""Independently match every AgentCore envelope to saved native call bytes."""

import argparse
import base64
import hashlib
import json
from pathlib import Path


def audit(directory):
    directory = Path(directory)
    registration = json.loads((directory / "demo-registration.json").read_text())
    identifiers, operations = set(), set()
    native_count = outer_count = missing_outer_responses = 0
    statuses = {}
    for rid in ("red", "blue", "green"):
        packets = sorted((directory / rid / "agentcore-wire").glob("*.json"))
        calls = sorted((directory / rid / "calls").glob("*.json"))
        assert len(packets) == len(calls) + 1
        session = None
        for index, path in enumerate(packets):
            packet = json.loads(path.read_text())
            request = json.loads(base64.b64decode(packet["request_b64"], validate=True))
            assert request["operation_id"] not in operations
            operations.add(request["operation_id"])
            body = base64.b64decode(request["request_b64"], validate=True)
            assert hashlib.sha256(body).hexdigest() == request["request_sha256"]
            assert request["mode"] == ("paid" if registration["model_requests_enabled"] and index else "mock")
            if "response_b64" not in packet:
                assert index and path.name.endswith("-failure.json")
                assert packet["type"] and packet["unknown_billing"] == registration["model_requests_enabled"]
                capture = json.loads(calls[index - 1].read_text())
                sent, received = capture["wire"]["requests"], capture["wire"]["responses"]
                assert len(sent) == 1 and not received and body == sent[0]["body_utf8"].encode("utf-8")
                assert not capture["record"]["ok"] and capture["record"]["cost_source"] == "reservation"
                assert not capture["record"]["usage"]
                missing_outer_responses += 1
                statuses["no_reply"] = statuses.get("no_reply", 0) + 1
                native_count += 1
                outer_count += 1
                continue
            response = json.loads(base64.b64decode(packet["response_b64"], validate=True))
            meta = packet["aws_response_metadata"]
            assert meta["HTTPStatusCode"] == 200 and meta["RetryAttempts"] == 0
            assert meta["RequestId"] not in identifiers
            identifiers.add(meta["RequestId"])
            assert packet["runtime_arn"] == registration["agentcore_runtime_arn"]
            if session is None:
                session = packet["session_id"]
            assert packet["session_id"] == session
            assert packet["response_received_ns"] >= packet["request_started_ns"]
            assert request["request_sha256"] == response["request_sha256"]
            native = base64.b64decode(response["response_b64"], validate=True)
            if index:
                capture = json.loads(calls[index - 1].read_text())
                sent = capture["wire"]["requests"]
                received = capture["wire"]["responses"]
                assert len(sent) == len(received) == 1
                assert body == sent[0]["body_utf8"].encode("utf-8")
                assert native == received[0]["body_utf8"].encode("utf-8")
                assert response["status"] == received[0]["status"]
                assert hashlib.sha256(native).hexdigest() == received[0]["body_sha256"]
                assert json.loads(body)["provider"]["allow_fallbacks"] is False
                statuses[str(response["status"])] = statuses.get(str(response["status"]), 0) + 1
                native_count += 1
            else:
                assert request["mode"] == "mock" and response["status"] == 200
            outer_count += 1
    return {"passed": True, "outer_invocations": outer_count, "native_calls": native_count,
            "native_statuses": statuses, "observed_sdk_retries": 0,
            "missing_outer_responses": missing_outer_responses,
            "exact_available_native_bytes": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.directory), indent=2))


if __name__ == "__main__":
    main()
