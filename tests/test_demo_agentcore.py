import asyncio
import base64
import io
import json

import httpx
import pytest

pytest.importorskip("bedrock_agentcore")

from mcpkart.demo_agentcore import invoke
from mcpkart.demo_transport import AgentCoreTransport
from mcpkart.duel import TRIO_RACERS, DuelSimulation
from mcpkart.duel_decisions import DuelDecisionClient, duel_facts


class RuntimeClient:
    def __init__(self):
        self.requests = []

    def invoke_agent_runtime(self, **kwargs):
        self.requests.append(kwargs)
        envelope = asyncio.run(invoke(json.loads(kwargs["payload"])))
        return {"response": io.BytesIO(json.dumps(envelope).encode())}


async def test_agentcore_bridge_preserves_native_bytes_and_omits_authorization():
    client = RuntimeClient()
    sim = DuelSimulation(racer_ids=TRIO_RACERS, contact="ghost")
    api = DuelDecisionClient(facts=duel_facts(sim.observation("green"), sim.config(), "green"),
                             handling=sim.config()["handling"], budget=None,
                             http_client=object(), api_key="test-secret")
    body = json.dumps({"model": "cloudflare/clef", "state": {}, "questions": api.questions,
                       "provider": {"only": ["primeintellect"], "allow_fallbacks": False}}).encode()
    transport = AgentCoreTransport("arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/mock",
                                   "us-west-2", "green", "mcpkart-agentcore-test", client=client)
    async with httpx.AsyncClient(transport=transport) as http:
        response = await http.post("https://openrouter.ai/api/alpha/decisions", content=body,
                                   headers={"Authorization": "Bearer test-secret"})
    assert response.status_code == 200
    assert response.json()["model"] == "cloudflare/clef-mock"
    assert response.json()["provider"] == "Prime Intellect"
    envelope = json.loads(client.requests[0]["payload"])
    assert base64.b64decode(envelope["request_b64"]) == body
    assert "test-secret" not in repr(client.requests)
    assert len(client.requests) == 1


async def test_agentcore_adapter_cannot_enable_paid_inference():
    with pytest.raises(ValueError, match="release"):
        await invoke({"mode": "paid"})


async def test_live_adapter_forwards_exact_bytes_once_without_policy(monkeypatch):
    import hashlib

    import mcpkart.demo_agentcore as adapter

    monkeypatch.setenv("MCPKART_RELEASE_SHA256", "a" * 64)
    monkeypatch.setenv("MCPKART_EXPIRES_UTC", "2099-01-01T00:00:00+00:00")
    monkeypatch.setattr(adapter, "key", lambda: "private-test-key")
    monkeypatch.setattr(adapter, "_seen", set())
    calls = []
    native = b'{"error":"test infrastructure failure","usage":{"cost":0}}'

    async def wire(request):
        calls.append(request.content)
        assert request.headers["Authorization"] == "Bearer private-test-key"
        return httpx.Response(503, content=native)

    original_client = httpx.AsyncClient
    monkeypatch.setattr(adapter.httpx, "AsyncClient", lambda **kwargs: original_client(
        transport=httpx.MockTransport(wire), **kwargs,
    ))
    original = json.dumps({"model": "cloudflare/clef", "state": {},
                           "questions": {"wheel": {}, "pedal": {}},
                           "provider": {"only": ["primeintellect"], "allow_fallbacks": False}}).encode()
    packet = {"mode": "paid", "release_sha256": "a" * 64, "operation_id": "mcpkart-test:green:0",
              "request_b64": base64.b64encode(original).decode(),
              "request_sha256": hashlib.sha256(original).hexdigest()}
    result = await invoke(packet)
    assert result["status"] == 503 and base64.b64decode(result["response_b64"]) == native
    with pytest.raises(ValueError, match="Duplicate"):
        await invoke(packet)
    assert calls == [original]
    monkeypatch.setenv("MCPKART_EXPIRES_UTC", "2000-01-01T00:00:00+00:00")
    with pytest.raises(ValueError, match="expired"):
        await invoke({**packet, "operation_id": "mcpkart-test:green:1"})
    assert calls == [original]
