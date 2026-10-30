import asyncio
import copy
import json

import pytest
from fastmcp import Client

from mcpkart.bench import tool
from mcpkart.demo_broker import DemoBroker, Receipts, UnresolvedStep
from mcpkart.duel import RACERS, TRIO_RACERS, DuelSimulation
from mcpkart.duel_decisions import DuelDecisionClient, duel_facts
from mcpkart.duel_web import create_app
from mcpkart.question_context import PromptDomainError


def test_trio_ghosts_cross_without_contact_and_reconstruct_exactly():
    sim = DuelSimulation(racer_ids=TRIO_RACERS, contact="ghost")
    assert tuple(sim.karts) == TRIO_RACERS
    for rid in TRIO_RACERS:
        sim.set_control(rid, "straight_accelerate")
    for _ in range(90):
        sim.step()
    clone = DuelSimulation.from_config({**sim.config(), "parameters": {
        **sim.config()["parameters"], "checkpoint": sim.checkpoint(),
    }})
    for _ in range(90):
        sim.step()
        clone.step()
        assert sim.state() == clone.state()
    assert sim.contact_count == 0
    assert sim.config()["contact_solver"] == "none_ghost"
    with pytest.raises(ValueError, match="ghost"):
        DuelSimulation(racer_ids=TRIO_RACERS)
    with pytest.raises(ValueError, match="three grid"):
        DuelSimulation(racer_ids=TRIO_RACERS, contact="ghost", grid=sim.grid[:2])
    assert DuelSimulation().config()["racer_ids"] == list(RACERS)


def test_every_trio_prompt_has_two_valid_opponents_and_ghost_rules():
    sim = DuelSimulation(racer_ids=TRIO_RACERS, contact="ghost")
    for rid in TRIO_RACERS:
        raw = sim.observation(rid)
        facts = duel_facts(raw, sim.config(), rid)
        assert [o["racer_id"] for o in facts["wheel_facts"]["competition"]["opponents"]] == [
            r for r in TRIO_RACERS if r != rid
        ]
        api = DuelDecisionClient(facts=facts, handling=sim.config()["handling"], budget=None,
                                 http_client=object(), api_key="mock")
        assert "three-kart" in api.questions["wheel"]["instructions"]["rules"]
        assert "do not collide" in api.questions["pedal"]["instructions"]["rules"]
        bad = copy.deepcopy(raw)
        bad["competition"]["opponents"][1]["ego_x_m"] = float("nan")
        with pytest.raises(PromptDomainError, match="Nonfinite"):
            duel_facts(bad, sim.config(), rid)
        bad = copy.deepcopy(raw)
        bad["competition"]["opponents"].reverse()
        with pytest.raises(PromptDomainError, match="identity"):
            duel_facts(bad, sim.config(), rid)


async def test_three_actual_mcp_capabilities_controls_and_private_replay(tmp_path):
    app = create_app(trio=True, replay_root=tmp_path)
    runtime = app.state.race_runtime
    try:
        async with Client(app.state.mcp_server) as mcp:
            assert (await tool(mcp, "runtime_info"))["mode"] == "trio"
            start = await tool(mcp, "start_duel", {"deadline": 3})
            assert set(start["drivers"]) == set(TRIO_RACERS)
            async def drive(rid, action):
                return await tool(mcp, "drive_duel", {
                    "race_id": start["race_id"], "racer_id": rid,
                    "driver_token": start["drivers"][rid]["driver_token"],
                    "action_id": action, "observation_tick": 0, "command_seq": 0,
                })
            replies = await asyncio.gather(*(drive(r, a) for r, a in zip(
                TRIO_RACERS, ("straight_accelerate", "left_coast", "right_brake"), strict=True,
            )))
            assert all(reply["applied"] for reply in replies)
            assert len({reply["applied_tick"] for reply in replies}) == 1
            race = await tool(mcp, "finish_duel", {
                "race_id": start["race_id"], "owner_token": start["owner_token"],
            })
            assert len(race["commands"]) == 3
            assert "driver_token" not in json.dumps(race)
            assert "owner_token" not in json.dumps(race)
    finally:
        await runtime.close()


def test_receipts_survive_reopen_and_never_repeat_unknown_dispatch(tmp_path):
    path = tmp_path / "receipts.sqlite3"
    journal = Receipts(path)
    journal.begin("mcpkart-race:red:0")
    journal.complete("mcpkart-race:red:0", {"done": False, "seq": 0})
    journal.begin("mcpkart-race:red:1")
    journal.close()
    reopened = Receipts(path)
    assert reopened.get("mcpkart-race:red:0") == {"done": False, "seq": 0}
    with pytest.raises(UnresolvedStep):
        reopened.get("mcpkart-race:red:1")
    reopened.close()


async def test_local_activity_reexecution_returns_same_broker_receipt_without_charge(tmp_path):
    app = create_app(trio=True, replay_root=tmp_path)
    runtime = app.state.race_runtime
    try:
        async with DemoBroker(url=app.state.mcp_server, output=tmp_path / "trial",
                              logical_id="mcpkart-replay-test", mock_delay=.01) as broker:
            await broker.start()
            results = await asyncio.gather(*(broker.step(r, 0) for r in TRIO_RACERS))
            for rid, result in zip(TRIO_RACERS, results, strict=True):
                query = json.loads((tmp_path / "trial" / rid / "query-00000.json").read_text())
                model_facts = query["facts"]
                assert result["model_saw"]["speed_m_s"] == model_facts["pedal_facts"]["kart"]["speed_m_s"]
                assert result["model_saw"]["road_preview_15m_bearing_deg_left_positive"] == model_facts["wheel_facts"]["road"]["preview_15m_bearing_deg"]
                assert result["model_saw"]["gates_passed"] == model_facts["pedal_facts"]["race"]["checkpoints_passed"]
                record = broker.samples[rid][0]
                assert result["model_chose"]["steering"] == record["component_choices"]["wheel"]
                assert result["model_chose"]["pedal"] == record["component_choices"]["pedal"]
                assert result["model_chose"]["held_input"] == record["action"]
                assert result["game_acknowledgement"]["applied"] == result["applied"]
                assert result["decision_number"] == 1 and len(json.dumps(result).encode()) < 2000
                for private in [broker.initial["owner_token"], *(d["driver_token"] for d in broker.initial["drivers"].values())]:
                    assert private not in json.dumps(result)
            before = broker.budget.summary()
            duplicate = await broker.step("green", 0)
            assert duplicate == results[2]
            assert broker.budget.summary() == before
            assert len(broker.samples["green"]) == 1
            receipt = await broker.finish()
            assert receipt["audit"]["passed"]
            assert receipt["audit"]["exact_queries"] == 3
    finally:
        await runtime.close()


def test_paid_demo_cannot_bypass_new_registration(tmp_path):
    with pytest.raises(ValueError, match="registration"):
        DemoBroker(url="unused", output=tmp_path, logical_id="mcpkart-paid", paid=True)


async def test_failed_reply_stops_other_controls_and_keeps_all_reservations(tmp_path):
    import httpx

    from mcpkart.demo_mock import free_choices

    def transport(rid):
        async def reply(request):
            packet = json.loads(request.content)
            if rid == "red":
                await asyncio.sleep(.05)
                return httpx.Response(503, json={"error": "injected failure"})
            await asyncio.sleep(.1)
            facts = {h + "_facts": packet["questions"][h]["instructions"]["current_facts"][h + "_facts"]
                     for h in ("wheel", "pedal")}
            wheel, pedal = free_choices(facts)
            return httpx.Response(200, json={"id": "mock-" + rid, "model": packet["model"] + "-mock",
                "provider": {"blue": "OpenAI", "green": "Prime Intellect"}[rid],
                "answers": {"wheel": {"type": "choice", "choice": wheel},
                            "pedal": {"type": "choice", "choice": pedal}},
                "usage": {"input_tokens": 0, "output_tokens": 0, "cost": 0}})
        return httpx.MockTransport(reply)

    app = create_app(trio=True, replay_root=tmp_path)
    try:
        async with DemoBroker(url=app.state.mcp_server, output=tmp_path / "trial",
                              logical_id="mcpkart-failed-reply", mock_delay=.01) as broker:
            # Install after prepare to avoid prewarming the intentionally failed route.
            for rid in TRIO_RACERS:
                broker.drivers[rid].http._transport = transport(rid)
            await broker.start()
            await asyncio.gather(*(broker.step(r, 0) for r in TRIO_RACERS), return_exceptions=True)
            receipt = await broker.finish()
            assert receipt["audit"] is None
            assert all(not s["applied"] for rows in broker.samples.values() for s in rows)
            budget = broker.journal.check()
            assert budget["uncertain_requests"] == 1 and not budget["pending"] and budget["requests"] == 3
            assert budget["charged_tokens"] == 16384 + 235929
            proof = json.loads((tmp_path / "trial/failure-audit.json").read_text())
            assert proof["passed"] and proof["exact_queries"] == 3
    finally:
        await app.state.race_runtime.close()


def test_trio_builds_own_telemetry_once_and_preserves_opponent_packets(monkeypatch):
    sim = DuelSimulation(racer_ids=TRIO_RACERS, contact="ghost")
    kart = sim.karts["red"]
    original = kart.observation
    calls = []

    def observe():
        calls.append(1)
        return original()

    monkeypatch.setattr(kart, "observation", observe)
    observation = sim.observation("red")
    assert len(calls) == 1
    for actual in observation["competition"]["opponents"]:
        expected = sim._observation_with_opponent("red", actual["racer_id"])["competition"]["opponent"]
        assert actual == expected


async def test_provider_dnf_stops_only_failed_racer_without_new_controls(tmp_path):
    import httpx

    from mcpkart.demo_mock import free_choices

    counts = dict.fromkeys(TRIO_RACERS, 0)

    def transport(rid):
        async def reply(request):
            counts[rid] += 1
            await asyncio.sleep(.02)
            packet = json.loads(request.content)
            if rid == "green" and counts[rid] == 2:
                return httpx.Response(429, json={"error": {"message": "injected provider concurrency limit"}})
            facts = {h + "_facts": packet["questions"][h]["instructions"]["current_facts"][h + "_facts"]
                     for h in ("wheel", "pedal")}
            wheel, pedal = free_choices(facts)
            return httpx.Response(200, json={"id": f"mock-{rid}-{counts[rid]}",
                "model": packet["model"] + "-mock",
                "provider": {"red": "TypeSafe", "blue": "OpenAI", "green": "Prime Intellect"}[rid],
                "answers": {"wheel": {"type": "choice", "choice": wheel},
                            "pedal": {"type": "choice", "choice": pedal}},
                "usage": {"input_tokens": 0, "output_tokens": 0, "cost": 0}})
        return httpx.MockTransport(reply)

    app = create_app(trio=True, replay_root=tmp_path)
    try:
        async with DemoBroker(url=app.state.mcp_server, output=tmp_path / "trial",
                              logical_id="mcpkart-provider-dnf", deadline=.8,
                              retire_provider_errors=True) as broker:
            for rid in TRIO_RACERS:
                broker.drivers[rid].http._transport = transport(rid)
            await broker.start()

            async def drive(rid):
                for seq in range(100):
                    if (await broker.step(rid, seq))["done"]:
                        return
                pytest.fail("Driver did not stop")

            await asyncio.gather(*(drive(r) for r in TRIO_RACERS))
            assert counts["green"] == 2 and counts["red"] > 2 and counts["blue"] > 2
            assert (await broker.step("green", 1))["retired"]  # Replayed marker never dispatches again.
            retired = await broker.step("green", 1)
            assert retired["model_chose"] is None and not retired["model_response"]["valid_decision"]
            assert retired["game_acknowledgement"] == {"applied": False, "reason": "HTTP 429"}
            assert "no replacement control" in retired["summary"]
            assert counts["green"] == 2
            receipt = await broker.finish()
            assert receipt["audit"]["provider_dnfs"] == ["green"]
            race = json.loads((tmp_path / "trial/race.json").read_text())
            green = [c for c in race["commands"] if c["racer_id"] == "green"]
            assert len(green) == 1  # The rejected reply supplies no replacement control.
            assert race["driver_metrics"]["green"]["retirement_reason"] == "HTTP 429"
            assert broker.journal.check()["uncertain_requests"] == 1
    finally:
        await app.state.race_runtime.close()


async def test_trio_publication_is_bounded_and_matches_exact_latest_sample(monkeypatch):
    from mcpkart.duel_runtime import DuelRuntime
    runtime = DuelRuntime(trio=True)
    try:
        runtime.start(deadline=3)
        race = runtime.current
        original_timing = runtime._timing
        monkeypatch.setattr(runtime, "_timing", lambda *_args, **_kwargs: pytest.fail("Live publication must not scan timing history"))
        for _ in range(750):
            race.sim.step()
            runtime._sample(race, 0, 0)
        state = runtime.state()
        assert state["observation"] == race.sim.state()
        assert state["track"] == race.sim.track.as_dict()
        for rid in TRIO_RACERS:
            expected = [[s["racers"][rid]["kart"]["x"], s["racers"][rid]["kart"]["y"]]
                        for s in race.samples[-600::3]
                        if s["tick"] >= (race.sim.karts[rid].last_reset_tick or 0)]
            assert state["trail"][rid] == expected
            assert len(race.live_trails[rid]) == 600
        assert state["timing"]["metrics_complete"] is False
        assert state["timing"]["infrastructure_valid"] is None
        monkeypatch.setattr(runtime, "_timing", original_timing)
    finally:
        await runtime.close()
