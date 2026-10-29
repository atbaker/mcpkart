"""Isolated AgentCore mock model adapter. No provider dispatch is enabled."""

import asyncio
import base64
import hashlib
import json

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from .demo_contract import MODELS, PROVIDERS
from .demo_mock import free_choices

app = BedrockAgentCoreApp()


async def invoke(payload):
    if payload.get("mode") != "mock":
        raise ValueError("Only explicitly labeled free mocks are admitted in this deployment")
    original = base64.b64decode(payload["request_b64"], validate=True)
    if len(original) > 128 * 1024 or hashlib.sha256(original).hexdigest() != payload["request_sha256"]:
        raise ValueError("Invalid bounded request bytes")
    packet = json.loads(original)
    model = packet["model"]
    if model not in MODELS or packet["provider"] != {
        "only": [PROVIDERS[model]], "allow_fallbacks": False,
    } or set(packet["questions"]) != {"wheel", "pedal"}:
        raise ValueError("Request differs from the frozen three-model contract")
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
    return {"mode": "mock", "status": 200, "request_sha256": payload["request_sha256"],
            "response_b64": base64.b64encode(body).decode()}


app.entrypoint(invoke)

if __name__ == "__main__":
    app.run()
