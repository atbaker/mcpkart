"""Two-kart spectator and Streamable HTTP MCP server."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import re
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Lock

from fastmcp import FastMCP
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

from .duel_process import ProcessDuelRuntime


async def resolved(value):
    return await value if inspect.isawaitable(value) else value


class DuelReplays:
    """An explicit small manifest avoids scanning the historical artifact tree."""

    def __init__(self, root, busy=lambda: False):
        self.root = Path(root).resolve()
        self.entries = {}
        self.busy, self.lock = busy, Lock()

    def warm(self, force=False):
        # Admission waits for earlier catalog work; queued browser reads must
        # recheck the active clock after obtaining the lock.
        with self.lock:
            if not force and self.busy():
                return
            self._warm()

    def _warm(self):
        manifest = self.root / "replays.json"
        entries = {}
        try:
            items = json.loads(manifest.read_text())
        except (OSError, ValueError):
            items = []
        if isinstance(items, list):
            for item in items[:64]:
                if not isinstance(item, dict) or not all(
                    isinstance(item.get(k), str) for k in ("file", "label")
                ):
                    continue
                path = self.root / item["file"]
                if path.is_symlink() or not path.resolve().is_relative_to(self.root):
                    continue
                try:
                    if not path.is_file() or path.stat().st_size > 32 * 1024 * 1024:
                        continue
                    race = json.loads(path.read_text())
                    if (
                        not isinstance(race, dict)
                        or not race.get("samples")
                        or "racers" not in race["samples"][0]
                    ):
                        continue
                    body = JSONResponse(race).body
                except (OSError, ValueError, KeyError, TypeError):
                    continue
                identity = hashlib.sha256(item["file"].encode()).hexdigest()
                entries[identity] = {
                    "id": identity,
                    "label": item["label"],
                    "body": body,
                    "featured": item.get("featured") is True,
                }
        self.entries = entries


def create_app(runtime=None, replay_root=None, *, trio=False):
    runtime = runtime if runtime is not None else ProcessDuelRuntime(trio=trio)
    root = replay_root or Path(__file__).resolve().parents[2] / "artifacts" / "two-kart-session-v1"
    admitting = False
    mcp = FastMCP("MCP Kart — two-kart racing")

    def busy():
        return admitting or runtime.current is not None and runtime.current.status == "running"

    catalog = DuelReplays(root, busy)

    @mcp.tool
    async def start_duel(
        seed: int = 0, deadline: float = 240.0, label: str = "", race_setup: dict | None = None
    ) -> dict:
        """Start two karts on one realtime clock; return separate driver capabilities.

        Each driver uses its own racer_id/token, observations and increasing
        command_seq. Keep the owner token for stopping the entire duel.
        """
        nonlocal admitting
        if busy():
            raise ValueError("A duel is already running or being admitted")
        admitting = True
        try:
            await asyncio.to_thread(catalog.warm, True)
            return await resolved(
                runtime.start(seed=seed, deadline=deadline, label=label, race_setup=race_setup)
            )
        finally:
            admitting = False

    @mcp.tool
    async def runtime_info() -> dict:
        """Read Python shared-clock provenance without starting a race."""
        return runtime.runtime_info()

    @mcp.tool
    async def observe_duel(race_id: str, racer_id: str) -> dict:
        """Read the named racer's current kart, road and opponent measurements."""
        return await resolved(runtime.observe(race_id, racer_id))

    @mcp.tool
    async def drive_duel(
        race_id: str,
        racer_id: str,
        driver_token: str,
        action_id: str,
        observation_tick: int,
        command_seq: int,
    ) -> dict:
        """Apply a direct native input only to the capability's racer at a physics tick.

        The previous input remains held during inference. Rescue invalidates
        only that racer's older observations. No other racer's loop is blocked.
        """
        return await runtime.drive(race_id, racer_id, driver_token, action_id, observation_tick, command_seq)

    @mcp.tool
    async def finish_duel(race_id: str, owner_token: str, reason: str = "cancelled") -> dict:
        """Stop both racers and collect the complete shared-clock recording."""
        return await resolved(runtime.finish(race_id, reason=reason, owner_token=owner_token))

    app = mcp.http_app(path="/mcp", json_response=True, stateless_http=True)
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        async with original_lifespan(application):
            try:
                yield
            finally:
                await runtime.close()

    app.router.lifespan_context = lifespan

    async def index(request):
        page = Path(__file__).with_name("static") / "duel.html"
        return HTMLResponse(page.read_text(), headers={"Cache-Control": "no-store"})

    async def state(request):
        value = runtime.state()
        try:
            telemetry = json.loads((Path(root) / "live-status.json").read_text())
            if telemetry.get("race_id") == value.get("race_id"):
                value.update(
                    driver_labels=telemetry["driver_labels"], driver_metrics=telemetry["driver_metrics"]
                )
        except (OSError, ValueError, KeyError):
            pass
        return JSONResponse(value, headers={"Cache-Control": "no-store"})

    async def replay(request):
        if busy():
            return JSONResponse({"error": "Recording becomes available when the duel stops"}, status_code=409)
        if runtime.current is None:
            return JSONResponse({"error": "No duel yet"}, status_code=404)
        race = dict(await runtime.result())
        try:
            telemetry = json.loads((Path(root) / "live-status.json").read_text())
            if telemetry.get("race_id") == race.get("race_id"):
                race["driver_labels"] = telemetry["driver_labels"]
        except (OSError, ValueError, KeyError):
            pass
        return JSONResponse(race)

    async def replays(request):
        if not busy():
            await asyncio.to_thread(catalog.warm)
        return JSONResponse(
            {"replays": [{k: v for k, v in e.items() if k != "body"} for e in catalog.entries.values()]}
        )

    async def saved(request):
        identity = request.path_params["identity"]
        item = catalog.entries.get(identity) if re.fullmatch("[0-9a-f]{64}", identity) else None
        if item is None:
            return JSONResponse({"error": "Replay not found"}, status_code=404)
        return Response(item["body"], media_type="application/json")

    app.router.routes[0:0] = [
        Route("/", index),
        Route("/api/state", state),
        Route("/api/replay", replay),
        Route("/api/replays", replays),
        Route("/api/replays/{identity}", saved),
    ]
    app.state.race_runtime, app.state.mcp_server, app.state.start_duel = runtime, mcp, start_duel
    return app


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Two-kart Python race and spectator")
    parser.add_argument("--trio", action="store_true", help="Three ghost karts on the shared clock")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--replay-root", type=Path)
    args = parser.parse_args()
    uvicorn.run(create_app(replay_root=args.replay_root, trio=args.trio), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
