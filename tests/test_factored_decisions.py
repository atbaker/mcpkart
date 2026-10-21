"""Free factored-client contracts, including frozen pre-change joint wire hashes."""

import asyncio
import copy
import hashlib
import json

import httpx
import pytest

from mcpkart import decisions as draft
from mcpkart.sim import ACTIONS, Simulation
from mcpkart.telemetry import represent

# Captured through MockTransport from the pre-factored production client.
# Source SHA256: 95af5de48052c3f684211a35378f587614730b26cc6460210a026931d4f06089.
# State {"same": "full observation"}, ACTIONS and HANDLING below, same ROUTE.
# These fixed full-body hashes are independent of DecisionClient.questions.
BASELINE_JOINT_WIRE = {
    ("original", "numeric"): ("3b3e4261cd0d5259b36ad58666146cd9cb212cca16d6279e5e5cbb48590486dc", 1628),
    ("original", "explicit"): ("44df451cec15b859028ce9814aa11d7b2b7f8229f4c2203fd840c82e992dd896", 2333),
    ("original", "geometry"): ("6d5f2a50b6d59e6b421dae6aeaacda48d63cc68cc8a1b738447563bec9c4cd9c", 3101),
    ("damped", "numeric"): ("0764241afc926347ab5068806cff6c9bd521ed43a0bfe40921f4257fe85249b1", 2930),
    ("damped", "explicit"): ("95abb48800e9725542f481860e601b2edbb884b91ba9bb411325ead186f3ae11", 3635),
    ("damped", "geometry"): ("e6cdebee15891a3f263d32e1b88fb6808833e0fbde5145ad2f608dcd9e5caf6d", 4403),
}

ROUTE = {
    "model": "typesafe/jev-1.14",
    "resolved_model": "typesafe/jev-1.14-20261014",
    "provider": "typesafe",
    "provider_name": "TypeSafe",
    "price_input_per_token": 0.000000042,
    "price_output_per_token": 0.00000001,
    "price_per_request": 0.000001,
    "context_length": 262144,
    "max_completion_tokens": 235929,
}
HANDLING = Simulation(max_steering_angle=.12).config()["handling"]
COMPONENTS = [(wheel, pedal) for wheel, _ in draft._WHEEL_SETTINGS
              for pedal, _, _ in draft._PEDAL_SETTINGS]


def good_response(wheel="left", pedal="coast", **updates):
    return {
        "model": ROUTE["resolved_model"],
        "provider": "TypeSafe",
        "id": "mock-factored-request",
        "answers": {
            "wheel": {"type": "choice", "choice": wheel},
            "pedal": {"type": "choice", "choice": pedal},
        },
        "usage": {"input_tokens": 500, "output_tokens": 30, "cost": .000021},
        **updates,
    }


class CountingBudget(draft.Budget):
    def __init__(self, path, **kwargs):
        self.reservations, self.commits = [], []
        super().__init__(path, **kwargs)

    def reserve(self, *args, **kwargs):
        self.reservations.append((args, kwargs))
        return super().reserve(*args, **kwargs)

    def commit(self, *args, **kwargs):
        self.commits.append((args, kwargs))
        return super().commit(*args, **kwargs)


async def request_once(tmp_path, body=None, *, status=200, handler=None, **client_kwargs):
    received = []

    def respond(request):
        received.append(request)
        if handler:
            return handler(request)
        return httpx.Response(status, json=good_response() if body is None else body)

    budget = CountingBudget(tmp_path / "budget.json")
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        api = draft.DecisionClient(
            budget=budget, actions=ACTIONS, handling=HANDLING, api_key="fake-test-key",
            http_client=http, max_input_tokens=16384, decision_layout="factored", **client_kwargs,
        )
        result = await api.decide(ROUTE, {"complete_state": {"values": [1, 2, 3]}, "unicode": "←"})
    return result, received, budget, api


@pytest.mark.parametrize("wheel,pedal", COMPONENTS)
async def test_every_native_combination_maps_atomically_to_existing_action(tmp_path, wheel, pedal):
    result, requests, budget, api = await request_once(tmp_path, good_response(wheel, pedal))
    assert len(requests) == 1
    assert result["ok"] and result["action"] == f"{wheel}_{pedal}"
    assert result["action"] in ACTIONS
    assert result["component_choices"] == {"wheel": wheel, "pedal": pedal}
    assert result["component_errors"] is None
    assert result["decision_layout"] == "factored"
    assert len(budget.reservations) == len(budget.commits) == 1
    assert budget.summary()["requests"] == 1
    assert budget.summary()["charged_tokens"] == 530
    assert budget.summary()["charged_usd"] == .000021
    assert not budget.summary()["pending"]
    args, kwargs = budget.reservations[0]
    assert args == (pytest.approx(16384 * ROUTE["price_input_per_token"]
                                  + 235929 * ROUTE["price_output_per_token"]
                                  + ROUTE["price_per_request"]), 16384 + 235929)
    assert kwargs == {"model": ROUTE["model"], "provider": ROUTE["provider"]}
    assert result["request_started_ns"] <= result["response_received_ns"]
    assert result["latency_ms"] >= 0
    assert result["choice_confidence"] is result["choice_probabilities"] is None
    assert "fake-test-key" not in json.dumps(result)
    assert len(api.criteria) == 15


@pytest.mark.parametrize("style", ["original", "damped"])
@pytest.mark.parametrize("language", ["numeric", "explicit", "geometry"])
async def test_factored_payload_preserves_full_state_guide_and_fixed_geometry(tmp_path, style, language):
    result, requests, _, api = await request_once(
        tmp_path, instruction_style=style, control_language=language,
    )
    request = requests[0]
    payload = json.loads(request.content)
    expected = {
        "model": ROUTE["model"],
        "state": {"complete_state": {"values": [1, 2, 3]}, "unicode": "←"},
        "questions": {
            "wheel": {
                "type": "choice",
                "instructions": draft.INSTRUCTION_STYLES[style] + draft.FACTORED_WHEEL_INSTRUCTIONS,
                "criteria": api.component_criteria["wheel"],
            },
            "pedal": {
                "type": "choice",
                "instructions": draft.INSTRUCTION_STYLES[style] + draft.FACTORED_PEDAL_INSTRUCTIONS,
                "criteria": api.component_criteria["pedal"],
            },
        },
        "provider": {"only": ["typesafe"], "allow_fallbacks": False},
    }
    encoded = json.dumps(expected, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    assert payload == expected
    assert request.content == encoded
    assert result["payload_bytes"] == len(encoded)
    assert result["input_byte_bound"] == len(encoded) + 512 + len(json.dumps(
        expected["state"], ensure_ascii=False, separators=(",", ":"), allow_nan=False,
    ).encode())
    assert result["input_token_ceiling"] == 16384
    assert str(request.url) == draft.DECISIONS_URL
    assert request.headers["Authorization"] == "Bearer fake-test-key"
    assert set(payload["questions"]["wheel"]["criteria"]) == {wheel for wheel, _ in draft._WHEEL_SETTINGS}
    assert set(payload["questions"]["pedal"]["criteria"]) == {pedal for pedal, _, _ in draft._PEDAL_SETTINGS}
    for wheel_id, steer in draft._WHEEL_SETTINGS:
        if language == "geometry":
            assert api.component_criteria["wheel"][wheel_id] == draft.geometry_control_description(
                {"steer": steer, "throttle": 0, "brake": 0}, HANDLING,
            ).removesuffix(" COAST.")
        else:
            assert f"absolute wheel angle {steer * .12:+g} radians" in api.component_criteria["wheel"][wheel_id]
    if language == "geometry":
        assert "radius of 14.9 metres" in api.component_criteria["wheel"]["hard_left"]
        assert "a straight nominal path" in api.component_criteria["wheel"]["straight"]


@pytest.mark.parametrize("component", ["wheel", "pedal"])
@pytest.mark.parametrize("bad_answer,kind", [
    (None, "missing_answer"),
    ([], "missing_answer"),
    ({"type": "choice"}, "invalid_choice"),
    ({"type": "choice", "choice": 1}, "invalid_choice"),
    ({"type": "choice", "choice": "not-a-component"}, "invalid_choice"),
    ({"choice": "left"}, "invalid_type"),
    ({"type": "text", "choice": "left"}, "invalid_type"),
    ({"type": "choice", "choice": "left", "refusal": "fake-test-key refused"}, "refusal"),
])
async def test_either_bad_head_rejects_entire_control_without_retry(tmp_path, component, bad_answer, kind):
    body = good_response()
    body["answers"][component] = bad_answer
    result, requests, budget, _ = await request_once(tmp_path, body)
    assert len(requests) == 1
    assert result["ok"] is False and result["action"] is None
    assert result["error"] == ("refusal" if kind == "refusal" else "invalid_action")
    assert result["component_errors"] == {component: kind}
    assert result["component_choices"][component] is None
    other = "pedal" if component == "wheel" else "wheel"
    assert result["component_choices"][other] == body["answers"][other]["choice"]
    assert len(budget.reservations) == len(budget.commits) == 1
    assert budget.summary()["charged_tokens"] == 530
    assert "fake-test-key" not in json.dumps(result)


@pytest.mark.parametrize("answers", [None, [], {}, {"control": {"type": "choice", "choice": "left_coast"}}])
async def test_missing_both_heads_cannot_be_replaced_by_joint_answer(tmp_path, answers):
    result, requests, _, _ = await request_once(tmp_path, good_response(answers=answers))
    assert len(requests) == 1
    assert not result["ok"] and result["action"] is None
    assert result["component_errors"] == {"wheel": "missing_answer", "pedal": "missing_answer"}


@pytest.mark.parametrize("updates,error", [
    ({"model": None}, "missing_response_identity"),
    ({"provider": None}, "missing_response_identity"),
    ({"model": "wrong-model"}, "unexpected_model"),
    ({"provider": "OtherProvider"}, "unexpected_provider"),
    ({"refusal": "fake-test-key refused"}, "refusal"),
])
async def test_response_identity_and_refusal_gate_both_components(tmp_path, updates, error):
    result, requests, _, _ = await request_once(tmp_path, good_response(**updates))
    assert len(requests) == 1
    assert not result["ok"] and result["action"] is None
    assert result["error"] == error
    assert "fake-test-key" not in json.dumps(result)


async def test_uncertainty_stays_per_component_and_does_not_reselect(tmp_path):
    body = good_response()
    body["answers"]["wheel"].update(confidence=.2, probabilities={
        "left": .1, "hard_right": .9, "not-wheel": .9, "straight": True,
    })
    body["answers"]["pedal"].update(confidence=.3, probabilities={"coast": .1, "brake": .9})
    result, _, _, _ = await request_once(tmp_path, body)
    assert result["action"] == "left_coast"
    assert result["component_confidence"] == {"wheel": .2, "pedal": .3}
    assert result["component_probabilities"] == {
        "wheel": {"left": .1, "hard_right": .9}, "pedal": {"coast": .1, "brake": .9},
    }
    assert result["choice_confidence"] is result["choice_probabilities"] is None


@pytest.mark.parametrize("failure", ["timeout", "http_503", "transport_error"])
async def test_request_failures_charge_once_without_retry_or_partial_control(tmp_path, failure):
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("sensitive fake-test-key must not be logged", request=request)
        if failure == "transport_error":
            raise httpx.ConnectError("sensitive fake-test-key must not be logged", request=request)
        return httpx.Response(503, json={"error": "unavailable fake-test-key"})

    result, requests, budget, _ = await request_once(tmp_path, handler=handler)
    assert len(requests) == len(budget.reservations) == len(budget.commits) == 1
    assert not result["ok"] and result["action"] is None
    assert result["error"] == failure
    assert result["component_choices"] == {"wheel": None, "pedal": None}
    assert result["cost_source"] == "reservation"
    assert budget.summary()["charged_tokens"] == 16384 + 235929
    assert budget.summary()["uncertain_requests"] == 1
    assert not budget.summary()["pending"]
    assert "fake-test-key" not in json.dumps(result)


async def test_cancellation_commits_once_and_propagates(tmp_path):
    calls = []

    async def handler(request):
        calls.append(request)
        raise asyncio.CancelledError()

    budget = CountingBudget(tmp_path / "budget.json")
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = draft.DecisionClient(
            budget=budget, actions=ACTIONS, handling=HANDLING, api_key="fake-test-key",
            http_client=http, max_input_tokens=16384, decision_layout="factored",
        )
        with pytest.raises(asyncio.CancelledError):
            await api.decide(ROUTE, {})
    assert len(calls) == len(budget.reservations) == len(budget.commits) == 1
    assert budget.summary()["uncertain_requests"] == 1
    assert not budget.summary()["pending"]


@pytest.mark.parametrize("mutation", ["incomplete", "duplicate", "non-native", "boolean", "infinite", "text"])
def test_factored_rejects_ambiguous_or_incomplete_physical_menu_before_network(tmp_path, mutation):
    actions = copy.deepcopy(ACTIONS)
    if mutation == "incomplete":
        actions.pop("left_coast")
    elif mutation == "duplicate":
        actions["left_coast"] = copy.deepcopy(actions["right_coast"])
    elif mutation == "text":
        actions = {key: value["description"] for key, value in actions.items()}
    else:
        actions["left_coast"]["steer"] = {"non-native": .25, "boolean": True, "infinite": float("inf")}[mutation]
    budget = CountingBudget(tmp_path / "budget.json")
    with pytest.raises(ValueError, match="Factored decisions"):
        draft.DecisionClient(
            budget=budget, actions=actions, handling=HANDLING, api_key="fake-test-key",
            decision_layout="factored",
        )
    assert not budget.reservations and budget.summary()["requests"] == 0


@pytest.mark.parametrize("handling", [None, {}, {"max_steering_angle": True, "wheelbase": 1.8},
                                     {"max_steering_angle": .12, "wheelbase": 0}])
def test_factored_requires_valid_handling_without_changing_joint_requirements(tmp_path, handling):
    budget = CountingBudget(tmp_path / "budget.json")
    with pytest.raises(ValueError, match="Factored decisions"):
        draft.DecisionClient(budget=budget, actions=ACTIONS, handling=handling, api_key="fake-test-key",
                             decision_layout="factored")
    assert budget.summary()["requests"] == 0


async def test_input_guard_and_hard_budget_prevent_network_and_reservation(tmp_path):
    def handler(request):
        pytest.fail("Rejected requests must never reach the network")

    budget = CountingBudget(tmp_path / "budget.json", cap_usd=0)
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = draft.DecisionClient(
            budget=budget, actions=ACTIONS, handling=HANDLING, api_key="fake-test-key",
            http_client=http, max_input_tokens=16384, decision_layout="factored",
        )
        with pytest.raises(draft.BudgetExceeded):
            await api.decide(ROUTE, {})
        attempted_reservations = len(budget.reservations)
        with pytest.raises(ValueError, match="input token ceiling"):
            await api.decide(ROUTE, {"huge": "x" * 16384})
    assert len(budget.reservations) == attempted_reservations
    assert not budget.commits
    assert budget.summary()["requests"] == 0


async def test_factored_admission_counts_second_state_copy_before_reservation(tmp_path):
    def handler(request):
        pytest.fail("Second-state admission failure must happen before the POST")

    budget = CountingBudget(tmp_path / "budget.json")
    observation = {"full_state": "s" * 3000}
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = draft.DecisionClient(
            budget=budget, actions=ACTIONS, handling=HANDLING, api_key="fake-test-key",
            http_client=http, max_input_tokens=16384, decision_layout="factored",
        )
        payload = {
            "model": ROUTE["model"], "state": observation, "questions": api.questions,
            "provider": {"only": [ROUTE["provider"]], "allow_fallbacks": False},
        }
        wire_bytes = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())
        # The physical body fits, but duplicated shared state does not.
        api.max_input_tokens = wire_bytes + 512
        with pytest.raises(ValueError, match="input token ceiling"):
            await api.decide(ROUTE, observation)
    assert not budget.reservations and budget.summary()["requests"] == 0


async def test_actual_stadium_navigation_fits_factored_16k_guard(tmp_path):
    sim = Simulation(course="stadium", road_width=24, max_speed=8, max_steering_angle=.12)
    observation = represent(sim.observation(), sim.config(), "road_navigation")
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json=good_response())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = draft.DecisionClient(
            budget=CountingBudget(tmp_path / "budget.json"), actions=ACTIONS, handling=HANDLING,
            api_key="fake-test-key", http_client=http, max_input_tokens=16384,
            decision_layout="factored", control_language="geometry", instruction_style="damped",
        )
        result = await api.decide(ROUTE, observation)
    assert captured[0]["state"] == observation
    assert result["ok"] and result["input_byte_bound"] <= 16384


async def test_component_mapping_uses_physical_triples_rather_than_action_id_spelling(tmp_path):
    actions = {f"native_{index}": value for index, value in enumerate(ACTIONS.values())}
    target_id = next(key for key, value in actions.items()
                     if (value["steer"], value["throttle"], value["brake"]) == (.5, 0, 0))
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=good_response()),
    )) as http:
        api = draft.DecisionClient(
            budget=CountingBudget(tmp_path / "budget.json"), actions=actions, handling=HANDLING,
            api_key="fake-test-key", http_client=http, max_input_tokens=16384, decision_layout="factored",
        )
        result = await api.decide(ROUTE, {})
    assert result["ok"] and result["action"] == target_id


async def test_questions_property_copies_menu_and_tracks_current_instructions(tmp_path):
    async with httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=good_response()),
    )) as http:
        api = draft.DecisionClient(
            budget=CountingBudget(tmp_path / "budget.json"), actions=ACTIONS, handling=HANDLING,
            api_key="fake-test-key", http_client=http, max_input_tokens=16384, decision_layout="factored",
        )
        questions = api.questions
        questions["wheel"]["criteria"]["left"] = "Changed provenance copy"
        assert api.questions["wheel"]["criteria"]["left"] != "Changed provenance copy"
        api.instructions = "Current overridden instructions"
        assert api.questions["wheel"]["instructions"] == api.instructions + draft.FACTORED_WHEEL_INSTRUCTIONS
        assert api.questions["pedal"]["instructions"] == api.instructions + draft.FACTORED_PEDAL_INSTRUCTIONS


@pytest.mark.parametrize("style", ["original", "damped"])
@pytest.mark.parametrize("language", ["numeric", "explicit", "geometry"])
async def test_default_joint_payload_bytes_and_acceptance_remain_identical(tmp_path, style, language):
    requests = []
    body = {
        "model": ROUTE["resolved_model"], "provider": "TypeSafe",
        "answers": {"control": {"choice": "right_brake", "confidence": .4,
                                 "probabilities": {"right_brake": .3, "left_coast": .7}}},
        "usage": {"input_tokens": 500, "output_tokens": 30, "cost": .000021},
    }

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = draft.DecisionClient(
            budget=draft.Budget(tmp_path / "budget.json"), actions=ACTIONS,
            handling=HANDLING, api_key="fake-test-key", http_client=http,
            max_input_tokens=16384, control_language=language, instruction_style=style,
        )
        result = await api.decide(ROUTE, {"same": "full observation"})
    assert len(requests) == 1
    expected_hash, expected_bytes = BASELINE_JOINT_WIRE[(style, language)]
    assert hashlib.sha256(requests[0].content).hexdigest() == expected_hash
    assert len(requests[0].content) == expected_bytes
    assert set(json.loads(requests[0].content)["questions"]) == {"control"}
    expected_result = {
        "ok": True, "action": "right_brake", "error": None,
        "choice_confidence": .4,
        "choice_probabilities": {"right_brake": .3, "left_coast": .7},
        "payload_bytes": expected_bytes, "input_token_ceiling": 16384,
        "usage": {"input_tokens": 500, "output_tokens": 30, "cost": .000021},
        "cost": .000021, "cost_source": "reported",
        "control_language": language, "instruction_style": style,
        "decision_layout": "joint", "component_choices": None,
    }
    assert {name: result[name] for name in expected_result} == expected_result


async def test_joint_custom_numeric_choices_continue_to_support_static_experiments(tmp_path):
    actions = {"value_a": "241.004 square metres.", "value_b": {"description": "242.004 square metres."}}

    def handler(request):
        payload = json.loads(request.content)
        assert payload["questions"]["control"]["criteria"] == {
            "value_a": "241.004 square metres.", "value_b": "242.004 square metres.",
        }
        return httpx.Response(200, json={
            "model": ROUTE["model"], "provider": "TypeSafe",
            "answers": {"control": {"choice": "value_a"}},
            "usage": {"input_tokens": 10, "output_tokens": 1, "cost": 0},
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        api = draft.DecisionClient(budget=draft.Budget(tmp_path / "budget.json"), actions=actions,
                                   api_key="fake-test-key", http_client=http)
        api.instructions = "Exact custom static question"
        result = await api.decide(ROUTE, {"x": 15.504, "y": .794})
    assert result["ok"] and result["action"] == "value_a"


async def test_default_factored_client_honors_environment_proxy_without_retries(tmp_path, monkeypatch):
    received = []
    body = json.dumps(good_response()).encode()

    async def proxy(reader, writer):
        try:
            headers = await reader.readuntil(b"\r\n\r\n")
            length = next(int(line.split(b":", 1)[1]) for line in headers.split(b"\r\n")
                          if line.lower().startswith(b"content-length:"))
            payload = await reader.readexactly(length)
            received.append((headers, json.loads(payload)))
            writer.write(f"HTTP/1.1 200 Test\r\nContent-Type: application/json\r\n"
                         f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body)
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY",
                 "http_proxy", "https_proxy", "all_proxy", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(draft, "DECISIONS_URL", "http://decisions.invalid/api/alpha/decisions")
    server = await asyncio.start_server(proxy, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{port}")
    budget = CountingBudget(tmp_path / "budget.json")
    async with server, draft.DecisionClient(
        budget=budget, actions=ACTIONS, handling=HANDLING, api_key="fake-test-key",
        decision_layout="factored", timeout_s=1, max_input_tokens=16384,
    ) as api:
        result = await api.decide(ROUTE, {"full": "observation"})
    assert len(received) == 1
    headers, payload = received[0]
    assert headers.startswith(b"POST http://decisions.invalid/api/alpha/decisions HTTP/1.1\r\n")
    assert set(payload["questions"]) == {"wheel", "pedal"}
    assert result["ok"] and result["action"] == "left_coast"
