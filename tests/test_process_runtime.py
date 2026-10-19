import asyncio
import os
import time
from threading import Event

import pytest

from mcpkart.process_runtime import ProcessRaceRuntime
from mcpkart.runtime import ASYNCIO_CLOCK_MODE, NATIVE_CLOCK_MODE
from mcpkart.sim import Simulation


@pytest.mark.asyncio
@pytest.mark.parametrize("native_sleeper", [False, True])
async def test_child_clock_survives_parent_loop_block_and_acknowledges_real_application(native_sleeper):
    # Omitting the flag must retain the old asyncio process default.
    runtime = ProcessRaceRuntime(native_sleeper=True) if native_sleeper else ProcessRaceRuntime()
    clock_mode = NATIVE_CLOCK_MODE if native_sleeper else ASYNCIO_CLOCK_MODE
    assert runtime.runtime_info()["clock_mode"] == clock_mode
    try:
        initial = await runtime.start(deadline=3, label="Isolation control")
        assert ("--native-sleeper" in runtime._session.process.arguments) == native_sleeper
        assert runtime._session.clock_mode == clock_mode
        submitted_ns = time.monotonic_ns()
        ack = await runtime.drive(initial["race_id"], "straight_accelerate", initial["tick"], 0)
        assert ack["applied"]
        assert ack["applied_tick"] > initial["tick"]
        assert submitted_ns <= ack["queued_ns"] <= ack["applied_ns"] <= ack["observation"]["observed_ns"]
        before = await runtime.observe()
        block_started_ns = time.monotonic_ns()
        time.sleep(.25)  # noqa: ASYNC251 — deliberately block the parent, never the child.
        block_ended_ns = time.monotonic_ns()
        after = await runtime.observe()
        assert after["tick"]-before["tick"] >= 12
        assert after["time"]-before["time"] >= .2
        assert after["control"] == "straight_accelerate"
        assert after["kart"]["speed"] > before["kart"]["speed"]
        with pytest.raises(ValueError, match="Stop the race"):
            await runtime.result()
        state = runtime.state()
        assert state["snapshot_age_ms"] >= 0
        assert "samples" not in state and "commands" not in state
        result = await runtime.finish(reason="test_finished")
        assert result["runtime_info"]["backend"] == "process"
        assert result["runtime_info"]["clock_mode"] == result["timing"]["clock_mode"] == clock_mode
        provenance = result["process_provenance"]
        assert provenance["child_pid"] != os.getpid()
        assert result["runtime_info"]["process_pid"] == os.getpid()
        assert provenance["worker_module"] == "mcpkart.physics_worker"
        assert provenance["child_web_modules_loaded"] == []
        assert provenance["child_clock_mode"] == clock_mode
        assert provenance["worker_ready_ns"] <= provenance["clock_started_ns"]
        if native_sleeper:
            assert result["timing"]["pacing"]["native_sleeper_ready_ns"] <= provenance["clock_started_ns"]
        else:
            assert result["timing"]["pacing"]["native_sleeper_ready_ns"] is None
        assert result["timing"]["pacing"]["native_sleeper_thread_alive"] is False
        assert result["commands"][0]["applied_ns"] == ack["applied_ns"]
        assert sum(block_started_ns < sample["wall_ns"] < block_ended_ns for sample in result["samples"]) >= 10
        # Validate the recorded applied-tick contract by reproducing every pose,
        # rather than merely checking that an acknowledgement carried a value.
        sim = Simulation(seed=result["seed"], laps=result["config"]["laps"],
                         reset_after_s=result["config"]["rescue"]["after_s"])
        commands = {command["applied_tick"]: command["action_id"] for command in result["commands"]}
        for sample in result["samples"]:
            if sample["tick"]:
                if sample["tick"] in commands:
                    sim.set_control(commands[sample["tick"]])
                sim.step()
            assert sim.observation()["kart"] == sample["kart"]
        assert runtime._session is None
        late = await runtime.drive(initial["race_id"], "hard_left_accelerate", initial["tick"], 1)
        assert late["applied"] is False
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_worker_clock_identity_mismatch_is_rejected_before_a_race_starts(monkeypatch):
    runtime = ProcessRaceRuntime()
    message = runtime._message
    sessions = []

    def mismatched_ready(session, value):
        if value["type"] == "ready":
            sessions.append(session)
            value = {**value, "clock_mode": NATIVE_CLOCK_MODE}
        message(session, value)

    monkeypatch.setattr(runtime, "_message", mismatched_ready)
    with pytest.raises(RuntimeError, match="Worker clock mode"):
        await runtime.start(deadline=2)
    assert runtime.current is None and runtime._session is None
    assert len(sessions) == 1 and sessions[0].closed
    assert not sessions[0].process.is_alive()
    await runtime.close()


@pytest.mark.asyncio
async def test_rescue_and_sequence_guards_are_enforced_inside_worker():
    runtime = ProcessRaceRuntime()
    try:
        initial = await runtime.start(deadline=4, reset_after_s=.05)
        await runtime.drive(initial["race_id"], "hard_left_accelerate", initial["tick"], 0)
        deadline = time.monotonic()+3
        while time.monotonic() < deadline:
            observed = await runtime.observe()
            if observed["rescue"]["count"]:
                break
            await asyncio.sleep(.05)
        assert observed["rescue"]["count"] > 0
        stale = await runtime.drive(initial["race_id"], "hard_right_accelerate", initial["tick"], 1)
        assert not stale["applied"]
        assert stale["reason"] == "observation_before_rescue"
        fresh = await runtime.drive(initial["race_id"], "straight_accelerate", stale["observation"]["tick"], 1)
        assert fresh["applied"]
        with pytest.raises(ValueError, match="out-of-order"):
            await runtime.drive(initial["race_id"], "straight_brake", fresh["observation"]["tick"], 1)
        result = await runtime.finish()
        assert result["reset_events"] and result["rejected_commands"]
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_ended_worker_is_collected_and_old_race_cannot_affect_next_worker():
    runtime = ProcessRaceRuntime()
    try:
        old = await runtime.start(deadline=.05)
        old_session = runtime._session
        await asyncio.sleep(.1)
        ended = await runtime.observe()
        assert ended["status"] != "running"
        first = await runtime.result()
        assert first["reason"] == "deadline"
        assert runtime.state()["reason"] == "deadline"
        assert not old_session.process.is_alive()
        current = await runtime.start(seed=1, deadline=2)
        with pytest.raises(ValueError, match="Stale race_id"):
            await runtime.drive(old["race_id"], "straight_accelerate", 0, 0)
        # An already-queued callback from the previous worker is ignored even
        # if its old snapshot is assigned an artificially later timestamp.
        old_session.latest = {"state": {"race_id": old["race_id"], "status": "running"},
                              "captured_ns": time.monotonic_ns()+1_000_000_000}
        runtime._consume_snapshot(old_session)
        assert runtime.current.race_id == current["race_id"]
        second = await runtime.finish()
        assert first["process_provenance"]["child_pid"] != second["process_provenance"]["child_pid"]
    finally:
        await runtime.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["finish", "result"])
@pytest.mark.parametrize("pause_phase", ["before_cache", "before_cleanup"])
async def test_old_collection_cannot_cache_over_or_close_replacement_worker(monkeypatch, method, pause_phase):
    runtime = ProcessRaceRuntime()
    paused, release = asyncio.Event(), asyncio.Event()
    collecting = None
    original_rpc, original_shutdown = runtime._rpc, runtime._shutdown

    async def delayed_rpc(name, arguments=None, *, session=None):
        value = await original_rpc(name, arguments, session=session)
        if name == method and asyncio.current_task() is collecting and pause_phase == "before_cache":
            paused.set()
            await release.wait()
        return value

    async def delayed_shutdown(*, session):
        if asyncio.current_task() is collecting and pause_phase == "before_cleanup":
            paused.set()
            await release.wait()
        await original_shutdown(session=session)

    monkeypatch.setattr(runtime, "_rpc", delayed_rpc)
    monkeypatch.setattr(runtime, "_shutdown", delayed_shutdown)
    try:
        old = await runtime.start(deadline=.04 if method == "result" else 2)
        old_session = runtime._session
        runtime.record_timing_span("old_http", time.monotonic_ns(), time.process_time_ns())
        if method == "result":
            await asyncio.sleep(.08)
            assert (await runtime.observe())["status"] != "running"
        collecting = asyncio.create_task(runtime.finish(old["race_id"]) if method == "finish" else runtime.result())
        await asyncio.wait_for(paused.wait(), 2)

        # start() joins the old worker while its collector is suspended. That
        # collector may resume either before caching its result or at cleanup.
        new = await runtime.start(seed=1, deadline=2)
        new_session = runtime._session
        runtime.record_timing_span("new_http", time.monotonic_ns(), time.process_time_ns())
        release.set()
        old_result = await asyncio.wait_for(collecting, 2)
        assert old_result["race_id"] == old["race_id"]
        assert set(old_result["timing"]["parent_http_spans"]) == {"old_http"}
        assert old_session.closed and not old_session.process.is_alive()
        assert runtime._result is None
        assert runtime._session is new_session and new_session.process.is_alive()
        assert runtime.current.race_id == new["race_id"] and runtime.current.status == "running"
        observed = await runtime.observe(new["race_id"])
        ack = await runtime.drive(new["race_id"], "straight_accelerate", observed["tick"], 0)
        assert ack["applied"] and ack["observation"]["race_id"] == new["race_id"]
        new_result = await runtime.finish(new["race_id"])
        assert set(new_result["timing"]["parent_http_spans"]) == {"new_http"}
    finally:
        release.set()
        if collecting is not None:
            await asyncio.gather(collecting, return_exceptions=True)
        await runtime.close()


@pytest.mark.asyncio
async def test_old_race_commands_cannot_target_a_worker_being_admitted(monkeypatch):
    runtime = ProcessRaceRuntime()
    spawned, release = asyncio.Event(), asyncio.Event()
    starting = None
    original_spawn = runtime._spawn

    async def paused_spawn():
        session = await original_spawn()
        spawned.set()
        await release.wait()
        return session

    try:
        old = await runtime.start(deadline=2)
        await runtime.finish(old["race_id"])
        monkeypatch.setattr(runtime, "_spawn", paused_spawn)
        starting = asyncio.create_task(runtime.start(seed=1, deadline=2))
        await asyncio.wait_for(spawned.wait(), 2)
        session = runtime._session
        for operation in (runtime.observe(old["race_id"]),
                          runtime.drive(old["race_id"], "straight_accelerate", 0, 0),
                          runtime.finish(old["race_id"]), runtime.result()):
            with pytest.raises(ValueError, match="being admitted"):
                await operation
        assert session.process.is_alive() and not session.closing
        release.set()
        new = await starting
        ack = await runtime.drive(new["race_id"], "straight_accelerate", new["tick"], 0)
        assert ack["applied"]
    finally:
        release.set()
        if starting is not None:
            await asyncio.gather(starting, return_exceptions=True)
        await runtime.close()


@pytest.mark.asyncio
async def test_worker_death_fails_pending_command_and_does_not_restart():
    runtime = ProcessRaceRuntime()
    try:
        initial = await runtime.start(deadline=2)
        session = runtime._session
        pending = asyncio.create_task(runtime.drive(initial["race_id"], "straight_accelerate", initial["tick"], 0))
        await asyncio.sleep(0)
        session.process.terminate()
        with pytest.raises((RuntimeError, OSError)):
            await asyncio.wait_for(pending, 2)
        await asyncio.sleep(.03)
        assert runtime._session is session
        assert runtime.current.status == "failed"
        assert not runtime.state()["timing"]["infrastructure_valid"]
        with pytest.raises(RuntimeError, match="disconnected"):
            await runtime.finish()
        assert runtime._session is None
    finally:
        await runtime.close()
    assert not session.process.is_alive()
    assert runtime._session is None


@pytest.mark.asyncio
async def test_cancelled_start_joins_child_and_repeated_close_is_safe():
    runtime = ProcessRaceRuntime()
    start = asyncio.create_task(runtime.start(deadline=2))
    await asyncio.sleep(.01)
    session = runtime._session
    start.cancel()
    with pytest.raises(asyncio.CancelledError):
        await start
    await runtime.close()
    await runtime.close()
    assert runtime._session is None
    assert session.process.pid is None or not session.process.is_alive()


@pytest.mark.asyncio
async def test_blocked_parent_reader_does_not_backpressure_physics_clock():
    runtime = ProcessRaceRuntime()
    release = Event()
    try:
        initial = await runtime.start(deadline=3)
        original = runtime._session.connection

        class PausedConnection:
            def recv(self):
                message = original.recv()
                release.wait(timeout=2)
                return message

            def send(self, message):
                original.send(message)

            def close(self):
                original.close()

        runtime._session.connection = PausedConnection()
        # Several compact snapshots fill the pipe while the child's writer
        # waits. Its publication slot is overwritten, never awaited by physics.
        block_started_ns = time.monotonic_ns()
        await asyncio.sleep(1)
        block_ended_ns = time.monotonic_ns()
        release.set()
        current = await runtime.observe()
        assert current["tick"]-initial["tick"] >= 50
        assert current["time"] >= .85
        result = await runtime.finish()
        assert sum(block_started_ns < sample["wall_ns"] < block_ended_ns for sample in result["samples"]) >= 45
    finally:
        release.set()
        await runtime.close()
