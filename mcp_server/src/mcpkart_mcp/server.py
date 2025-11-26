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

CONTROLS (SIMPLIFIED FOR AI):
- target_speed: Set desired speed 0-3 directly (no accelerate/brake buttons!)
  * Your kart automatically accelerates (+1/tick) or brakes (up to -2/tick) toward target
  * Example: going speed 3, set target_speed=1 → kart brakes to 1 in ONE tick
  * Example: stopped at 0, set target_speed=3 → kart accelerates over 3 ticks
- steer: "left", "straight", or "right"
  * IMPORTANT: Steering auto-resets to "straight" after one tick!
  * Just send "left" once per turn - no need to reset manually
- use_item: True to use your held power-up
- execute_at_tick: Optional - schedule input for a future tick (max 20 ticks ahead)

CRITICAL - TURNS (EASIER NOW):
- Turns are at tiles 2, 7, 12, and 17
- You MUST be at speed 1 to navigate turns (speed > 1 = crash)
- You have 3 ticks to steer "left" while on a turn tile (any tick counts!)
- At speed 1, it takes 3 ticks to cross a tile - plenty of time to steer
- Crashing costs you 2 ticks (penalty) and resets your speed to 0

STRATEGY:
1. On straightaways: set target_speed=3 for max speed
2. Before turns: set target_speed=1 EARLY (you can brake from 3→1 in one tick!)
3. On turn tile at speed 1: steer "left" (any of the 3 ticks you're on it works)
4. After turn: set target_speed=3 to accelerate (steering auto-resets)
5. Use speed boosts on straightaways ONLY - boost on turn = guaranteed crash!

EXAMPLE TURN SEQUENCE (immediate):
- Tick 5: control(race_id, target_speed=1)  # Brake for turn at tile 2
- Tick 7: control(race_id, steer="left")     # Steer on turn
- Tick 10: control(race_id, target_speed=3)  # Accelerate out of turn

EXAMPLE TURN SEQUENCE (scheduled from tick 5):
- control(race_id, target_speed=1, execute_at_tick=5)
- control(race_id, steer="left", execute_at_tick=7)
- control(race_id, target_speed=3, execute_at_tick=10)

Item boxes are at tiles 5, 10, 15 - you automatically pick up items.
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

    # Count scheduled inputs for this player
    scheduled_inputs = state.get("scheduled_inputs", {}).get("player1", {})
    scheduled_count = len(scheduled_inputs)

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
            "target_speed": controls.get("target_speed", 0),
            "max_speed": 5 if racer.get("boost_ticks_remaining", 0) > 0 else 3,
            "steering": controls.get("steering", "straight"),
            "on_turn_tile": racer.get("on_turn_tile", False),
            "steered_left_during_turn": racer.get("steered_left_during_turn", False),
            "power_up": racer.get("power_up"),
            "boost_ticks_remaining": racer.get("boost_ticks_remaining", 0),
            "status": racer.get("status", "racing"),
            "penalty_ticks_remaining": racer.get("penalty_ticks_remaining", 0),
            "finish_position": racer.get("finish_position"),
        },
        "scheduled_inputs_count": scheduled_count,
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
            "message": "Race started! Set target_speed=3 for straightaways, target_speed=1 before turns. Steer 'left' at speed 1 on turn tiles (you have 3 ticks!). Steering auto-resets.",
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
    target_speed: Optional[int] = None,
    steer: Optional[str] = None,
    use_item: bool = False,
    execute_at_tick: Optional[int] = None,
) -> dict[str, Any]:
    """Send control inputs for your kart.

    Args:
        race_id: The race ID returned from join_race
        target_speed: Set desired speed 0-3. Your kart automatically accelerates
                     (+1/tick) or brakes (up to -2/tick) toward this speed.
                     Example: speed 3 → target 1 = brakes to 1 in ONE tick.
                     Example: speed 0 → target 3 = accelerates over 3 ticks.
        steer: Set steering direction: "left", "straight", or "right".
               Auto-resets to "straight" after one tick - just send "left" once!
               IMPORTANT: You must steer "left" AND be at speed 1 to make turns!
        use_item: Set to True to use your held item (if any).
        execute_at_tick: Optional. If set, schedules this input for the specified
                        future tick instead of applying immediately. Max 20 ticks ahead.

    Returns:
        Updated game state after applying your input.

    Tips:
        - On straightaways: set target_speed=3
        - Before turns (tiles 2, 7, 12, 17): set target_speed=1 early
        - Fast braking: can go from speed 3 to 1 in just ONE tick!
        - On turn tile at speed 1: steer="left" (you have 3 ticks while on the tile)
        - Steering auto-resets, so just send "left" once per turn
        - Schedule ahead: control(race_id, target_speed=1, execute_at_tick=10)
        - Item boxes give you speed boosts - use them on straightaways ONLY!
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BACKEND_URL}/races/{race_id}/input",
            json={
                "player_id": "player1",  # PoC: single player
                "target_speed": target_speed,
                "steering": steer,
                "use_item": use_item,
                "execute_at_tick": execute_at_tick,
            },
        )
        response.raise_for_status()
        data = response.json()

        return _format_state_for_ai(data["state"])


if __name__ == "__main__":
    # Run with streamable HTTP transport for remote MCP clients
    mcp.run(transport="http", host="0.0.0.0", port=8080)
