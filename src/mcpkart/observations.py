"""Bounded factual memory of observations the driver actually received.

No predicted states or chosen controls are generated here. A progress timestamp
records when a changed checkpoint count was observed, not the physics tick at
which the gate was crossed. Rescue clears motion history, not the race clock.
"""

from __future__ import annotations

import copy
import math
from collections import deque

HISTORY_WINDOW_S = 1.0
HISTORY_PRIOR_LIMIT = 3


def _wrap(angle: float) -> float:
    return (angle + math.pi) % (2 * math.pi) - math.pi


class ObservationHistory:
    """Consume successive raw observations and return detached, past-only facts."""

    def __init__(self) -> None:
        self._samples: deque[dict] = deque(maxlen=HISTORY_PRIOR_LIMIT+1)
        self._last: tuple[int, float] | None = None
        self._race_id: str | None = None
        self._reset_marker: tuple | None = None
        self._tracking_since: float | None = None
        self._initial_checkpoints = 0
        self._checkpoints = 0
        self._last_progress_at: float | None = None

    def observe(self, raw: dict) -> dict:
        """Current raw state is returned separately by the normal telemetry path.

        Repeated reads of one physics tick replace that tick's stored sample.
        Time rewinds or a new race identity start a new tracking session. Samples
        from a previous rescue epoch never appear as continuous recent motion.
        """
        tick, now = int(raw["tick"]), float(raw["time"])
        count = int(raw["progress"]["checkpoints_passed"])
        race_id = raw.get("race_id")
        if not math.isfinite(now) or tick < 0 or now < 0 or count < 0:
            raise ValueError("Observation history requires finite nonnegative racing time and progress")
        rewind = self._last is not None and (tick < self._last[0] or now < self._last[1])
        changed_race = self._race_id is not None and race_id is not None and self._race_id != race_id
        if rewind or changed_race or count < self._checkpoints:
            self.__init__()
        if race_id is not None:
            self._race_id = race_id
        if self._tracking_since is None:
            self._tracking_since = now
            self._initial_checkpoints = self._checkpoints = count
        if count > self._checkpoints:
            self._last_progress_at = now
            self._checkpoints = count
        rescue = raw.get("rescue", {})
        reset_marker = (rescue.get("count", raw["progress"].get("resets", 0)),
                        rescue.get("last_reset_tick"))
        if self._reset_marker is not None and reset_marker != self._reset_marker:
            self._samples.clear()
        self._reset_marker = reset_marker
        # Exclude the current tick on duplicate reads, and discard old samples
        # even after long network delays. They do not become recent by caching.
        prior = [sample for sample in self._samples
                 if sample["tick"] < tick and 0 < now-sample["time_s"] <= HISTORY_WINDOW_S + 1e-9][-HISTORY_PRIOR_LIMIT:]
        recent = [{**copy.deepcopy(sample), "age_s": round(now-sample["time_s"], 4)} for sample in prior]
        self._samples = deque(prior, maxlen=HISTORY_PRIOR_LIMIT+1)
        self._samples.append(self._sample(raw))
        self._last = tick, now
        origin = self._last_progress_at if self._last_progress_at is not None else self._tracking_since
        return {
            "recent_motion": {"window_s": HISTORY_WINDOW_S,
                              "maximum_prior_observations": HISTORY_PRIOR_LIMIT, "samples": recent},
            "checkpoint_clock": {
                "tracking_since_s": round(self._tracking_since, 4),
                "checkpoints_at_tracking_start": self._initial_checkpoints,
                "last_progress_observed_at_s": round(self._last_progress_at, 4)
                if self._last_progress_at is not None else None,
                "seconds_without_observed_checkpoint_progress": round(now-origin, 4),
                "current_checkpoints_passed": count,
                "timing_note": "Credit times are when this driver observed a higher count, not exact crossings. "
                               "No prior credit time is assumed before tracking began; rescue retains this clock.",
            },
        }

    @staticmethod
    def _sample(raw: dict) -> dict:
        kart, track = raw["kart"], raw["track"]
        speed = float(kart["speed"])
        road_heading = float(kart["heading"]) + float(track["heading_error"])
        velocity_angle = math.atan2(kart["vy"], kart["vx"])
        return {
            "tick": int(raw["tick"]), "time_s": float(raw["time"]),
            "offset_m": float(track["offset"]), "speed_m_s": speed,
            "nose_vs_road_deg": round(-math.degrees(track["heading_error"]), 3),
            "velocity_vs_road_deg": round(math.degrees(_wrap(velocity_angle-road_heading)), 3)
            if speed > 1e-6 else None,
            "road_lateral_m_s": round(-kart["vx"]*math.sin(road_heading)+kart["vy"]*math.cos(road_heading), 4),
            "yaw_deg_s": round(math.degrees(kart["yaw_rate"]), 3),
            "wheel_deg": round(math.degrees(kart["steering_angle"]), 3),
            "held_control": raw["control"],
            "checkpoints_passed": raw["progress"]["checkpoints_passed"],
            "on_road": track["on_road"],
        }
