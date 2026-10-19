"""MCP/HTTP integration of asynchronous isolated-race operations."""

import asyncio
import os
import time

import httpx
import pytest
from fastmcp import Client

from mcpkart.bench import tool
from mcpkart.process_runtime import ProcessRaceRuntime
from mcpkart.runtime import RaceRuntime
from mcpkart.web import create_app


@pytest.mark.asyncio
@pytest.mark.parametrize("runtime_type,backend", [(RaceRuntime, "event_loop"), (ProcessRaceRuntime, "process")])
@pytest.mark.parametrize("native_sleeper", [False, True])
async def test_runtime_provenance_is_available_without_starting_a_race(tmp_path, runtime_type, backend, native_sleeper):
    runtime = runtime_type(native_sleeper=native_sleeper)
    app = create_app(runtime=runtime, replay_root=tmp_path)
    try:
        async with Client(app.state.mcp_server) as client:
            info = await tool(client, "runtime_info")
        assert info["process_pid"] == os.getpid()
        assert {k: v for k, v in info.items() if k != "process_pid"} == {
                        "backend": backend, "protocol_version": 1, "watchdog_enabled": False,
                        "clock_mode": "fixed_step_native_sleeper" if native_sleeper else "fixed_step_wall_clock", "physics_hz": 60}
        assert runtime.current is None
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            config = (await client.get("/api/config")).json()
        assert config["runtime_info"] == info
    finally:
        await runtime.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("native_sleeper", [False, True])
async def test_process_backend_mcp_commands_and_http_recording_are_awaited(tmp_path, native_sleeper):
    runtime = ProcessRaceRuntime(native_sleeper=native_sleeper)
    expected_mode = "fixed_step_native_sleeper" if native_sleeper else "fixed_step_wall_clock"
    app = create_app(runtime=runtime, replay_root=tmp_path)
    try:
        async with Client(app.state.mcp_server) as client:
            initial = await tool(client, "start_race", {"deadline": 3})
            queued_at = time.monotonic_ns()
            ack = await tool(client, "drive", {"race_id": initial["race_id"],
                "action_id": "straight_accelerate", "observation_tick": initial["tick"], "command_seq": 1})
            assert ack["applied"] and ack["applied_ns"] >= queued_at
            assert ack["observation"]["kart"]["speed"] > 0
            observation = await tool(client, "observe", {"race_id": initial["race_id"]})
            assert observation["observed_ns"] <= time.monotonic_ns()
            assert observation["tick"] >= ack["applied_tick"]
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as http:
                assert (await http.get("/api/replay")).status_code == 409
                await asyncio.sleep(.06)
                state = (await http.get("/api/state")).json()
                assert state["observation"]["race_id"] == initial["race_id"]
                assert state["runtime_info"]["backend"] == "process"
                result = await tool(client, "finish_race", {"race_id": initial["race_id"], "reason": "test_finished"})
                assert result["race_id"] == initial["race_id"]
                assert result["runtime_info"]["backend"] == "process"
                assert result["runtime_info"]["clock_mode"] == expected_mode
                assert result["timing"]["clock_mode"] == expected_mode
                download = await http.get("/api/replay")
                assert download.status_code == 200
                assert download.json()["commands"] == result["commands"]
    finally:
        await runtime.close()
