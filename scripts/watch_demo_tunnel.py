"""Keep the read-only spectator forward connected without touching any race."""

import argparse
import fcntl
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def listening(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def stop(child):
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-port", type=int, default=17773)
    args = parser.parse_args()
    lock = (ROOT / "artifacts" / f"aws-demo-tunnel-{args.local_port}.lock").open("a")
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit("A spectator tunnel watcher is already running for this port") from None
    host = json.loads((ROOT / "artifacts/aws-demo-ec2-v1/resources.json").read_text())
    env = dict(os.environ)
    plugin = ROOT / "artifacts/aws-demo-ssm-plugin/sessionmanager-bundle/bin"
    env["PATH"] = str(plugin) + os.pathsep + env.get("PATH", "")
    command = ["aws", "ssm", "start-session", "--region", host["region"],
               "--target", host["resources"]["instance"],
               "--document-name", "AWS-StartPortForwardingSession", "--parameters",
               json.dumps({"portNumber": ["8771"], "localPortNumber": [str(args.local_port)]})]
    child, delay = None, 2
    try:
        while True:
            if listening(args.local_port):
                print(f"Spectator forward on {args.local_port} is available; watching for disconnects.", flush=True)
                while listening(args.local_port):
                    time.sleep(2)
            print("Connecting spectator tunnel; races run independently on AWS.", flush=True)
            started = time.monotonic()
            try:
                child = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL, start_new_session=True)
                code = child.wait()
                print(f"Spectator tunnel closed (exit {code}).", flush=True)
            except OSError as error:
                print(f"Could not start spectator tunnel: {error}", flush=True)
            finally:
                stop(child)
                child = None
            if time.monotonic() - started > 30:
                delay = 2
            print(f"Reconnecting in {delay}s. Ctrl+C stops this watcher.", flush=True)
            time.sleep(delay)
            delay = min(30, delay * 2)
    except KeyboardInterrupt:
        print("\nStopped spectator tunnel watcher; remote races continue.", flush=True)
    finally:
        stop(child)
        lock.close()


if __name__ == "__main__":
    main()
