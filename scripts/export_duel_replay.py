"""Export a compact two-kart spectator replay as standalone offline HTML."""

import argparse
import json
from pathlib import Path


def visual_recording(recording, stride=3):
    if isinstance(stride, bool) or not isinstance(stride, int) or not 1 <= stride <= 60:
        raise ValueError("Visual sample stride must be an integer from 1 to 60")
    race = json.loads(Path(recording).read_text())
    race = race.get("race", race)
    if not race.get("samples") or "racers" not in race["samples"][0]:
        raise ValueError("A two-kart recording is required")
    keys = (
        "race_id",
        "label",
        "status",
        "reason",
        "summary",
        "track",
        "events",
        "driver_labels",
        "driver_metrics",
        "driver_timeline",
        "started_ns",
        "episode_origin",
        "episode",
    )
    visual = {key: race[key] for key in keys if key in race}
    samples = race["samples"][::stride]
    if samples[-1]["tick"] != race["samples"][-1]["tick"]:
        samples.append(race["samples"][-1])
    visual["samples"] = samples
    previous = race.get("visualization", {})
    input_hz = previous.get("sample_rate_hz", 60)
    visual["visualization"] = {
        "sample_rate_hz": input_hz / stride,
        "sample_stride": stride,
        "input_sample_count": len(race["samples"]),
        "source_physics_hz": previous.get("source_physics_hz", 60),
        "purpose": "spectator_replay",
        "not_physics_audit_recording": True,
    }
    calls_path = Path(recording).with_name("decisions.json")
    if calls_path.exists() and "started_ns" in race:
        calls = json.loads(calls_path.read_text())
        visual["driver_timeline"] = {
            rid: [
                {
                    "request_s": (c["request_started_ns"] - race["started_ns"]) / 1e9,
                    "response_s": (c["response_received_ns"] - race["started_ns"]) / 1e9,
                    "latency_ms": c["latency_ms"],
                }
                for c in calls.get(rid, [])
            ]
            for rid in race["samples"][0]["racers"]
        }
    return visual


def export(recording, output, stride=3):
    race = visual_recording(recording, stride)
    page = Path(__file__).resolve().parents[1] / "src/mcpkart/static/duel.html"
    data = json.dumps(race, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace(
        "<", "\\u003c"
    )
    content = page.read_text().replace(
        "<script>", "<script>window.EMBEDDED_RACE=" + data + ";</script>\n<script>", 1
    )
    with Path(output).open("x") as stream:
        stream.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--stride", type=int, default=3, help="Visual sampling only; default 20 fps from 60 Hz masters"
    )
    args = parser.parse_args()
    export(args.recording, args.output, args.stride)


if __name__ == "__main__":
    main()
