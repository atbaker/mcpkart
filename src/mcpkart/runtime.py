"""Wall-clock race runtime, shared by the MCP server and spectator view.

The fixed physics clock owns input application. A drive acknowledgement is sent
only after a physics step has actually used the submitted controls.
"""

from __future__ import annotations

import asyncio
import gc
import math
import os
import sys
import time
import uuid
import weakref
from collections import deque
from dataclasses import dataclass, field
from threading import Condition, Event, Thread, get_ident
from typing import Any

from .sim import ACTIONS, DT, Simulation

ASYNCIO_CLOCK_MODE = "fixed_step_wall_clock"
NATIVE_CLOCK_MODE = "fixed_step_native_sleeper"


class NativeSleeper:
    """One absolute wait, paced by time.sleep outside the asyncio selector.

    The helper only posts a signal. The event-loop thread still owns physics,
    command application, and all recorded wake/application timestamps. Each
    race owns its helper, so canceled callbacks cannot wake a replacement race.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.condition = Condition()
        self.pending: tuple[int, asyncio.Future] | None = None
        self.current: tuple[int, asyncio.Future] | None = None
        self.closed = False
        self.error: str | None = None
        self.ready = Event()
        self.ready_ns: int | None = None
        self.thread = Thread(target=self._run, name="mcpkart-native-sleeper", daemon=True)
        self.thread.start()
        # Warm the thread and native sleep path before the race epoch exists.
        if not self.ready.wait(timeout=2) or self.error is not None:
            self.close()
            raise RuntimeError(self.error or "Native sleeper failed to initialize")

    async def wait_until(self, deadline_ns: int) -> None:
        future = self.loop.create_future()
        request = (deadline_ns, future)
        with self.condition:
            if self.closed or self.error is not None:
                raise RuntimeError(self.error or "Native sleeper is closed")
            if self.current is not None:
                raise RuntimeError("A native sleep is already pending")
            self.current = self.pending = request
            self.condition.notify()
        try:
            # Even an overdue deadline posts through the loop, yielding a turn
            # per catch-up tick just as asyncio.sleep(0) does in the old clock.
            await future
        finally:
            with self.condition:
                if self.current is request:
                    self.current = None
                if self.pending is request:
                    self.pending = None

    def _complete(self, request: tuple[int, asyncio.Future], error: str | None = None) -> None:
        with self.condition:
            if self.closed or self.current is not request:
                return
        future = request[1]
        if not future.done():
            if error is None:
                future.set_result(None)
            else:
                future.set_exception(RuntimeError(error))

    def _run(self) -> None:
        request = None
        try:
            time.sleep(0)
            self.ready_ns = time.monotonic_ns()
            self.ready.set()
            while True:
                with self.condition:
                    self.condition.wait_for(lambda: self.closed or self.pending is not None)
                    if self.closed:
                        return
                    request, self.pending = self.pending, None
                # A normal request is at most one physics interval away. The
                # cap also bounds shutdown latency for an accidental far wait;
                # it never changes the absolute target or advances simulation.
                while not self.closed:
                    with self.condition:
                        if self.current is not request:
                            break
                    delay = (request[0] - time.monotonic_ns()) / 1e9
                    if delay <= 0:
                        break
                    time.sleep(min(delay, DT))
                if self.closed:
                    return
                with self.condition:
                    if self.current is not request:
                        request = None
                        continue
                self.loop.call_soon_threadsafe(self._complete, request)
                request = None
        except Exception as exc:  # noqa: BLE001 — fail the wait instead of silently losing its clock.
            self.error = f"Native sleeper failed: {type(exc).__name__}: {exc}"
            if request is not None:
                try:
                    self.loop.call_soon_threadsafe(self._complete, request, self.error)
                except RuntimeError:  # Event loop already closed during teardown.
                    pass
        finally:
            self.ready.set()

    def close(self) -> None:
        with self.condition:
            self.closed = True
            request, self.current, self.pending = self.current, None, None
            self.condition.notify()
        if request is not None and not request[1].done():
            request[1].cancel()
        # No helper operation waits for the event loop. Native sleeps are at
        # most one interval, and joins happen after the race is marked ended.
        if self.thread.ident != get_ident():
            self.thread.join()


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)]


class TimingDiagnostics:
    """Bounded evidence only: no GC policy, disk writes, or clock adjustments."""

    LIMIT = 64
    SLOW_SPAN_MS = 5.0

    def __init__(self, watchdog_enabled: bool = False) -> None:
        self.active = False
        self.spans: dict[str, dict[str, float | int]] = {}
        self.slow_spans: deque[dict] = deque(maxlen=self.LIMIT)
        self.gc_events: deque[dict] = deque(maxlen=self.LIMIT)
        self.late_wakes: deque[dict] = deque(maxlen=self.LIMIT)
        self.gc_count = self.late_wake_count = self.slow_span_count = 0
        self.gc_max_ms = 0.0
        self.largest_late_wake: dict | None = None
        self._gc_started: dict[int, tuple[int, int]] = {}
        self._previous_wake: tuple[int, int] | None = None
        self.watchdog_enabled = watchdog_enabled
        self.watchdog_events: deque[dict] = deque(maxlen=self.LIMIT)
        self.watchdog_sample_count = self.watchdog_stall_count = 0
        self.watchdog_max_gap_ms = 0.0
        self.watchdog_largest_gap: dict | None = None
        self._watchdog_previous: tuple[int, int] | None = None
        self._watchdog_stop = Event()
        self._watchdog_thread: Thread | None = None
        self._watched_thread_id: int | None = None
        # Keep the same callback object for reliable lifecycle removal. It owns
        # this recorder only, never a race/runtime or their growing replay logs.
        reference = weakref.ref(self)

        def callback(phase, info):
            recorder = reference()
            if recorder is not None:
                recorder._on_gc(phase, info)

        self._callback = callback

    def start(self, started_ns: int) -> None:
        self.active = True
        self._previous_wake = (started_ns, time.process_time_ns())
        gc.callbacks.append(self._callback)
        if self.watchdog_enabled:
            self._watched_thread_id = get_ident()
            self._watchdog_previous = self._previous_wake
            self._watchdog_stop.clear()
            self._watchdog_thread = Thread(target=self._watchdog, name="mcpkart-watchdog", daemon=True)
            self._watchdog_thread.start()

    def stop(self) -> None:
        self.active = False
        self._watchdog_stop.set()
        if self._callback in gc.callbacks:
            gc.callbacks.remove(self._callback)
        self._gc_started.clear()
        if self._watchdog_thread is not None and self._watchdog_thread.ident not in (None, get_ident()):
            self._watchdog_thread.join(timeout=.1)

    def _watchdog(self) -> None:
        while not self._watchdog_stop.wait(.016):
            if not self.active:
                break
            self._watchdog_sample(time.monotonic_ns(), time.process_time_ns())

    def _watchdog_sample(self, now_ns: int, cpu_ns: int) -> None:
        previous = self._watchdog_previous
        self._watchdog_previous = (now_ns, cpu_ns)
        if not self.active or previous is None or self._previous_wake is None:
            return
        self.watchdog_sample_count += 1
        gap_ms = (now_ns-previous[0])/1e6
        event = {"watchdog_ns": now_ns, "previous_watchdog_ns": previous[0], "watchdog_gap_ms": gap_ms,
                 "process_cpu_since_previous_watchdog_ms": (cpu_ns-previous[1])/1e6,
                 "last_physics_wake_ns": self._previous_wake[0],
                 "physics_gap_ms": (now_ns-self._previous_wake[0])/1e6}
        if gap_ms > self.watchdog_max_gap_ms:
            self.watchdog_max_gap_ms = gap_ms
            self.watchdog_largest_gap = event
        if event["physics_gap_ms"] <= 50:
            return
        # Never retain frame objects or read locals. Only source coordinates
        # leave this helper, bounded to 24 frames for each of 64 stall samples.
        frame = sys._current_frames().get(self._watched_thread_id)
        stack = []
        try:
            while frame is not None and len(stack) < 24:
                stack.append({"filename": frame.f_code.co_filename,
                              "function": frame.f_code.co_name, "line": frame.f_lineno})
                frame = frame.f_back
        finally:
            del frame
        self.watchdog_stall_count += 1
        self.watchdog_events.append({**event, "main_thread_stack": stack})

    def _on_gc(self, phase: str, info: dict) -> None:
        if not self.active:
            return
        generation = info["generation"]
        if phase == "start":
            self._gc_started[generation] = (time.monotonic_ns(), time.process_time_ns())
            return
        started = self._gc_started.pop(generation, None)
        if phase != "stop" or started is None:
            return
        ended_ns, cpu_ns = time.monotonic_ns(), time.process_time_ns()
        duration_ms = (ended_ns-started[0])/1e6
        self.gc_count += 1
        self.gc_max_ms = max(self.gc_max_ms, duration_ms)
        self.gc_events.append({"generation": generation, "started_ns": started[0], "ended_ns": ended_ns,
                               "duration_ms": duration_ms, "process_cpu_ms": (cpu_ns-started[1])/1e6,
                               "collected": info.get("collected", 0), "uncollectable": info.get("uncollectable", 0)})

    def span(self, name: str, started_ns: int, started_cpu_ns: int) -> None:
        if not self.active:
            return
        ended_ns, cpu_ns = time.monotonic_ns(), time.process_time_ns()
        duration_ms = (ended_ns-started_ns)/1e6
        cpu_ms = (cpu_ns-started_cpu_ns)/1e6
        aggregate = self.spans.setdefault(name, {"count": 0, "total_ms": 0.0, "max_ms": 0.0, "max_process_cpu_ms": 0.0})
        aggregate["count"] += 1
        aggregate["total_ms"] += duration_ms
        aggregate["max_ms"] = max(aggregate["max_ms"], duration_ms)
        aggregate["max_process_cpu_ms"] = max(aggregate["max_process_cpu_ms"], cpu_ms)
        if duration_ms >= self.SLOW_SPAN_MS:
            self.slow_span_count += 1
            self.slow_spans.append({"name": name, "started_ns": started_ns, "ended_ns": ended_ns,
                                    "duration_ms": duration_ms, "process_cpu_ms": cpu_ms})

    def wake(self, tick: int, wake_ns: int, lateness_ms: float) -> None:
        cpu_ns = time.process_time_ns()
        previous = self._previous_wake
        self._previous_wake = (wake_ns, cpu_ns)
        if lateness_ms <= 25 or previous is None:
            return
        event = {"tick": tick, "wake_ns": wake_ns, "lateness_ms": lateness_ms,
                 "previous_wake_ns": previous[0], "wall_since_previous_wake_ms": (wake_ns-previous[0])/1e6,
                 "process_cpu_since_previous_wake_ms": (cpu_ns-previous[1])/1e6}
        self.late_wake_count += 1
        self.late_wakes.append(event)
        if self.largest_late_wake is None or lateness_ms > self.largest_late_wake["lateness_ms"]:
            self.largest_late_wake = event

    def snapshot(self, detail: bool = False) -> dict:
        value = {"active": self.active, "event_limit": self.LIMIT, "slow_span_threshold_ms": self.SLOW_SPAN_MS,
                 "late_wake_threshold_ms": 25, "gc_count": self.gc_count, "gc_max_ms": self.gc_max_ms,
                 "slow_span_count": self.slow_span_count, "late_wake_count": self.late_wake_count,
                 "spans": {name: dict(aggregate) for name, aggregate in self.spans.items()},
                 "largest_late_wake": self.largest_late_wake,
                 "watchdog": {"enabled": self.watchdog_enabled, "sample_interval_ms": 16, "stall_threshold_ms": 50,
                              "sample_count": self.watchdog_sample_count, "stall_sample_count": self.watchdog_stall_count,
                              "max_sample_gap_ms": self.watchdog_max_gap_ms, "largest_sample_gap": self.watchdog_largest_gap,
                              "last_sample_ns": self._watchdog_previous[0] if self._watchdog_previous else None,
                              "note": "Thread samples require the GIL; missing samples can reflect process scheduling or GIL blockage."},
                 "cpu_note": "Process CPU covers all server threads; compare with wall gap, not model API latency."}
        if detail:
            value.update(gc_events=list(self.gc_events), slow_spans=list(self.slow_spans), late_wakes=list(self.late_wakes))
            value["watchdog"]["stall_samples"] = list(self.watchdog_events)
        return value


@dataclass
class _Race:
    race_id: str
    sim: Simulation
    seed: int
    deadline: float
    label: str
    started_ns: int
    status: str = "running"
    reason: str | None = None
    finished_ns: int | None = None
    last_command_seq: int = -1
    pending: tuple[dict[str, Any], asyncio.Future] | None = None
    task: asyncio.Task | None = None
    samples: list[dict[str, Any]] = field(default_factory=list)
    commands: list[dict[str, Any]] = field(default_factory=list)
    rejected_commands: list[dict[str, Any]] = field(default_factory=list)
    lateness_ms: list[float] = field(default_factory=list)
    last_observed_ns: int | None = None
    diagnostics: TimingDiagnostics = field(default_factory=TimingDiagnostics)
    sleeper: NativeSleeper | None = None


class RaceRuntime:
    """One local race at a time; inference never advances the physics clock."""

    def __init__(self, *, watchdog: bool = False, native_sleeper: bool = False) -> None:
        self.current: _Race | None = None
        self._preview: Simulation | None = None
        self._watchdog_enabled = watchdog
        self._native_sleeper = native_sleeper

    def runtime_info(self) -> dict[str, Any]:
        return {"backend": "event_loop", "protocol_version": 1,
                "watchdog_enabled": self._watchdog_enabled,
                "clock_mode": NATIVE_CLOCK_MODE if self._native_sleeper else ASYNCIO_CLOCK_MODE, "physics_hz": round(1 / DT),
                "process_pid": os.getpid()}

    def start(self, seed: int = 0, deadline: float = 120.0, label: str = "", reset_after_s: float | None = 3.0,
              race_setup: dict | None = None) -> dict[str, Any]:
        if not math.isfinite(deadline) or deadline <= 0 or deadline > 86400:
            raise ValueError("deadline must be a positive number of seconds, at most 86400")
        if self.current is not None and self.current.status == "running":
            raise ValueError("A race is already running; finish it before starting another")
        sim = Simulation(seed=seed, laps=3, reset_after_s=reset_after_s, **(race_setup or {}))
        sleeper = NativeSleeper(asyncio.get_running_loop()) if self._native_sleeper else None
        race = _Race(uuid.uuid4().hex, sim, seed, deadline, label, time.monotonic_ns(),
                     diagnostics=TimingDiagnostics(watchdog_enabled=self._watchdog_enabled), sleeper=sleeper)
        self.current = race
        try:
            race.diagnostics.start(race.started_ns)
            self._sample(race, race.started_ns, 0.0)
            race.task = asyncio.create_task(self._run(race), name=f"race-{race.race_id}")
            reference = weakref.ref(race)

            def task_ended(task):
                remaining = reference()
                # Cancellation before the coroutine's first instruction never
                # enters its try/finally. Do not leave a global GC hook behind.
                if remaining is not None and remaining.status == "running":
                    RaceRuntime._end(remaining, "runtime_cancelled" if task.cancelled() else "runtime_error:task_ended")

            race.task.add_done_callback(task_ended)
            return self.observe()
        except BaseException:
            self._end(race, "runtime_error:initialization")
            raise

    def observe(self, race_id: str | None = None) -> dict[str, Any]:
        race = self._require_race(race_id)
        captured_ns = time.monotonic_ns()
        race.last_observed_ns = captured_ns
        return {**race.sim.observation(), "race_id": race.race_id, "observed_ns": captured_ns, "status": race.status, "finished": race.sim.finished}

    async def drive(
        self, race_id: str, action_id: str, observation_tick: int, command_seq: int
    ) -> dict[str, Any]:
        race = self._require_race(race_id)
        if race.status != "running":
            return {"race_id": race_id, "command_seq": command_seq, "action_id": action_id,
                    "applied": False, "reason": "race_already_ended", "observation": self.observe(race_id)}
        if action_id not in ACTIONS:
            raise ValueError(f"Unknown action_id: {action_id}")
        if isinstance(command_seq, bool) or not isinstance(command_seq, int) or command_seq < 0:
            raise ValueError("command_seq must be a nonnegative integer")
        if isinstance(observation_tick, bool) or not isinstance(observation_tick, int) or not 0 <= observation_tick <= race.sim.tick:
            raise ValueError("observation_tick must refer to an existing physics tick")
        if race.sim.last_reset_tick is not None and observation_tick < race.sim.last_reset_tick:
            return self._reject(race, {"race_id": race_id, "action_id": action_id, "command_seq": command_seq,
                                      "observation_tick": observation_tick}, "observation_before_rescue")
        if command_seq <= race.last_command_seq:
            raise ValueError("Duplicate or out-of-order command_seq")
        if race.pending is not None:
            raise ValueError("A command is already waiting for its physics step")
        record = {
            "race_id": race_id, "action_id": action_id, "command_seq": command_seq,
            "observation_tick": observation_tick, "queued_ns": time.monotonic_ns(),
        }
        future = asyncio.get_running_loop().create_future()
        race.pending = (record, future)
        # Shield leaves an accepted command in force even if its HTTP caller
        # disconnects before acknowledgement. No cancellation policy is a driver.
        return await asyncio.shield(future)

    def finish(self, race_id: str | None = None, reason: str = "cancelled") -> dict[str, Any]:
        race = self._require_race(race_id)
        if race.status == "running":
            self._end(race, reason)
            if race.task is not None:
                race.task.cancel()
        return self.result()

    def result(self) -> dict[str, Any]:
        race = self._require_race()
        timing = self._timing(race, diagnostics_detail=True)
        summary = {**race.sim.summary(), "deadline": race.deadline, "realtime_valid": timing["infrastructure_valid"]}
        return {
            "race_id": race.race_id, "seed": race.seed, "label": race.label,
            "status": race.status, "reason": race.reason, "deadline": race.deadline,
            "started_ns": race.started_ns, "finished_ns": race.finished_ns,
            "summary": summary, "config": race.sim.config(),
            "track": race.sim.track.as_dict(), "timing": timing,
            "runtime_info": self.runtime_info(),
            "samples": list(race.samples), "commands": list(race.commands),
            "controls": list(race.commands), "realtime_valid": timing["infrastructure_valid"],
            "rejected_commands": list(race.rejected_commands), "reset_events": list(race.sim.reset_events),
        }

    def state(self) -> dict[str, Any]:
        started_ns, cpu_ns = time.monotonic_ns(), time.process_time_ns()
        try:
            return self._state()
        finally:
            self.record_timing_span("runtime_state", started_ns, cpu_ns)

    def record_timing_span(self, name: str, started_ns: int, started_cpu_ns: int) -> None:
        if self.current is not None:
            self.current.diagnostics.span(name, started_ns, started_cpu_ns)

    def _state(self) -> dict[str, Any]:
        race = self.current
        if race is None:
            if self._preview is None:
                self._preview = Simulation(seed=0, laps=3)
            preview = self._preview
            return {"status": "idle", "track": preview.track.as_dict(), "actions": ACTIONS, "config": preview.config()}
        now = time.monotonic_ns()
        # This read does not count as a model observation.
        observation = {**race.sim.observation(), "race_id": race.race_id, "status": race.status}
        return {
            "status": race.status, "race_id": race.race_id, "label": race.label,
            "reason": race.reason, "seed": race.seed, "deadline": race.deadline,
            "observation": observation, "track": race.sim.track.as_dict(), "actions": ACTIONS,
            "timing": self._timing(race), "command_count": len(race.commands),
            "waiting_for_reply": race.status == "running" and race.pending is None,
            "observation_age_ms": None if race.last_observed_ns is None else (now - race.last_observed_ns) / 1e6,
            "trail": [[s["kart"]["x"], s["kart"]["y"]] for s in race.samples[-600::3]
                      if s["tick"] >= (race.sim.last_reset_tick or 0)],
        }

    async def close(self) -> None:
        if self.current is not None and self.current.status == "running":
            self.finish(reason="server_shutdown")
        task = self.current.task if self.current is not None else None
        if task is not None:
            await asyncio.gather(task, return_exceptions=True)

    def _require_race(self, race_id: str | None = None) -> _Race:
        if self.current is None:
            raise ValueError("No race has started")
        if race_id is not None and race_id != self.current.race_id:
            raise ValueError("Stale race_id; the command belongs to a different race")
        return self.current

    async def _run(self, race: _Race) -> None:
        try:
            while race.status == "running":
                target_ns = race.started_ns + round((race.sim.tick + 1) * DT * 1e9)
                if race.sleeper is None:
                    await asyncio.sleep(max(0, (target_ns - time.monotonic_ns()) / 1e9))
                else:
                    await race.sleeper.wait_until(target_ns)
                if race.status != "running":
                    break
                step_ns = time.monotonic_ns()
                late_ms = max(0.0, (step_ns - target_ns) / 1e6)
                race.diagnostics.wake(race.sim.tick+1, step_ns, late_ms)
                pending = race.pending
                race.pending = None
                reset_before = race.sim.last_reset_tick
                stale_pending = pending is not None and reset_before is not None and pending[0]["observation_tick"] < reset_before
                if pending is not None and not stale_pending:
                    race.sim.set_control(pending[0]["action_id"])
                physics_ns, physics_cpu = time.monotonic_ns(), time.process_time_ns()
                try:
                    race.sim.step(DT)
                finally:
                    race.diagnostics.span("physics_step", physics_ns, physics_cpu)
                applied_ns = time.monotonic_ns()
                race.lateness_ms.append(late_ms)
                self._sample(race, applied_ns, late_ms)
                if race.sim.finished:
                    self._end(race, "completed")
                elif race.sim.elapsed >= race.deadline:
                    self._end(race, "deadline")
                if pending is not None:
                    record, future = pending
                    if stale_pending:
                        ack = self._reject(race, record, "observation_before_rescue")
                    else:
                        race.last_command_seq = record["command_seq"]
                        record.update(applied_ns=applied_ns, applied_tick=race.sim.tick,
                                      reset_during_step=race.sim.last_reset_tick is not None and race.sim.last_reset_tick != reset_before)
                        race.commands.append(record)
                        ack = {**record, "applied": True, "observation": self.observe(race.race_id)}
                    if not future.done():
                        future.set_result(ack)
                # If late, following iterations catch up against the original
                # epoch. No dropped physics ticks and no reset of the clock.
        except asyncio.CancelledError:
            if race.status == "running":
                self._end(race, "runtime_cancelled")
            raise
        except Exception as exc:  # noqa: BLE001 — retain evidence and close a crashed physics task.
            self._end(race, f"runtime_error:{type(exc).__name__}:{exc}")

    def _sample(self, race: _Race, wall_ns: int, late_ms: float) -> None:
        started_ns, cpu_ns = time.monotonic_ns(), time.process_time_ns()
        try:
            self._capture_sample(race, wall_ns, late_ms)
        finally:
            race.diagnostics.span("physics_sample", started_ns, cpu_ns)

    def _capture_sample(self, race: _Race, wall_ns: int, late_ms: float) -> None:
        observation = race.sim.observation()
        race.samples.append({
            "tick": race.sim.tick, "time": race.sim.elapsed, "wall_ns": wall_ns,
            "kart": observation["kart"], "progress": observation["progress"],
            "control": observation["control"], "lateness_ms": late_ms,
            "rescue": observation.get("rescue", {}),
        })

    def _reject(self, race: _Race, record: dict[str, Any], reason: str) -> dict[str, Any]:
        rejected = {**record, "applied": False, "reason": reason, "rejected_ns": time.monotonic_ns()}
        race.rejected_commands.append(rejected)
        return {**rejected, "observation": self.observe(race.race_id)}

    @staticmethod
    def _end(race: _Race, reason: str) -> None:
        race.status = "completed" if reason == "completed" else "failed" if reason == "deadline" or reason.startswith("runtime_error") else "stopped"
        race.reason = reason
        race.finished_ns = time.monotonic_ns()
        race.diagnostics.stop()
        if race.sleeper is not None:
            race.sleeper.close()
        if race.pending is not None:
            _, future = race.pending
            race.pending = None
            if not future.done():
                future.set_exception(ValueError(f"Race ended before input application: {reason}"))

    def _timing(self, race: _Race, diagnostics_detail: bool = False) -> dict[str, Any]:
        now_ns = race.finished_ns or time.monotonic_ns()
        wall_elapsed = (now_ns - race.started_ns) / 1e9
        drift_ms = (wall_elapsed - race.sim.elapsed) * 1000
        maximum = max(race.lateness_ms, default=0.0)
        p95 = _percentile(race.lateness_ms, 0.95)
        return {
            "wall_elapsed": wall_elapsed, "simulation_elapsed": race.sim.elapsed,
            "drift_ms": drift_ms, "max_lateness_ms": maximum, "p95_lateness_ms": p95,
            "physics_hz": round(1 / DT), "physics_steps": race.sim.tick,
            "clock_mode": NATIVE_CLOCK_MODE if race.sleeper is not None else ASYNCIO_CLOCK_MODE,
            "pacing": {"native_sleeper_ready_ns": race.sleeper.ready_ns if race.sleeper else None,
                       "native_sleeper_thread_alive": race.sleeper.thread.is_alive() if race.sleeper else False},
            "diagnostics": race.diagnostics.snapshot(detail=diagnostics_detail),
            # A delayed run remains playable but cannot establish viability.
            "infrastructure_valid": maximum <= 100 and p95 <= 25 and abs(drift_ms) <= 100 and not (race.reason or "").startswith("runtime_error"),
            "validity_limits_ms": {"max_lateness": 100, "p95_lateness": 25, "absolute_drift": 100},
        }
