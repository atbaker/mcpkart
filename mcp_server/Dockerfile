FROM python:3.14-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

# Install dependencies
RUN uv sync --no-dev

# Run MCP server with streamable HTTP transport
CMD ["uv", "run", "fastmcp", "run", "--transport", "http", "--host", "0.0.0.0", "--port", "8080", "src/mcpkart_mcp/server.py:mcp"]
