"""Export the actual demo's 20-fps display fields, preserving its audit master."""

import argparse
import json
from pathlib import Path

from export_duel_replay import visual_recording


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recording", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    visual = visual_recording(args.recording)
    for sample in visual["samples"]:
        for rid, original in sample["racers"].items():
            # These exact original fields drive every rendered kart, card,
            # gate, trail and contact indicator. Model facts are not displayed.
            racer = {key: original[key] for key in ("kart", "progress", "rescue", "control", "finished", "body")}
            racer["track"] = {"on_road": original["track"]["on_road"]}
            racer["competition"] = {"contact_count": original["competition"]["contact_count"]}
            sample["racers"][rid] = racer
    visual["visualization"]["display_fields_only"] = True
    body = json.dumps(visual, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    args.output.mkdir(exist_ok=False)
    (args.output / "replay.json").write_text(body)
    source = Path(__file__).resolve().parents[1] / "src/mcpkart/static/duel.html"
    page = source.read_text().replace(
        "<script>", "<script>window.EMBEDDED_RACE=" + body.replace("<", "\\u003c") + ";</script>\n<script>", 1,
    )
    (args.output / "replay.html").write_text(page)
    print(json.dumps({"source_unchanged": True, "visual_frames": len(visual["samples"]),
                      "visual_sample_rate_hz": visual["visualization"]["sample_rate_hz"],
                      "json_bytes": len(body.encode()), "output": str(args.output)}))


if __name__ == "__main__":
    main()
