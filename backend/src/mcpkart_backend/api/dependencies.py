"""FastAPI dependencies for MCP Kart."""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

logger = logging.getLogger(__name__)

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
    logger.info("Connecting to Temporal at %s...", TEMPORAL_HOST)
    temporal_client = await Client.connect(TEMPORAL_HOST, data_converter=pydantic_data_converter)
    logger.info("Connected to Temporal!")
    yield
    logger.info("Shutting down...")
