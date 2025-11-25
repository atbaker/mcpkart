"""FastAPI dependencies for MCP Kart."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from temporalio.client import Client

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")

# Global Temporal client (initialized on startup)
temporal_client: Client | None = None


async def get_temporal_client() -> Client:
    """Get the Temporal client."""
    if temporal_client is None:
        raise RuntimeError("Temporal client not initialized")
    return temporal_client


@asynccontextmanager
async def lifespan_context() -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI."""
    global temporal_client
    print(f"Connecting to Temporal at {TEMPORAL_HOST}...")
    temporal_client = await Client.connect(TEMPORAL_HOST)
    print("Connected to Temporal!")
    yield
    print("Shutting down...")
