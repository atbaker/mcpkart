"""Behavioral checks of the clock and command isolation, without inference."""

import asyncio
import gc
import json
import time
from threading import Event, get_ident

import httpx
import pytest

from mcpkart.runtime import (
    ASYNCIO_CLOCK_MODE,
    NATIVE_CLOCK_MODE,
    NativeSleeper,
    RaceRuntime,
    TimingDiagnostics,
)
from mcpkart.sim import ACTIONS, DT


@pytest.mark.asyncio
async def test_native_pacing_preserves_actual_ack_clock_and_all_catchup_ticks():
    runtime = RaceRuntime(native_sleeper=True)
    assert RaceRuntime().runtime_info()["clock_mode"] == ASYNCIO_CLOCK_MODE
    try:
        initial = runtime.start(deadline=2)
        race = runtime.current
        assert race.sleeper.ready_ns <= race.started_ns
        assert race.sleeper.thread.is_alive()
        first = await runtime.drive(initial["race_id"], "straight_accelerate", 0, 0)
        started_ns = race.started_ns
        blocked_from_ns = time.monotonic_ns()
        time.sleep(.15)  # noqa: ASYNC251 — native pacing must not conceal a blocked physics owner.
        blocked_until_ns = time.monotonic_ns()
        queued_ns = time.monotonic_ns()
        second = await runtime.drive(initial["race_id"], "straight_brake", first["applied_tick"], 1)
        assert second["queued_ns"] >= queued_ns
        assert second["applied_ns"] >= second["queued_ns"]
        assert second["observation"]["observed_ns"] >= second["applied_ns"]
        await asyncio.sleep(.05)
        assert race.started_ns == started_ns
        assert abs((time.monotonic_ns() - started_ns) / 1e9 - race.sim.elapsed) < .06
        result = runtime.finish(reason="test_finished")
        assert result["runtime_info"]["clock_mode"] == result["timing"]["clock_mode"] == NATIVE_CLOCK_MODE
        assert result["timing"]["max_lateness_ms"] > 100
        assert not result["realtime_valid"]
        assert not any(blocked_from_ns < sample["wall_ns"] < blocked_until_ns for sample in result["samples"])
        assert [sample["tick"] for sample in result["samples"]] == list(range(race.sim.tick + 1))
        assert all(sample["control"] == "straight_accelerate" for sample in result["samples"]
                   if first["applied_tick"] <= sample["tick"] < second["applied_tick"])
        assert result["samples"][second["applied_tick"]]["control"] == "straight_brake"
        assert not result["timing"]["pacing"]["native_sleeper_thread_alive"]
    finally:
        await runtime.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("ending", ["finish", "deadline", "cancel", "early_cancel", "error", "shutdown", "init_error"])
async def test_native_sleeper_is_joined_on_every_race_lifecycle_path(ending, monkeypatch):
    runtime = RaceRuntime(native_sleeper=True)
    if ending == "init_error":
        def broken_initial_sample(*args):
            raise RuntimeError("Expected initialization failure")

        monkeypatch.setattr(runtime, "_sample", broken_initial_sample)
        with pytest.raises(RuntimeError, match="initialization failure"):
            runtime.start(deadline=2)
    else:
        runtime.start(deadline=2 * DT if ending == "deadline" else 2)
    race = runtime.current
    sleeper = race.sleeper
    if ending != "init_error":
        if ending != "early_cancel":
            await asyncio.sleep(.005)  # Hand the first request to the native thread.
        if ending == "finish":
            runtime.finish()
        elif ending == "shutdown":
            await runtime.close()
        elif ending in {"cancel", "early_cancel"}:
            race.task.cancel()
            await asyncio.gather(race.task, return_exceptions=True)
        elif ending == "error":
            def broken_step(dt):
                raise RuntimeError("Expected physics failure")

            monkeypatch.setattr(race.sim, "step", broken_step)
            await asyncio.sleep(.05)
        else:
            await asyncio.sleep(.06)
    assert race.status != "running"
    assert sleeper.closed and not sleeper.thread.is_alive()
    await runtime.close()
    await runtime.close()
    assert not sleeper.thread.is_alive()


@pytest.mark.asyncio
async def test_native_cancelled_delivery_cannot_resolve_next_wait_and_far_close_is_bounded(monkeypatch):
    sleeper = NativeSleeper(asyncio.get_running_loop())
    deliveries = asyncio.Queue()
    complete = sleeper._complete
    monkeypatch.setattr(sleeper, "_complete", lambda request, error=None: deliveries.put_nowait((request, error)))
    waiting = []

    def submit(delay_ns):
        task = asyncio.create_task(sleeper.wait_until(time.monotonic_ns() + delay_ns))
        waiting.append(task)
        return task

    try:
        first = submit(5_000_000)
        old_request, old_error = await asyncio.wait_for(deliveries.get(), .5)
        first.cancel()
        await asyncio.gather(first, return_exceptions=True)
        second = submit(5_000_000)
        current_request, current_error = await asyncio.wait_for(deliveries.get(), .5)
        complete(old_request, old_error)
        await asyncio.sleep(0)
        assert not second.done()
        complete(current_request, current_error)
        await second
        far = submit(5_000_000_000)
        await asyncio.sleep(.005)
        far.cancel()
        await asyncio.gather(far, return_exceptions=True)
        # Canceling an in-flight far target must also release the helper so a
        # new near target can complete, without waiting out five seconds.
        near = submit(5_000_000)
        request, error = await asyncio.wait_for(deliveries.get(), .5)
        complete(request, error)
        await near
        far = submit(5_000_000_000)
        await asyncio.sleep(.005)
        started = time.monotonic()
        sleeper.close()
        assert time.monotonic() - started < .5
        await asyncio.gather(far, return_exceptions=True)
        complete(current_request, current_error)  # Closed/done delivery is harmless.
        sleeper.close()
        assert not sleeper.thread.is_alive()
    finally:
        sleeper.close()
        await asyncio.gather(*waiting, return_exceptions=True)


@pytest.mark.asyncio
async def test_old_native_callback_cannot_advance_a_replacement_race():
    runtime = RaceRuntime(native_sleeper=True)
    try:
        runtime.start(deadline=2)
        old = runtime.current
        await asyncio.sleep(.005)
        request = old.sleeper.current
        assert request is not None
        runtime.finish()
        initial = runtime.start(seed=1, deadline=2)
        old.sleeper._complete(request)
        assert runtime.current is not old and runtime.current.sim.tick == 0
        assert old.sim.tick == 0 and not old.sleeper.thread.is_alive()
        ack = await runtime.drive(initial["race_id"], "straight_accelerate", 0, 0)
        assert ack["applied"] and ack["observation"]["race_id"] == initial["race_id"]
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_clock_keeps_advancing_while_driver_waits():
    runtime = RaceRuntime()
    initial = runtime.start(deadline=2)
    await asyncio.sleep(0.13)  # Represents an outstanding model/network request.
    current = runtime.observe()
    assert current["tick"] >= initial["tick"] + 5
    assert current["time"] >= 5 * DT
    assert current["control"] == initial["control"]
    assert runtime.state()["timing"]["infrastructure_valid"]
    await runtime.close()


@pytest.mark.asyncio
async def test_acknowledgement_follows_a_physics_step_and_controls_persist():
    runtime = RaceRuntime()
    initial = runtime.start(deadline=2)
    action = next(key for key, value in ACTIONS.items() if value["throttle"] == 1 and value["steer"] == 0)
    queued_ns = time.monotonic_ns()
    ack = await runtime.drive(initial["race_id"], action, initial["tick"], 0)
    assert ack["applied_tick"] > initial["tick"]
    assert ack["applied_ns"] >= queued_ns
    assert ack["observation"]["control"] == action
    assert ack["observation"]["kart"]["speed"] > initial["kart"]["speed"]
    await asyncio.sleep(0.06)
    current = runtime.observe()
    assert current["tick"] > ack["applied_tick"]
    assert current["control"] == action
    assert current["kart"]["speed"] > ack["observation"]["kart"]["speed"]
    await runtime.close()


@pytest.mark.asyncio
async def test_rejects_old_commands_and_future_observations_without_changing_controls():
    runtime = RaceRuntime()
    initial = runtime.start(deadline=2)
    action, other = list(ACTIONS)[:2]
    ack = await runtime.drive(initial["race_id"], action, 0, 4)
    for sequence in [4, 3]:
        with pytest.raises(ValueError, match="out-of-order"):
            await runtime.drive(initial["race_id"], other, 0, sequence)
    with pytest.raises(ValueError, match="existing physics tick"):
        await runtime.drive(initial["race_id"], other, ack["applied_tick"] + 100, 5)
    assert runtime.observe()["control"] == action
    await runtime.close()


@pytest.mark.asyncio
async def test_old_race_reply_cannot_control_a_new_race():
    runtime = RaceRuntime()
    old = runtime.start(deadline=2)
    runtime.finish(reason="cancelled")
    current = runtime.start(seed=1, deadline=2)
    with pytest.raises(ValueError, match="Stale race_id"):
        await runtime.drive(old["race_id"], next(iter(ACTIONS)), 0, 0)
    assert runtime.observe()["race_id"] == current["race_id"]
    assert runtime.observe()["control"] == current["control"]
    await runtime.close()


@pytest.mark.asyncio
async def test_deadline_is_a_failure_and_late_reply_is_never_applied():
    runtime = RaceRuntime()
    initial = runtime.start(deadline=3 * DT)
    await asyncio.sleep(0.1)
    result = runtime.result()
    assert result["reason"] == "deadline"
    assert not result["summary"]["finished"]
    assert result["summary"]["elapsed"] >= 3 * DT
    ack = await runtime.drive(initial["race_id"], next(iter(ACTIONS)), 0, 0)
    assert ack["applied"] is False
    assert ack["observation"]["status"] != "running"
    assert runtime.result()["commands"] == []
    await runtime.close()


@pytest.mark.asyncio
async def test_clock_stall_is_reported_instead_of_silently_slowing_the_world():
    runtime = RaceRuntime()
    runtime.start(deadline=2)
    await asyncio.sleep(0.03)
    time.sleep(0.16)  # noqa: ASYNC251 — deliberately stall the physics scheduler.
    await asyncio.sleep(0.06)
    state = runtime.state()
    assert state["timing"]["max_lateness_ms"] > 100
    assert not state["timing"]["infrastructure_valid"]
    assert abs(state["timing"]["drift_ms"]) < 60  # Catches up; failure evidence survives.
    diagnostic = runtime.result()["timing"]["diagnostics"]
    assert diagnostic["largest_late_wake"]["wall_since_previous_wake_ms"] > 150
    assert diagnostic["largest_late_wake"]["process_cpu_since_previous_wake_ms"] >= 0
    assert diagnostic["late_wake_count"] > 0
    await runtime.close()


def test_diagnostics_bound_events_and_distinguish_wall_time_from_process_cpu(monkeypatch):
    from mcpkart import runtime as module

    recorder = TimingDiagnostics()
    recorder.active = True  # Exercise measurements without changing global GC policy.
    clock = {"wall": 1_000_000, "cpu": 100_000}
    monkeypatch.setattr(module.time, "monotonic_ns", lambda: clock["wall"])
    monkeypatch.setattr(module.time, "process_time_ns", lambda: clock["cpu"])
    recorder.wake(1, clock["wall"], 0)
    clock.update(wall=201_000_000, cpu=2_100_000)
    recorder.wake(2, clock["wall"], 180)
    event = recorder.snapshot(detail=True)["largest_late_wake"]
    assert event["wall_since_previous_wake_ms"] == 200
    assert event["process_cpu_since_previous_wake_ms"] == 2
    for tick in range(70):
        started_wall, started_cpu = clock["wall"], clock["cpu"]
        recorder._on_gc("start", {"generation": 2})
        clock["wall"] += 6_000_000
        clock["cpu"] += 500_000
        recorder._on_gc("stop", {"generation": 2, "collected": 3, "uncollectable": 0})
        recorder.span("test_work", started_wall, started_cpu)
        recorder.wake(tick+3, clock["wall"], 30)
    full = recorder.snapshot(detail=True)
    assert full["gc_count"] == full["slow_span_count"] == 70
    assert full["late_wake_count"] == 71
    assert len(full["gc_events"]) == len(full["slow_spans"]) == len(full["late_wakes"]) == 64
    assert full["gc_max_ms"] == full["spans"]["test_work"]["max_ms"] == 6
    assert full["spans"]["test_work"]["max_process_cpu_ms"] == .5
    assert full["gc_events"][-1]["generation"] == 2
    assert "gc_events" not in recorder.snapshot()
    recorder.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("ending", ["finish", "deadline", "cancel", "error", "shutdown"])
async def test_gc_callback_lifecycle_is_limited_to_active_race(ending, monkeypatch):
    runtime = RaceRuntime(watchdog=True)
    runtime.start(deadline=2 * DT if ending == "deadline" else 2)
    race = runtime.current
    recorder = race.diagnostics
    assert recorder._callback in gc.callbacks
    if ending == "finish":
        runtime.finish(reason="test_finished")
    elif ending == "shutdown":
        await runtime.close()
    elif ending == "cancel":
        race.task.cancel()
        await asyncio.gather(race.task, return_exceptions=True)
    elif ending == "error":
        def broken_step(dt):
            raise RuntimeError("Expected physics failure")

        monkeypatch.setattr(race.sim, "step", broken_step)
        await asyncio.sleep(.05)
    else:
        await asyncio.sleep(.06)
    assert not recorder.active
    assert recorder._callback not in gc.callbacks
    assert not recorder._watchdog_thread.is_alive()
    assert runtime.result()["timing"]["diagnostics"]["active"] is False
    await runtime.close()


@pytest.mark.asyncio
async def test_watchdog_captures_blocked_event_loop_stack_without_values():
    runtime = RaceRuntime(watchdog=True)
    runtime.start(deadline=2)
    await asyncio.sleep(.03)
    time.sleep(.12)  # noqa: ASYNC251 — release GIL while deliberately blocking the loop thread.
    await asyncio.sleep(.03)
    result = runtime.finish(reason="test_finished")
    watchdog = result["timing"]["diagnostics"]["watchdog"]
    assert watchdog["enabled"] and watchdog["sample_count"] > 0
    assert watchdog["stall_sample_count"] > 0
    samples = watchdog["stall_samples"]
    assert any(sample["physics_gap_ms"] > 80 for sample in samples)
    assert any(frame["function"] == "test_watchdog_captures_blocked_event_loop_stack_without_values"
               for sample in samples for frame in sample["main_thread_stack"])
    assert all(set(frame) == {"filename", "function", "line"} for sample in samples for frame in sample["main_thread_stack"])
    assert "stall_samples" not in runtime.state()["timing"]["diagnostics"]["watchdog"]
    assert not runtime.current.diagnostics._watchdog_thread.is_alive()
    await runtime.close()


def test_watchdog_keeps_bounded_stacks_and_records_sampling_gaps():
    recorder = TimingDiagnostics(watchdog_enabled=True)
    recorder.active = True
    recorder._watched_thread_id = get_ident()
    recorder._previous_wake = (0, 0)
    recorder._watchdog_previous = (0, 0)
    for index in range(1, 81):
        recorder._watchdog_sample(index * 100_000_000, index * 1_000_000)
    watchdog = recorder.snapshot(detail=True)["watchdog"]
    assert watchdog["sample_count"] == watchdog["stall_sample_count"] == 80
    assert len(watchdog["stall_samples"]) == 64
    assert watchdog["max_sample_gap_ms"] == 100
    assert watchdog["largest_sample_gap"]["process_cpu_since_previous_watchdog_ms"] == 1
    assert all(len(sample["main_thread_stack"]) <= 24 for sample in watchdog["stall_samples"])
    recorder.stop()


@pytest.mark.asyncio
async def test_state_exposes_lightweight_summary_and_records_serialization_span(tmp_path):
    from mcpkart.web import create_app

    runtime = RaceRuntime()
    app = create_app(runtime=runtime, replay_root=tmp_path)
    runtime.start(deadline=2)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        first = (await client.get("/api/state")).json()
        await asyncio.sleep(.04)
        state = (await client.get("/api/state")).json()
    summary = state["timing"]["diagnostics"]
    assert "slow_spans" not in summary and "late_wakes" not in summary and "gc_events" not in summary
    full = runtime.result()["timing"]["diagnostics"]
    assert full["spans"]["runtime_state"]["count"] == 2
    assert full["spans"]["state_json_encoding"]["count"] == 2
    assert full["spans"]["physics_step"]["count"] > 0
    assert full["spans"]["physics_sample"]["count"] > full["spans"]["physics_step"]["count"]
    assert state["observation"]["tick"] > first["observation"]["tick"]
    await runtime.close()


@pytest.mark.asyncio
async def test_replay_api_only_serves_valid_recordings_with_opaque_ids(tmp_path):
    from mcpkart.web import create_app

    root = tmp_path / "artifacts"
    root.mkdir()
    race = {"race_id": "saved", "label": "Recorded driver", "track": {"points": [[0, 0], [10, 0]], "width": 9},
            "samples": [{"tick": 0, "time": 0, "kart": {"x": 0, "y": 0, "heading": 0, "speed": 0},
                         "control": "straight_coast", "progress": {"lap": 1}}],
            "summary": {"finished": False}, "config": {"actions": ACTIONS}}
    (root / "trial.json").write_text(json.dumps({"race": race, "requests": [{"private": "sentinel"}]}))
    (root / "budget.json").write_text(json.dumps({"race": race, "secret": "sentinel"}))
    (root / "not-a-trial.json").write_text('{"private":"sentinel"}')
    (root / "partial.json").write_text('{"race":')
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps({"race": race, "private": "sentinel"}))
    (root / "linked.json").symlink_to(outside)
    transport = httpx.ASGITransport(app=create_app(replay_root=root))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/replays")
        assert response.status_code == 200
        entries = response.json()["replays"]
        assert [entry["file"] for entry in entries] == ["trial.json"]
        identity = entries[0]["id"]
        assert len(identity) == 64
        playback = await client.get(f"/api/replays/{identity}")
        assert playback.status_code == 200
        assert playback.json()["samples"] == race["samples"]
        assert "sentinel" not in playback.text
        for invalid in ["trial.json", "budget.json", "0" * 64, "..%2Foutside.json", "%2e%2e%2f.env"]:
            assert (await client.get(f"/api/replays/{invalid}")).status_code == 404


@pytest.mark.asyncio
async def test_rescue_preserves_race_clock_and_rejects_stale_reply_without_consuming_sequence():
    runtime = RaceRuntime()
    initial = runtime.start(deadline=2, reset_after_s=3 * DT)
    race = runtime.current
    assert race is not None
    started_ns = race.started_ns
    race.sim.x, race.sim.y, race.sim.offset = 1000, 1000, 1000
    await asyncio.sleep(0.09)
    rescued = runtime.observe()
    assert rescued["rescue"]["count"] == 1
    assert rescued["tick"] > rescued["rescue"]["last_reset_tick"]
    assert rescued["time"] > initial["time"]
    assert race.started_ns == started_ns
    assert rescued["progress"]["checkpoints_passed"] == initial["progress"]["checkpoints_passed"]
    stale = await runtime.drive(initial["race_id"], "hard_left_accelerate", initial["tick"], 0)
    assert not stale["applied"]
    assert stale["reason"] == "observation_before_rescue"
    assert stale["observation"]["rescue"]["count"] == 1
    assert runtime.observe()["control"] == "straight_coast"
    # The rejected input did not use sequence zero; a fresh decision may use it.
    fresh = await runtime.drive(initial["race_id"], "straight_accelerate", stale["observation"]["tick"], 0)
    assert fresh["applied"]
    assert runtime.result()["rejected_commands"][0]["reason"] == "observation_before_rescue"
    assert any(sample["rescue"]["count"] == 1 for sample in runtime.result()["samples"])
    assert runtime.result()["reset_events"]
    await runtime.close()


@pytest.mark.asyncio
async def test_acknowledges_rescue_during_input_step_and_never_reapplies_old_control():
    runtime = RaceRuntime()
    initial = runtime.start(deadline=2, reset_after_s=DT)
    race = runtime.current
    assert race is not None
    race.sim.x, race.sim.y, race.sim.offset = 1000, 1000, 1000
    ack = await runtime.drive(initial["race_id"], "hard_left_accelerate", initial["tick"], 0)
    assert ack["applied"]
    assert ack["reset_during_step"]
    assert ack["observation"]["rescue"]["count"] == 1
    assert ack["observation"]["control"] == "straight_coast"
    await asyncio.sleep(0.04)
    assert runtime.observe()["control"] == "straight_coast"
    assert runtime.observe()["time"] > ack["observation"]["time"]
    await runtime.close()


@pytest.mark.asyncio
async def test_race_admission_warms_archive_before_clock_and_cached_playback_stays_available(tmp_path, monkeypatch):
    from mcpkart.web import create_app

    runtime = RaceRuntime()
    sample = {"tick": 0, "time": 0, "kart": {"x": 0, "y": 0, "heading": 0, "speed": 0},
              "control": "straight_coast", "progress": {"lap": 1}}
    race = {"race_id": "saved", "label": "Saved driver", "track": {"points": [[0, 0], [10, 0]], "width": 9},
            "samples": [sample] * 5000, "summary": {"finished": False}, "config": {"actions": ACTIONS}}
    trial = tmp_path / "trial.json"
    trial.write_text(json.dumps({"race": race, "requests": [{"private": "sentinel"}]}))
    app = create_app(runtime=runtime, replay_root=tmp_path)
    catalog = app.state.replay_catalog
    original_load, original_encode = catalog._load_entry, catalog._encode_race
    parsing_started, finish_parsing = Event(), Event()
    completed_ns = []
    loads, encodes = [], []

    def load_before_clock(*args):
        assert runtime.current is None or runtime.current.status != "running"
        loads.append(args[0])
        parsing_started.set()
        assert finish_parsing.wait(timeout=2)
        result = original_load(*args)
        completed_ns.append(time.monotonic_ns())
        return result

    def encode_before_clock(value):
        assert runtime.current is None or runtime.current.status != "running"
        encodes.append(1)
        return original_encode(value)

    monkeypatch.setattr(catalog, "_load_entry", load_before_clock)
    monkeypatch.setattr(catalog, "_encode_race", encode_before_clock)
    idle_refresh = asyncio.create_task(asyncio.to_thread(catalog.list))
    assert await asyncio.to_thread(parsing_started.wait, 1)
    # This browser operation queued while idle must check admission again after
    # taking the lock; it cannot thaw the catalog after the clock starts.
    queued_refresh = asyncio.create_task(asyncio.to_thread(catalog.list))
    start = asyncio.create_task(app.state.start_race(deadline=2))
    await asyncio.sleep(0.01)
    assert runtime.current is None
    assert not start.done()
    with pytest.raises(ValueError, match="being admitted"):
        await app.state.start_race(deadline=2)
    finish_parsing.set()
    entries = await idle_refresh
    initial = await start
    await queued_refresh
    assert runtime.current.started_ns >= completed_ns[-1]
    assert loads == [trial]
    assert len(encodes) == 1
    identity = entries[0]["id"]
    # A new/changed file and an expired refresh interval would normally trigger
    # parsing and encoding. While racing both operations must remain frozen.
    (tmp_path / "new-trial.json").write_text(json.dumps({"race": race}))
    catalog._checked_at = -10
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get("/api/replays")
        assert len(listed.json()["replays"]) == 1
        playback = await client.get(f"/api/replays/{identity}")
        assert playback.status_code == 200
        assert len(playback.json()["samples"]) == 5000
        assert "sentinel" not in playback.text
        assert (await client.get("/api/replay")).status_code == 409
        assert loads == [trial]
        assert len(encodes) == 1
        await asyncio.sleep(0.04)
        assert runtime.observe()["tick"] > initial["tick"]
        runtime.finish(reason="test_finished")
        listed = await client.get("/api/replays")
        assert len(listed.json()["replays"]) == 2
        assert len(loads) == 2
        assert len(encodes) == 2
        assert (await client.get("/api/replay")).status_code == 200
    await runtime.close()
