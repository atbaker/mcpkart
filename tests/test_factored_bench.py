"""Free benchmark checks for joint and factored direct decisions."""

import argparse
import copy
import json
import sys
from typing import ClassVar

import httpx
import pytest

from mcpkart.sim import ACTIONS, Simulation

RUNTIME_INFO = {
    "backend": "process", "protocol_version": 1, "watchdog_enabled": True,
    "clock_mode": "fixed_step_wall_clock", "physics_hz": 60,
}
SETUP = {"course": "stadium", "road_width": 24, "max_steering_angle": .12}
ROUTE = {
    "model": "typesafe/jev-1.14", "resolved_model": "typesafe/jev-1.14-20261014",
    "provider": "typesafe", "provider_name": "TypeSafe", "endpoint_name": "test endpoint",
    "price_input_per_token": .000000042, "price_output_per_token": 0,
    "price_per_request": 0, "context_length": 262144, "max_prompt_tokens": 262144,
    "max_completion_tokens": 235929,
}


@pytest.fixture
def modules():
    from mcpkart import bench, decisions
    return bench, decisions


def initial_observation():
    return {
        **Simulation(**SETUP).observation(), "observed_ns": 100,
        "race_id": "factored-test", "status": "running",
    }


def fake_race():
    return {
        "summary": {"finished": True, "elapsed": 1},
        "config": Simulation(**SETUP).config(),
        "runtime_info": copy.deepcopy(RUNTIME_INFO),
        "timing": {"backend": "process", "infrastructure_valid": True},
    }


@pytest.mark.parametrize("bad_component", [None, "wheel", "pedal", "http"])
async def test_factored_request_applies_exactly_one_atomic_native_action_or_none(
    modules, monkeypatch, tmp_path, bad_component,
):
    bench, decisions = modules
    calls, payloads = [], []
    initial = initial_observation()

    async def fake_tool(client, name, arguments=None):
        calls.append((name, copy.deepcopy(arguments)))
        if name == "start_race":
            return copy.deepcopy(initial)
        if name == "drive":
            return {"applied": True, "observation": {**initial, "finished": True}}
        assert name == "finish_race"  # No observe or drive after a component failure.
        return fake_race()

    def respond(request):
        payloads.append(json.loads(request.content))
        answers = {
            "wheel": {"type": "choice", "choice": "left"},
            "pedal": {"type": "choice", "choice": "brake"},
        }
        if bad_component in answers:
            answers[bad_component]["choice"] = "invalid-component"
        return httpx.Response(503 if bad_component == "http" else 200, json={
            "model": ROUTE["resolved_model"], "provider": "TypeSafe", "answers": answers,
            "usage": {"input_tokens": 300, "output_tokens": 20, "cost": .0000126},
        })

    monkeypatch.setattr(bench, "tool", fake_tool)
    monkeypatch.setattr(bench, "fingerprint", lambda: "frozen-draft")
    path = tmp_path / "trial.json"
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        api = decisions.DecisionClient(
            budget=decisions.Budget(path=tmp_path / "local-budget.json"), actions=ACTIONS,
            api_key="test-key", http_client=http, max_input_tokens=16384,
            decision_layout="factored", handling=Simulation(**SETUP).config()["handling"],
        )
        expected_questions = copy.deepcopy(api.questions)
        report = await bench.run_trial(
            None, api, ROUTE, 0, 56.7, path, telemetry="road_navigation",
            runtime_info=RUNTIME_INFO, race_setup=SETUP, stop_on_first_error=True,
        )
    assert len(payloads) == len(report["requests"]) == 1
    assert report["questions"] == expected_questions == payloads[0]["questions"]
    assert report["action_criteria"] == api.criteria
    assert report["decision_layout"] == "factored" and report["stop_on_first_error"]
    assert json.loads(path.read_text())["requests"] == report["requests"]
    if bad_component is None:
        assert [name for name, _ in calls] == ["start_race", "drive", "finish_race"]
        assert calls[1][1] == {
            "race_id": "factored-test", "action_id": "left_brake",
            "observation_tick": initial["tick"], "command_seq": 1,
        }
        assert report["requests"][0]["applied"]
        assert calls[-1][1] == {"reason": "completed"}
    else:
        assert [name for name, _ in calls] == ["start_race", "finish_race"]
        assert calls[-1][1] == {"reason": "first_endpoint_error"}
        assert not report["requests"][0]["ok"]
        assert report["requests"][0]["action"] is None
        assert "applied" not in report["requests"][0]


async def test_default_joint_policy_retains_three_consecutive_errors(modules, monkeypatch, tmp_path):
    bench, _ = modules
    calls = []

    async def fake_tool(client, name, arguments=None):
        calls.append((name, arguments))
        if name in {"start_race", "observe"}:
            return initial_observation()
        assert name == "finish_race"
        return fake_race()

    class FailedDriver:
        async def decide(self, route, evidence):
            return {"ok": False, "action": None, "latency_ms": 1, "cost": 0}

    monkeypatch.setattr(bench, "tool", fake_tool)
    result = await bench.run_trial(
        None, FailedDriver(), ROUTE, 0, 56.7, tmp_path / "joint.json", runtime_info=RUNTIME_INFO,
    )
    assert len(result["requests"]) == 3
    assert result["decision_layout"] == "joint" and not result["stop_on_first_error"]
    assert calls[-1] == ("finish_race", {"reason": "three_consecutive_endpoint_errors"})
    assert all(name != "drive" for name, _ in calls)


def resume_values(bench, layout="joint"):
    questions = {"control": {"type": "choice", "instructions": "guide", "criteria": {"a": "A"}}}
    if layout == "factored":
        questions = {
            "wheel": {"type": "choice", "instructions": "guide wheel", "criteria": {"left": "L"}},
            "pedal": {"type": "choice", "instructions": "guide pedal", "criteria": {"brake": "B"}},
        }
    kwargs = {
        "route": copy.deepcopy(ROUTE), "seed": 0, "baseline": 56.7, "telemetry": "raw",
        "control_language": "numeric", "instruction_style": "original", "instructions": "guide",
        "action_criteria": {"a": "A"}, "runtime_info": copy.deepcopy(RUNTIME_INFO),
        "decision_layout": layout, "questions": copy.deepcopy(questions),
    }
    saved = {
        "fingerprint": "frozen-draft", "model": ROUTE["model"], "route": copy.deepcopy(ROUTE),
        "seed": 0, "telemetry": "raw", "control_language": "numeric", "instruction_style": "original",
        "instructions": "guide", "action_criteria": {"a": "A"},
        "runtime_info": copy.deepcopy(RUNTIME_INFO), "decision_layout": layout,
        "questions": copy.deepcopy(questions), "metrics": {"reference_s": 56.7},
        "race": {"config": Simulation(reset_after_s=bench.RESET_AFTER_S).config(), "deadline": 56.7 * 3},
    }
    return saved, kwargs


@pytest.mark.parametrize("layout", ["joint", "factored"])
def test_resume_accepts_exact_definitions_and_rejects_changed_question_fields(modules, monkeypatch, layout):
    bench, _ = modules
    monkeypatch.setattr(bench, "fingerprint", lambda: "frozen-draft")
    saved, kwargs = resume_values(bench, layout)
    bench.validate_resume(saved, **kwargs)
    question = next(iter(saved["questions"].values()))
    question["criteria"][next(iter(question["criteria"]))] = "changed exact description"
    with pytest.raises(ValueError, match="exact question definitions"):
        bench.validate_resume(saved, **kwargs)


@pytest.mark.parametrize("saved_layout,current_layout", [("joint", "factored"), ("factored", "joint")])
def test_resume_cannot_mix_decision_layouts(modules, monkeypatch, saved_layout, current_layout):
    bench, _ = modules
    monkeypatch.setattr(bench, "fingerprint", lambda: "frozen-draft")
    saved, kwargs = resume_values(bench, saved_layout)
    kwargs["decision_layout"] = current_layout
    with pytest.raises(ValueError, match="decision layouts"):
        bench.validate_resume(saved, **kwargs)


def test_resume_old_joint_files_remain_compatible_but_factored_requires_definitions(modules, monkeypatch):
    bench, _ = modules
    monkeypatch.setattr(bench, "fingerprint", lambda: "frozen-draft")
    saved, kwargs = resume_values(bench)
    saved.pop("decision_layout")
    saved.pop("questions")
    bench.validate_resume(saved, **kwargs)
    saved["decision_layout"] = kwargs["decision_layout"] = "factored"
    with pytest.raises(ValueError, match="without exact question definitions"):
        bench.validate_resume(saved, **kwargs)


def test_resume_stopping_policy_cannot_change(modules, monkeypatch):
    bench, _ = modules
    monkeypatch.setattr(bench, "fingerprint", lambda: "frozen-draft")
    saved, kwargs = resume_values(bench)
    kwargs["stop_on_first_error"] = True
    with pytest.raises(ValueError, match="stopping policies"):
        bench.validate_resume(saved, **kwargs)


def test_saved_joint_questions_require_current_definitions_for_resume(modules, monkeypatch):
    bench, _ = modules
    monkeypatch.setattr(bench, "fingerprint", lambda: "frozen-draft")
    saved, kwargs = resume_values(bench)
    kwargs["questions"] = None
    with pytest.raises(ValueError, match="without current exact question definitions"):
        bench.validate_resume(saved, **kwargs)


@pytest.mark.parametrize("layout", ["joint", "factored"])
def test_cli_parses_and_forwards_layout_and_stopping_policy(modules, monkeypatch, layout):
    bench, _ = modules
    received = []

    async def capture(args):
        received.append(args)

    monkeypatch.setattr(bench, "remote_command", capture)
    monkeypatch.setattr(sys, "argv", [
        "mcpkart-bench", "latency", "--decision-layout", layout, "--stop-on-first-error",
    ])
    bench.main()
    assert received[0].decision_layout == layout and received[0].stop_on_first_error


def test_cli_defaults_to_joint_and_existing_error_policy(modules, monkeypatch):
    bench, _ = modules
    received = []

    async def capture(args):
        received.append(args)

    monkeypatch.setattr(bench, "remote_command", capture)
    monkeypatch.setattr(sys, "argv", ["mcpkart-bench", "latency"])
    bench.main()
    assert received[0].decision_layout == "joint" and not received[0].stop_on_first_error


@pytest.mark.parametrize("layout,telemetry,language,expected", [
    ("joint", "raw", "numeric", 8192),
    ("factored", "raw", "numeric", 16384),
    ("joint", "raw", "geometry", 16384),
    ("factored", "road_navigation", "numeric", 16384),
    ("joint", "scene_svg", "numeric", 16384),
    ("factored", "scene_image", "numeric", 262144),
])
async def test_remote_client_receives_layout_and_conservative_input_guard(
    modules, monkeypatch, tmp_path, layout, telemetry, language, expected,
):
    bench, decisions = modules
    captured = []
    (tmp_path / "routes.json").write_text(json.dumps([ROUTE]))

    class FakeBudget:
        def __init__(self, *args, **kwargs):
            pass

        def summary(self):
            return {}

    class FakeDriver:
        def __init__(self, **kwargs):
            captured.append(kwargs)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    monkeypatch.setattr(decisions, "Budget", FakeBudget)
    monkeypatch.setattr(decisions, "DecisionClient", FakeDriver)
    args = argparse.Namespace(
        command="latency", output=str(tmp_path), models=ROUTE["model"], telemetry=telemetry,
        control_language=language, instruction_style="damped", decision_layout=layout, samples=0,
    )
    await bench.remote_command(args)
    assert captured[0]["decision_layout"] == layout
    assert captured[0]["max_input_tokens"] == expected


async def test_remote_comparison_stops_before_second_seed_after_first_endpoint_error(
    modules, monkeypatch, tmp_path,
):
    bench, decisions = modules
    starts = []
    (tmp_path / "routes.json").write_text(json.dumps([ROUTE]))

    async def fake_tool(client, name, arguments=None):
        if name == "runtime_info":
            return RUNTIME_INFO
        if name == "start_race":
            starts.append(arguments["seed"])
            return initial_observation()
        assert name == "finish_race"
        return fake_race()

    class FakeContext:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class FakeBudget(FakeContext):
        def summary(self):
            return {}

    class FakeDriver(FakeContext):
        instructions = "guide"
        criteria: ClassVar[dict] = {"a": "A"}
        decision_layout = "factored"
        questions: ClassVar[dict] = {"wheel": {"type": "choice"}, "pedal": {"type": "choice"}}

        async def decide(self, route, evidence):
            return {"ok": False, "action": None, "latency_ms": 1, "cost": 0}

    monkeypatch.setattr(bench, "tool", fake_tool)
    monkeypatch.setattr(bench, "Client", FakeContext)
    monkeypatch.setattr(bench, "reference_durations", lambda *args, **kwargs: {0: 56.7, 1: 56.7})
    monkeypatch.setattr(decisions, "Budget", FakeBudget)
    monkeypatch.setattr(decisions, "DecisionClient", FakeDriver)
    args = argparse.Namespace(
        command="compare", output=str(tmp_path), models=ROUTE["model"], telemetry="raw",
        control_language="numeric", instruction_style="damped", decision_layout="factored",
        url="fake://local", reference="unused", trials=2, stop_when_target_impossible=False,
        stop_on_first_error=True,
    )
    with pytest.raises(RuntimeError, match="first endpoint error"):
        await bench.remote_command(args)
    assert starts == [0]
    summary = json.loads((tmp_path / "summary.json").read_text())["models"][0]
    assert summary["trials"] == 1
    saved = json.loads((tmp_path / "typesafe--jev-1.14--seed-0.json").read_text())
    assert len(saved["requests"]) == 1 and not saved["requests"][0]["ok"]
