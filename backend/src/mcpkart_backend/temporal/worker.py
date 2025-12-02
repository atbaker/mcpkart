"""Temporal worker for MCP Kart."""

import asyncio
import os

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from mcpkart_backend.temporal.activities import store_race_results
from mcpkart_backend.temporal.workflows import RaceWorkflow

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE = "mcpkart-task-queue"


async def run_worker() -> None:
    """Run the Temporal worker."""
    print(f"Connecting to Temporal at {TEMPORAL_HOST}...")
    client = await Client.connect(TEMPORAL_HOST, data_converter=pydantic_data_converter)

    print(f"Starting worker on task queue: {TASK_QUEUE}")
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[RaceWorkflow],
        activities=[store_race_results],
    )

    print("Worker started. Press Ctrl+C to stop.")
    await worker.run()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("\nWorker stopped.")


if __name__ == "__main__":
    main()
