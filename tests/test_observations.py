import copy
import math

import pytest

from mcpkart.observations import ObservationHistory
from mcpkart.sim import Simulation


def state(tick, *, gates=0, resets=0, race_id="race-a"):
    raw = Simulation().observation()
    raw.update(tick=tick, time=tick/60, race_id=race_id)
    raw["progress"].update(checkpoints_passed=gates, resets=resets)
    raw["rescue"].update(count=resets, last_reset_tick=60 if resets else None)
    return raw


def test_history_is_past_only_bounded_and_uses_actual_observation_times():
    history = ObservationHistory()
    for tick in (0, 7, 20, 33, 51):
        context = history.observe(state(tick))
    samples = context["recent_motion"]["samples"]
    assert [sample["tick"] for sample in samples] == [7, 20, 33]
    assert [sample["age_s"] for sample in samples] == [.7333, .5167, .3]
    assert not history.observe(state(120))["recent_motion"]["samples"]


def test_history_current_pose_signs_and_stationary_direction():
    raw = state(0)
    raw["kart"].update(heading=0, speed=10, vx=10, vy=0)
    raw["track"].update(heading_error=-math.pi/6, offset=2)
    history = ObservationHistory()
    history.observe(raw)
    sample = history.observe(state(12))["recent_motion"]["samples"][0]
    assert sample["nose_vs_road_deg"] == 30
    assert sample["velocity_vs_road_deg"] == 30
    assert sample["road_lateral_m_s"] == 5
    stationary = history.observe(state(24))["recent_motion"]["samples"][-1]
    assert stationary["velocity_vs_road_deg"] is None


def test_rescue_clears_motion_history_but_not_time_without_checkpoint_progress():
    history = ObservationHistory()
    history.observe(state(0))
    history.observe(state(12, gates=1))
    context = history.observe(state(60, gates=1, resets=1))
    assert context["recent_motion"]["samples"] == []
    assert context["checkpoint_clock"]["last_progress_observed_at_s"] == .2
    assert context["checkpoint_clock"]["seconds_without_observed_checkpoint_progress"] == .8
    after = history.observe(state(72, gates=1, resets=1))
    assert [s["tick"] for s in after["recent_motion"]["samples"]] == [60]


def test_late_tracking_does_not_invent_earlier_checkpoint_times():
    history = ObservationHistory()
    context = history.observe(state(600, gates=40))
    assert context["checkpoint_clock"]["tracking_since_s"] == 10
    assert context["checkpoint_clock"]["checkpoints_at_tracking_start"] == 40
    assert context["checkpoint_clock"]["last_progress_observed_at_s"] is None
    assert history.observe(state(660, gates=40))["checkpoint_clock"]["seconds_without_observed_checkpoint_progress"] == 1


@pytest.mark.parametrize("next_state", [state(0), state(45, gates=0), state(72, gates=1, race_id="race-b")])
def test_new_race_rewind_or_regressing_progress_clears_all_tracking(next_state):
    history = ObservationHistory()
    history.observe(state(12))
    history.observe(state(60, gates=1))
    context = history.observe(next_state)
    assert context["recent_motion"]["samples"] == []
    assert context["checkpoint_clock"]["last_progress_observed_at_s"] is None
    assert context["checkpoint_clock"]["seconds_without_observed_checkpoint_progress"] == 0


def test_duplicate_tick_does_not_create_history_and_outputs_do_not_alias_inputs():
    history = ObservationHistory()
    raw = state(0)
    original = copy.deepcopy(raw)
    assert history.observe(raw)["recent_motion"]["samples"] == []
    assert history.observe(raw)["recent_motion"]["samples"] == []
    context = history.observe(state(12))
    context["recent_motion"]["samples"][0]["offset_m"] = 999
    assert history.observe(state(24))["recent_motion"]["samples"][0]["offset_m"] != 999
    assert raw == original


def test_duplicate_read_preserves_all_three_prior_observations_when_buffer_is_full():
    history = ObservationHistory()
    for tick in (0, 12, 24, 36):
        context = history.observe(state(tick))
    assert [sample["tick"] for sample in context["recent_motion"]["samples"]] == [0, 12, 24]
    assert history.observe(state(36)) == context


def test_invalid_time_is_rejected():
    raw = state(0)
    raw["time"] = float("nan")
    with pytest.raises(ValueError, match="finite nonnegative"):
        ObservationHistory().observe(raw)
