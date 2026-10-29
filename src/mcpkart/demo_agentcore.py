"""Hash-bound AgentCore Decisions adapter; mocks and live inference stay explicit."""

import asyncio
import base64
import hashlib
import json
import os
from datetime import UTC, datetime

import httpx
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .demo_contract import MODELS, PROVIDERS
from .demo_mock import free_choices

app = BedrockAgentCoreApp()
_seen = set()
_secret = None


def authorization(payload):
    release = os.environ.get("MCPKART_RELEASE_SHA256")
    if not release or len(release) != 64 or payload.get("release_sha256") != release:
        raise ValueError("Live release is not configured or does not match")
    if datetime.now(UTC) >= datetime.fromisoformat(os.environ["MCPKART_EXPIRES_UTC"]):
        raise ValueError("Live release has expired")


def key():
    global _secret
    if _secret is None:
        import boto3
        from botocore.config import Config
        arn = os.environ["MCPKART_OPENROUTER_SECRET_ARN"]
        _secret = boto3.client("secretsmanager", config=Config(
            retries={"total_max_attempts": 1}, connect_timeout=3, read_timeout=3,
        )).get_secret_value(SecretId=arn)["SecretString"]
        if not _secret or "\n" in _secret:
            raise ValueError("Invalid inference credential")
    return _secret


async def invoke(payload):
    mode = payload.get("mode")
    if mode not in ("mock", "paid"):
        raise ValueError("Choose explicit mock or paid mode")
    if mode == "paid" or payload.get("release_sha256"):
        authorization(payload)
        # Prewarm credential access in explicit zero-model-call mock mode.
        await asyncio.to_thread(key)
    original = base64.b64decode(payload["request_b64"], validate=True)
    if len(original) > 128 * 1024 or hashlib.sha256(original).hexdigest() != payload["request_sha256"]:
        raise ValueError("Invalid bounded request bytes")
    packet = json.loads(original)
    model = packet["model"]
    if model not in MODELS or packet["provider"] != {
        "only": [PROVIDERS[model]], "allow_fallbacks": False,
    } or set(packet["questions"]) != {"wheel", "pedal"}:
        raise ValueError("Request differs from the frozen three-model contract")
    if mode == "paid":
        identity = payload["operation_id"]
        if not isinstance(identity, str) or not identity.startswith("mcpkart-") or identity in _seen:
            raise ValueError("Duplicate or invalid live operation; never redispatch")
        if len(_seen) >= 1100:
            raise ValueError("Per-session finite request ceiling reached")
        _seen.add(identity)  # Consume before any network effect; errors never retry.
        async with httpx.AsyncClient(timeout=5, follow_redirects=False) as client:
            response = await client.post("https://openrouter.ai/api/alpha/decisions", content=original,
                                         headers={"Authorization": "Bearer " + key(),
                                                  "Content-Type": "application/json"})
            body, status = response.content, response.status_code
        if len(body) > 1024 * 1024 or key().encode() in body:
            raise ValueError("Unsafe or oversized native reply; preserve the full reservation")
    else:
        facts = {h + "_facts": packet["questions"][h]["instructions"]["current_facts"][h + "_facts"]
                 for h in ("wheel", "pedal")}
        wheel, pedal = free_choices(facts)
        await asyncio.sleep(.2)
        body = json.dumps({
            "id": "mock-" + hashlib.sha256(payload["operation_id"].encode()).hexdigest(),
            "model": model + "-mock",
            "provider": {"typesafe": "TypeSafe", "openai": "OpenAI", "primeintellect": "Prime Intellect"}[
                PROVIDERS[model]
            ],
            "answers": {"wheel": {"type": "choice", "choice": wheel},
                        "pedal": {"type": "choice", "choice": pedal}},
            "usage": {"input_tokens": 0, "output_tokens": 0, "cost": 0},
        }, separators=(",", ":")).encode()
        status = 200
    return {"mode": mode, "status": status, "request_sha256": payload["request_sha256"],
            "response_b64": base64.b64encode(body).decode()}


app.entrypoint(invoke)

if __name__ == "__main__":
    app.run()
