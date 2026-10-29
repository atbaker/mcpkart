import json
import re

import pytest

from mcpkart.duel import DuelSimulation
from scripts.export_duel_replay import export, visual_recording


def recording(tmp_path):
    sim = DuelSimulation()
    samples = [sim.state()]
    for _ in range(7):
        sim.step()
        samples.append(sim.state())
    race = {
        "race_id": "test",
        "label": "</script><script>window.REPLAY_INJECTED=true</script>",
        "samples": samples,
        "track": sim.track.as_dict(),
        "summary": sim.summary(),
        "started_ns": 1000000000,
        "owner_token": "private-control-capability",
    }
    path = tmp_path / "race.json"
    path.write_text(json.dumps(race))
    (tmp_path / "decisions.json").write_text(
        json.dumps(
            {
                "red": [
                    {"request_started_ns": 1100000000, "response_received_ns": 1350000000, "latency_ms": 250}
                ],
                "blue": [],
            }
        )
    )
    return path, race


def test_export_preserves_last_sample_and_text_without_executing_markup(tmp_path):
    path, original = recording(tmp_path)
    before = path.read_bytes()
    target = tmp_path / "replay.html"
    export(path, target)
    html = target.read_text()
    encoded = re.search(r"window\.EMBEDDED_RACE=(.*?);</script>", html, re.DOTALL).group(1)
    visual = json.loads(encoded)
    assert visual["label"] == original["label"]
    assert "<script>window.REPLAY_INJECTED" not in html
    assert "private-control-capability" not in html
    assert [s["tick"] for s in visual["samples"]] == [0, 3, 6, 7]
    assert visual["samples"][-1] == original["samples"][-1]
    assert visual["visualization"]["sample_rate_hz"] == 20
    assert visual["visualization"]["not_physics_audit_recording"]
    assert visual["driver_timeline"]["red"][0] == {"request_s": 0.1, "response_s": 0.35, "latency_ms": 250}
    assert path.read_bytes() == before
    with pytest.raises(FileExistsError):
        export(path, target)


def test_checkpoint_export_retains_world_clock_and_episode_metadata(tmp_path):
    path, original = recording(tmp_path)
    original["episode_origin"] = {"tick": 600, "time_s": 10}
    original["episode"] = {"racer_id": "red", "gate_credits": 3, "outcome": "credited"}
    for sample in original["samples"]:
        sample["time"] += 10
        sample["tick"] += 600
    path.write_text(json.dumps(original))
    visual = visual_recording(path)
    assert visual["episode_origin"] == original["episode_origin"]
    assert visual["episode"] == original["episode"]
    assert visual["samples"][0]["time"] == 10
    assert visual["samples"][-1] == original["samples"][-1]


@pytest.mark.parametrize("stride", [0, 61, True, 1.5])
def test_invalid_visual_stride_is_rejected(tmp_path, stride):
    path, _ = recording(tmp_path)
    with pytest.raises(ValueError, match="stride"):
        visual_recording(path, stride)
