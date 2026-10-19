"""Optional standalone Rust worker; Python retains MCP and experiment tooling."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import threading
import time
import uuid
from dataclasses import asdict
from pathlib import Path

from .process_runtime import ProcessRaceRuntime, _Session
from .sim import DT, Simulation

RUST_CLOCK_MODE = "rust_fixed_step_wall_clock"


def simulation_fixture(sim: Simulation) -> dict:
    """Export full precision geometry/initial conditions; Rust does not reseed."""
    return {
        "track": {**vars(sim.track), "width": sim.track.width},
        "handling": asdict(sim.handling),
        "initial_state": {key: value for key, value in vars(sim).items() if key not in {"track", "handling"}},
        "config": sim.config(),
    }


class _JsonConnection:
    """Private framed JSON transport; send/recv run off the HTTP event loop."""

    def __init__(self) -> None:
        self.process: subprocess.Popen | None = None

    def send(self, message: dict) -> None:
        if self.process is None or self.process.stdin is None:
            raise EOFError("Rust worker input is closed")
        payload = json.dumps(message, separators=(",", ":"), allow_nan=False).encode()+b"\n"
        self.process.stdin.write(payload)
        self.process.stdin.flush()

    def recv(self) -> dict:
        if self.process is None or self.process.stdout is None:
            raise EOFError("Rust worker output is closed")
        line = self.process.stdout.readline(128*1024*1024)
        if not line:
            raise EOFError("Rust worker disconnected")
        if not line.endswith(b"\n"):
            raise RuntimeError("Rust worker exceeded the frame size limit")
        try:
            value = json.loads(line)
        except ValueError as exc:
            raise RuntimeError("Rust worker emitted invalid JSON") from exc
        if not isinstance(value, dict):
            raise RuntimeError("Rust worker protocol requires an object message")  # noqa: TRY004 — transport failure.
        return value

    def close(self) -> None:
        if self.process is not None:
            for stream in (self.process.stdin, self.process.stdout):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        # A crashed worker can break a buffered stdin flush.
                        # Still close stdout and let inherited cleanup finish.
                        pass


class _RustWorker:
    def __init__(self, binary: Path, session_id: str, connection: _JsonConnection, idle: dict) -> None:
        self.arguments = [str(binary), "--session", session_id]
        self.session_id, self.connection, self.idle = session_id, connection, idle
        self.process: subprocess.Popen | None = None

    @property
    def pid(self) -> int | None:
        return self.process.pid if self.process is not None else None

    def start(self) -> None:
        self.process = subprocess.Popen(self.arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        close_fds=True)
        self.connection.process = self.process
        self.connection.send({"session_id": self.session_id, "method": "initialize",
                              "arguments": {"idle": self.idle}})

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


class RustRaceRuntime(ProcessRaceRuntime):
    """Same race API and cleanup as Python, with an explicit native worker."""

    def __init__(self, *, binary: str | Path | None = None, watchdog: bool = False) -> None:
        if watchdog:
            raise ValueError("The Python watchdog is unavailable for the Rust engine")
        super().__init__()
        default = Path(__file__).resolve().parents[2]/"rust-race"/"target"/"release"/"mcpkart-race"
        self.binary = Path(binary or os.environ.get("MCPKART_RUST_WORKER", default)).resolve()
        if not self.binary.is_file() or not os.access(self.binary, os.X_OK):
            raise ValueError(f"Build the release Rust worker first; executable missing: {self.binary}")
        self._binary_sha256 = hashlib.sha256(self.binary.read_bytes()).hexdigest()

    def runtime_info(self) -> dict:
        return {"backend": "process", "engine": "rust", "protocol_version": 1,
                "watchdog_enabled": False, "clock_mode": RUST_CLOCK_MODE,
                "physics_hz": round(1/DT), "process_pid": os.getpid(),
                "worker_binary_sha256": self._binary_sha256}

    async def _spawn(self) -> _Session:
        # Pin the executable before starting. Rebuilds belong between batches.
        if hashlib.sha256(self.binary.read_bytes()).hexdigest() != self._binary_sha256:
            raise RuntimeError("Rust worker changed after server initialization; restart the server")
        loop = asyncio.get_running_loop()
        identity, connection = uuid.uuid4().hex, _JsonConnection()
        process = _RustWorker(self.binary, identity, connection, self._idle)
        session = _Session(identity, process, connection, loop, loop.create_future(), time.monotonic_ns(),
                           parent_spans=self._parent_spans)
        self._session = session
        starter = asyncio.create_task(asyncio.to_thread(process.start))
        try:
            await asyncio.shield(starter)
        except asyncio.CancelledError:
            await starter
            raise
        session.reader = threading.Thread(target=self._read, args=(session,), name="rust-parent-reader", daemon=True)
        session.reader.start()
        await asyncio.wait_for(asyncio.shield(session.ready), 20)
        if session.clock_mode != RUST_CLOCK_MODE:
            raise RuntimeError(f"Worker clock mode {session.clock_mode!r} differs from configured {RUST_CLOCK_MODE!r}")
        return session

    async def _rpc(self, method: str, arguments: dict | None = None, *, session: _Session | None = None):
        if method == "start":
            arguments = dict(arguments or {})
            sim = Simulation(seed=arguments.get("seed", 0), laps=3,
                             reset_after_s=arguments.get("reset_after_s", 3))
            arguments["fixture"] = simulation_fixture(sim)
        return await super()._rpc(method, arguments, session=session)

    def _decorate(self, value: dict, session: _Session) -> dict:
        result = super()._decorate(value, session)
        result["process_provenance"]["worker_binary_sha256"] = self._binary_sha256
        return result
