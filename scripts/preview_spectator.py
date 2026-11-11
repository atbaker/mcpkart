"""Serve the current spectator UI over a read-only feed from an existing server.

For the qualified AWS demo, keep its SSM forward on 17773 and run:
    python scripts/preview_spectator.py
Then open http://127.0.0.1:17774/. No game worker is started.
"""

import argparse
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

PAGE = Path(__file__).resolve().parents[1] / "src/mcpkart/static/duel.html"
DEMO_SEATS = {"red": "Jev", "blue": "OpenAI Decisions", "green": "Clef"}


def create_app(upstream):
    @asynccontextmanager
    async def lifespan(app):
        async with httpx.AsyncClient(base_url=upstream, timeout=10, trust_env=False) as client:
            app.state.upstream = client
            yield

    async def index(request):
        return HTMLResponse(PAGE.read_text(), headers={"Cache-Control": "no-store"})

    async def feed(request):
        try:
            result = await request.app.state.upstream.get(request.url.path)
        except httpx.HTTPError:
            return JSONResponse({"error": "Spectator feed unavailable"}, status_code=502)
        if request.url.path == "/api/state" and result.is_success:
            value = result.json()
            # Clock controls have no model telemetry. Name the demo seats while
            # explicitly identifying their scripted drivers; never reuse stale
            # labels from a previous race or modify the qualified server.
            racers = value.get("observation", {}).get("racers", {})
            if value.get("label", "").startswith("FREE ") and set(racers) == set(DEMO_SEATS):
                supplied = value.get("driver_labels") or {}
                value["driver_labels"] = {
                    rid: supplied.get(rid) or f"{name} · scripted"
                    for rid, name in DEMO_SEATS.items()
                }
            return JSONResponse(value, headers={"Cache-Control": "no-store"})
        return Response(result.content, status_code=result.status_code,
                        media_type="application/json", headers={"Cache-Control": "no-store"})

    return Starlette(lifespan=lifespan, routes=[
        Route("/", index), Route("/api/state", feed), Route("/api/replay", feed),
        Route("/api/replays", feed), Route("/api/replays/{identity}", feed),
    ])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", default="http://127.0.0.1:17773")
    parser.add_argument("--port", type=int, default=17774)
    args = parser.parse_args()
    uvicorn.run(create_app(args.upstream), host="127.0.0.1", port=args.port, access_log=False)
