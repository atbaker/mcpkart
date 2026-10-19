#!/bin/bash
# Start MCP Kart backend (API and worker)

cd "$(dirname "$0")/../backend" || exit 1

echo "Running database migrations..."
uv run alembic upgrade head

echo ""
echo "Starting Temporal worker in background..."
uv run python -m mcpkart_backend.temporal.worker &
WORKER_PID=$!

echo "Starting FastAPI server..."
uv run uvicorn mcpkart_backend.api.main:app --reload --port 8000 &
API_PID=$!

echo ""
echo "Backend started!"
echo "  - API: http://localhost:8000"
echo "  - API docs: http://localhost:8000/docs"
echo "  - Worker PID: $WORKER_PID"
echo "  - API PID: $API_PID"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for both processes
wait $WORKER_PID $API_PID
