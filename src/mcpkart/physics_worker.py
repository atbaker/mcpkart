"""Private physics entrypoint with optional native pacing; no web/MCP imports."""

import argparse
from multiprocessing.connection import Connection

from .process_runtime import _worker


def main() -> None:
    parser = argparse.ArgumentParser(description="Private MCP Kart physics worker")
    parser.add_argument("--worker-fd", type=int, required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--watchdog", action="store_true")
    parser.add_argument("--native-sleeper", action="store_true")
    options = parser.parse_args()
    _worker(Connection(options.worker_fd), options.session, options.watchdog, options.native_sleeper)


if __name__ == "__main__":
    main()
