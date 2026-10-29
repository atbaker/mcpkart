import asyncio
import math
import time

import pytest

from mcpkart.duel import RACERS, DuelSimulation
from mcpkart.duel_process import ProcessDuelRuntime
from mcpkart.duel_runtime import DuelRuntime
from mcpkart.sim import DT


def collide(*, ghost=False, glancing=False):
    sim = DuelSimulation(contact="ghost" if ghost else "solid")
    a, b = (sim.karts[r] for r in RACERS)
    a.x, a.y, a.vx, a.vy = 0.0, -30.0, 8.0, 0.0
    b.x, b.y, b.vx, b.vy = 2.05, -29.3 if glancing else -30.0, 0.0, 0.0
    old = {r: (k.x, k.y) for r, k in sim.karts.items()}
    a.x += a.vx * DT
    sim._contact(old)
    return sim, a, b


def test_rear_contact_conserves_momentum_and_dissipates_energy():
    sim, a, b = collide()
    assert len(sim.contacts) == sim.contact_count == 1
    assert a.vx == pytest.approx(3.4)
    assert b.vx == pytest.approx(4.6)
    assert a.vx + b.vx == pytest.approx(8.0)
    assert a.speed**2 + b.speed**2 < 64
    assert math.dist((a.x, a.y), (b.x, b.y)) >= 2 - 1e-9
    assert 0 < sim.contacts[0]["toi_fraction"] < 1


def test_glancing_contact_deflects_both_and_ghost_does_not():
    sim, a, b = collide(glancing=True)
    # A closer start is required for the offset contact in this one tick.
    a.x, a.y, b.x, b.y = 0.0, -30.0, 1.9, -29.3
    old = {"red": (a.x, a.y), "blue": (b.x, b.y)}
    a.x += a.vx * DT
    sim._contact(old)
    assert a.vy < 0 < b.vy
    assert a.vy + b.vy == pytest.approx(0.0)
    ghost, a, b = collide(ghost=True)
    assert not ghost.contacts
    assert (a.vx, b.vx) == (8.0, 0.0)


def test_swept_contact_catches_crossing_and_speed_cap():
    sim = DuelSimulation()
    a, b = (sim.karts[r] for r in RACERS)
    old = {"red": (0.0, -30.0), "blue": (3.0, -30.0)}
    a.x, a.y, b.x, b.y = 4.0, -30.0, -1.0, -30.0
    a.vx, b.vx = 12.0, -12.0
    a.vy = b.vy = 0.0
    sim._contact(old)
    assert len(sim.contacts) == 1
    assert a.x < b.x
    assert max(a.speed, b.speed) <= 12


def test_body_margin_gate_width_and_progress_metric():
    sim = DuelSimulation()
    k = sim.karts["red"]
    assert k._road_half_width() == 11
    k.offset = 11.01
    assert not k.observation()["track"]["on_road"]
    gx, gy, heading, _ = sim.track.checkpoints[1]
    tx, ty = math.cos(heading), math.sin(heading)
    nx, ny = -ty, tx
    for lateral, expected in ((11.01, 0), (10.99, 1)):
        k.x, k.y = gx + tx * 0.1 + nx * lateral, gy + ty * 0.1 + ny * lateral
        k._check_progress(gx - tx * 0.1 + nx * lateral, gy - ty * 0.1 + ny * lateral)
        assert k.checkpoints_passed == expected
    segment = sim.track.length / 40
    k.s = segment + segment * 0.5
    assert sim.progress_m("red") == pytest.approx(segment * 1.5)


def test_simultaneous_finish_is_tie_and_ghosts_finished_karts():
    sim = DuelSimulation()
    gx, gy, heading, _ = sim.track.checkpoints[0]
    for i, k in enumerate(sim.karts.values()):
        offset = -2 if i == 0 else 2
        k.x, k.y = gx - 0.05, gy + offset
        k.heading = heading
        k.vx, k.vy = 6.0, 0.0
        k.next_checkpoint, k.checkpoints_passed, k.laps_completed = 0, 119, 2
        k.s, k.offset, _ = sim.track.project(k.x, k.y)
    sim.step()
    assert sim.finished
    assert sim.summary()["winner_ids"] == list(RACERS)
    assert sim.leader() is None
    assert all(sim.phased(r) and k.speed == 0 for r, k in sim.karts.items())
    tick = sim.tick
    sim.step()
    assert sim.tick == tick


def test_rescue_is_local_and_phased_until_separated():
    sim = DuelSimulation(reset_after_s=DT, phase_s=0)
    a, b = (sim.karts[r] for r in RACERS)
    a.y = -50
    a.s, a.offset, _ = sim.track.project(a.x, a.y)
    sim.step()
    assert a.last_reset_tick == 1 and b.last_reset_tick is None
    assert sim.phased("red")
    b.x, b.y = a.x, a.y
    b.s, b.offset, _ = sim.track.project(b.x, b.y)
    sim.step()
    assert sim.phased("red") and not sim.contacts
    b.y += 4
    b.s, b.offset, _ = sim.track.project(b.x, b.y)
    sim.step()
    assert not sim.phased("red")


def test_configuration_reconstructs_and_lane_swap_is_symmetric():
    sim = DuelSimulation()
    swapped = DuelSimulation(grid=list(reversed(sim.grid)))
    for tick in range(300):
        action = "hard_left_accelerate" if tick < 100 else "right_coast"
        sim.set_control("red", action)
        sim.set_control("blue", "straight_accelerate")
        swapped.set_control("blue", action)
        swapped.set_control("red", "straight_accelerate")
        sim.step()
        swapped.step()
        assert sim.karts["red"].observation() == swapped.karts["blue"].observation()
        assert sim.karts["blue"].observation() == swapped.karts["red"].observation()
    assert DuelSimulation.from_config(sim.config()).config() == sim.config()


async def run_concurrent(runtime):
    initial = runtime.start(deadline=2)
    if asyncio.iscoroutine(initial):
        initial = await initial
    race_id = initial["race_id"]

    async def drive(rid, action, token=None, tick=0, seq=0):
        return await runtime.drive(
            race_id, rid, token or initial["drivers"][rid]["driver_token"], action, tick, seq
        )

    with pytest.raises(ValueError, match="capability"):
        await drive("red", "straight_accelerate", initial["drivers"]["blue"]["driver_token"])
    a, b = await asyncio.gather(drive("red", "straight_accelerate"), drive("blue", "hard_left_accelerate"))
    assert a["applied"] and b["applied"]
    assert a["applied_tick"] == b["applied_tick"]
    with pytest.raises(ValueError, match="Duplicate"):
        await drive("red", "straight_coast")
    with pytest.raises(ValueError, match="capability"):
        result = runtime.finish(race_id, owner_token="wrong")
        if asyncio.iscoroutine(result):
            await result
    await asyncio.sleep(0.08)
    observed = runtime.observe(race_id)
    if asyncio.iscoroutine(observed):
        observed = await observed
    assert observed["status"] == "running"
    assert observed["racers"]["red"]["control"] == "straight_accelerate"
    assert observed["racers"]["blue"]["control"] == "hard_left_accelerate"
    result = runtime.finish(race_id, owner_token=initial["owner_token"])
    if asyncio.iscoroutine(result):
        result = await result
    assert "driver_token" not in str(result) and "owner_token" not in str(result)
    replay = DuelSimulation.from_config(result["config"])
    commands = {}
    for c in result["commands"]:
        commands.setdefault(c["applied_tick"], []).append(c)
    for sample in result["samples"]:
        if sample["tick"]:
            for c in commands.get(sample["tick"], []):
                replay.set_control(c["racer_id"], c["action_id"])
            replay.step()
        assert sample["racers"] == replay.state()["racers"]
    return result


@pytest.mark.parametrize("runtime_class", [DuelRuntime, ProcessDuelRuntime])
async def test_independent_capabilities_concurrency_and_exact_replay(runtime_class):
    runtime = runtime_class()
    try:
        result = await run_concurrent(runtime)
        if runtime_class is ProcessDuelRuntime:
            assert result["worker_memory"]["cyclic_gc_enabled"] is False
            assert result["worker_memory"]["maximum_duel_duration_s"] == 600
            memory = result["worker_memory"]
            assert memory["resource_peak_rss_kib"] > 0
            if memory["current_rss_kib"] is not None:
                assert 0 < memory["current_rss_kib"] <= memory["process_peak_rss_kib"]
            assert memory["measured_before_recording_transfer"]
            assert result["process_provenance"]["worker_module"] == "mcpkart.duel_worker"
            assert result["process_provenance"]["child_web_modules_loaded"] == []
            assert runtime._session is None
    finally:
        await runtime.close()


async def test_stale_rescue_reply_affects_only_its_racer():
    runtime = DuelRuntime()
    try:
        initial = runtime.start(deadline=2)
        await asyncio.sleep(0.04)
        runtime.current.sim.karts["red"].last_reset_tick = 1

        async def apply(rid):
            return await runtime.drive(
                initial["race_id"], rid, initial["drivers"][rid]["driver_token"], "straight_accelerate", 0, 0
            )

        red, blue = await asyncio.gather(apply("red"), apply("blue"))
        assert not red["applied"] and red["reason"] == "observation_before_rescue"
        assert blue["applied"]
    finally:
        await runtime.close()


async def test_child_duel_clock_survives_parent_block():
    runtime = ProcessDuelRuntime()
    try:
        initial = await runtime.start(deadline=2)
        before = await runtime.observe(initial["race_id"])
        started = time.monotonic_ns()
        time.sleep(0.25)  # noqa: ASYNC251 -- deliberately block only the parent.
        ended = time.monotonic_ns()
        after = await runtime.observe(initial["race_id"])
        assert after["tick"] - before["tick"] >= 12
        result = await runtime.finish(initial["race_id"], owner_token=initial["owner_token"])
        assert sum(started < s["wall_ns"] < ended for s in result["samples"]) >= 10
    finally:
        await runtime.close()


async def test_failed_finish_closes_worker_and_allows_a_new_duel(monkeypatch):
    runtime = ProcessDuelRuntime()
    try:
        initial = await runtime.start(deadline=2)
        session = runtime._session
        original_rpc = runtime._rpc

        async def failed_finish(method, *args, **kwargs):
            if method == "finish":
                raise RuntimeError("simulated finish transport failure")
            return await original_rpc(method, *args, **kwargs)

        monkeypatch.setattr(runtime, "_rpc", failed_finish)
        with pytest.raises(RuntimeError, match="simulated finish"):
            await runtime.finish(initial["race_id"], owner_token=initial["owner_token"])
        assert runtime._session is None and not session.process.is_alive()
        assert runtime.current.status != "running"
        assert runtime.state()["status"] == "failed"
        monkeypatch.setattr(runtime, "_rpc", original_rpc)
        replacement = await runtime.start(deadline=2)
        assert replacement["race_id"] != initial["race_id"]
        await runtime.finish(replacement["race_id"], owner_token=replacement["owner_token"])
    finally:
        await runtime.close()


async def test_disconnected_racer_keeps_accepted_input_and_old_tokens_cannot_reenter():
    runtime = DuelRuntime()
    try:
        initial = runtime.start(deadline=2)
        driver = initial["drivers"]["red"]
        task = asyncio.create_task(
            runtime.drive(initial["race_id"], "red", driver["driver_token"], "straight_accelerate", 0, 0)
        )
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0.04)
        assert runtime.observe(initial["race_id"], "red")["control"] == "straight_accelerate"
        assert runtime.observe(initial["race_id"], "blue")["control"] == "straight_coast"
        assert len(runtime.current.commands) == 1
        runtime.finish(initial["race_id"], owner_token=initial["owner_token"])
        replacement = runtime.start(deadline=2)
        with pytest.raises(ValueError, match="Stale"):
            await runtime.drive(
                initial["race_id"], "red", driver["driver_token"], "hard_left_accelerate", 0, 1
            )
        with pytest.raises(ValueError, match="capability"):
            await runtime.drive(
                replacement["race_id"], "red", driver["driver_token"], "hard_left_accelerate", 0, 0
            )
        assert runtime.observe(replacement["race_id"], "red")["control"] == "straight_coast"
    finally:
        await runtime.close()


async def test_physics_failure_releases_both_pending_acknowledgements(monkeypatch):
    runtime = DuelRuntime()
    try:
        initial = runtime.start(deadline=2)

        def fail():
            raise RuntimeError("injected physics failure")

        monkeypatch.setattr(runtime.current.sim, "step", fail)

        async def submit(rid):
            return await runtime.drive(
                initial["race_id"], rid, initial["drivers"][rid]["driver_token"], "straight_accelerate", 0, 0
            )

        acks = await asyncio.wait_for(asyncio.gather(*(submit(r) for r in RACERS)), 1)
        assert all(not ack["applied"] and ack["reason"] == "runtime_ended_before_ack" for ack in acks)
        assert runtime.current.status == "failed" and not runtime.current.pending
    finally:
        await runtime.close()


async def test_one_finisher_does_not_stop_the_other_driver():
    runtime = DuelRuntime()
    try:
        initial = runtime.start(deadline=2)
        sim = runtime.current.sim
        red = sim.karts["red"]
        gx, gy, heading, _ = sim.track.checkpoints[0]
        red.x, red.y, red.heading = gx - 0.05, gy - 2, heading
        red.vx, red.vy = 6.0, 0.0
        red.s, red.offset, _ = sim.track.project(red.x, red.y)
        red.next_checkpoint, red.checkpoints_passed, red.laps_completed = 0, 119, 2

        async def drive(rid, seq, tick):
            return await runtime.drive(
                initial["race_id"],
                rid,
                initial["drivers"][rid]["driver_token"],
                "straight_accelerate",
                tick,
                seq,
            )

        first = await asyncio.gather(drive("red", 0, 0), drive("blue", 0, 0))
        assert first[0]["observation"]["finished"] and not first[1]["observation"]["finished"]
        red_finish = sim.finish_ticks["red"]
        assert runtime.current.status == "running"
        red_ack, blue_ack = await asyncio.gather(drive("red", 1, 1), drive("blue", 1, 1))
        assert not red_ack["applied"] and red_ack["reason"] == "racer_finished"
        assert blue_ack["applied"] and sim.tick > red_finish
        assert sim.summary()["winner_ids"] == ["red"]
    finally:
        await runtime.close()


def test_overlap_separation_does_not_credit_a_gate():
    sim = DuelSimulation()
    gx, gy, heading, _ = sim.track.checkpoints[1]
    for rid, before in [("red", 0.5), ("blue", 0.01)]:
        k = sim.karts[rid]
        k.x, k.y, k.heading = gx - before, gy, heading
        k.s, k.offset, _ = sim.track.project(k.x, k.y)
    sim.step()
    assert sim.karts["blue"].x > gx
    assert all(k.checkpoints_passed == 0 for k in sim.karts.values())
    assert sim.contacts[0]["separation_correction_m"] > 0


def test_opponent_measurements_rotate_with_the_current_nose():
    sim = DuelSimulation()
    red, blue = (sim.karts[r] for r in RACERS)
    red.x, red.y, red.heading, red.vx, red.vy = 0.0, 0.0, math.pi / 2, 1.0, 2.0
    blue.x, blue.y, blue.heading, blue.vx, blue.vy = -3.0, 4.0, 0.0, -2.0, 8.0
    for k in sim.karts.values():
        k.s, k.offset, _ = sim.track.project(k.x, k.y)
    other = sim.observation("red")["competition"]["opponent"]
    assert (other["ego_x_m"], other["ego_y_m"]) == (4.0, 3.0)
    assert (other["relative_forward_velocity_m_s"], other["relative_left_velocity_m_s"]) == (6.0, 3.0)
    assert other["surface_gap_m"] == 3.0
    assert other["heading_relative_rad"] == pytest.approx(-math.pi / 2, abs=1e-5)


def test_glancing_impulse_obeys_declared_speed_cap():
    sim = DuelSimulation()
    a, b = (sim.karts[r] for r in RACERS)
    old = {"red": (0.0, -30.0), "blue": (2.05, -30.0)}
    a.vx, a.vy, b.vx, b.vy = 12.0, 0.0, 0.0, 12.0
    a.x, a.y, b.x, b.y = 0.2, -30.0, 2.05, -29.8
    sim._contact(old)
    assert sim.contacts
    assert b.speed == pytest.approx(12)
    assert max(a.speed, b.speed) <= 12 + 1e-12
    assert a.speed**2 + b.speed**2 <= 288
