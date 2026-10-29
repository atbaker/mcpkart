"""AgentCore bridge preserving the original Decisions wire bytes and zero retries."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import time
import uuid
from pathlib import Path

import httpx


class AgentCoreTransport(httpx.AsyncBaseTransport):
    def __init__(self, arn, region, racer_id, logical_id, *, client=None, evidence_path=None, paid=False, release_sha256=None):
        if not arn.startswith("arn:aws:bedrock-agentcore:"):
            raise ValueError("Expected an AgentCore Runtime ARN")
        if client is None:
            import boto3
            from botocore.config import Config
            client = boto3.client("bedrock-agentcore", region_name=region, config=Config(
                retries={"total_max_attempts": 1}, connect_timeout=5, read_timeout=10,
            ))
        self.client, self.arn = client, arn
        self.paid, self.release_sha256 = paid, release_sha256
        if paid and (not release_sha256 or len(release_sha256) != 64):
            raise ValueError("Live transport requires a frozen release hash")
        self.session = str(uuid.uuid5(uuid.NAMESPACE_URL, logical_id + ":" + racer_id))
        self.logical_id, self.racer_id, self.seq = logical_id, racer_id, 0
        self.evidence_path = Path(evidence_path) if evidence_path else None

    async def handle_async_request(self, request):
        if request.method != "POST" or str(request.url) != "https://openrouter.ai/api/alpha/decisions":
            raise ValueError("Only the fixed Decisions endpoint is admitted")
        original = await request.aread()
        digest = hashlib.sha256(original).hexdigest()
        mode = "paid" if self.paid and not request.extensions.get("mcpkart_mock") else "mock"
        payload = json.dumps({
            "mode": mode, "release_sha256": self.release_sha256, "operation_id": f"{self.logical_id}:{self.racer_id}:{self.seq}",
            "request_b64": base64.b64encode(original).decode(), "request_sha256": digest,
        }).encode()
        self.seq += 1
        started = time.monotonic_ns()

        def invoke():
            result = self.client.invoke_agent_runtime(
                agentRuntimeArn=self.arn, runtimeSessionId=self.session,
                payload=payload, contentType="application/json", accept="application/json",
            )
            stream = result["response"]
            try:
                body = stream.read(2 * 1024 * 1024 + 1)
                if len(body) > 2 * 1024 * 1024:
                    raise ValueError("AgentCore response exceeds the evidence bound")
                return json.loads(body), body, result.get("ResponseMetadata", {})
            finally:
                stream.close()

        try:
            envelope, outer_body, metadata = await asyncio.to_thread(invoke)
        except Exception as error:  # noqa: BLE001 - preserve unknown dispatch evidence, never retry
            if self.evidence_path:
                self.evidence_path.mkdir(parents=True, exist_ok=True)
                with (self.evidence_path / f"{self.seq - 1:05d}-failure.json").open("x") as stream:
                    json.dump({"request_b64": base64.b64encode(payload).decode(),
                               "type": type(error).__name__, "unknown_billing": mode == "paid"}, stream)
            raise httpx.TransportError("AgentCore dispatch failed; no retry", request=request) from None
        if self.evidence_path:
            self.evidence_path.mkdir(parents=True, exist_ok=True)
            with (self.evidence_path / f"{self.seq - 1:05d}.json").open("x") as stream:
                json.dump({"runtime_arn": self.arn, "session_id": self.session,
                           "request_started_ns": started, "response_received_ns": time.monotonic_ns(),
                           "request_b64": base64.b64encode(payload).decode(),
                           "response_b64": base64.b64encode(outer_body).decode(),
                           "aws_response_metadata": metadata}, stream)
        if envelope.get("request_sha256") != digest or envelope.get("mode") != mode:
            raise httpx.TransportError("AgentCore response does not bind the original request", request=request)
        content = base64.b64decode(envelope["response_b64"], validate=True)
        return httpx.Response(envelope["status"], content=content, headers={"Content-Type": "application/json"})
