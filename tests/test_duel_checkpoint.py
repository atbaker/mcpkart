import copy
import json
import math

import pytest

from mcpkart.duel import KART_FIELDS, WORLD_FIELDS, DuelSimulation
from mcpkart.duel_runtime import DuelRuntime
from mcpkart.sim import ACTIONS


def restore(sim, **kwargs):
    config = sim.config()["parameters"].copy()
    config.pop("checkpoint", None)
    config.pop("episode", None)
    return DuelSimulation(**config, checkpoint=json.loads(json.dumps(sim.checkpoint())), **kwargs)


def move(k, x, y):
    k.x, k.y = x, y
    k.s, k.offset, _ = k.track.project(x, y)
    k.departure_s = k.s


def test_full_precision_checkpoint_continuation_and_default_config():
    sim = DuelSimulation(seed=17)
    old_config = copy.deepcopy(sim.config())
    controls = list(ACTIONS)
    for tick in range(180):
        if tick % 12 == 0:
            for i, r in enumerate(("red", "blue")):
                sim.set_control(r, controls[(tick // 12 + i) % len(controls)])
        sim.step()
    assert sim.config() == old_config
    clone = restore(sim)
    assert sim.checkpoint() == clone.checkpoint()
    assert DuelSimulation.from_config(clone.config()).checkpoint() == clone.checkpoint()
    # Catch future state fields being omitted from checkpoint serialization.
    static_kart = {"radius", "seed", "laps", "reset_after_s", "track", "handling", "start_pose"}
    assert set(vars(sim.karts["red"])) == set(KART_FIELDS) | static_kart
    static_world = {
        "grid", "seed", "radius", "restitution", "contact", "phase_s", "karts", "track",
        "_checkpoint_input", "episode", "_episode_baseline", "racer_ids",
    }
    assert set(vars(sim)) == set(WORLD_FIELDS) | static_world
    for tick in range(240):
        if tick % 13 == 0:
            for i, r in enumerate(("red", "blue")):
                action = controls[(tick // 13 + 2 * i) % len(controls)]
                sim.set_control(r, action)
                clone.set_control(r, action)
        sim.step()
        clone.step()
        assert sim.checkpoint() == clone.checkpoint()


def test_checkpoint_preserves_rescue_phase_and_contact_memory():
    sim = DuelSimulation()
    red = sim.karts["red"]
    move(red, 0, -44)
    for _ in range(181):
        sim.step()
    assert len(red.reset_events) == 1 and sim.phase_until["red"] > sim.tick
    clone = restore(sim)
    assert clone.checkpoint() == sim.checkpoint()
    for _ in range(80):
        sim.step()
        clone.step()
        assert clone.checkpoint() == sim.checkpoint()


def test_checkpoint_config_hash_accepts_equal_json_numeric_forms():
    sim = DuelSimulation(reset_after_s=3)
    restored = DuelSimulation(reset_after_s=3.0, checkpoint=sim.checkpoint())
    assert restored.checkpoint() == sim.checkpoint()


def test_checkpoint_preserves_stopped_finisher_with_older_clock():
    sim = DuelSimulation()
    k = sim.karts["blue"]
    x, y, h, _ = sim.track.checkpoints[0]
    move(k, x - .01 * math.cos(h), y - .01 * math.sin(h))
    k.heading, k.vx, k.vy = h, math.cos(h), math.sin(h)
    k.next_checkpoint, k.checkpoints_passed, k.laps_completed = 0, 119, 2
    sim.step()
    for _ in range(10):
        sim.step()
    assert k.finished and k.tick < sim.tick
    clone = restore(sim)
    for _ in range(20):
        sim.step()
        clone.step()
        assert sim.checkpoint() == clone.checkpoint()


@pytest.mark.parametrize("fault", ["missing", "bool_clock", "nan_velocity", "config", "unknown_input"])
def test_malformed_checkpoint_is_rejected(fault):
    sim = DuelSimulation()
    cp = sim.checkpoint()
    if fault == "missing":
        del cp["karts"]["red"]["steering"]
    elif fault == "bool_clock":
        cp["world"]["tick"] = True
    elif fault == "nan_velocity":
        cp["karts"]["red"]["vx"] = float("nan")
    elif fault == "config":
        cp["base_config_sha256"] = "wrong"
    else:
        cp["karts"]["red"]["action_id"] = "autopilot"
    with pytest.raises(ValueError):
        DuelSimulation(checkpoint=cp)


async def test_checkpoint_clock_is_relative_and_keeps_world_time():
    sim = DuelSimulation()
    for _ in range(90):
        sim.step()
    runtime = DuelRuntime()
    start = runtime.start(deadline=.08, race_setup={"checkpoint": sim.checkpoint()})
    try:
        assert start["drivers"]["red"]["observation"]["tick"] == 90
        import asyncio
        await asyncio.sleep(.13)
        result = runtime.result()
        assert result["reason"] == "deadline"
        assert result["samples"][0]["tick"] == 90
        assert 4 <= result["timing"]["physics_steps"] <= 6
        assert result["summary"]["elapsed"] > 1.5
        assert result["timing"]["simulation_elapsed"] < .12
        assert result["episode_origin"]["time_s"] == sim.elapsed
    finally:
        await runtime.close()


async def test_episode_stops_at_credit_without_claiming_race_finish():
    sim = DuelSimulation()
    k = sim.karts["red"]
    x, y, h, _ = sim.track.checkpoints[1]
    move(k, x - .01 * math.cos(h), y - .01 * math.sin(h))
    k.heading, k.vx, k.vy = h, math.cos(h), math.sin(h)
    runtime = DuelRuntime()
    runtime.start(race_setup={"checkpoint": sim.checkpoint(), "episode": {"racer_id": "red", "gate_credits": 1}})
    try:
        import asyncio
        await asyncio.sleep(.08)
        result = runtime.result()
        assert result["reason"] == "episode_credited" and not result["summary"]["finished"]
        assert result["episode"]["outcome"] == "credited"
        assert result["summary"]["racers"]["red"]["checkpoints_passed"] == 1
    finally:
        await runtime.close()
