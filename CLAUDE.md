# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Kart is a turn-based kart racing game played via MCP (Model Context Protocol). AI assistants drive "racers" using MCP tools, following directions from human users. The game is inspired by Mario Kart with simplified mechanics.

## Common Commands

### Backend (from `backend/` directory)
```bash
# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start the Temporal worker (required for game logic)
uv run python -m mcpkart_backend.temporal.worker

# Start the API server
uv run uvicorn mcpkart_backend.api.main:app --reload --port 8000

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_game_logic.py -v

# Run a specific test
uv run pytest tests/test_game_logic.py::TestTrack::test_create_oval -v
```

### MCP Server (from `mcp_server/` directory)
```bash
# Install dependencies
uv sync

# Run the MCP server
uv run fastmcp run mcpkart_mcp/server.py
```

### Frontend (from `frontend/` directory)
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Type check
npm run check

# Build for production
npm run build
```

### Infrastructure
```bash
# Start Temporal server (required for backend)
docker compose up -d temporal

# View spectator UI for a race
# http://localhost:5173/races/{race_id}

# View debug UI for a race (backend)
# http://localhost:8000/debug/{race_id}
```

## Architecture

```
MCP Client → FastMCP Server → FastAPI Backend → Temporal Workflow
                                    ↑
                              Svelte Frontend (spectator UI)
```

### Data Flow
1. **MCP Server** (`mcp_server/src/mcpkart_mcp/server.py`): Exposes three tools (`join_race`, `get_state`, `control`) to AI assistants via FastMCP. Transforms JSON game state to natural language using Jinja2 templates.

2. **FastAPI Backend** (`backend/src/mcpkart_backend/api/main.py`): Thin HTTP layer that starts Temporal workflows and forwards queries/updates. Endpoints: POST `/races`, GET `/races/{id}/state`, POST `/races/{id}/input`.

3. **Temporal Workflow** (`backend/src/mcpkart_backend/temporal/workflows.py`): `RaceWorkflow` contains all game logic. Runs as a durable workflow with 1-second tick rate. Uses `@workflow.query` for state reads and `@workflow.update` for player inputs.

4. **Svelte Frontend** (`frontend/`): SvelteKit 2 spectator UI using Svelte 5 runes. Polls backend for race state and renders an SVG-based track visualization.

### Frontend (`frontend/src/`)

Built with SvelteKit 2 and Svelte 5 (runes syntax: `$state`, `$derived`, `$props`, `$effect`).

**Key Components** (`lib/components/`):
- `TrackViewSVG.svelte`: SVG-based track visualization with 40-tile rectangular layout
- `Standings.svelte`: Live race standings with position, lap count, speed, power-ups
- `EventLog.svelte`: Scrolling list of race events

**Routes** (`routes/`):
- `/races/[id]`: Race spectator page - polls `/api/races/{id}/spectator-state` every second

**Types** (`lib/types.ts`):
- `SpectatorState`: Complete race view (track, racers, standings, events)
- `Racer`, `Track`, `Tile`, `Standing`: Game entity types

**Track Visualization**:
- Rectangular track with 90-degree corners matching game model
- Turn tiles: orange diamonds (6, 13, 26, 33)
- Drift zones: cyan dots (3 tiles before each turn)
- Item boxes: yellow question marks
- Start/finish: checkered pattern at tile 0
- Racers: colored circles with initial, color indicates status (green=racing, yellow=boosting, cyan=drifting, red=crashed, purple=finished)

### Key Game Logic (in `workflows.py`)
- **Turn tiles**: 6, 13, 26, 33 (40-tile oval track)
- **Drift zones**: 3 tiles before each turn (e.g., 3-5 for turn at tile 6)
- **Speed mechanics**: 0-3 normally, up to 5 with boost. Accelerates +1/tick, brakes up to -2/tick.
- **Turn safety**: Speed 1 always safe, speed 2 requires drift, speed 3+ crashes

### Models (`backend/src/mcpkart_backend/models/`)
- `GameState`: Complete race state including track, racers, standings, events
- `RacerState`: Position (tile + subunit), speed, lap, power-ups, controls, drift state
- `Track`/`Tile`: 40-tile oval with turns and item boxes
- `PlayerInput`: Control inputs (target_speed, drift, use_item)

## Testing

### Backend
Tests use pytest with `asyncio_mode = "auto"`. The test suite includes:
- `test_game_logic.py`: Unit tests for models (Track, RacerState, GameState)
- `test_workflow.py`: Temporal workflow tests

Run tests with `uv run pytest tests/ -v` from the `backend/` directory. Test dependencies are in the `[project.optional-dependencies]` section - install with `uv sync --all-extras`.

### Frontend
Run `npm run check` from the `frontend/` directory for TypeScript type checking.
