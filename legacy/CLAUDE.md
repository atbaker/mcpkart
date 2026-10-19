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
# Start all infrastructure (Temporal, PostgreSQL, Redis)
docker compose up -d temporal postgres redis

# View spectator UI for a race
# http://localhost:5173/races/{race_id}

# For GitHub OAuth testing locally, use ngrok:
ngrok start --config ~/.ngrok2/ngrok.yml,ngrok.yml --all
```

## Architecture

```
MCP Client → FastMCP Server → FastAPI Backend → Temporal Workflow
     ↓            ↓                 ↓                  ↓
  GitHub      Redis            PostgreSQL         Game State
   OAuth     (tokens,          (users,
             cache)           race results)
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
- `TrackViewSVG.svelte`: SVG-based track visualization with 44-tile rectangular layout
- `Standings.svelte`: Live race standings with position, lap count, speed, power-ups
- `EventLog.svelte`: Scrolling list of race events

**Routes** (`routes/`):
- `/races/[id]`: Race spectator page - polls `/api/races/{id}/spectator-state` every second

**Types** (`lib/types.ts`):
- `SpectatorState`: Complete race view (track, racers, standings, events)
- `Racer`, `Track`, `Tile`, `Standing`: Game entity types

**Track Visualization**:
- Rectangular track with 90-degree corners matching game model
- Turn tiles: orange dots (7, 15, 29, 37)
- Drift zones: cyan dots (3 tiles before each turn)
- Item boxes: yellow question marks
- Start/finish: checkered pattern at tile 0
- Racers: colored circles with initial, color indicates status (green=racing, yellow=boosting, cyan=drifting, red=crashed, purple=finished)

### Key Game Logic (in `workflows.py`)
- **Turn tiles**: 7, 15, 29, 37 (44-tile oval track)
- **Item boxes**: 11, 22, 33
- **Drift zones**: 3 tiles before each turn (e.g., 4-6 for turn at tile 7)
- **Speed mechanics**: 0-3 normally, up to 5 with boost. Accelerates +1/tick, brakes up to -2/tick.
- **Turn safety**: Speed 1 always safe, speed 2 requires drift, speed 3+ crashes

### Models (`backend/src/mcpkart_backend/models/`)
- `GameState`: Complete race state including track, racers, standings, events
- `RacerState`: Position (tile + subunit), speed, lap, power-ups, controls, drift state
- `Track`/`Tile`: 44-tile oval with turns and item boxes
- `PlayerInput`: Control inputs (target_speed, drift, use_item)

### NPC Bots (`backend/src/mcpkart_backend/npc/`, `npcs/`)

NPC bots fill empty race slots with AI opponents during public matchmaking.

**How it works:**
1. When a race enters PLANNING phase, Temporal workflow calculates `npcs_needed = max_racers - human_count`
2. `spawn_npcs` activity spawns Docker containers running the Vibe CLI (Mistral)
3. Each NPC gets a unique token stored in Redis for authentication
4. NPCs join via MCP server and race autonomously
5. When race ends, `cleanup_npcs` activity stops the containers

**Configuration:**
- `MAX_RACERS` env var: Total racers per race (humans + NPCs). Default 8 for prod, use 4 for dev.
- `MCP_SERVER_URL` env var: URL NPCs use to reach MCP server (use Docker service name: `http://mcp-server:8080/mcp`)
- `MISTRAL_API_KEY` env var: API key for Vibe CLI
- NPC definitions: `backend/config/npcs.toml`

**Docker image:**
- Built from `npcs/vibe/Dockerfile`
- Build with: `docker build -t mcpkart-vibe:latest ./npcs/vibe/`

### Authentication

MCP Kart uses GitHub OAuth via FastMCP's GitHubProvider:

**Flow:**
1. MCP client connects to MCP server
2. FastMCP redirects to GitHub OAuth for authentication
3. User authorizes and GitHub returns token
4. FastMCP stores encrypted token in Redis, issues JWT to client
5. MCP server extracts GitHub username from JWT claims
6. GitHub username becomes the player_id in races

**Key Files:**
- `mcp_server/src/mcpkart_mcp/server.py`: GitHubProvider configuration, `_get_player_id()` extracts username
- `backend/src/mcpkart_backend/api/auth.py`: GitHub token validation (for future use)
- `backend/src/mcpkart_backend/db/models.py`: User model with github_user_id, github_username, organizations

**Environment Variables (for OAuth):**
- `GITHUB_CLIENT_ID`: OAuth app client ID
- `GITHUB_CLIENT_SECRET`: OAuth app client secret
- `MCP_BASE_URL`: Public URL for OAuth callback (use ngrok locally)
- `JWT_SIGNING_KEY`: Secret for signing FastMCP JWTs
- `STORAGE_ENCRYPTION_KEY`: Fernet key for encrypting stored tokens

**Database:**
- PostgreSQL (postgresql+psycopg://) replaces SQLite
- Redis for OAuth token storage and spectator state cache
- See `.env.example` for connection strings

## Testing

### Backend
Tests use pytest with `asyncio_mode = "auto"`. The test suite includes:
- `test_game_logic.py`: Unit tests for models (Track, RacerState, GameState)
- `test_workflow.py`: Temporal workflow tests

Run tests with `uv run pytest tests/ -v` from the `backend/` directory. Test dependencies are in the `[project.optional-dependencies]` section - install with `uv sync --all-extras`.

### Frontend
Run `npm run check` from the `frontend/` directory for TypeScript type checking.
