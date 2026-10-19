"""Process-isolated physics with lossless RPC and coalesced spectator snapshots.

The child imports no web or MCP framework. Its asyncio loop never writes a
pipe: a separate writer owns serialization/backpressure, and only compact state
is published while the physics clock runs. Full recordings leave after stop.
"""

from __future__ import annotations

import asyncio
import multiprocessing as mp
import os
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .runtime import ASYNCIO_CLOCK_MODE, NATIVE_CLOCK_MODE, RaceRuntime
from .sim import ACTIONS, DT, Simulation


class _Outbox:
    def __init__(self, connection, session_id: str) -> None:
        self.connection, self.session_id = connection, session_id
        self.condition = threading.Condition()
        self.replies: deque[dict] = deque()
        self.latest: dict | None = None
        self.closed = False
        self.failed = threading.Event()

    def reply(self, value: dict) -> None:
        with self.condition:
            if len(self.replies) >= 128:
                self.failed.set()
                raise RuntimeError("Worker RPC reply queue exhausted")
            self.replies.append({**value, "session_id": self.session_id})
            self.condition.notify()

    def publish(self, state: dict) -> None:
        with self.condition:
            self.latest = {"type": "state", "session_id": self.session_id,
                           "captured_ns": time.monotonic_ns(), "state": state}
            self.condition.notify()

    def run(self) -> None:
        try:
            while True:
                with self.condition:
                    self.condition.wait_for(lambda: self.replies or self.latest is not None or self.closed)
                    if self.replies:
                        value = self.replies.popleft()
                    elif self.latest is not None:
                        value, self.latest = self.latest, None
                    else:
                        return
                # Never hold the publication lock across serialization/write.
                self.connection.send(value)
        except (OSError, EOFError):
            self.failed.set()

    def close(self) -> None:
        with self.condition:
            self.closed = True
            self.condition.notify()


async def _worker_loop(connection, session_id: str, watchdog: bool, native_sleeper: bool) -> None:
    runtime = RaceRuntime(watchdog=watchdog, native_sleeper=native_sleeper)
    # Initialize the immutable track/handling and interpreter paths before any
    # race epoch. HTTP/MCP/application metadata is absent from this process.
    preview = runtime.state()
    loop = asyncio.get_running_loop()
    stopping = asyncio.Event()
    outbox = _Outbox(connection, session_id)
    writer = threading.Thread(target=outbox.run, name="kart-ipc-writer", daemon=True)
    writer.start()
    tasks: set[asyncio.Task] = set()

    async def request(message: dict) -> None:
        if message.get("session_id") != session_id:
            return
        identity, method = message["id"], message["method"]
        try:
            arguments = message.get("arguments", {})
            if method == "start":
                value = runtime.start(**arguments)
            elif method == "observe":
                value = runtime.observe(**arguments)
            elif method == "drive":
                value = await runtime.drive(**arguments)
            elif method == "finish":
                value = runtime.finish(**arguments)
            elif method == "result":
                if runtime.current is not None and runtime.current.status == "running":
                    raise ValueError("Stop the race before transferring its full recording")
                value = runtime.result()
            elif method == "shutdown":
                await runtime.close()
                value = {"closed": True}
            else:
                raise ValueError(f"Unknown worker method: {method}")
            reply = {"type": "reply", "id": identity, "ok": True, "value": value}
            if method in {"start", "finish", "result"}:
                reply.update(state=runtime.state(), captured_ns=time.monotonic_ns())
            if method in {"finish", "result"}:
                reply["terminal_observation"] = runtime.observe()
            outbox.reply(reply)
        except Exception as exc:  # noqa: BLE001 — propagate worker errors to their RPC caller.
            outbox.reply({"type": "reply", "id": identity, "ok": False,
                          "error_type": type(exc).__name__, "error": str(exc)})
        finally:
            if method == "shutdown":
                stopping.set()

    def dispatch(message: dict) -> None:
        task = asyncio.create_task(request(message))
        tasks.add(task)
        task.add_done_callback(tasks.discard)

    def read() -> None:
        try:
            while True:
                message = connection.recv()
                loop.call_soon_threadsafe(dispatch, message)
        except (OSError, EOFError, RuntimeError):
            try:
                loop.call_soon_threadsafe(stopping.set)
            except RuntimeError:
                pass

    reader = threading.Thread(target=read, name="kart-ipc-reader", daemon=True)
    reader.start()
    main = sys.modules.get("__main__")
    entrypoint = getattr(getattr(main, "__spec__", None), "name", None)
    outbox.reply({"type": "ready", "pid": os.getpid(), "ready_ns": time.monotonic_ns(), "state": preview,
                  "entrypoint": entrypoint,
                  "clock_mode": runtime.runtime_info()["clock_mode"],
                  "web_modules_loaded": [name for name in ("fastmcp", "starlette", "uvicorn") if name in sys.modules]})

    async def publish() -> None:
        while not stopping.is_set():
            if outbox.failed.is_set():
                stopping.set()
                break
            outbox.publish(runtime.state())
            await asyncio.sleep(.05)

    publisher = asyncio.create_task(publish())
    try:
        await stopping.wait()
    finally:
        await runtime.close()
        publisher.cancel()
        await asyncio.gather(publisher, return_exceptions=True)
        for task in list(tasks):
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        outbox.close()
        # This happens after physics stops. A non-reading parent cannot hold up
        # an active clock, and the parent's shutdown path can terminate us.
        await asyncio.to_thread(writer.join, 2)
        connection.close()


def _worker(connection, session_id: str, watchdog: bool, native_sleeper: bool = False) -> None:
    try:
        asyncio.run(_worker_loop(connection, session_id, watchdog, native_sleeper))
    finally:
        connection.close()


class _WorkerProcess:
    """Fresh Python entrypoint; never reexecute the web server's __main__.

    multiprocessing's spawn preparation imports its caller's main module, which
    would load FastMCP for ``python -m mcpkart.web``. Explicit exec keeps the
    child module graph minimal on both supported targets: macOS and Linux.
    """

    def __init__(self, fd: int, session_id: str, watchdog: bool, native_sleeper: bool) -> None:
        self.arguments = [sys.executable, "-m", "mcpkart.physics_worker", "--worker-fd", str(fd), "--session", session_id]
        if watchdog:
            self.arguments.append("--watchdog")
        if native_sleeper:
            self.arguments.append("--native-sleeper")
        self.fd = fd
        self.process: subprocess.Popen | None = None

    @property
    def pid(self) -> int | None:
        return self.process.pid if self.process is not None else None

    def start(self) -> None:
        self.process = subprocess.Popen(self.arguments, pass_fds=(self.fd,), close_fds=True)

    def is_alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def join(self, timeout: float) -> None:
        if self.process is not None:
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                pass

    def terminate(self) -> None:
        if self.process is not None:
            self.process.terminate()

    def kill(self) -> None:
        if self.process is not None:
            self.process.kill()


@dataclass
class RaceProxy:
    race_id: str
    status: str


@dataclass
class _Session:
    identity: str
    process: Any
    connection: Any
    loop: asyncio.AbstractEventLoop
    ready: asyncio.Future
    created_ns: int
    pending: dict[int, asyncio.Future] = field(default_factory=dict)
    next_id: int = 0
    reader: threading.Thread | None = None
    error: str | None = None
    closing: bool = False
    ready_ns: int | None = None
    web_modules_loaded: list[str] = field(default_factory=list)
    entrypoint: str | None = None
    clock_mode: str | None = None
    snapshot_lock: threading.Lock = field(default_factory=threading.Lock)
    latest: dict | None = None
    snapshot_scheduled: bool = False
    send_lock: threading.Lock = field(default_factory=threading.Lock)
    parent_spans: dict[str, dict] = field(default_factory=dict)
    shutdown_task: asyncio.Task | None = None
    closed: bool = False


class ProcessRaceRuntime:
    """Async race commands; synchronous spectator reads use complete cached state."""

    def __init__(self, *, watchdog: bool = False, native_sleeper: bool = False) -> None:
        self.watchdog = watchdog
        self.native_sleeper = native_sleeper
        self.current: RaceProxy | None = None
        self._session: _Session | None = None
        self._snapshot: dict | None = None
        self._snapshot_ns: int | None = None
        self._result: dict | None = None
        self._starting = False
        self._worker_error: str | None = None
        self._terminal_observation: dict | None = None
        self._parent_spans: dict[str, dict] = {}
        self._rpc_slots = asyncio.Semaphore(32)
        preview = Simulation()
        self._idle = {"status": "idle", "track": preview.track.as_dict(), "actions": ACTIONS, "config": preview.config()}

    def runtime_info(self) -> dict:
        return {"backend": "process", "protocol_version": 1, "watchdog_enabled": self.watchdog,
                "clock_mode": NATIVE_CLOCK_MODE if self.native_sleeper else ASYNCIO_CLOCK_MODE,
                "physics_hz": round(1/DT), "process_pid": os.getpid()}

    async def start(self, seed: int = 0, deadline: float = 120, label: str = "",
                    reset_after_s: float | None = 3) -> dict:
        if self._starting or (self.current is not None and self.current.status == "running"):
            raise ValueError("A race is already running or being admitted")
        self._starting = True
        try:
            await self._shutdown(session=self._session)
            self._result = None
            self._worker_error = None
            self._terminal_observation = None
            self._parent_spans = {}
            session = await self._spawn()
            value = await self._rpc("start", {"seed": seed, "deadline": deadline, "label": label,
                                               "reset_after_s": reset_after_s}, session=session)
            if self.current is None or self.current.race_id != value["race_id"]:
                self.current = RaceProxy(value["race_id"], value["status"])
            return value
        except BaseException:
            await self._shutdown(session=self._session)
            raise
        finally:
            self._starting = False

    async def observe(self, race_id: str | None = None) -> dict:
        self._check_race(race_id)
        if self._session is None:
            if self._result is None:
                raise ValueError("No race has started")
            return {**self._terminal_observation, "worker_closed": True}
        return await self._rpc("observe", {"race_id": race_id})

    async def drive(self, race_id: str, action_id: str, observation_tick: int, command_seq: int) -> dict:
        self._check_race(race_id)
        if self._result is not None:
            return {"race_id": race_id, "action_id": action_id, "command_seq": command_seq,
                    "applied": False, "reason": "race_already_ended", "observation": await self.observe(race_id)}
        return await self._rpc("drive", {"race_id": race_id, "action_id": action_id,
                                          "observation_tick": observation_tick, "command_seq": command_seq})

    async def finish(self, race_id: str | None = None, reason: str = "cancelled") -> dict:
        self._check_race(race_id)
        if self._result is not None:
            return self._result
        session = self._session
        try:
            value = await self._rpc("finish", {"race_id": race_id, "reason": reason}, session=session)
            result = self._decorate(value, session)
            if self._session is session:
                self._result = result
            return result
        finally:
            await self._shutdown(session=session)

    async def result(self) -> dict:
        if self._starting:
            raise ValueError("A race is being admitted; wait for start_race to return")
        if self._result is not None:
            return self._result
        session = self._session
        try:
            value = await self._rpc("result", session=session)
        except ValueError:
            # An active-race collection is refused without disturbing its clock.
            raise
        except BaseException:
            await self._shutdown(session=session)
            raise
        result = self._decorate(value, session)
        if self._session is session:
            self._result = result
        await self._shutdown(session=session)
        return result

    def state(self) -> dict:
        if self._snapshot is None:
            return {**self._idle, "status": "admitting" if self._starting else "idle", "runtime_info": self.runtime_info(),
                    "snapshot_age_ms": None}
        state = dict(self._snapshot)
        state["runtime_info"] = self.runtime_info()
        state["snapshot_age_ms"] = (time.monotonic_ns()-self._snapshot_ns)/1e6 if self._snapshot_ns else None
        if self._worker_error is not None:
            state.update(status="failed", reason="worker_disconnected")
            state["timing"] = {**state.get("timing", {}), "infrastructure_valid": False}
        return state

    def record_timing_span(self, name: str, started_ns: int, started_cpu_ns: int) -> None:
        if self.current is None or self.current.status != "running":
            return
        wall_ms = (time.monotonic_ns()-started_ns)/1e6
        cpu_ms = (time.process_time_ns()-started_cpu_ns)/1e6
        span = self._parent_spans.setdefault(name, {"count": 0, "max_ms": 0.0, "max_process_cpu_ms": 0.0})
        span["count"] += 1
        span["max_ms"] = max(span["max_ms"], wall_ms)
        span["max_process_cpu_ms"] = max(span["max_process_cpu_ms"], cpu_ms)

    async def close(self) -> None:
        session, current = self._session, self.current
        await self._shutdown(session=session)
        if (current is not None and self.current is not None and self.current.race_id == current.race_id
                and self.current.status == "running" and self._session in (None, session)):
            self.current.status = "stopped"

    def _check_race(self, race_id: str | None) -> None:
        if self._starting:
            raise ValueError("A race is being admitted; wait for start_race to return")
        if self.current is None:
            raise ValueError("No race has started")
        if race_id is not None and race_id != self.current.race_id:
            raise ValueError("Stale race_id; the command belongs to a different race")

    async def _spawn(self) -> _Session:
        loop = asyncio.get_running_loop()
        context = mp.get_context("spawn")
        connection, child = context.Pipe()
        identity = uuid.uuid4().hex
        native_sleeper = self.native_sleeper
        expected_clock_mode = NATIVE_CLOCK_MODE if native_sleeper else ASYNCIO_CLOCK_MODE
        process = _WorkerProcess(child.fileno(), identity, self.watchdog, native_sleeper)
        session = _Session(identity, process, connection, loop, loop.create_future(), time.monotonic_ns(),
                           parent_spans=self._parent_spans)
        self._session = session
        try:
            starter = asyncio.create_task(asyncio.to_thread(process.start))
            try:
                await asyncio.shield(starter)
            except asyncio.CancelledError:
                # A cancelled spawn still has to finish obtaining its PID so
                # the outer cleanup can join/terminate the real child.
                await starter
                raise
            child.close()
            session.reader = threading.Thread(target=self._read, args=(session,), name="kart-parent-reader", daemon=True)
            session.reader.start()
            await asyncio.wait_for(asyncio.shield(session.ready), 20)
            if session.clock_mode != expected_clock_mode:
                raise RuntimeError(f"Worker clock mode {session.clock_mode!r} differs from configured {expected_clock_mode!r}")
            return session
        finally:
            child.close()

    def _read(self, session: _Session) -> None:
        try:
            while True:
                message = session.connection.recv()
                if message.get("session_id") != session.identity:
                    continue
                if message["type"] == "state":
                    with session.snapshot_lock:
                        session.latest = message
                        if session.snapshot_scheduled:
                            continue
                        session.snapshot_scheduled = True
                    session.loop.call_soon_threadsafe(self._consume_snapshot, session)
                else:
                    session.loop.call_soon_threadsafe(self._message, session, message)
        except (OSError, EOFError, RuntimeError):
            try:
                session.loop.call_soon_threadsafe(self._disconnected, session)
            except RuntimeError:
                pass

    def _consume_snapshot(self, session: _Session) -> None:
        with session.snapshot_lock:
            message, session.latest = session.latest, None
            session.snapshot_scheduled = False
        if self._session is session and message is not None:
            self._set_snapshot(message["state"], message["captured_ns"])

    def _set_snapshot(self, state: dict, captured_ns: int) -> None:
        if self._snapshot_ns is not None and captured_ns < self._snapshot_ns:
            return
        self._snapshot, self._snapshot_ns = state, captured_ns
        if state.get("race_id"):
            self.current = RaceProxy(state["race_id"], state["status"])

    def _message(self, session: _Session, message: dict) -> None:
        if self._session is not session:
            return
        if "state" in message:
            self._set_snapshot(message["state"], message.get("captured_ns", message.get("ready_ns")))
        if "terminal_observation" in message:
            self._terminal_observation = message["terminal_observation"]
        if message["type"] == "ready":
            session.ready_ns = message["ready_ns"]
            session.web_modules_loaded = message["web_modules_loaded"]
            session.entrypoint = message["entrypoint"]
            session.clock_mode = message["clock_mode"]
            if not session.ready.done():
                session.ready.set_result(None)
            return
        future = session.pending.get(message["id"])
        if future is None or future.done():
            return
        if message["ok"]:
            future.set_result(message["value"])
        else:
            kind = ValueError if message.get("error_type") == "ValueError" else RuntimeError
            future.set_exception(kind(message.get("error", "Race worker failed")))

    def _disconnected(self, session: _Session) -> None:
        if session.closing:
            return
        session.error = "Race worker disconnected"
        for future in [session.ready, *session.pending.values()]:
            if not future.done():
                future.set_exception(RuntimeError(session.error))
        if self._session is session and self.current is not None:
            self.current.status = "failed"
            self._worker_error = session.error

    async def _rpc(self, method: str, arguments: dict | None = None, *, session: _Session | None = None) -> Any:
        session = session or self._session
        if session is None or session.error or session.closed:
            raise RuntimeError(session.error or "Race worker closed" if session else "No race worker is running")
        async with self._rpc_slots:
            identity = session.next_id
            session.next_id += 1
            future = session.loop.create_future()
            session.pending[identity] = future
            try:
                # Parent IO is off the HTTP loop too. The child's dedicated
                # reader can drain requests regardless of model request timing.
                message = {"session_id": session.identity, "id": identity, "method": method, "arguments": arguments or {}}

                def send():
                    with session.send_lock:
                        session.connection.send(message)

                await asyncio.to_thread(send)
                return await asyncio.wait_for(asyncio.shield(future), 20)
            finally:
                session.pending.pop(identity, None)
                if not future.done():
                    future.cancel()

    def _decorate(self, value: dict, session: _Session) -> dict:
        provenance = {"child_pid": session.process.pid, "parent_pid": os.getpid(), "session_id": session.identity,
                      "start_method": "subprocess_exec", "worker_module": session.entrypoint,
                      "child_clock_mode": session.clock_mode,
                      "child_web_modules_loaded": session.web_modules_loaded, "worker_created_ns": session.created_ns,
                      "worker_ready_ns": session.ready_ns, "clock_started_ns": value.get("started_ns")}
        return {**value, "runtime_info": self.runtime_info(), "process_provenance": provenance,
                "timing": {**value["timing"], "backend": "process", "process_provenance": provenance,
                           "parent_http_spans": {key: dict(span) for key, span in session.parent_spans.items()}}}

    async def _shutdown(self, *, session: _Session | None) -> None:
        if session is None:
            return
        # All callers collecting this worker share one cleanup. In particular,
        # an old collection resuming after a new start must never pick up the
        # replacement worker from self._session.
        if session.shutdown_task is None:
            session.closing = True
            session.shutdown_task = asyncio.create_task(self._shutdown_session(session))
        try:
            await asyncio.shield(session.shutdown_task)
        except asyncio.CancelledError:
            await session.shutdown_task
            raise

    async def _shutdown_session(self, session: _Session) -> None:
        try:
            if session.process.pid is not None and session.process.is_alive() and session.error is None:
                try:
                    await asyncio.wait_for(self._rpc("shutdown", session=session), 3)
                except (TimeoutError, OSError, RuntimeError):
                    pass
            if session.process.pid is not None:
                await asyncio.to_thread(session.process.join, 2)
                if session.process.is_alive():
                    session.process.terminate()
                    await asyncio.to_thread(session.process.join, 2)
                if session.process.is_alive():
                    session.process.kill()
                    await asyncio.to_thread(session.process.join, 2)
        finally:
            session.connection.close()
            if session.reader is not None:
                await asyncio.to_thread(session.reader.join, .2)
            if not session.ready.done():
                session.ready.cancel()
            for future in session.pending.values():
                if not future.done():
                    future.set_exception(RuntimeError("Race worker closed"))
            session.closed = True
            if self._session is session:
                self._session = None
