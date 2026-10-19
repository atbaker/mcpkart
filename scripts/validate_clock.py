"""Free real-MCP controls with HTTP polling and one declared parent-process pause.

Run against this project's local process-backend development server. This never
loads model credentials or runs a model command. All evidence goes to a fresh
artifact directory, including failed controls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


def read_state(url: str) -> dict:
    with urllib.request.urlopen(url.rstrip("/")+"/api/state", timeout=3) as response:
        return json.load(response)


class SpectatorPoller:
    def __init__(self, url: str) -> None:
        self.url = url
        self.stop = threading.Event()
        self.latest: dict = {}
        self.count = self.errors = 0
        self.max_roundtrip_ms = 0.0
        self.thread = threading.Thread(target=self.run, name="validation-spectator", daemon=True)

    def run(self) -> None:
        while not self.stop.is_set():
            started = time.monotonic_ns()
            try:
                self.latest = read_state(self.url)
                self.count += 1
            except (OSError, ValueError):
                self.errors += 1
            self.max_roundtrip_ms = max(self.max_roundtrip_ms, (time.monotonic_ns()-started)/1e6)
            self.stop.wait(.05)

    def close(self) -> None:
        self.stop.set()
        self.thread.join(timeout=4)


def pause_parent(state: dict, expected_pid: int, duration: float) -> dict:
    info = state.get("runtime_info", {})
    if (info.get("backend") != "process" or info.get("process_pid") != expected_pid
            or expected_pid <= 1 or expected_pid == os.getpid()):
        raise ValueError("Refusing to signal a process that is not the verified local HTTP parent")
    started_ns = time.monotonic_ns()
    try:
        os.kill(expected_pid, signal.SIGSTOP)
        time.sleep(duration)
    finally:
        # Always resume, including on an interrupted controller sleep. SIGSTOP
        # targets the positive parent PID only, never the worker/process group.
        os.kill(expected_pid, signal.SIGCONT)
    ended_ns = time.monotonic_ns()
    return {"parent_pid": expected_pid, "race_id": state["race_id"], "started_ns": started_ns,
            "ended_ns": ended_ns, "requested_duration_s": duration,
            "actual_duration_s": (ended_ns-started_ns)/1e9,
            "last_polled_tick": state["observation"]["tick"],
            "last_polled_race_s": state["observation"]["time"], "signals": ["SIGSTOP", "SIGCONT"]}


def run(args) -> dict:
    if urlparse(args.url).hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Clock validation only signals a local development server")
    initial = read_state(args.url)
    info = initial.get("runtime_info", {})
    if (info.get("backend") != "process" or info.get("process_pid") != args.parent_pid
            or info.get("clock_mode") != args.clock_mode):
        raise ValueError("Server must report the expected process backend, clock mode and parent PID")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    poller = SpectatorPoller(args.url)
    poller.thread.start()
    rows, pause = [], None
    report = {"script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "runtime_info": info, "expected_clock_mode": args.clock_mode,
              "reference": args.reference, "required_consecutive_controls": 3,
              "pause_run": 2, "pause_at_s": args.pause_at, "pause_duration_s": args.pause_for,
              "validity_limits_ms": {"max_lateness": 100, "p95_lateness": 25, "absolute_drift": 100},
              "model_requests": 0, "controls": rows, "passes": False}
    try:
        for index in range(1, 4):
            directory = output/f"run-{index:02d}"
            count_before = poller.count
            command = [sys.executable, "-m", "mcpkart.bench", "live-reference", "--url",
                       args.url.rstrip("/")+"/mcp", "--reference", args.reference, "--output", str(directory)]
            with (output/f"run-{index:02d}.log").open("w") as log:
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                try:
                    while process.poll() is None:
                        state = poller.latest
                        if (index == 2 and pause is None and state.get("status") == "running"
                                and state.get("observation", {}).get("time", 0) >= args.pause_at):
                            # Revalidate identity via a fresh response immediately
                            # before signaling, rather than trust an old PID.
                            pause = pause_parent(read_state(args.url), args.parent_pid, args.pause_for)
                        time.sleep(.02)
                    if process.returncode:
                        raise RuntimeError(f"Control {index} failed; see {log.name}")
                finally:
                    if process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
            path = directory/"scripted-live.json"
            trial = json.loads(path.read_text())
            race, metrics = trial["race"], trial["metrics"]
            row = {"trial": str(path), "fingerprint": trial["fingerprint"],
                   "runtime_info": trial["runtime_info"], "metrics": metrics,
                   "checkpoints_passed": race["summary"]["checkpoints_passed"],
                   "spectator_polls": poller.count-count_before}
            row["passes"] = bool(metrics["finished"] and metrics["realtime_valid"]
                                 and row["checkpoints_passed"] == 120 and row["spectator_polls"] > 0)
            if index == 2:
                if pause is None or pause["race_id"] != race["race_id"]:
                    raise RuntimeError("The declared parent-pause injection did not occur in control 2")
                samples = [sample for sample in race["samples"]
                           if pause["started_ns"] <= sample["wall_ns"] <= pause["ended_ns"]]
                pause["physics_samples_during_parent_pause"] = len(samples)
                pause["maximum_child_lateness_during_parent_pause_ms"] = max(
                    (sample["lateness_ms"] for sample in samples), default=None)
                row["passes"] = row["passes"] and len(samples) >= 12
                row["parent_pause"] = pause
            rows.append(row)
            print(json.dumps({"run": index, "passes": row["passes"], "elapsed": metrics["elapsed"],
                              "max_lateness_ms": metrics["timing"]["max_lateness_ms"]}), flush=True)
            if not row["passes"]:
                # Preserve failure and stop. Do not search repeatedly for three
                # lucky successes while hiding intervening invalid controls.
                break
        report["passes"] = len(rows) == 3 and all(row["passes"] for row in rows)
        report["source_unchanged"] = len({row["fingerprint"] for row in rows}) <= 1
        report["passes"] = report["passes"] and report["source_unchanged"]
        return report
    finally:
        poller.close()
        report["spectator"] = {"polls": poller.count, "errors": poller.errors,
                               "max_roundtrip_ms": poller.max_roundtrip_ms}
        (output/"validation.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--parent-pid", required=True, type=int)
    parser.add_argument("--clock-mode", choices=("fixed_step_wall_clock", "fixed_step_native_sleeper", "rust_fixed_step_wall_clock"),
                        required=True)
    parser.add_argument("--reference", default="scripts/clock_helpers/reference.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--pause-at", type=float, default=20)
    parser.add_argument("--pause-for", type=float, default=.35)
    args = parser.parse_args()
    if not (0 < args.pause_for <= 1 and 0 < args.pause_at < 40):
        parser.error("Use a pause of at most one second during the first forty race seconds")
    summary = run(args)
    raise SystemExit(0 if summary["passes"] else 1)


if __name__ == "__main__":
    main()
