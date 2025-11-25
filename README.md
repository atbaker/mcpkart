# MCP Kart

A turn-based kart racing game played via MCP (Model Context Protocol), inspired by Mario Kart. AI assistants drive "racers" using MCP tools, following high-level directions from their human users.

## Project Structure

```
mcpkart/
├── backend/           # FastAPI + Temporal backend
│   ├── src/mcpkart_backend/
│   │   ├── api/       # FastAPI endpoints
│   │   ├── temporal/  # Temporal workflows & activities
│   │   ├── db/        # SQLAlchemy models
│   │   └── models/    # Pydantic models
│   └── tests/         # pytest tests
├── mcp_server/        # FastMCP server
│   └── src/mcpkart_mcp/
├── research/          # Design documents
└── scripts/           # Helper scripts
```

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Docker (for Temporal server)

### 1. Start Temporal Server

```bash
# Using Docker Compose (recommended)
docker compose up -d temporal temporal-ui

# Or using the helper script
./scripts/start-temporal.sh
```

Temporal UI will be available at http://localhost:8080

### 2. Start the Backend

```bash
cd backend

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start the worker (in one terminal)
uv run python -m mcpkart_backend.temporal.worker

# Start the API (in another terminal)
uv run uvicorn mcpkart_backend.api.main:app --reload --port 8000
```

API docs will be available at http://localhost:8000/docs

### 3. Start the MCP Server

```bash
cd mcp_server

# Install dependencies
uv sync

# Run the MCP server
uv run fastmcp run mcpkart_mcp/server.py
```

## Game Rules

- **Track**: 20-tile oval with 4 turns (tiles 4, 9, 14, 19)
- **Laps**: 3 laps to finish
- **Speed**: 0-3 (or 5 with speed boost)
- **Turns**: Must be at speed 1 AND steering "left" to navigate turns
- **Item boxes**: At tiles 0, 5, 10, 15 - give speed boosts
- **Tick rate**: 1 second per tick, ~180 ticks max

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
