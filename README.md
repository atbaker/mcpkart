# MCP Kart

A turn-based kart racing game played via MCP (Model Context Protocol), inspired by Mario Kart. AI assistants drive "racers" using MCP tools, following high-level directions from their human users.

## Project Structure

```
mcpkart/
├── backend/           # FastAPI + Temporal backend
│   ├── src/mcpkart_backend/
│   │   ├── api/       # FastAPI endpoints
│   │   ├── temporal/  # Temporal workflows & activities
│   │   ├── npc/       # NPC bot spawning
│   │   ├── db/        # SQLAlchemy models
│   │   └── models/    # Pydantic models
│   └── tests/         # pytest tests
├── mcp_server/        # FastMCP server
│   └── src/mcpkart_mcp/
├── npcs/              # NPC bot Docker images
│   └── vibe/          # Vibe CLI (Mistral) NPC
├── frontend/          # SvelteKit spectator UI
├── research/          # Design documents
└── scripts/           # Helper scripts
```

## Quick Start

### Prerequisites

- Python 3.14+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Docker (for Temporal, PostgreSQL, and Redis)
- [ngrok](https://ngrok.com/) (for local GitHub OAuth testing)

### 1. Start Infrastructure Services

```bash
# Start Temporal, PostgreSQL, and Redis
docker compose up -d temporal postgres redis

# Or start all services including backend
docker compose up -d
```

- Temporal UI: http://localhost:8233
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 2. Run Database Migrations

```bash
cd backend
uv sync
uv run alembic upgrade head
```

### 3. Start the Backend

```bash
cd backend

# Start the worker (in one terminal)
uv run python -m mcpkart_backend.temporal.worker

# Start the API (in another terminal)
uv run uvicorn mcpkart_backend.api.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 4. Start the MCP Server

```bash
cd mcp_server
uv sync

# Without authentication (dev mode)
uv run python -m mcpkart_mcp.server

# With GitHub OAuth (see Authentication Setup below)
GITHUB_CLIENT_ID=xxx GITHUB_CLIENT_SECRET=xxx MCP_BASE_URL=https://your-ngrok-url.ngrok.io \
  uv run python -m mcpkart_mcp.server
```

## Authentication Setup

MCP Kart uses GitHub OAuth for player authentication. Your GitHub username becomes your player identity in races.

### Local Development with ngrok

GitHub OAuth requires a public callback URL. Use ngrok for local development:

1. **Install ngrok**: `brew install ngrok` or download from [ngrok.com](https://ngrok.com)

2. **Start ngrok**:
   ```bash
   # Using the included config (update domains in ngrok.yml first)
   ngrok start --config ~/.ngrok2/ngrok.yml,ngrok.yml --all

   # Or for a quick single tunnel
   ngrok http 8080
   ```
   Copy the HTTPS URL for the MCP server (e.g., `https://mcpkart.ngrok.io`)

3. **Create a GitHub OAuth App**:
   - Go to [GitHub Developer Settings](https://github.com/settings/developers)
   - Click "New OAuth App"
   - **Application name**: MCP Kart (Dev)
   - **Homepage URL**: Your ngrok URL
   - **Authorization callback URL**: `{ngrok-url}/auth/callback`
   - Click "Register application"
   - Generate a client secret

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your values:
   # - GITHUB_CLIENT_ID
   # - GITHUB_CLIENT_SECRET
   # - MCP_BASE_URL (your ngrok URL)
   # - JWT_SIGNING_KEY (generate with: openssl rand -base64 32)
   ```

5. **Start the MCP server** with the environment variables set

### Security Keys

Generate required keys:

```bash
# JWT signing key
openssl rand -base64 32

# Fernet encryption key (for production token storage)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Game Rules

- **Track**: 44-tile oval with 4 turns (tiles 7, 15, 29, 37)
- **Laps**: 3 laps to finish
- **Speed**: 0-3 (or 5 with speed boost)
- **Turns**: Speed 1 always safe, speed 2 requires drift, speed 3+ crashes
- **Drift zones**: 3 tiles before each turn (4-6, 12-14, 26-28, 34-36)
- **Item boxes**: At tiles 11, 22, 33 - give speed boosts
- **Tick rate**: 1 second per tick

## MCP Tools

The MCP server exposes three tools:

1. **join_race()** - Join/create a new race
2. **get_state(race_id)** - Get current game state
3. **control(race_id, accelerate?, brake?, steer?, use_item?)** - Send input

## Development

### Running Tests

```bash
cd backend
uv sync --all-extras
uv run pytest tests/ -v
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /races | Create a new race |
| GET | /races/{race_id}/state | Get current game state |
| POST | /races/{race_id}/input | Send player input |

## Architecture

```
MCP Client → FastMCP Server → FastAPI Backend → Temporal Workflow
     ↑              ↓               ↓                  ↓
     └──────────────┴───────────────┴──────────────────┘
                    Game State (returned on every call)
```

The race workflow runs in Temporal, maintaining all game state. The FastAPI backend is a thin layer that starts workflows and forwards queries/updates. The MCP server wraps the HTTP API as MCP tools for AI assistants.

## License

MIT
