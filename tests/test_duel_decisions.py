import asyncio
import copy
import json
import math

import httpx
import pytest

from mcpkart.decisions import Budget
from mcpkart.duel import RACERS, DuelSimulation
from mcpkart.duel_decisions import BudgetJournal, DuelDecisionClient, DuelDriver, duel_facts, gate_geometry
from mcpkart.question_context import PromptDomainError
from mcpkart.question_context_driver import WireCapture

ROUTE = {
    "model": "typesafe/jev-1.14",
    "resolved_model": "typesafe/jev-1.14-test",
    "provider": "typesafe",
    "provider_name": "TypeSafe",
    "price_input_per_token": 0,
    "price_output_per_token": 0,
    "price_per_request": 0,
    "context_length": 262144,
    "max_completion_tokens": 235929,
}


def response(identity, wheel="straight", pedal="accelerate"):
    return {
        "id": identity,
        "model": ROUTE["resolved_model"],
        "provider": "TypeSafe",
        "answers": {
            "wheel": {"type": "choice", "choice": wheel},
            "pedal": {"type": "choice", "choice": pedal},
        },
        "usage": {"input_tokens": 100, "output_tokens": 2, "cost": 0},
    }


@pytest.mark.parametrize("wheel", ["hard_right", "right", "straight", "left", "hard_left"])
@pytest.mark.parametrize("pedal", ["accelerate", "coast", "brake"])
@pytest.mark.parametrize("geometry", [False, True])
@pytest.mark.parametrize(
    "motion,timing,pedal_timing",
    [(False, False, False), (True, False, False), (False, True, False),
     (True, True, False), (False, True, True), (True, True, True)],
)
async def test_all_fifteen_native_choices_and_shared_budget_chain(
    tmp_path, wheel, pedal, geometry, motion, timing, pedal_timing,
):
    sim = DuelSimulation()
    budget = Budget(tmp_path / "budget.json")
    journal = BudgetJournal(budget, tmp_path / "events.jsonl")
    captures = {r: WireCapture() for r in RACERS}
    entered = set()
    both_entered = asyncio.Event()
    seen = set()

    async def run(rid):
        async def handler(request):
            body = json.loads(request.content)
            for head in ("wheel", "pedal"):
                facts = body["questions"][head]["instructions"]["current_facts"][head + "_facts"]
                assert facts["competition"]["racer_id"] == rid
                assert "FIXED POLICY" not in json.dumps(body)
                assert ("geometry" in facts["next_gate"]) == (geometry and head == "wheel")
                assert ("motion" in facts) == (motion and head == "wheel")
                assert ("control_timing" in facts) == (timing and (head == "wheel" or pedal_timing))
                if timing and (head == "wheel" or pedal_timing):
                    assert facts["control_timing"]["post_response_wait_s"] == 1.0
            entered.add(rid)
            if len(entered) == 2:
                both_entered.set()
            await asyncio.wait_for(both_entered.wait(), 1)
            return httpx.Response(200, json=response(rid, wheel, pedal))

        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), event_hooks=captures[rid].hooks
        ) as http:
            driver = DuelDriver(
                racer_id=rid,
                config=sim.config(),
                route=ROUTE,
                budget=journal.view(rid),
                http=http,
                capture=captures[rid],
                output=tmp_path / rid,
                api_key="mock-duel-secret-unique",
                seen_ids=seen,
                include_gate_geometry=geometry,
                include_wheel_motion=motion,
                control_timing_s=1.0 if timing else None,
                include_pedal_timing=pedal_timing,
            )
            record = await driver.decide(sim.observation(rid))
            assert record["ok"] and record["action"] == wheel + "_" + pedal

    try:
        await asyncio.gather(*(run(r) for r in RACERS))
    finally:
        journal.close()
    assert [e["kind"] for e in journal.events] == ["reserve", "reserve", "commit", "commit"]
    assert len(journal.events[1]["after"]["pending"]) == 2
    assert budget.summary()["requests"] == 2 and budget.summary()["charged_tokens"] == 204
    assert not budget.summary()["pending"]
    for a, b in zip(journal.events, journal.events[1:]):
        assert a["after"] == b["before"]


@pytest.mark.parametrize("course", ["stadium", "stadium_clockwise"])
def test_gate_geometry_is_a_rigid_world_measurement_and_isolates_wheel(course):
    sim = DuelSimulation(course=course)
    raw, config = sim.observation("red"), sim.config()
    baseline = duel_facts(raw, config, "red")
    augmented = duel_facts(raw, config, "red", include_gate_geometry=True)
    geometry = augmented["wheel_facts"]["next_gate"].pop("geometry")
    assert augmented == baseline
    left, right, centre, normal = (
        geometry[k] for k in (
            "left_endpoint_ego_m", "right_endpoint_ego_m", "centre_ego_m", "forward_normal_ego"
        )
    )
    assert math.dist(left, right) == pytest.approx(24, abs=0.0002)
    assert [(a + b) / 2 for a, b in zip(left, right)] == pytest.approx(centre, abs=0.0001)
    assert math.hypot(*normal) == pytest.approx(1, abs=0.000002)
    assert -sum(a * b for a, b in zip(centre, normal)) == pytest.approx(
        baseline["wheel_facts"]["next_gate"]["signed_plane_m"], abs=0.0002
    )
    # Rotate and translate the entire world: the kart-frame packet must be invariant.
    angle, tx, ty = 1.234, 17.3, -65.2
    c, s = math.cos(angle), math.sin(angle)
    for point in [raw["kart"], *config["track"]["checkpoints"]]:
        x, y = point["x"], point["y"]
        point.update(x=c*x-s*y+tx, y=s*x+c*y+ty, heading=point["heading"]+angle)
    assert gate_geometry(raw, config) == geometry


@pytest.mark.parametrize("fault", ["bool_index", "negative_index", "missing_index", "nan_pose"])
async def test_malformed_gate_measurement_stops_before_reservation_or_post(tmp_path, fault):
    sim = DuelSimulation()
    raw = sim.observation("red")
    if fault == "bool_index":
        raw["progress"]["checkpoint"] = True
    elif fault == "negative_index":
        raw["progress"]["checkpoint"] = -1
    elif fault == "missing_index":
        del raw["progress"]["checkpoint"]
    else:
        raw["kart"]["heading"] = float("nan")
    budget = Budget(tmp_path / "budget.json")
    journal = BudgetJournal(budget, tmp_path / "events.jsonl")
    posted = []

    def handler(request):
        posted.append(request)
        raise AssertionError("Malformed geometry reached the network")

    try:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            driver = DuelDriver(
                racer_id="red", config=sim.config(), route=ROUTE, budget=journal.view("red"),
                http=http, capture=WireCapture(), output=tmp_path / "red",
                api_key="free-malformed-test", include_gate_geometry=True,
            )
            with pytest.raises((PromptDomainError, KeyError)):
                await driver.decide(raw)
    finally:
        journal.close()
    assert not posted and budget.summary()["requests"] == 0 and not journal.events


def test_body_clearances_and_no_supplied_driving_policy(tmp_path):
    sim = DuelSimulation()
    raw = sim.observation("red")
    facts = duel_facts(raw, sim.config(), "red")
    assert facts["pedal_facts"]["road"]["right_edge_clearance_m"] == 9
    assert facts["wheel_facts"]["competition"] == facts["pedal_facts"]["competition"]
    api = DuelDecisionClient(
        facts=facts,
        handling=sim.config()["handling"],
        budget=Budget(tmp_path / "b.json"),
        http_client=None,
        api_key="mock-duel-secret-unique",
    )
    assert "solo" not in json.dumps(api.questions)
    assert "threshold" not in json.dumps(api.questions).lower()
    assert all("eligibility" not in json.dumps(q).lower() for q in api.questions.values())
    with pytest.raises(PromptDomainError):
        duel_facts(raw, sim.config(), "blue")
    raw["body"]["left_edge_clearance_m"] += 1
    with pytest.raises(PromptDomainError):
        duel_facts(raw, sim.config(), "red")


@pytest.mark.parametrize(
    "fault", ["model", "provider", "id", "extra_head", "malformed_choice", "cost", "tokens", "refusal"]
)
async def test_invalid_replies_are_unapplied_and_no_retry(tmp_path, fault):
    sim = DuelSimulation()
    body = response("id1")
    if fault == "model":
        body["model"] = "wrong"
    elif fault == "provider":
        body["provider"] = "wrong"
    elif fault == "id":
        body["id"] = ""
    elif fault == "extra_head":
        body["answers"]["other"] = {}
    elif fault == "malformed_choice":
        body["answers"]["wheel"]["choice"] = ["left"]
    elif fault == "cost":
        del body["usage"]["cost"]
    elif fault == "tokens":
        del body["usage"]["input_tokens"]
    else:
        body["answers"]["wheel"]["refusal"] = "no"
    budget = Budget(tmp_path / "budget.json")
    journal = BudgetJournal(budget, tmp_path / "events.jsonl")
    capture = WireCapture()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=copy.deepcopy(body))),
        event_hooks=capture.hooks,
    ) as http:
        driver = DuelDriver(
            racer_id="red",
            config=sim.config(),
            route=ROUTE,
            budget=journal.view("red"),
            http=http,
            capture=capture,
            output=tmp_path / "red",
            api_key="mock-duel-secret-unique",
        )
        record = await driver.decide(sim.observation("red"))
        assert not record["ok"] and record["action"] is None
        with pytest.raises(RuntimeError):
            await driver.decide(sim.observation("red"))
    journal.close()
    assert budget.summary()["requests"] == 1 and not budget.summary()["pending"]


def test_other_writer_and_wrong_reservation_owner_are_rejected(tmp_path):
    budget = Budget(tmp_path / "budget.json")
    journal = BudgetJournal(budget, tmp_path / "events.jsonl")
    red, blue = journal.view("red"), journal.view("blue")
    reservation = red.reserve(0.001, 100, model="m", provider="p")
    with pytest.raises(RuntimeError, match="another racer"):
        blue.commit(reservation, cost=0, tokens=0)
    red.commit(reservation, cost=0, tokens=0)
    budget.reserve(0.001, 100, model="outside", provider="outside")
    with pytest.raises(RuntimeError, match="outside"):
        blue.reserve(0.001, 100, model="m", provider="p")
    journal.close()


async def test_implicitly_loaded_key_is_redacted_before_any_control(tmp_path, monkeypatch):
    secret = "nonstandard-private-test-credential"
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)
    sim = DuelSimulation()
    body = response("echo-key")
    body["unexpected_echo"] = secret
    budget = Budget(tmp_path / "budget.json")
    journal = BudgetJournal(budget, tmp_path / "events.jsonl")
    capture = WireCapture()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body)),
        event_hooks=capture.hooks,
    ) as http:
        driver = DuelDriver(
            racer_id="red",
            config=sim.config(),
            route=ROUTE,
            budget=journal.view("red"),
            http=http,
            capture=capture,
            output=tmp_path / "red",
        )
        result = await driver.decide(sim.observation("red"))
    journal.close()
    assert not result["ok"] and result["action"] is None
    assert "unsafe_wire" in result["wrapper_failures"]
    evidence = (tmp_path / "red/calls/00000.json").read_text()
    assert secret not in evidence and "[REDACTED]" in evidence


async def test_cancelled_racer_settles_only_its_own_reservation(tmp_path):
    sim = DuelSimulation()
    budget = Budget(tmp_path / "budget.json")
    journal = BudgetJournal(budget, tmp_path / "events.jsonl")
    started = asyncio.Event()
    release = asyncio.Event()

    async def handler(request):
        rid = json.loads(request.content)["questions"]["wheel"]["instructions"]["current_facts"][
            "wheel_facts"
        ]["competition"]["racer_id"]
        if rid == "red":
            started.set()
            await release.wait()
        return httpx.Response(200, json=response(rid))

    async def run(rid):
        capture = WireCapture()
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler), event_hooks=capture.hooks
        ) as http:
            driver = DuelDriver(
                racer_id=rid,
                config=sim.config(),
                route=ROUTE,
                budget=journal.view(rid),
                http=http,
                capture=capture,
                output=tmp_path / rid,
                api_key="mock-duel-test-key",
            )
            return await driver.decide(sim.observation(rid))

    red = asyncio.create_task(run("red"))
    await started.wait()
    blue = await run("blue")
    assert blue["ok"]
    red.cancel()
    with pytest.raises(asyncio.CancelledError):
        await red
    journal.close()
    state = budget.summary()
    assert state["requests"] == 2 and state["uncertain_requests"] == 1 and not state["pending"]
    assert json.loads((tmp_path / "red/interrupted-00000.json").read_text())["wire"]["requests"]


@pytest.mark.parametrize("motion,timing", [(True, False), (False, True), (True, True)])
def test_wheel_observability_adds_only_measured_facts_and_leaves_pedal_rules_menus_exact(motion, timing):
    sim = DuelSimulation()
    kart = sim.karts["red"]
    kart.vx, kart.vy, kart.steering, kart.yaw_rate, kart.action_id = 3.0, 4.0, 0.07, -0.3, "right_coast"
    raw, config = sim.observation("red"), sim.config()
    original = copy.deepcopy(raw)
    baseline = duel_facts(raw, config, "red")
    augmented = duel_facts(
        raw, config, "red", include_wheel_motion=motion, control_timing_s=1.0 if timing else None,
    )
    stripped = copy.deepcopy(augmented)
    if motion:
        measured = stripped["wheel_facts"].pop("motion")
        assert measured["speed_m_s"] == 5.0
        assert measured["steering_angle_rad"] == 0.07
        assert measured["yaw_rate_rad_s"] == -0.3
        assert measured["held_input"] == "right_coast"
        assert stripped["wheel_facts"].pop("current_road_frame") == baseline["pedal_facts"]["current_road_frame"]
    if timing:
        measured = stripped["wheel_facts"].pop("control_timing")
        assert measured["post_response_wait_s"] == 1.0 and measured["physics_hz"] == 60
        assert "additional and variable" in measured["units"]
    assert raw == original and stripped == baseline
    clients = [DuelDecisionClient(facts=f, handling=config["handling"], budget=None, http_client=object(), api_key="free-observability") for f in (baseline, augmented)]
    assert clients[0].questions["pedal"] == clients[1].questions["pedal"]
    assert clients[0].component_criteria == clients[1].component_criteria
    for head in ("wheel", "pedal"):
        assert clients[0].questions[head]["instructions"]["rules"] == clients[1].questions[head]["instructions"]["rules"]


@pytest.mark.parametrize("delay", [0.0, 1.0, 2.0])
def test_known_control_wait_is_explicit_even_at_zero_and_never_claims_current_inference_time(delay):
    sim = DuelSimulation()
    f = duel_facts(sim.observation("red"), sim.config(), "red", control_timing_s=delay)
    timing = f["wheel_facts"]["control_timing"]
    assert timing["post_response_wait_s"] == delay
    assert "current response time is unknown" in timing["units"]
    assert "control_timing" not in f["pedal_facts"]


@pytest.mark.parametrize("delay", [True, -0.001, 2.001, float("nan"), float("inf"), "1"])
def test_invalid_control_timing_is_rejected_before_request_or_reservation(tmp_path, delay):
    sim = DuelSimulation()
    budget = Budget(tmp_path / "budget.json")
    journal = BudgetJournal(budget, tmp_path / "events.jsonl")
    try:
        with pytest.raises(PromptDomainError):
            DuelDriver(
                racer_id="red", config=sim.config(), route=ROUTE, budget=journal.view("red"),
                http=object(), capture=WireCapture(), output=tmp_path / "red",
                api_key="free-invalid-timing", control_timing_s=delay,
            )
    finally:
        journal.close()
    assert budget.summary()["requests"] == 0 and not journal.events


def test_nonfinite_wheel_motion_and_wrong_clock_are_rejected():
    sim = DuelSimulation()
    raw, config = sim.observation("red"), sim.config()
    raw["kart"]["yaw_rate"] = float("nan")
    with pytest.raises(PromptDomainError):
        duel_facts(raw, config, "red", include_wheel_motion=True)
    config["dt"] = 1 / 30
    with pytest.raises(PromptDomainError, match="control timing"):
        duel_facts(sim.observation("red"), config, "red", control_timing_s=0)


@pytest.mark.parametrize("delay", [0.0, 1.0, 2.0])
def test_both_head_timing_adds_only_independent_mechanics_packets(delay):
    sim = DuelSimulation()
    raw, config = sim.observation("red"), sim.config()
    unchanged = copy.deepcopy(raw)
    baseline = duel_facts(raw, config, "red")
    facts = duel_facts(raw, config, "red", control_timing_s=delay, include_pedal_timing=True)
    stripped = copy.deepcopy(facts)
    for head in ("wheel", "pedal"):
        packet = stripped[head + "_facts"].pop("control_timing")
        assert packet["post_response_wait_s"] == delay and packet["physics_hz"] == 60
        assert "current response time is unknown" in packet["units"]
        assert "Physics and the held input continue" in packet["units"]
    assert stripped == baseline and raw == unchanged
    original, treatment = [
        DuelDecisionClient(facts=f, handling=config["handling"], budget=None,
                           http_client=object(), api_key="free-both-head-timing")
        for f in (baseline, facts)
    ]
    assert original.component_criteria == treatment.component_criteria
    for head in ("wheel", "pedal"):
        assert original.questions[head]["criteria"] == treatment.questions[head]["criteria"]
        assert original.questions[head]["instructions"]["rules"] == treatment.questions[head]["instructions"]["rules"]
    facts["pedal_facts"]["control_timing"]["physics_hz"] = -1
    assert facts["wheel_facts"]["control_timing"]["physics_hz"] == 60


@pytest.mark.parametrize("value", [None, 1, "true", []])
def test_invalid_pedal_timing_profile_is_rejected_before_reservation(tmp_path, value):
    sim = DuelSimulation()
    budget = Budget(tmp_path / "budget.json")
    journal = BudgetJournal(budget, tmp_path / "events.jsonl")
    try:
        with pytest.raises(TypeError, match="Pedal timing"):
            DuelDriver(
                racer_id="red", config=sim.config(), route=ROUTE, budget=journal.view("red"),
                http=object(), capture=WireCapture(), output=tmp_path / "red",
                api_key="free-invalid-pedal-timing", control_timing_s=1.0,
                include_pedal_timing=value,
            )
    finally:
        journal.close()
    assert budget.summary()["requests"] == 0 and not journal.events
    with pytest.raises(TypeError, match="Pedal timing"):
        duel_facts(sim.observation("red"), sim.config(), "red", include_pedal_timing=value)


def test_pedal_timing_requires_an_explicit_known_wait(tmp_path):
    sim = DuelSimulation()
    with pytest.raises(PromptDomainError, match="requires declared"):
        duel_facts(sim.observation("red"), sim.config(), "red", include_pedal_timing=True)
    with pytest.raises(PromptDomainError, match="requires declared"):
        DuelDriver(
            racer_id="red", config=sim.config(), route=ROUTE, budget=object(), http=object(),
            capture=WireCapture(), output=tmp_path, include_pedal_timing=True,
        )


@pytest.mark.parametrize("options,error", [
    ({"include_pedal_timing": "true"}, TypeError),
    ({"include_pedal_timing": True}, ValueError),
])
async def test_invalid_collector_timing_profile_stops_before_session_or_budget(tmp_path, options, error):
    from mcpkart.duel_bench import collect_duel

    destination = tmp_path / "must-not-exist"
    with pytest.raises(error, match="Pedal timing"):
        await collect_duel(
            url="invalid-unused", routes={}, setup={}, seed=0, output=destination,
            budget=object(), **options,
        )
    assert not destination.exists()
