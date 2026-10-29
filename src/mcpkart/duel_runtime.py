"""Shared realtime duel clock; inference is outside this physics process."""

from __future__ import annotations

import asyncio
import gc
import math
import os
import resource
import secrets
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

from .duel import RACERS, DuelSimulation
from .runtime import ASYNCIO_CLOCK_MODE, RaceRuntime, TimingDiagnostics
from .sim import ACTIONS, DT


def worker_memory():
    """Report this exec's resident memory separately from inherited rusage."""
    resource_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result = {
        "cyclic_gc_enabled": gc.isenabled(),
        "maximum_duel_duration_s": 600,
        "current_rss_kib": None,
        "process_peak_rss_kib": None,
        "resource_peak_rss_kib": resource_peak / 1024 if sys.platform == "darwin" else resource_peak,
        "resource_peak_note": "Linux rusage may include the parent pre-exec high-water mark.",
        "measured_before_recording_transfer": True,
    }
    try:
        fields = {
            line.split(":", 1)[0]: line.split(":", 1)[1].strip()
            for line in Path("/proc/self/status").read_text().splitlines()
            if ":" in line
        }
        result.update(
            current_rss_kib=int(fields["VmRSS"].split()[0]),
            process_peak_rss_kib=int(fields["VmHWM"].split()[0]),
        )
    except (OSError, KeyError, ValueError):
        pass
    return result


@dataclass
class _DuelRace:
    race_id: str
    sim: DuelSimulation
    seed: int
    deadline: float
    label: str
    started_ns: int
    tokens: dict
    owner_token: str
    origin_tick: int = 0
    origin_elapsed: float = 0.0
    status: str = "running"
    reason: str | None = None
    finished_ns: int | None = None
    task: asyncio.Task | None = None
    pending: dict = field(default_factory=dict)
    last_command_seq: dict = field(default_factory=lambda: {r: -1 for r in RACERS})
    last_observed_ns: dict = field(default_factory=lambda: {r: None for r in RACERS})
    commands: list = field(default_factory=list)
    rejected_commands: list = field(default_factory=list)
    samples: list = field(default_factory=list)
    lateness_ms: list = field(default_factory=list)
    diagnostics: TimingDiagnostics = field(default_factory=TimingDiagnostics)
    sleeper: None = None


class DuelRuntime:
    def __init__(self, *, watchdog=False, native_sleeper=False):
        if native_sleeper:
            raise ValueError("Duel runtime uses asyncio pacing")
        self.current = None
        self.watchdog = watchdog
        self._preview = DuelSimulation()

    def runtime_info(self):
        return {
            "backend": "event_loop",
            "protocol_version": 2,
            "mode": "duel",
            "watchdog_enabled": self.watchdog,
            "clock_mode": ASYNCIO_CLOCK_MODE,
            "physics_hz": round(1 / DT),
            "process_pid": os.getpid(),
        }

    def start(self, seed=0, deadline=240.0, label="", reset_after_s=3.0, race_setup=None):
        if (
            isinstance(deadline, bool)
            or not isinstance(deadline, (int, float))
            or not math.isfinite(deadline)
            or not 0 < deadline <= 600
        ):
            raise ValueError("Duel deadline must be finite, positive and at most 600 seconds")
        if self.current is not None and self.current.status == "running":
            raise ValueError("A duel is already running")
        setup = dict(race_setup or {})
        if "reset_after_s" in setup and setup["reset_after_s"] != reset_after_s:
            raise ValueError("Conflicting rescue settings in checkpoint setup")
        setup.setdefault("reset_after_s", reset_after_s)
        sim = DuelSimulation(seed=seed, **setup)
        if sim.finished:
            raise ValueError("A finished checkpoint cannot start an active race")
        race = _DuelRace(
            uuid.uuid4().hex,
            sim,
            seed,
            float(deadline),
            label,
            time.monotonic_ns(),
            {r: secrets.token_urlsafe(24) for r in RACERS},
            secrets.token_urlsafe(24),
            origin_tick=sim.tick,
            origin_elapsed=sim.elapsed,
            diagnostics=TimingDiagnostics(watchdog_enabled=self.watchdog),
        )
        self.current = race
        race.diagnostics.start(race.started_ns)
        self._sample(race, race.started_ns, 0.0)
        race.task = asyncio.create_task(self._run(race), name=f"duel-{race.race_id}")

        def ended(task):
            if race.status == "running":
                self._end(race, "runtime_cancelled" if task.cancelled() else "runtime_error:task_ended")

        race.task.add_done_callback(ended)
        return {
            "race_id": race.race_id,
            "status": race.status,
            "started_ns": race.started_ns,
            "owner_token": race.owner_token,
            "drivers": {
                r: {
                    "racer_id": r,
                    "driver_token": race.tokens[r],
                    "observation": self.observe(race.race_id, r),
                }
                for r in RACERS
            },
        }

    def _require_race(self, race_id=None):
        if self.current is None:
            raise ValueError("No duel has started")
        if race_id is not None and race_id != self.current.race_id:
            raise ValueError("Stale race_id")
        return self.current

    def observe(self, race_id=None, racer_id=None):
        race = self._require_race(race_id)
        now = time.monotonic_ns()
        if racer_id is None:
            return {**race.sim.state(), "race_id": race.race_id, "status": race.status, "observed_ns": now}
        if racer_id not in RACERS:
            raise ValueError("Unknown racer")
        race.last_observed_ns[racer_id] = now
        return {
            **race.sim.observation(racer_id),
            "race_id": race.race_id,
            "racer_id": racer_id,
            "status": race.status,
            "observed_ns": now,
        }

    async def drive(self, race_id, racer_id, driver_token, action_id, observation_tick, command_seq):
        race = self._require_race(race_id)
        if (
            racer_id not in RACERS
            or not isinstance(driver_token, str)
            or not secrets.compare_digest(driver_token, race.tokens[racer_id])
        ):
            raise ValueError("Invalid racer control capability")
        if not isinstance(action_id, str) or action_id not in ACTIONS:
            raise ValueError("Unknown action_id")
        if isinstance(command_seq, bool) or not isinstance(command_seq, int) or command_seq < 0:
            raise ValueError("command_seq must be a nonnegative integer")
        if (
            isinstance(observation_tick, bool)
            or not isinstance(observation_tick, int)
            or not 0 <= observation_tick <= race.sim.tick
        ):
            raise ValueError("observation_tick must name an existing tick")
        record = {
            "race_id": race_id,
            "racer_id": racer_id,
            "action_id": action_id,
            "observation_tick": observation_tick,
            "command_seq": command_seq,
        }
        k = race.sim.karts[racer_id]
        if race.status != "running" or k.finished:
            return self._reject(race, record, "racer_finished" if k.finished else "race_already_ended")
        if command_seq <= race.last_command_seq[racer_id]:
            raise ValueError("Duplicate or out-of-order command_seq")
        if racer_id in race.pending:
            raise ValueError("Racer already has a pending command")
        if k.last_reset_tick is not None and observation_tick < k.last_reset_tick:
            return self._reject(race, record, "observation_before_rescue")
        record["queued_ns"] = time.monotonic_ns()
        future = asyncio.get_running_loop().create_future()
        race.pending[racer_id] = (record, future)
        return await asyncio.shield(future)

    def _reject(self, race, record, reason):
        rejected = {**record, "applied": False, "reason": reason}
        race.rejected_commands.append(rejected)
        return {**rejected, "observation": self.observe(race.race_id, record["racer_id"])}

    async def _run(self, race):
        accepted = {}
        try:
            while race.status == "running":
                target = race.started_ns + round((race.sim.tick - race.origin_tick + 1) * DT * 1e9)
                await asyncio.sleep(max(0.0, (target - time.monotonic_ns()) / 1e9))
                if race.status != "running":
                    break
                wake = time.monotonic_ns()
                late = max(0.0, (wake - target) / 1e6)
                race.diagnostics.wake(race.sim.tick + 1, wake, late)
                pending, race.pending = race.pending, {}
                reset_before = {r: race.sim.karts[r].last_reset_tick for r in RACERS}
                accepted = {}
                for rid, (record, future) in pending.items():
                    k = race.sim.karts[rid]
                    if (
                        k.finished
                        or reset_before[rid] is not None
                        and record["observation_tick"] < reset_before[rid]
                    ):
                        ack = self._reject(
                            race, record, "racer_finished" if k.finished else "observation_before_rescue"
                        )
                        if not future.done():
                            future.set_result(ack)
                    else:
                        race.sim.set_control(rid, record["action_id"])
                        accepted[rid] = record, future
                started, cpu = time.monotonic_ns(), time.process_time_ns()
                race.sim.step()
                race.diagnostics.span("physics_step", started, cpu)
                applied_ns = time.monotonic_ns()
                race.lateness_ms.append(late)
                self._sample(race, applied_ns, late)
                if race.sim.episode_outcome() is not None:
                    self._end(race, "episode_" + race.sim.episode_outcome())
                elif race.sim.finished:
                    self._end(race, "completed")
                elif race.sim.elapsed - race.origin_elapsed >= race.deadline:
                    self._end(race, "deadline")
                for rid, (record, future) in accepted.items():
                    race.last_command_seq[rid] = record["command_seq"]
                    record.update(
                        applied_ns=applied_ns,
                        applied_tick=race.sim.tick,
                        reset_during_step=race.sim.karts[rid].last_reset_tick != reset_before[rid],
                    )
                    race.commands.append(record)
                    if not future.done():
                        future.set_result(
                            {**record, "applied": True, "observation": self.observe(race.race_id, rid)}
                        )
        except asyncio.CancelledError:
            if race.status == "running":
                self._end(race, "runtime_cancelled")
            raise
        except Exception as error:  # noqa: BLE001
            self._end(race, f"runtime_error:{type(error).__name__}:{error}")
        finally:
            for record, future in accepted.values():
                if not future.done():
                    future.set_result(self._reject(race, record, "runtime_ended_before_ack"))

    def _sample(self, race, wall_ns, late):
        started, cpu = time.monotonic_ns(), time.process_time_ns()
        race.samples.append({**race.sim.state(), "wall_ns": wall_ns, "lateness_ms": late})
        race.diagnostics.span("physics_sample", started, cpu)

    def _end(self, race, reason):
        race.status = (
            "completed"
            if reason == "completed"
            else "failed"
            if reason == "deadline" or reason.startswith("runtime_error")
            else "stopped"
        )
        race.reason = reason
        race.finished_ns = time.monotonic_ns()
        race.diagnostics.stop()
        pending, race.pending = race.pending, {}
        for record, future in pending.values():
            if not future.done():
                future.set_result(self._reject(race, record, "race_already_ended"))

    def _timing(self, race, diagnostics_detail=False):
        proxy = SimpleNamespace(
            started_ns=race.started_ns, finished_ns=race.finished_ns, lateness_ms=race.lateness_ms,
            reason=race.reason, sleeper=race.sleeper, diagnostics=race.diagnostics,
            sim=SimpleNamespace(
                elapsed=race.sim.elapsed - race.origin_elapsed, tick=race.sim.tick - race.origin_tick
            ),
        )
        return RaceRuntime._timing(self, proxy, diagnostics_detail=diagnostics_detail)

    def finish(self, race_id=None, reason="cancelled", owner_token=None):
        race = self._require_race(race_id)
        if race.status == "running":
            if not isinstance(owner_token, str) or not secrets.compare_digest(owner_token, race.owner_token):
                raise ValueError("Invalid duel owner capability")
            self._end(race, reason)
            if race.task is not None:
                race.task.cancel()
        return self.result()

    def result(self):
        race = self._require_race()
        if race.status == "running":
            raise ValueError("Stop the duel before collecting its recording")
        timing = self._timing(race, diagnostics_detail=True)
        result = {
            "race_id": race.race_id,
            "seed": race.seed,
            "label": race.label,
            "status": race.status,
            "reason": race.reason,
            "deadline": race.deadline,
            "started_ns": race.started_ns,
            "finished_ns": race.finished_ns,
            "config": race.sim.config(),
            "track": race.sim.track.as_dict(),
            "summary": race.sim.summary(),
            "timing": timing,
            "runtime_info": self.runtime_info(),
            "samples": list(race.samples),
            "commands": list(race.commands),
            "rejected_commands": list(race.rejected_commands),
            "contacts": list(race.sim.contacts),
            "events": list(race.sim.events),
            "realtime_valid": timing["infrastructure_valid"],
            "worker_memory": worker_memory(),
        }
        if race.sim._checkpoint_input is not None:
            result["episode_origin"] = {"tick": race.origin_tick, "time_s": race.origin_elapsed}
        if race.sim.episode is not None:
            result["episode"] = {
                **race.sim.episode,
                "outcome": race.sim.episode_outcome() or race.reason,
            }
        return result

    def state(self):
        if self.current is None:
            return {
                "status": "idle",
                "track": self._preview.track.as_dict(),
                "config": self._preview.config(),
                "observation": self._preview.state(),
            }
        race = self.current
        result = {
            "race_id": race.race_id,
            "status": race.status,
            "reason": race.reason,
            "label": race.label,
            "observation": race.sim.state(),
            "track": race.sim.track.as_dict(),
            "timing": self._timing(race),
            "events": race.sim.events[-16:],
            "command_count": {r: race.last_command_seq[r] + 1 for r in RACERS},
            "pending": {r: r in race.pending for r in RACERS},
            "trail": {
                r: [
                    [s["racers"][r]["kart"]["x"], s["racers"][r]["kart"]["y"]]
                    for s in race.samples[-600::3]
                    if s["tick"] >= (race.sim.karts[r].last_reset_tick or 0)
                ]
                for r in RACERS
            },
        }
        if race.sim.episode is not None:
            result["episode"] = {**race.sim.episode, "outcome": race.sim.episode_outcome() or race.reason}
        return result

    def record_timing_span(self, name, started_ns, cpu_ns):
        if self.current is not None:
            self.current.diagnostics.span(name, started_ns, cpu_ns)

    async def close(self):
        race = self.current
        if race is not None:
            if race.status == "running":
                self._end(race, "server_shutdown")
            if race.task is not None:
                race.task.cancel()
                await asyncio.gather(race.task, return_exceptions=True)
