"""MCP server for MCP Kart racing game."""

import os
from typing import Any, Optional

import httpx
from fastmcp import FastMCP

# Backend URL from environment or default for local development
BACKEND_URL = os.environ.get("MCPKART_BACKEND_URL", "http://localhost:8000")

mcp = FastMCP(
    "MCP Kart",
    instructions="""You are playing MCP Kart, a turn-based racing game!

GAME RULES:
- The race has 3 laps around a 20-tile oval track
- Each tick (1 second), your kart moves based on your controls
- Speed ranges from 0-3 (or 5 with speed boost)
- Speed = subunits moved per tick (each tile has 3 subunits)

CONTROLS:
- accelerate: True to speed up (+1 speed per tick), False to coast
- brake: True to slow down (-1 speed per tick)
- steer: "left", "straight", or "right"
- use_item: True to use your held power-up

CRITICAL - TURNS:
- Turns are at tiles 4, 9, 14, and 19
- You MUST be at speed 1 AND steering "left" to make a turn
- If you hit a turn at speed > 1 or not steering left, you CRASH!
- Crashing costs you 2 ticks (penalty) and resets your speed to 0

STRATEGY:
1. On straightaways: accelerate to max speed (3)
2. Before turns: brake to speed 1 and steer "left"
3. After completing a turn: steer "straight" and accelerate again
4. Use speed boosts on long straightaways, not before turns!

Item boxes are at tiles 0, 5, 10, 15 - you automatically pick up items.
""",
)


def _format_state_for_ai(state: dict[str, Any]) -> dict[str, Any]:
    """Format game state in a way that's easy for AI assistants to understand.

    Includes helpful derived information like upcoming tiles.
    """
    racer = state.get("racers", {}).get("player1", {})
    track = state.get("track", {})
    tiles = track.get("tiles", [])

    if not racer or not tiles:
        return state

    # Calculate upcoming tiles (next 5)
    current_tile = racer.get("tile_index", 0)
    total_tiles = len(tiles)
    upcoming = []
    for i in range(1, 6):
        tile_idx = (current_tile + i) % total_tiles
        tile = tiles[tile_idx]
        upcoming.append(
            {
                "distance_tiles": i,
                "type": tile.get("tile_type", "unknown"),
                "has_item_box": tile.get("has_item_box", False),
            }
        )

    controls = racer.get("controls", {})
    current_tile_data = tiles[current_tile] if tiles else {}

    return {
        "race_id": state.get("race_id"),
        "tick": state.get("current_tick", 0),
        "max_ticks": state.get("max_ticks", 180),
        "your_racer": {
            "position": {
                "tile": current_tile,
                "subunit": racer.get("tile_subunit", 0),
                "lap": racer.get("current_lap", 0),
            },
            "speed": racer.get("speed", 0),
            "max_speed": 5 if racer.get("boost_ticks_remaining", 0) > 0 else 3,
            "steering": controls.get("steering", "straight"),
            "accelerating": controls.get("accelerating", True),
            "braking": controls.get("braking", False),
            "power_up": racer.get("power_up"),
            "boost_ticks_remaining": racer.get("boost_ticks_remaining", 0),
            "status": racer.get("status", "racing"),
            "penalty_ticks_remaining": racer.get("penalty_ticks_remaining", 0),
            "finish_position": racer.get("finish_position"),
        },
        "track": {
            "total_tiles": total_tiles,
            "laps_required": state.get("laps_required", 3),
            "current_tile": current_tile_data,
        },
        "upcoming_tiles": upcoming,
        "race_status": "finished" if state.get("is_finished") else "in_progress",
        "standings": state.get("standings", []),
    }


@mcp.tool()
async def join_race() -> dict[str, Any]:
    """Join a new race. For the PoC, this creates a solo race.

    Returns the race_id and initial game state. You'll need the race_id
    for all subsequent calls.

    The race starts immediately after joining. You have ~3 minutes to complete 3 laps.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/races",
            json={"player_ids": ["player1"]},  # PoC: single player
        )
        response.raise_for_status()
        data = response.json()

        state = data.get("state")
        if state:
            formatted = _format_state_for_ai(state)
        else:
            formatted = {"message": "Race started, use get_state to see current status"}

        return {
            "race_id": data["race_id"],
            "message": "Race started! You have 3 minutes to complete 3 laps. Remember: slow to speed 1 and steer LEFT for turns!",
            "state": formatted,
        }


@mcp.tool()
async def get_state(race_id: str) -> dict[str, Any]:
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

        return _format_state_for_ai(data["state"])


@mcp.tool()
async def control(
    race_id: str,
    accelerate: Optional[bool] = None,
    brake: Optional[bool] = None,
    steer: Optional[str] = None,
    use_item: bool = False,
) -> dict[str, Any]:
    """Send control inputs for your kart. Inputs persist until changed.

    Args:
        race_id: The race ID returned from join_race
        accelerate: Set to True to press gas pedal, False to release.
                   When accelerating, speed increases by 1 each tick (max 3).
        brake: Set to True to brake, False to release.
               When braking, speed decreases by 1 each tick (min 0).
        steer: Set steering direction: "left", "straight", or "right".
               IMPORTANT: You must steer "left" AND be at speed 1 to make turns!
        use_item: Set to True to use your held item (if any).

    Returns:
        Updated game state after applying your input.

    Tips:
        - On straight tiles, accelerate to max speed (3)
        - Before turns (tiles 4, 9, 14, 19), brake to speed 1 and set steering to "left"
        - If you crash (wrong speed/steering on turn), you'll be penalized 2 ticks
        - Item boxes give you speed boosts - use them on straightaways!
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/races/{race_id}/input",
            json={
                "player_id": "player1",  # PoC: single player
                "accelerating": accelerate,
                "braking": brake,
                "steering": steer,
                "use_item": use_item,
            },
        )
        response.raise_for_status()
        data = response.json()

        return _format_state_for_ai(data["state"])
