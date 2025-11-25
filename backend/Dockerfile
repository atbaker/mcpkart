# MCP Kart Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY alembic.ini .
COPY alembic/ alembic/

# Install dependencies
RUN uv sync --no-dev

# Create data directory for SQLite
RUN mkdir -p /app/data

# Run migrations and start the API
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn mcpkart_backend.api.main:app --host 0.0.0.0 --port 8000"]
