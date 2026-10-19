import copy
import json
import math
from argparse import Namespace
from collections import Counter

import httpx
import pytest

from mcpkart.decisions import (
    DRIVING_INSTRUCTIONS,
    Budget,
    BudgetExceeded,
    DecisionClient,
    explicit_control_description,
)
from mcpkart.probe import (
    REFERENCE_TICKS,
    WireCapture,
    action_effect,
    atomic_json,
    collect_fixtures,
    command,
    correction_fixtures,
    diagnostics,
    fixture,
    frozen_context,
    navigation_fixtures,
    replay_observations,
    run_probes,
    schedule,
    select_fixtures,
)
from mcpkart.sim import ACTIONS, Simulation


def fake_record_directory(tmp_path):
    before = Simulation().observation()
    before["kart"]["speed"] = 24
    before["kart"]["vx"] = 24
    after = json.loads(json.dumps(before))
    after["track"]["on_road"] = False
    data = {"requests": [{"observation": before, "action": "straight_accelerate", "latency_ms": 200},
                         {"observation": after, "action": "left_accelerate", "latency_ms": 210}]}
    for name in ("typesafe--jev-1.14", "openai--gpt-6-luna-decisions"):
        (tmp_path / f"{name}--seed-0.json").write_text(json.dumps(data))
    return tmp_path


def test_fixtures_are_deterministic_and_reference_labels_never_enter_model_state(tmp_path):
    records = fake_record_directory(tmp_path)
    first, second = collect_fixtures(records), collect_fixtures(records)
    assert first == second
    assert len(first) == 10
    assert {item["source"]["tick"] for item in first if item["source"]["kind"] == "scripted_reference"} == set(
        REFERENCE_TICKS)
    for item in first:
        assert item["diagnostic_reference_action"] in ACTIONS
        state = json.dumps(item["observation"])
        assert "diagnostic_reference_action" not in state
        assert "recorded_action" not in state
        assert "handling" in item["observation"] and "next_checkpoint" in item["observation"]
        for previous in item["context"]["recent_motion"]["samples"]:
            assert previous["tick"] < item["observation"]["tick"]
        if item["source"]["kind"] == "scripted_reference":
            assert all(tick % 12 == 0 and tick < item["observation"]["tick"] for tick in item["source"]["history"]["prior_ticks"])


def test_missing_historical_records_do_not_require_other_models(tmp_path):
    assert len(collect_fixtures(tmp_path)) == 8
    fake_record_directory(tmp_path)
    (tmp_path / "openai--gpt-6-luna-decisions--seed-0.json").unlink()
    snapshots = collect_fixtures(tmp_path)
    assert len(snapshots) == 9
    assert any(item["id"] == "jev_first_curve_pre_exit" for item in snapshots)
    assert not any(item["id"] == "luna_first_curve_pre_exit" for item in snapshots)


def runtime_replay_fixture(action):
    """Same step/command order as RaceRuntime, including a genuine rescue."""
    from mcpkart.bench import driving_evidence

    sim = Simulation(seed=0, reset_after_s=.5)
    commands = [{"applied_tick": 3, "action_id": action}]
    samples, requests, expected = [], [], {}
    for _ in range(220):
        if sim.tick+1 == 3:
            sim.set_control(action)
        sim.step()
        raw = sim.observation()
        samples.append(raw)
        if sim.tick in (37, 43):
            expected[sim.tick] = raw
        if sim.tick in (49, 55, 220):
            expected[sim.tick] = raw
            requests.append({"observation_tick": sim.tick,
                             "observation": driving_evidence(raw, variant="road_physics"), "action": action})
    return {"model": "fixture/model", "race": {"seed": 0, "config": sim.config(),
                                                "commands": commands, "samples": samples},
            "requests": requests}, expected


@pytest.mark.parametrize("action,side,tick", (("hard_left_accelerate", "left", 49),
                                            ("hard_right_accelerate", "right", 55)))
def test_replay_correction_uses_exact_runtime_pose_and_does_not_leak_diagnostics(tmp_path, action, side, tick):
    document, expected = runtime_replay_fixture(action)
    path = tmp_path / "driving.json"
    path.write_text(json.dumps(document))
    reconstructed = replay_observations(document, {tick, 220})
    assert reconstructed[tick] == expected[tick]
    assert reconstructed[220] == expected[220]
    assert reconstructed[220]["rescue"]["count"] == 1
    assert reconstructed[220]["control"] == "straight_coast"
    snapshots = correction_fixtures(path)
    assert len(snapshots) == 2
    snapshot = next(snapshot for snapshot in snapshots if snapshot["id"].endswith("_correction"))
    assert snapshot["id"] == f"recorded_{side}_oversteer_correction"
    assert snapshot["source"]["observation_tick"] == tick
    assert snapshot["source"]["pose_validation"]["runtime_pose_sample_checked"]
    assert set(snapshot["source"]["pose_validation"]["absolute_errors"].values()) == {0}
    assert snapshot["observation"]["kart"] == expected[tick]["kart"]
    state = json.dumps(snapshot["observation"])
    assert "diagnostic_reference_action" not in state
    assert "recorded_action" not in state
    assert "source_sha256" not in state
    early = next(snapshot for snapshot in snapshots if snapshot["id"].endswith("_early"))
    assert early["id"] == f"recorded_{side}_oversteer_early"
    assert early["observation"]["tick"] == tick-12
    assert early["observation"]["kart"] == expected[tick-12]["kart"]
    assert early["source"]["lookback_ticks"] == 12
    assert early["source"]["pose_validation"]["progress_rescue_control_checked"]
    assert not early["source"]["pose_validation"]["request_at_tick_required"]
    assert len(collect_fixtures(tmp_path, driving_record=path)) == 10
    for target in snapshots:
        prior = target["source"]["history"]["prior_ticks"]
        assert all(tick in (49, 55, 220) and tick < target["observation"]["tick"] for tick in prior)
        assert all(row["tick"] in prior for row in target["context"]["recent_motion"]["samples"])


def test_frozen_history_rejects_future_and_clears_motion_after_rescue_only():
    base = Simulation().observation()

    def state(tick, count=0, resets=0):
        value = copy.deepcopy(base)
        value.update(tick=tick, time=tick/60)
        value["progress"].update(checkpoints_passed=count, resets=resets)
        value["rescue"].update(count=resets, last_reset_tick=36 if resets else None)
        return value

    current = state(48, count=1, resets=1)
    context = frozen_context(current, [state(12), state(24, count=1), state(36, count=1, resets=1)])
    assert [row["tick"] for row in context["recent_motion"]["samples"]] == [36]
    assert context["checkpoint_clock"]["last_progress_observed_at_s"] == .4
    assert context["checkpoint_clock"]["seconds_without_observed_checkpoint_progress"] == .4
    with pytest.raises(ValueError, match="before the target"):
        frozen_context(state(12), [state(24)])


def test_navigation_fixture_selector_distinguishes_valid_behind_nose_and_missed_gate(tmp_path, monkeypatch):
    from mcpkart import probe

    sim = Simulation()
    config = sim.config()

    def state(tick, gate_id, distance, *, reverse=False, onroad=True, passed=1):
        gate = config["track"]["checkpoints"][gate_id]
        sim.x = gate["x"]+distance*math.cos(gate["heading"])
        sim.y = gate["y"]+distance*math.sin(gate["heading"])
        sim.heading = gate["heading"]+(math.pi if reverse else 0)
        sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)
        sim.tick, sim.elapsed = tick, tick/60
        sim.checkpoints_passed, sim.next_checkpoint = passed, gate_id
        raw = sim.observation()
        raw["track"]["on_road"] = onroad
        return raw

    states = {12: state(12, 1, -.1, reverse=True, passed=0), 24: state(24, 2, -2),
              60: state(60, 2, 1), 180: state(180, 2, 2, onroad=False), 192: state(192, 2, 2)}
    credit = copy.deepcopy(states[24])
    credit.update(tick=13, time=13/60)
    document = {"model": "test/model", "race": {"seed": 0, "config": config, "commands": [],
                                                  "samples": [*states.values(), credit]},
                "requests": [{"observation_tick": tick, "observation": {"tick": tick}} for tick in states]}
    states[13] = credit  # Available physics sample, intentionally not a driver request.
    path = tmp_path / "navigation.json"
    path.write_text(json.dumps(document))
    # Replay itself is covered independently; this isolates the fixed geometric
    # selection rule and validates every history/target against saved samples.
    monkeypatch.setattr(probe, "replay_observations", lambda document, ticks: {tick: states[tick] for tick in ticks})
    snapshots = {item["id"]: item for item in navigation_fixtures(path)}
    assert snapshots["recorded_gate_approach_behind_nose"]["observation"]["tick"] == 12
    assert snapshots["recorded_gate_after_credit"]["observation"]["tick"] == 24
    assert snapshots["recorded_missed_gate_early"]["observation"]["tick"] == 60
    stalled = snapshots["recorded_missed_gate_stalled"]
    assert stalled["observation"]["tick"] == 192  # Prefer first on-road >=2s later.
    assert stalled["source"]["actual_seconds_after_first_target"] == 2.2
    for item in snapshots.values():
        assert all(tick < item["observation"]["tick"] for tick in item["source"]["history"]["prior_ticks"])
        assert item["source"]["pose_validation"]["validated"]
    assert [row["tick"] for row in stalled["context"]["recent_motion"]["samples"]] == [180]


def test_replay_rejects_wrong_configuration_or_pose_instead_of_probing_wrong_state(tmp_path):
    document, _ = runtime_replay_fixture("hard_left_accelerate")
    wrong_config = json.loads(json.dumps(document))
    wrong_config["race"]["config"]["handling"]["max_speed"] = 99
    with pytest.raises(ValueError, match="configuration"):
        replay_observations(wrong_config, {49})
    wrong_pose = json.loads(json.dumps(document))
    wrong_pose["requests"][0]["observation"]["road"]["offset_m"] += .1
    path = tmp_path / "wrong_pose.json"
    path.write_text(json.dumps(wrong_pose))
    with pytest.raises(ValueError, match="pose validation"):
        correction_fixtures(path)
    wrong_commands = json.loads(json.dumps(document))
    wrong_commands["race"]["commands"].append(wrong_commands["race"]["commands"][0])
    with pytest.raises(ValueError, match="increasing applied ticks"):
        replay_observations(wrong_commands, {49})
    wrong_early = json.loads(json.dumps(document))
    next(sample for sample in wrong_early["race"]["samples"] if sample["tick"] == 37)["kart"]["x"] += .1
    path = tmp_path / "wrong_early.json"
    path.write_text(json.dumps(wrong_early))
    with pytest.raises(ValueError, match="runtime sample validation"):
        correction_fixtures(path)


@pytest.mark.parametrize("model_count,variant_count", ((1, 1), (3, 4), (2, 4), (4, 3)))
def test_schedule_includes_every_pair_once_and_rotates_order(model_count, variant_count):
    fixtures = [{"id": "a"}, {"id": "b"}]
    routes = [{"model": f"model-{index}"} for index in range(model_count)]
    variants = [f"variant-{index}" for index in range(variant_count)]
    order = schedule(fixtures, routes, variants)
    counts = Counter((snapshot["id"], route["model"], variant) for snapshot, route, variant, repeat in order)
    assert len(counts) == 2*model_count*variant_count
    assert set(counts.values()) == {1}
    assert order == schedule(fixtures, routes, variants)
    if model_count > 1:
        assert order[0][1] != order[model_count*variant_count][1]


def test_repeated_schedule_covers_each_pair_three_times_and_rotates_profiles():
    fixtures = [{"id": "a"}, {"id": "b"}]
    routes = [{"model": "jev"}, {"model": "another"}]
    variants = ["road_physics", "road", "road_text"]
    order = schedule(fixtures, routes, variants, repeats=3)
    counts = Counter((snapshot["id"], route["model"], variant) for snapshot, route, variant, repeat in order)
    assert len(order) == 36
    assert set(counts.values()) == {3}
    assert {repeat for *_, repeat in order} == {1, 2, 3}
    first_profiles = [next(variant for *_, variant, block in order if block == repeat) for repeat in (1, 2, 3)]
    assert len(set(first_profiles)) > 1
    assert order == schedule(fixtures, routes, variants, repeats=3)
    for repeats in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="integer"):
            schedule(fixtures, routes, variants, repeats=repeats)


def test_fixture_selection_keeps_requested_order_and_rejects_bad_ids():
    fixtures = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    assert select_fixtures(fixtures, " c, a ") == [fixtures[2], fixtures[0]]
    for selection in ("", ",", "a,", "a,a", "unknown"):
        with pytest.raises(ValueError, match="Fixtures|Unknown fixture"):
            select_fixtures(fixtures, selection)


@pytest.mark.asyncio
async def test_invalid_fixture_selection_fails_before_budget_or_paid_client(tmp_path, monkeypatch):
    from mcpkart import probe

    def must_not_run(*args, **kwargs):
        raise AssertionError("Paid client/budget/discovery must not run for invalid selection")

    monkeypatch.setattr(probe, "Budget", must_not_run)
    monkeypatch.setattr(probe, "DecisionClient", must_not_run)
    monkeypatch.setattr(probe, "discover_routes", must_not_run)
    args = Namespace(output=str(tmp_path / "output"), variants="raw", repeats=3,
                     records=str(tmp_path), driving_record=None, fixtures="unknown", routes="missing",
                     models="typesafe/jev-1.14", control_language="numeric")
    with pytest.raises(ValueError, match="Unknown fixture"):
        await command(args)
    assert not (tmp_path / "output").exists()


def test_action_effects_are_deterministic_and_diagnostics_are_not_exact_groundtruth():
    observation = Simulation().observation()
    original = json.loads(json.dumps(observation))
    accelerate = action_effect(observation, "straight_accelerate")
    coast = action_effect(observation, "straight_coast")
    assert accelerate == action_effect(observation, "straight_accelerate")
    assert observation == original
    assert accelerate["end_speed_m_s"] > coast["end_speed_m_s"]
    assert accelerate["centreline_progress_m"] > coast["centreline_progress_m"]
    assert accelerate["rescue_enabled"] is False
    snapshot = fixture("rest", observation, {})
    assert diagnostics(snapshot, snapshot["diagnostic_reference_action"])["exact_agreement"]
    assert diagnostics(snapshot, None)["action_effect"] is None


def test_atomic_json_rejects_existing_artifacts(tmp_path):
    path = tmp_path / "record.json"
    atomic_json(path, {"first": True})
    with pytest.raises(FileExistsError):
        atomic_json(path, {"first": False})
    assert json.loads(path.read_text()) == {"first": True}
    atomic_json(path, {"second": True}, replace=True)
    assert json.loads(path.read_text()) == {"second": True}
    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("control_language", ["numeric", "explicit"])
@pytest.mark.parametrize("instruction_style", ["original", "question_first"])
async def test_real_client_wire_capture_keeps_instructions_exact_and_redacts_credentials(tmp_path, control_language,
                                                                                      instruction_style):
    secret = "sk-or-v1-ThisIsATestOnly"
    capture = WireCapture()
    capture.secret = secret
    route = {"model": "test/model", "provider": "test", "provider_name": "Test",
             "price_input_per_token": 0, "price_output_per_token": 0,
             "max_completion_tokens": 1, "context_length": 10000}

    def handler(request):
        body = json.loads(request.content)
        assert body["questions"]["control"]["instructions"] == client.instructions
        assert client.instructions == DRIVING_INSTRUCTIONS if instruction_style == "original" else client.instructions != DRIVING_INSTRUCTIONS
        assert body["questions"]["control"]["criteria"] == {
            key: action["description"] if control_language == "numeric" else explicit_control_description(action)
            for key, action in ACTIONS.items()}
        assert request.headers["Authorization"] == f"Bearer {secret}"
        return httpx.Response(200, json={"model": "test/model", "provider": "Test",
                                       "answers": {"control": {"choice": "straight_accelerate"}},
                                       "usage": {"cost": 0, "input_tokens": 100, "output_tokens": 0},
                                       "echoed_secret": secret})

    budget = Budget(path=tmp_path / "budget.json", cap_usd=10)
    async with (
        httpx.AsyncClient(transport=httpx.MockTransport(handler),
                          event_hooks={"request": [capture.request], "response": [capture.response]}) as http,
        DecisionClient(budget=budget, actions=ACTIONS, api_key=secret, http_client=http,
                       control_language=control_language, instruction_style=instruction_style) as client,
    ):
        result = await run_probes(client, budget, [route], [fixture("rest", Simulation().observation(), {})],
                                  ["raw"], tmp_path / "output", capture, control_language=control_language,
                                  instruction_style=instruction_style)
    assert result["complete"]
    saved = json.loads(next((tmp_path / "output" / "calls").glob("*.json")).read_text())
    wire = saved["wire"][0]
    assert secret not in json.dumps(saved)
    assert "Authorization" not in json.dumps(wire)
    assert wire["response_json"]["echoed_secret"] == "[REDACTED]"
    assert saved["encoded_bytes"] == len(wire["request_body_utf8"].encode())
    assert json.loads(wire["request_body_utf8"])["state"] == saved["state"]
    assert "diagnostic_reference_action" not in wire["request_body_utf8"]
    assert saved["request_questions"] == json.loads(wire["request_body_utf8"])["questions"]
    assert saved["admissible_choice_ids"] == list(ACTIONS)
    assert saved["control_language"] == control_language
    assert saved["instruction_style"] == instruction_style
    assert result["instruction_style"] == instruction_style
    manifest = json.loads((tmp_path / "output" / "manifest.json").read_text())
    assert manifest["question_contract"] == saved["request_questions"]
    assert manifest["instruction_style"] == instruction_style
    assert manifest["instructions_changed"] == (instruction_style != "original")


class FakeBudget:
    def summary(self):
        return {"cap_usd": 10}


@pytest.mark.asyncio
async def test_probe_forwards_frozen_context_only_to_history_profile(tmp_path):
    class Client:
        async def decide(self, route, evidence):
            return {"ok": True, "action": "straight_accelerate", "cost": 0, "latency_ms": 1}

    snapshot = next(item for item in collect_fixtures(tmp_path) if item["id"] == "first_bend_approach")
    original_context = copy.deepcopy(snapshot["context"])
    output = tmp_path / "history"
    await run_probes(Client(), FakeBudget(), [{"model": "test/model"}], [snapshot], ["raw", "road_history"], output)
    records = [json.loads(path.read_text()) for path in (output / "calls").glob("*.json")]
    raw = next(record for record in records if record["variant"] == "raw")
    historical = next(record for record in records if record["variant"] == "road_history")
    assert "history" not in raw["state"]
    assert historical["state"]["history"]["status"] == "available"
    assert historical["state"]["history"]["recent_motion"] == original_context["recent_motion"]
    assert historical["state"]["history"]["checkpoint_clock"] == original_context["checkpoint_clock"]
    assert snapshot["context"] == original_context
    assert "history_contract" in json.loads((output / "manifest.json").read_text())


@pytest.mark.asyncio
async def test_budget_stop_preserves_prior_calls_and_never_overwrites_output(tmp_path):
    class Client:
        calls = 0

        async def decide(self, route, evidence):
            self.calls += 1
            if self.calls == 2:
                raise BudgetExceeded("stop")
            return {"ok": True, "action": "straight_accelerate", "cost": .001,
                    "latency_ms": 123, "payload_bytes": 100}

    client = Client()
    output = tmp_path / "output"
    snapshots = [fixture("rest", Simulation().observation(), {})]
    summary = await run_probes(client, FakeBudget(), [{"model": "test/model"}], snapshots,
                               ["raw", "road"], output)
    assert summary["status"] == "budget_exhausted"
    assert not summary["complete"]
    assert summary["completed_requests"] == 1
    assert len(list((output / "calls").glob("*.json"))) == 1
    assert json.loads((output / "summary.json").read_text()) == summary
    with pytest.raises(FileExistsError):
        await run_probes(client, FakeBudget(), [{"model": "test/model"}], snapshots, ["raw"], output)
    assert client.calls == 2


@pytest.mark.asyncio
async def test_endpoint_error_stays_in_denominator_without_retry(tmp_path):
    class Client:
        calls = 0

        async def decide(self, route, evidence):
            self.calls += 1
            return {"ok": False, "action": None, "cost": .001, "latency_ms": 123,
                    "payload_bytes": 100, "error": "refusal"}

    client = Client()
    summary = await run_probes(client, FakeBudget(), [{"model": "test/model"}],
                               [fixture("rest", Simulation().observation(), {})], ["raw"], tmp_path / "output")
    assert client.calls == 1
    assert summary["complete"]
    assert summary["groups"][0]["requests"] == summary["groups"][0]["errors"] == 1
    assert summary["groups"][0]["diagnostic_denominator"] == 0


@pytest.mark.asyncio
async def test_repeated_probe_artifacts_are_unique_and_report_action_distributions(tmp_path):
    class Client:
        calls = 0
        control_language = "explicit"

        async def decide(self, route, evidence):
            self.calls += 1
            return {"ok": True, "action": "right_accelerate", "cost": .001,
                    "latency_ms": 123, "payload_bytes": 100}

    client = Client()
    output = tmp_path / "repeated"
    snapshots = [fixture("rest", Simulation().observation(), {})]
    summary = await run_probes(client, FakeBudget(), [{"model": "test/model"}], snapshots,
                               ["raw", "road", "road_text"], output, repeats=3, control_language="explicit")
    files = list((output / "calls").glob("*.json"))
    records = [json.loads(path.read_text()) for path in files]
    manifest = json.loads((output / "manifest.json").read_text())
    assert len(files) == len({path.name for path in files}) == 9
    assert {record["repeat"] for record in records} == {1, 2, 3}
    assert all(f"repeat-{record['repeat']:02d}" in path.name for path, record in zip(files, records))
    assert all(record["control_language"] == "explicit" for record in records)
    assert manifest["repeats"] == summary["repeats"] == 3
    assert manifest["planned_requests"] == summary["planned_requests"] == 9
    assert len(manifest["request_order"]) == 9
    for group in summary["fixture_groups"]:
        assert group["requests"] == 3
        assert group["action_counts"] == {"right_accelerate": 3}
        assert sum(group["direction_counts"].values()) == 3
    with pytest.raises(FileExistsError):
        await run_probes(client, FakeBudget(), [{"model": "test/model"}], snapshots,
                         ["raw"], output, repeats=3)
    assert client.calls == 9
