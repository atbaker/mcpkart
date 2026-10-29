"""Private duel physics worker; never imports a web or MCP framework."""

import argparse
import asyncio
import gc
from multiprocessing.connection import Connection

from .duel_runtime import DuelRuntime
from .process_runtime import _worker_loop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-fd", type=int, required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--watchdog", action="store_true")
    parser.add_argument("--native-sleeper", action="store_true")
    args = parser.parse_args()
    connection = Connection(args.worker_fd)
    # Each duel gets a fresh process and a maximum 600 s lifetime. Recording
    # retains many acyclic snapshot trees; repeatedly tracing that history can
    # pause the clock. Reference counting still frees ordinary objects. Defer
    # cyclic collection until this bounded worker exits, outside active physics.
    gc.collect()
    gc.disable()
    try:
        asyncio.run(
            _worker_loop(
                connection, args.session, args.watchdog, args.native_sleeper, runtime_factory=DuelRuntime
            )
        )
    finally:
        connection.close()
        gc.enable()


if __name__ == "__main__":
    main()
