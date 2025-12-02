"""MCP server for MCP Kart racing game."""

import os
from pathlib import Path
from typing import Any, Optional

import httpx
from fastmcp import FastMCP
from jinja2 import Environment, FileSystemLoader

# Template setup
TEMPLATE_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# Backend URL from environment or default for local development
BACKEND_URL = os.environ.get("MCPKART_BACKEND_URL", "http://localhost:8000")

mcp = FastMCP(
    "MCP Kart",
    instructions="""You are playing MCP Kart, a turn-based racing game!

GAME RULES:
- Race 3 laps around a 40-tile oblong oval track
- Each tick (1 second), your kart moves based on your speed
- Speed ranges from 0-3 (or 5 with speed boost)
- Speed = subunits moved per tick (each tile has 3 subunits)

CONTROLS:
- target_speed: Set desired speed 0-3 (kart accelerates/brakes automatically)
- drift: Enable drift mode (only works in drift zones)
- use_item: Activate your power-up

TURN MECHANICS (SIMPLIFIED!):
- Turns are at tiles 6, 13, 26, and 33
- Speed 1: Always safe through turns (slow but reliable)
- Speed 2: Requires DRIFT to be enabled before the turn
- Speed 3+: Will CRASH on turns (too fast even with drift)

DRIFT ZONES (2 tiles before each turn):
- Turn at tile 6 -> drift zone is tiles 4, 5
- Turn at tile 13 -> drift zone is tiles 11, 12
- Turn at tile 26 -> drift zone is tiles 24, 25
- Turn at tile 33 -> drift zone is tiles 31, 32

DRIFT STRATEGY:
1. When approaching a turn at speed 2-3, watch for "drift zone" in the status
2. Send control(race_id, drift=True) while in the drift zone
3. Drift lets you take the turn at speed 2 without crashing
4. After exiting the turn, drift resets automatically

SAFE STRATEGY (slower but guaranteed to work):
1. Approach turn at any speed
2. Brake to speed 1 before entering turn
3. Navigate turn safely at speed 1
4. Accelerate back to speed 3 after exit

Item boxes are at tiles 3, 10, 20 - you automatically pick up items.
Speed boosts give you 3 ticks at speed 5 - use on straightaways only!
""",
)


def _format_state_as_text(state: dict[str, Any], race_id: str) -> str:
    """Transform game state JSON to natural language using Jinja2."""
    racer = state.get("racers", {}).get("player1", {})
    track = state.get("track", {})
    tiles = track.get("tiles", [])

    if not racer or not tiles:
        return str(state)

    # Calculate upcoming tiles (next 10)
    current_tile = racer.get("tile_index", 0)
    total_tiles = len(tiles)
    upcoming = []
    for i in range(1, 11):
        tile_idx = (current_tile + i) % total_tiles
        tile = tiles[tile_idx]
        upcoming.append({
            "distance_tiles": i,
            "type": tile.get("tile_type", "unknown"),
            "has_item_box": tile.get("has_item_box", False),
        })

    controls = racer.get("controls", {})

    template = jinja_env.get_template("state.jinja2")
    return template.render(
        race_id=race_id,
        race_clock=state.get("race_clock", "0:00"),
        max_race_clock=state.get("max_race_clock", "10:00"),
        race_status="finished" if state.get("is_finished") else "in_progress",
        racer={
            "position": {
                "tile": current_tile,
                "subunit": racer.get("tile_subunit", 0),
                "lap": racer.get("current_lap", 0),
            },
            "speed": racer.get("speed", 0),
            "target_speed": controls.get("target_speed", 0),
            "max_speed": 5 if racer.get("boost_seconds_remaining", 0) > 0 else 3,
            "in_drift_zone": racer.get("in_drift_zone", False),
            "drift_enabled": racer.get("drift_enabled", False),
            "on_turn_tile": racer.get("on_turn_tile", False),
            "power_up": racer.get("power_up"),
            "boost_seconds_remaining": racer.get("boost_seconds_remaining", 0),
            "status": racer.get("status", "racing"),
            "penalty_seconds_remaining": racer.get("penalty_seconds_remaining", 0),
            "finish_position": racer.get("finish_position"),
        },
        track={
            "total_tiles": total_tiles,
            "laps_required": state.get("laps_required", 3),
        },
        upcoming_tiles=upcoming,
        standings=state.get("standings", []),
    )


@mcp.tool()
async def join_race() -> str:
    """Join a new race. For the PoC, this creates a solo race.

    Returns the race_id and initial game state. You'll need the race_id
    for all subsequent calls.

    The race starts immediately after joining. You have ~10 minutes to complete 3 laps.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/races",
            json={"player_ids": ["player1"]},  # PoC: single player
        )
        response.raise_for_status()
        data = response.json()

        race_id = data["race_id"]
        state = data.get("state")

        if state:
            state_text = _format_state_as_text(state, race_id)
        else:
            state_text = "Race started, use get_state to see current status"

        join_template = jinja_env.get_template("join_race.jinja2")
        return join_template.render(race_id=race_id, state=state_text)


@mcp.tool()
async def get_state(race_id: str) -> str:
    """Get the current game state for your race.

    Args:
        race_id: The race ID returned from join_race

    Returns:
        Current game state including your position, speed, upcoming track, etc.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BACKEND_URL}/races/{race_id}/state")
        response.raise_for_status()
        data = response.json()

        return _format_state_as_text(data["state"], race_id)


@mcp.tool()
async def control(
    race_id: str,
    target_speed: Optional[int] = None,
    drift: bool = False,
    use_item: bool = False,
) -> str:
    """Send control inputs for your kart.

    Args:
        race_id: The race ID returned from join_race
        target_speed: Set desired speed 0-3. Your kart automatically accelerates
                     (+1/tick) or brakes (up to -2/tick) toward this speed.
        drift: Set to True to enable drift mode. Must be in drift zone
               (2 tiles before a turn). Drift lets you take turns at speed 2.
        use_item: Set to True to use your held item (if any).

    Returns:
        Updated game state after applying your input.

    Tips:
        - On straightaways: set target_speed=3
        - Before turns (tiles 6, 13, 26, 33): either brake to speed 1 OR enable drift
        - Drift zones are 2 tiles before each turn - watch for the notification!
        - With drift enabled, you can take turns at speed 2
        - Without drift, you must be at speed 1 to navigate turns safely
        - Speed 3+ will crash on turns even with drift enabled
        - Item boxes give you speed boosts - use them on straightaways ONLY!
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/races/{race_id}/input",
            json={
                "player_id": "player1",  # PoC: single player
                "target_speed": target_speed,
                "drift": drift,
                "use_item": use_item,
            },
        )
        response.raise_for_status()
        data = response.json()

        return _format_state_as_text(data["state"], race_id)


if __name__ == "__main__":
    # Run with streamable HTTP transport for remote MCP clients
    mcp.run(transport="http", host="0.0.0.0", port=8080)
