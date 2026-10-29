import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from mcpkart.decisions import (
    DRIVING_INSTRUCTIONS,
    Budget,
    BudgetExceeded,
    DecisionClient,
    RouteDiscoveryError,
    discover_routes,
    load_api_key,
)

ACTIONS = {
    "straight_accelerate": {"description": "Steering zero; throttle one; brake zero."},
    "left_brake": {"description": "Steer left; throttle zero; brake one."},
}
ROUTE = {
    "model": "typesafe/jev-1.14",
    "resolved_model": "typesafe/jev-1.14-20261014",
    "provider": "typesafe",
    "provider_name": "TypeSafe",
    "price_input_per_token": 0.000000042,
    "price_output_per_token": 0,
    "price_per_request": 0,
    "context_length": 262144,
    "max_completion_tokens": 235929,
}


def good_response(**updates):
    return {
        "model": ROUTE["resolved_model"],
        "provider": "TypeSafe",
        "id": "test-request",
        "answers": {"control": {"type": "choice", "choice": "straight_accelerate"}},
        "usage": {"input_tokens": 500, "output_tokens": 30, "cost": 0.000021},
        **updates,
    }


@pytest.mark.asyncio
async def test_typed_payload_pins_route_records_actual_identity_and_cost(tmp_path):
    requests = []

    def handler(request):
        requests.append(request)
        payload = json.loads(request.content)
        assert str(request.url) == "https://openrouter.ai/api/alpha/decisions"
        assert request.headers["Authorization"] == "Bearer fake-test-key"
        assert payload["model"] == ROUTE["model"]
        assert payload["provider"] == {"only": ["typesafe"], "allow_fallbacks": False}
        assert payload["state"] == {"observation_id": 1}
        assert payload["questions"]["control"]["type"] == "choice"
        assert payload["questions"]["control"]["criteria"] == {
            name: value["description"] for name, value in ACTIONS.items()
        }
        return httpx.Response(200, json=good_response())

    budget = Budget(tmp_path / "budget.json")
    async with (
        httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http,
        DecisionClient(budget=budget, actions=ACTIONS, api_key="fake-test-key", http_client=http) as api,
    ):
        result = await api.decide(ROUTE, {"observation_id": 1})
    assert len(requests) == 1
    assert result["ok"] and result["action"] == "straight_accelerate"
    assert result["model"] == ROUTE["resolved_model"]
    assert result["provider"] == "TypeSafe"
    assert result["request_started_ns"] <= result["response_received_ns"]
    assert result["latency_ms"] >= 0
    assert result["cost_source"] == "reported"
    assert result["cost"] == 0.000021
    assert "fake-test-key" not in json.dumps(result)
    assert budget.summary()["charged_tokens"] == 530
    assert budget.summary()["reserved_usd"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [200, 503])
async def test_default_client_uses_environment_proxy_without_retry(tmp_path, monkeypatch, status):
    from mcpkart import decisions

    received = []
    body = json.dumps(good_response() if status == 200 else {"error": "unavailable"}).encode()

    async def proxy(reader, writer):
        try:
            headers = await reader.readuntil(b"\r\n\r\n")
            length = next(int(line.split(b":", 1)[1]) for line in headers.split(b"\r\n")
                          if line.lower().startswith(b"content-length:"))
            payload = await reader.readexactly(length)
            received.append((headers, json.loads(payload)))
            writer.write(f"HTTP/1.1 {status} Test\r\nContent-Type: application/json\r\n"
                         f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
                 "http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    # This reserved target can only succeed through the loopback test proxy.
    monkeypatch.setattr(decisions, "DECISIONS_URL", "http://decisions.invalid/api/alpha/decisions")
    server = await asyncio.start_server(proxy, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{port}")
    async with server, DecisionClient(budget=Budget(tmp_path / "budget.json"), actions=ACTIONS,
                                     api_key="fake-test-key", timeout_s=1) as api:
        result = await api.decide(ROUTE, {"observation_id": 1})

    assert len(received) == 1
    headers, payload = received[0]
    assert headers.startswith(b"POST http://decisions.invalid/api/alpha/decisions HTTP/1.1\r\n")
    assert payload["state"] == {"observation_id": 1}
    assert result["ok"] is (status == 200)
    assert result["http_status"] == status
    assert result["error"] == (None if status == 200 else "http_503")


@pytest.mark.asyncio
async def test_explicit_controls_keep_action_ids_and_physical_inputs_and_retain_uncertainty(tmp_path):
    from mcpkart.sim import ACTIONS as physical_actions

    def handler(request):
        payload = json.loads(request.content)
        criteria = payload["questions"]["control"]["criteria"]
        assert set(criteria) == set(physical_actions)
        assert "moderate RIGHT wheel angle (-0.5)" in criteria["right_brake"]
        assert "BRAKE: throttle 0, brake 1" in criteria["right_brake"]
        assert "wheels STRAIGHT" in criteria["straight_accelerate"]
        assert payload["questions"]["control"]["instructions"] == DRIVING_INSTRUCTIONS
        return httpx.Response(200, json=good_response(answers={"control": {
            "choice": "straight_accelerate", "type": "choice", "confidence": .12,
            "probabilities": {"straight_accelerate": .4, "left_brake": .6,
                              "not_a_control": .99, "right_brake": "invalid"},
        }}))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = DecisionClient(budget=Budget(tmp_path / "budget.json"), actions=physical_actions,
                                control_language="explicit", api_key="test-key", http_client=http)
        result = await client.decide(ROUTE, {})
    # Instrumentation must not replace the provider's selected direct control.
    assert result["ok"] and result["action"] == "straight_accelerate"
    assert result["choice_confidence"] == .12
    assert result["choice_probabilities"] == {"straight_accelerate": .4, "left_brake": .6}
    assert result["control_language"] == "explicit"


@pytest.mark.parametrize(
    "body,status,error",
    [
        (good_response(answers={"control": {"choice": "autopilot"}}), 200, "invalid_action"),
        (good_response(answers={"control": {"refusal": "No"}}), 200, "refusal"),
        (good_response(refusal="No"), 200, "refusal"),
        ({"error": {"message": "invalid key fake-test-key"}}, 401, "http_401"),
        ({"error": {"message": "overloaded"}}, 200, "api_error"),
        ({"answers": {"control": {"choice": "straight_accelerate"}}}, 200, "missing_response_identity"),
        (good_response(provider="Unexpected"), 200, "unexpected_provider"),
        (good_response(model="different-model"), 200, "unexpected_model"),
        ([], 200, "invalid_action"),
        ({"metadata": ["malformed"]}, 200, "invalid_action"),
    ],
)
@pytest.mark.asyncio
async def test_failed_decisions_never_retry_or_add_controls(tmp_path, body, status, error):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(status, json=body)

    budget = Budget(tmp_path / "budget.json")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = DecisionClient(budget=budget, actions=ACTIONS, api_key="fake-test-key", http_client=http)
        result = await api.decide(ROUTE, {})
    assert calls == 1
    assert result["ok"] is False
    assert result["action"] is None
    assert result["error"] == error
    assert "fake-test-key" not in json.dumps(result)
    assert not budget.summary()["pending"]


@pytest.mark.asyncio
async def test_timeout_charges_full_reservation_and_no_retry(tmp_path):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("sensitive payload must not be logged", request=request)

    budget = Budget(tmp_path / "budget.json")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = DecisionClient(budget=budget, actions=ACTIONS, api_key="fake-test-key", http_client=http)
        result = await api.decide(ROUTE, {})
    assert calls == 1
    assert result["error"] == "timeout"
    assert result["cost"] == 8192 * ROUTE["price_input_per_token"]
    assert result["cost_source"] == "reservation"
    assert budget.summary()["uncertain_requests"] == 1
    assert "sensitive" not in json.dumps(result)


@pytest.mark.asyncio
async def test_actionable_error_details_are_redacted_and_bounded(tmp_path):
    def handler(request):
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "bad_provider",
                    "message": "fake-test-key Bearer other-key " + "details " * 100,
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = DecisionClient(
            budget=Budget(tmp_path / "budget.json"),
            actions=ACTIONS,
            api_key="fake-test-key",
            http_client=http,
        )
        result = await api.decide(ROUTE, {})
    assert result["error_detail"].startswith("bad_provider: [REDACTED] Bearer [REDACTED]")
    assert len(result["error_detail"]) <= 250
    assert "other-key" not in json.dumps(result)
    assert "fake-test-key" not in json.dumps(result)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message,expected_error",
    [
        ('OpenAI refused to answer question "control"', "refusal"),
        ('openai refused to answer question "control"', "refusal"),
        ("OpenAI upstream connection failed", "http_502"),
    ],
)
async def test_upstream_openai_refusal_retains_http_status_without_retry(tmp_path, message, expected_error):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return httpx.Response(502, json={"error": {"code": 502, "message": message}})

    budget = Budget(tmp_path / "budget.json")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = DecisionClient(budget=budget, actions=ACTIONS, api_key="fake-test-key", http_client=http)
        result = await api.decide(ROUTE, {})
    assert calls == 1
    assert not result["ok"]
    assert result["action"] is None
    assert result["http_status"] == 502
    assert result["error"] == expected_error
    assert result["error_detail"] == f"502: {message}"
    assert result["cost_source"] == "reservation"
    assert budget.summary()["uncertain_requests"] == 1


def test_shared_instructions_explain_game_and_configurable_rescue():
    assert (
        "fictional kart-racing video-game simulation; no real vehicles are controlled" in DRIVING_INSTRUCTIONS
    )
    assert "state.rescue.after_s" in DRIVING_INSTRUCTIONS
    assert "at rest with coast controls" in DRIVING_INSTRUCTIONS
    assert "null value disables rescue" in DRIVING_INSTRUCTIONS


@pytest.mark.asyncio
async def test_cost_in_metadata_is_supported(tmp_path):
    body = good_response(usage=None, metadata={"cost": 0.000015})
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    ) as http:
        api = DecisionClient(
            budget=Budget(tmp_path / "budget.json"),
            actions=ACTIONS,
            api_key="fake-test-key",
            http_client=http,
        )
        result = await api.decide(ROUTE, {})
    assert result["ok"]
    assert result["cost"] == 0.000015
    assert result["cost_source"] == "reported"


@pytest.mark.asyncio
async def test_cancel_charges_and_propagates_to_prevent_late_control(tmp_path):
    async def handler(request):
        raise asyncio.CancelledError()

    budget = Budget(tmp_path / "budget.json")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = DecisionClient(budget=budget, actions=ACTIONS, api_key="fake-test-key", http_client=http)
        with pytest.raises(asyncio.CancelledError):
            await api.decide(ROUTE, {})
    assert not budget.summary()["pending"]
    assert budget.summary()["uncertain_requests"] == 1
    assert budget.summary()["charged_usd"] > 0


def test_budget_persists_pending_reservations_and_cannot_reset_cap(tmp_path):
    path = tmp_path / "budget.json"
    budget = Budget(path, cap_usd=0.001)
    reservation = budget.reserve(0.0008, 100, model="m", provider="p")
    reopened = Budget(path, cap_usd=10)
    assert reopened.summary()["requests"] == 1
    assert reopened.summary()["cap_usd"] == 0.001
    with pytest.raises(BudgetExceeded):
        reopened.reserve(0.0003, 1, model="m", provider="p")
    reopened.commit(reservation, cost=0.0007, tokens=50)
    next_reservation = budget.reserve(0.0002, 20, model="m", provider="p")
    budget.commit(next_reservation)
    assert budget.summary()["charged_usd"] == pytest.approx(0.0009)
    assert budget.summary()["charged_tokens"] == 70


@pytest.mark.parametrize("limit,value", [("max_requests", 1), ("max_tokens", 10)])
def test_budget_hard_request_and_token_ceilings(tmp_path, limit, value):
    budget = Budget(tmp_path / "budget.json", **{limit: value})
    reservation = budget.reserve(0.001, 10, model="m", provider="p")
    budget.commit(reservation)
    with pytest.raises(BudgetExceeded):
        budget.reserve(0.001, 1, model="m", provider="p")


def test_budget_reopening_preserves_authorized_request_limit_and_history(tmp_path):
    path = tmp_path / "budget.json"
    budget = Budget(path, max_requests=50_000)
    reservation = budget.reserve(0.001, 10, model="m", provider="p")
    budget.commit(reservation)
    before = budget.summary()
    assert Budget(path).summary() == before
    assert Budget(path, max_requests=60_000).summary() == before
    lowered = Budget(path, max_requests=40_000).summary()
    assert lowered == {**before, "max_requests": 40_000}


def test_new_budget_keeps_default_request_limit_and_hard_dollar_cap(tmp_path):
    assert Budget(tmp_path / "budget.json").summary()["max_requests"] == 25_000
    with pytest.raises(ValueError, match="at most"):
        Budget(tmp_path / "over-budget.json", cap_usd=20.01)


def test_two_ledger_instances_cannot_over_reserve_concurrently(tmp_path):
    path = tmp_path / "budget.json"
    budgets = [Budget(path, cap_usd=0.001), Budget(path, cap_usd=0.001)]

    def reserve(budget):
        try:
            return budget.reserve(0.0008, 100, model="m", provider="p")
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, budgets))
    assert sum(item is not None for item in results) == 1
    assert budgets[0].summary()["reserved_usd"] == 0.0008


@pytest.mark.asyncio
async def test_input_limit_and_budget_fail_before_network(tmp_path):
    def handler(request):
        pytest.fail("No inference request should be sent")

    budget = Budget(tmp_path / "budget.json", cap_usd=0)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = DecisionClient(budget=budget, actions=ACTIONS, api_key="fake-test-key", http_client=http)
        with pytest.raises(BudgetExceeded):
            await api.decide(ROUTE, {})
        with pytest.raises(ValueError, match="input token ceiling"):
            await api.decide(ROUTE, {"huge": "a" * 8192})
    assert budget.summary()["requests"] == 0


@pytest.mark.asyncio
async def test_discovery_uses_decisions_catalog_and_pins_preselected_provider():
    def handler(request):
        if request.url.path == "/api/v1/models":
            assert request.url.params["output_modalities"] == "decisions"
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "cloudflare/clef",
                            "canonical_slug": "cloudflare/clef",
                            "architecture": {"output_modalities": ["decisions"]},
                        }
                    ]
                },
            )
        assert request.url.path == "/api/v1/models/cloudflare/clef/endpoints"
        return httpx.Response(
            200,
            json={
                "data": {
                    "endpoints": [
                        {
                            "tag": tag,
                            "provider_name": name,
                            "name": name + " | cloudflare/clef",
                            "pricing": {"prompt": price, "completion": "0"},
                            "context_length": 16384,
                            "max_completion_tokens": 14745,
                            "status": 0,
                        }
                        for tag, name, price in [
                            ("primeintellect", "PrimeIntellect", "0.000000042"),
                            ("cloudflare", "Cloudflare", "0.00000024"),
                        ]
                    ]
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        routes = await discover_routes(http, models=["cloudflare/clef"])
        assert routes[0]["provider"] == "primeintellect"
        assert routes[0]["price_input_per_token"] == 0.000000042
        routes = await discover_routes(
            http, models=["cloudflare/clef"], provider_overrides={"cloudflare/clef": "cloudflare"}
        )
        assert routes[0]["provider"] == "cloudflare"
        with pytest.raises(RouteDiscoveryError):
            await discover_routes(
                http, models=["cloudflare/clef"], provider_overrides={"cloudflare/clef": "missing"}
            )


def test_key_loading_does_not_mutate_env_or_print(tmp_path, monkeypatch, capsys):
    path = tmp_path / ".env"
    path.write_text("OPENROUTER_API_KEY=fake-from-file\n")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert load_api_key(path) == "fake-from-file"
    assert not capsys.readouterr().out
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-from-env")
    assert load_api_key(path) == "fake-from-env"


def test_twenty_dollar_authorization_preserves_charges_and_old_saved_cap(tmp_path):
    path = tmp_path / 'budget20.json'
    budget = Budget(path, cap_usd=20, max_requests=100000, max_tokens=500000000)
    reservation = budget.reserve(.002, 123, model='test', provider='test')
    budget.commit(reservation)
    before = budget.summary()
    assert Budget(path, cap_usd=20, max_requests=100000, max_tokens=500000000).summary() == before
    assert before['cap_usd'] == 20 and before['uncertain_requests'] == 1
    old = Budget(tmp_path / 'budget10.json', cap_usd=10)
    assert Budget(old.path, cap_usd=20).summary()['cap_usd'] == 10
