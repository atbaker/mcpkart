"""Poll only the VM's loopback spectator at 5 Hz and save aggregate timings."""

from __future__ import annotations

import argparse
import json
import signal
import time
import urllib.request
from collections import Counter
from pathlib import Path
from threading import Event

URL = "http://127.0.0.1:8765/api/state"
POLL_INTERVAL = .2


def poll(directory: Path) -> dict:
    output, stop_file = directory/"host-spectator.json", directory/"host-spectator.stop"
    if output.exists() or stop_file.exists():
        raise FileExistsError("Host spectator requires a fresh experiment directory")
    stopped = Event()

    def stop(_signal, _frame):
        stopped.set()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    durations: list[float] = []
    errors: Counter = Counter()
    successes, total_bytes = 0, 0
    started = time.monotonic()
    try:
        while not stopped.is_set() and not stop_file.exists():
            attempt = time.monotonic()
            try:
                with opener.open(URL, timeout=3) as response:
                    total_bytes += len(response.read())
                successes += 1
            except OSError as exc:
                errors[type(exc).__name__] += 1
            duration = time.monotonic()-attempt
            durations.append(duration*1000)
            # At most one request is active. Slow requests do not create a
            # catch-up burst that adds unintended load to the clock experiment.
            stopped.wait(max(0, POLL_INTERVAL-duration))
    finally:
        report = {"url": URL, "requested_poll_hz": 1/POLL_INTERVAL,
                  "polls": len(durations), "successes": successes, "errors": sum(errors.values()),
                  "error_types": dict(errors), "bytes": total_bytes,
                  "duration_s": time.monotonic()-started,
                  "max_roundtrip_ms": max(durations, default=None),
                  "clock_note": "Linux VM host HTTP round trips; physics lateness is measured inside the container.",
                  "model_requests": 0}
        temporary = output.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
        temporary.replace(output)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(poll(args.directory)), flush=True)


if __name__ == "__main__":
    main()
