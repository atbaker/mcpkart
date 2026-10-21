"""Local spectator UI and actual Streamable HTTP MCP transport."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import re
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock
from typing import Any

from fastmcp import FastMCP
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

from .process_runtime import ProcessRaceRuntime
from .runtime import RaceRuntime
from .sim import ACTIONS, Simulation


class ReplayCatalog:
    """Read only recorded trials under artifacts; public IDs are opaque hashes."""

    def __init__(self, root: Path, busy: Callable[[], bool] = lambda: False) -> None:
        self.root = root.resolve()
        self._busy = busy
        self._checked_at = -10.0
        self._entries: dict[str, dict] = {}
        self._cache: dict[Path, tuple[int, int, dict | None]] = {}
        self._lock = Lock()

    @staticmethod
    def _encode_race(race: dict) -> bytes:
        return JSONResponse(race).body

    def _load_entry(self, path: Path, relative: Path, modified_ns: int) -> dict | None:
        report = json.loads(path.read_text())
        race = report.get("race", report) if isinstance(report, dict) else None
        if not isinstance(race, dict) or not isinstance(race.get("samples"), list) or not race["samples"] or not isinstance(race.get("track"), dict) or not race["track"].get("points") or not all(isinstance(s, dict) and isinstance(s.get("kart"), dict) and all(k in s["kart"] for k in ("x", "y", "heading", "speed")) and isinstance(s.get("time"), (float, int)) for s in race["samples"]):
            return None
        identity = hashlib.sha256(relative.as_posix().encode()).hexdigest()
        config = race.get("config") if isinstance(race.get("config"), dict) else {}
        clean = {key: race.get(key) for key in ("race_id", "seed", "label", "status", "reason", "summary", "timing", "track", "samples", "commands", "reset_events")}
        clean["config"] = {key: config.get(key) for key in ("version", "dt", "laps", "handling", "actions", "coordinates", "reset_after_s", "rescue")}
        return {"id": identity, "label": race.get("label") or relative.stem,
                "file": relative.as_posix(), "duration": race["samples"][-1]["time"],
                "finished": bool((race.get("summary") or {}).get("finished")) if isinstance(race.get("summary"), dict) else False,
                "modified_ns": modified_ns, "body": self._encode_race(clean)}

    def _refresh(self, force: bool = False) -> None:
        # Called only with _lock held. Recheck admission/racing here so work
        # queued while idle cannot begin parsing after the race is admitted.
        if not force and self._busy():
            return
        now = time.monotonic()
        if not force and now - self._checked_at < 5:
            return
        self._checked_at = now
        entries = {}
        for path in self.root.rglob("*.json"):
            relative = path.relative_to(self.root)
            if any(part.startswith(".") for part in relative.parts):
                continue
            if any(word in path.stem.lower() for word in ("budget", "routes", "latency", "summary")) or path.name == "reference.json":
                continue
            # Never follow links out of (or within) the artifacts tree.
            if path.is_symlink() or path.resolve() != path.absolute():
                continue
            try:
                stat = path.stat()
                if not path.is_file() or stat.st_size > 32 * 1024 * 1024:
                    continue
                cached = self._cache.get(path)
                if cached is not None and cached[:2] == (stat.st_mtime_ns, stat.st_size):
                    entry = cached[2]
                else:
                    entry = self._load_entry(path, relative, stat.st_mtime_ns)
                    self._cache[path] = (stat.st_mtime_ns, stat.st_size, entry)
                if entry is None:
                    continue
                entries[entry["id"]] = entry
            except (OSError, ValueError, TypeError, KeyError):
                # Writers may be between truncation and completion. Retry after
                # the next refresh; partial JSON never appears as a replay.
                continue
        self._entries = entries

    def list(self) -> list[dict]:
        with self._lock:
            self._refresh()
            return [{key: value for key, value in entry.items() if key != "body"}
                    for entry in sorted(self._entries.values(), key=lambda entry: entry["modified_ns"], reverse=True)]

    def get(self, identity: str) -> bytes | None:
        if not re.fullmatch(r"[0-9a-f]{64}", identity):
            return None
        with self._lock:
            self._refresh()
            entry = self._entries.get(identity)
            return None if entry is None else entry["body"]

    def warm(self) -> None:
        """Wait for prior catalog work, then prepare every body before race time."""
        with self._lock:
            self._refresh(force=True)


async def _resolved(value):
    """The inline diagnostic backend is synchronous; process RPCs are async."""
    return await value if inspect.isawaitable(value) else value


def create_app(runtime: RaceRuntime | ProcessRaceRuntime | None = None, replay_root: Path | None = None):
    runtime = runtime if runtime is not None else ProcessRaceRuntime()
    admitting = False

    def replay_busy() -> bool:
        return admitting or (runtime.current is not None and runtime.current.status == "running")

    catalog = ReplayCatalog(replay_root or Path(__file__).resolve().parents[2] / "artifacts", busy=replay_busy)
    mcp = FastMCP("MCP Kart — realtime driving laboratory")

    async def admit_race(seed: int = 0, deadline: float = 120.0, label: str = "", reset_after_s: float | None = 3.0,
                         race_setup: dict | None = None) -> dict[str, Any]:
        """Start a solo three-lap race. Physics runs continuously at 60 Hz.

        Returns the first observation. Call drive with its race_id and tick,
        increasing command_seq for every accepted input. deadline is seconds.
        reset_after_s rescues the kart after this long continuously off road;
        use null to disable rescue. Race time and progress never rewind.
        """
        nonlocal admitting
        if replay_busy():
            raise ValueError("A race is already running or being admitted")
        # Set this before the first await: both already-queued browser work and
        # concurrent start requests must observe admission before taking _lock.
        admitting = True
        try:
            await asyncio.to_thread(catalog.warm)
            return await _resolved(runtime.start(seed=seed, deadline=deadline, label=label, reset_after_s=reset_after_s,
                                                 **({"race_setup": race_setup} if race_setup else {})))
        finally:
            admitting = False

    mcp.tool(admit_race, name="start_race")

    @mcp.tool
    async def runtime_info() -> dict[str, Any]:
        """Return backend/configuration provenance; this does not start a race."""
        return runtime.runtime_info()

    @mcp.tool
    async def observe(race_id: str | None = None) -> dict[str, Any]:
        """Read current kart telemetry and nearby road geometry without pausing time."""
        return await _resolved(runtime.observe(race_id))

    @mcp.tool
    async def drive(race_id: str, action_id: str, observation_tick: int, command_seq: int) -> dict[str, Any]:
        """Apply one direct action at the next physics step; return actual application time.

        The action persists until replaced. This call acknowledges after physics
        uses the input, and includes a fresh observation. Stale race identities,
        duplicate command sequences, and future observations are rejected.
        """
        return await runtime.drive(race_id, action_id, observation_tick, command_seq)

    @mcp.tool
    async def finish_race(race_id: str | None = None, reason: str = "cancelled") -> dict[str, Any]:
        """Close the trial and return its summary, timing evidence, inputs, and replay samples.

        Completed and expired trials can be collected with this tool as well.
        Closing prevents later replies from controlling a subsequent race.
        """
        return await _resolved(runtime.finish(race_id, reason))

    # Use the installed FastMCP transport and lifespan directly; this is not a
    # REST imitation of MCP. Stateless HTTP avoids dangling per-race sessions.
    app = mcp.http_app(path="/mcp", json_response=True, stateless_http=True)
    mcp_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        async with mcp_lifespan(application):
            try:
                yield
            finally:
                await runtime.close()

    app.router.lifespan_context = lifespan
    page = Path(__file__).with_name("static") / "index.html"

    async def index(request):
        return HTMLResponse(page.read_text(), headers={"Cache-Control": "no-store"})

    async def state(request):
        value = runtime.state()
        started_ns, cpu_ns = time.monotonic_ns(), time.process_time_ns()
        try:
            return JSONResponse(value, headers={"Cache-Control": "no-store"})
        finally:
            runtime.record_timing_span("state_json_encoding", started_ns, cpu_ns)

    async def config(request):
        sim = Simulation(seed=0, laps=3)
        return JSONResponse({"simulation": sim.config(), "track": sim.track.as_dict(), "actions": ACTIONS,
                             "runtime_info": runtime.runtime_info()})

    async def replay(request):
        if replay_busy():
            return JSONResponse({"error": "Current trial download is available after the race ends; saved replays remain available"}, status_code=409)
        if runtime.current is None:
            return JSONResponse({"error": "No race has started"}, status_code=404)
        result = await _resolved(runtime.result())
        return JSONResponse(result, headers={"Content-Disposition": f'attachment; filename="mcpkart-{result["race_id"]}.json"', "Cache-Control": "no-store"})

    async def replays(request):
        return JSONResponse({"replays": await asyncio.to_thread(catalog.list)}, headers={"Cache-Control": "no-store"})

    async def recorded_replay(request):
        recording = await asyncio.to_thread(catalog.get, request.path_params["identity"])
        if recording is None:
            return JSONResponse({"error": "Replay not found"}, status_code=404)
        return Response(recording, media_type="application/json", headers={"Cache-Control": "no-store"})

    app.router.routes[0:0] = [
        Route("/", index), Route("/api/state", state), Route("/api/config", config),
        Route("/api/replay", replay), Route("/api/replays", replays),
        Route("/api/replays/{identity}", recorded_replay),
    ]
    app.state.race_runtime = runtime
    app.state.mcp_server = mcp
    app.state.replay_catalog = catalog
    app.state.start_race = admit_race
    return app


app = create_app()


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="MCP Kart local race server and spectator view")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--watchdog", action="store_true", help="Capture bounded event-loop thread stacks during physics stalls")
    parser.add_argument("--clock-backend", choices=("process", "event_loop"), default="process",
                        help="Process isolates physics from HTTP; event_loop retains the original diagnostic backend")
    parser.add_argument("--clock-pacing", choices=("asyncio", "native"), default="asyncio",
                        help="Native sleeper pacing is experimental; neither pacing mode has established reliable local timing")
    parser.add_argument("--race-engine", choices=("python", "rust"), default="python")
    parser.add_argument("--rust-worker", help="Path to a prebuilt release Rust race worker")
    args = parser.parse_args()
    if args.race_engine == "rust":
        if args.clock_backend != "process" or args.clock_pacing != "asyncio":
            parser.error("Rust uses its own process clock; do not select Python pacing overrides")
        from .rust_runtime import RustRaceRuntime

        runtime = RustRaceRuntime(binary=args.rust_worker, watchdog=args.watchdog)
    else:
        runtime_type = ProcessRaceRuntime if args.clock_backend == "process" else RaceRuntime
        runtime = runtime_type(watchdog=args.watchdog, native_sleeper=args.clock_pacing == "native")
    application = create_app(runtime=runtime)
    uvicorn.run(application, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
