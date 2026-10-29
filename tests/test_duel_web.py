import asyncio
import json

import httpx
from fastmcp import Client

from mcpkart.bench import tool
from mcpkart.duel_web import create_app


async def test_actual_checkpoint_start_clock_episode_and_cleanup(tmp_path):
    from mcpkart.duel import DuelSimulation

    sim = DuelSimulation()
    for _ in range(60):
        sim.step()
    red = sim.karts["red"]
    red.x, red.y = sim.track.checkpoints[1][0] - .4, sim.track.checkpoints[1][1]
    red.s, red.offset, _ = sim.track.project(red.x, red.y)
    app = create_app(replay_root=tmp_path)
    runtime = app.state.race_runtime
    try:
        async with Client(app.state.mcp_server) as mcp:
            start = await tool(mcp, "start_duel", {"deadline": 1, "race_setup": {
                "checkpoint": sim.checkpoint(), "episode": {"racer_id": "red", "gate_credits": 1}
            }})
            assert start["drivers"]["red"]["observation"]["tick"] == 60
            ack = await tool(mcp, "drive_duel", {
                "race_id": start["race_id"], "racer_id": "red",
                "driver_token": start["drivers"]["red"]["driver_token"],
                "action_id": "straight_accelerate", "observation_tick": 60, "command_seq": 0,
            })
            assert ack["applied"] and ack["applied_tick"] >= 61
            await asyncio.sleep(.5)
            result = await tool(mcp, "finish_duel", {
                "race_id": start["race_id"], "owner_token": start["owner_token"]
            })
            assert result["reason"] == "episode_credited" and not result["summary"]["finished"]
            assert result["episode_origin"]["tick"] == 60
            assert result["timing"]["physics_steps"] < 50
            assert runtime._session is None
    finally:
        await runtime.close()


async def test_actual_mcp_tools_ownership_and_spectator_privacy(tmp_path):
    app = create_app(replay_root=tmp_path)
    runtime = app.state.race_runtime
    try:
        async with Client(app.state.mcp_server) as mcp:
            info = await tool(mcp, "runtime_info")
            assert info["mode"] == "duel"
            initial = await tool(mcp, "start_duel", {"deadline": 2})
            labels = {"red": "Jev · red", "blue": "OpenAI · blue"}
            telemetry = tmp_path / "live-status.json"
            telemetry.write_text(
                json.dumps({"race_id": initial["race_id"], "driver_labels": labels, "driver_metrics": {}})
            )

            async def drive(rid):
                return await tool(
                    mcp,
                    "drive_duel",
                    {
                        "race_id": initial["race_id"],
                        "racer_id": rid,
                        "driver_token": initial["drivers"][rid]["driver_token"],
                        "action_id": "straight_accelerate",
                        "observation_tick": 0,
                        "command_seq": 0,
                    },
                )

            red, blue = await asyncio.gather(*(drive(r) for r in ("red", "blue")))
            assert red["applied"] and blue["applied"]
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as web:
                page = await web.get("/")
                assert page.status_code == 200 and "HEAD TO HEAD" in page.text
                state = (await web.get("/api/state")).json()
                assert "driver_token" not in json.dumps(state) and "owner_token" not in json.dumps(state)
                assert (await web.get("/api/replay")).status_code == 409
            race = await tool(
                mcp, "finish_duel", {"race_id": initial["race_id"], "owner_token": initial["owner_token"]}
            )
            assert race["samples"][-1]["racers"]["red"]["kart"]["speed"] > 0
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as web:
                downloaded = (await web.get("/api/replay")).json()
                assert downloaded["driver_labels"] == labels
                assert "driver_token" not in json.dumps(downloaded)
                telemetry.write_text(json.dumps({"race_id": "different-race", "driver_labels": labels}))
                assert "driver_labels" not in (await web.get("/api/replay")).json()
    finally:
        await runtime.close()


def test_catalog_skips_bad_or_external_entries_and_supports_featured_replay(tmp_path):
    from mcpkart.duel import DuelSimulation
    from mcpkart.duel_web import DuelReplays

    sim = DuelSimulation()
    race = {"samples": [sim.state()], "track": sim.track.as_dict()}
    (tmp_path / "good.json").write_text(json.dumps(race))
    (tmp_path / "partial.json").write_text("{")
    entries = [
        {"file": "good.json", "label": "A recorded race", "featured": True},
        {"file": "missing.json", "label": "Missing"},
        {"file": "partial.json", "label": "Incomplete"},
        {"file": "../outside.json", "label": "Outside"},
        {"file": ["bad"], "label": "Malformed"},
    ]
    (tmp_path / "replays.json").write_text(json.dumps(entries))
    catalog = DuelReplays(tmp_path)
    catalog.warm()
    assert len(catalog.entries) == 1
    item = next(iter(catalog.entries.values()))
    assert item["featured"] and item["label"] == "A recorded race"
    assert json.loads(item["body"]) == race
    (tmp_path / "replays.json").write_text("{")
    catalog.warm()
    assert catalog.entries == {}


def test_queued_catalog_read_rechecks_clock_after_obtaining_lock(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from mcpkart.duel_web import DuelReplays

    busy, entered = [False], Event()
    catalog = DuelReplays(tmp_path, lambda: busy[0])
    catalog.entries = {"existing": {"label": "Preserve active cache"}}
    catalog.lock.acquire()

    def queued():
        entered.set()
        catalog.warm()

    with ThreadPoolExecutor(max_workers=1) as pool:
        work = pool.submit(queued)
        assert entered.wait(1)
        busy[0] = True
        catalog.lock.release()
        work.result(timeout=1)
    assert "existing" in catalog.entries
    catalog.warm(True)
    assert catalog.entries == {}
