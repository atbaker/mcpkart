"""Deterministic, unassisted solo kart simulation (metres, seconds, radians).

World coordinates are right handed: positive heading and steering turn left.
Lookahead coordinates are relative to the kart: x ahead, y left. Physics never
consults the reference driver. Its output is only used by an explicit caller.
"""

from __future__ import annotations

import math
import random
from bisect import bisect_right
from dataclasses import asdict, dataclass, replace
from itertools import pairwise

DT = 1 / 60
VERSION = "solo-v2-rescue"
COURSES = ("winding", "oval", "oval_clockwise", "circle", "circle_clockwise",
           "stadium", "stadium_clockwise")

_STEERING = (("hard_right", -1.0), ("right", -0.5), ("straight", 0.0),
             ("left", 0.5), ("hard_left", 1.0))
_PEDALS = (("accelerate", 1.0, 0.0), ("coast", 0.0, 0.0), ("brake", 0.0, 1.0))
ACTIONS = {
    f"{name}_{pedal}": {"steer": steer, "throttle": throttle, "brake": brake,
                          "description": f"Steer {steer:+g}; {pedal}."}
    for name, steer in _STEERING
    for pedal, throttle, brake in _PEDALS
}


def wrap(angle: float) -> float:
    return (angle + math.pi) % (2 * math.pi) - math.pi


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class Handling:
    max_speed: float = 24.0
    acceleration: float = 12.0
    braking: float = 24.0
    max_steering_angle: float = 0.32
    wheelbase: float = 1.8
    steering_response: float = 0.12
    yaw_response: float = 0.10
    lateral_grip: float = 13.0
    rolling_drag: float = 0.35
    aerodynamic_drag: float = 0.006
    grass_acceleration: float = 4.0
    grass_drag: float = 1.1
    grass_grip: float = 8.0


class Track:
    """Closed winding centreline, evenly sampled for geometry and gate checks."""

    width = 9.0

    def __init__(self, course: str = "winding", width: float = 9.0) -> None:
        if course not in COURSES:
            raise ValueError(f"Unknown course: {course}")
        if isinstance(width, bool) or not math.isfinite(width) or not 2 <= width <= 40:
            raise ValueError("Road width must be finite and between 2 and 40 metres")
        self.course, self.width = course, float(width)
        anchors = [(0, -25), (30, -25), (45, -10), (42, 8), (28, 17),
                   (30, 32), (8, 40), (-25, 30), (-40, 10), (-30, -18)]
        dense: list[tuple[float, float]] = []
        for i in range(len(anchors)):
            p0, p1, p2, p3 = (anchors[(i + j) % len(anchors)] for j in (-1, 0, 1, 2))
            for j in range(100):
                t = j / 100
                dense.append(tuple(0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t
                             + (2*p0[k] - 5*p1[k] + 4*p2[k] - p3[k]) * t*t
                             + (-p0[k] + 3*p1[k] - 3*p2[k] + p3[k]) * t*t*t)
                                   for k in (0, 1)))
        dense.append(dense[0])
        if course != "winding":
            # Analytic, symmetric geometry; no driving policy or racing line.
            major = 45.0 if course.startswith("oval") else 30.0
            direction = -1 if course.endswith("clockwise") else 1
            dense = [(direction * major * math.cos(-math.pi/2 + 2*math.pi*i/1000),
                      30.0 * math.sin(-math.pi/2 + 2*math.pi*i/1000)) for i in range(1000)]
            dense.append(dense[0])
        if course.startswith("stadium"):
            # Two 60m straights joined tangentially by radius-30 semicircles.
            # Start halfway along the lower straight, facing right (CCW).
            dense = []
            arc = math.pi * 30
            for i in range(1000):
                s = (120 + 2*arc) * i / 1000
                if s < 30:
                    x, y = s, -30.0
                elif s < 30 + arc:
                    angle = -math.pi/2 + (s-30)/30
                    x, y = 30+30*math.cos(angle), 30*math.sin(angle)
                elif s < 90 + arc:
                    x, y = 30-(s-30-arc), 30.0
                elif s < 90 + 2*arc:
                    angle = math.pi/2 + (s-90-arc)/30
                    x, y = -30+30*math.cos(angle), 30*math.sin(angle)
                else:
                    x, y = -30+(s-90-2*arc), -30.0
                dense.append((direction*x, y))
            dense.append(dense[0])
        lengths = [0.0]
        for a, b in pairwise(dense):
            lengths.append(lengths[-1] + math.dist(a, b))
        count = 256
        self.points = []
        for i in range(count):
            s = lengths[-1] * i / count
            j = min(bisect_right(lengths, s) - 1, len(dense) - 2)
            t = (s - lengths[j]) / (lengths[j + 1] - lengths[j])
            self.points.append(tuple(a + (b-a)*t for a, b in zip(dense[j], dense[j+1])))
        self.lengths = [0.0]
        self.segments = []
        for a, b in zip(self.points, self.points[1:] + self.points[:1]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            self.segments.append((a[0], a[1], dx, dy, length, dx/length, dy/length))
            self.lengths.append(self.lengths[-1] + length)
        self.length = self.lengths[-1]
        self.headings = []
        for i in range(count):
            a, b = self.points[(i-1) % count], self.points[(i+1) % count]
            self.headings.append(math.atan2(b[1]-a[1], b[0]-a[0]))
        self.curvatures = [wrap(self.headings[(i+1) % count] - self.headings[(i-1) % count])
                           / (self.length/count*2) for i in range(count)]
        self.checkpoints = [self.at(self.length * i / 40) for i in range(40)]

    def at(self, distance: float) -> tuple[float, float, float, float]:
        distance %= self.length
        i = min(bisect_right(self.lengths, distance) - 1, len(self.points) - 1)
        x, y, dx, dy, length, _, _ = self.segments[i]
        t = (distance - self.lengths[i]) / length
        j = (i+1) % len(self.points)
        heading = self.headings[i] + wrap(self.headings[j]-self.headings[i]) * t
        curvature = self.curvatures[i] + (self.curvatures[j]-self.curvatures[i]) * t
        return x+dx*t, y+dy*t, heading, curvature

    def project(self, x: float, y: float) -> tuple[float, float, float]:
        best = math.inf
        nearest_s = offset = 0.0
        for i, (ax, ay, dx, dy, length, tx, ty) in enumerate(self.segments):
            t = clamp(((x-ax)*dx + (y-ay)*dy) / (length*length), 0.0, 1.0)
            ex, ey = x - ax - dx*t, y - ay - dy*t
            squared = ex*ex + ey*ey
            if squared < best:
                best = squared
                nearest_s = self.lengths[i] + length*t
                offset = math.copysign(math.sqrt(squared), tx*ey - ty*ex)
        return nearest_s % self.length, offset, math.sqrt(best)

    def as_dict(self) -> dict:
        result = {"points": [[round(x, 5), round(y, 5)] for x, y in self.points],
                "width": self.width, "length": self.length,
                "checkpoints": [{"x": x, "y": y, "heading": heading}
                                for x, y, heading, _ in self.checkpoints]}
        if self.course != "winding":
            result["course"] = self.course
        return result


class Simulation:
    def __init__(self, seed: int = 0, laps: int = 3,
                 reset_after_s: float | None = 3.0, *, course: str = "winding",
                 road_width: float = 9.0, max_speed: float = 24.0,
                 max_steering_angle: float = 0.32) -> None:
        if laps < 1:
            raise ValueError("laps must be positive")
        if reset_after_s is not None and (
            isinstance(reset_after_s, bool) or not math.isfinite(reset_after_s) or reset_after_s <= 0
        ):
            raise ValueError("reset_after_s must be positive and finite, or None")
        self.seed, self.laps = seed, laps
        self.reset_after_s = reset_after_s
        for name, value, lower, upper in (("max_speed", max_speed, .5, 60),
                                           ("max_steering_angle", max_steering_angle, .01, .6)):
            if isinstance(value, bool) or not math.isfinite(value) or not lower <= value <= upper:
                raise ValueError(f"{name} must be finite and between {lower} and {upper}")
        self.track = Track(course, road_width)
        self.handling = replace(Handling(), max_speed=float(max_speed),
                                max_steering_angle=float(max_steering_angle))
        rng = random.Random(seed)
        x, y, heading, _ = self.track.at(0)
        offset = rng.uniform(-0.35, 0.35)
        self.x, self.y = x - math.sin(heading)*offset, y + math.cos(heading)*offset
        self.heading = heading + rng.uniform(-0.025, 0.025)
        self.vx = self.vy = self.steering = self.yaw_rate = 0.0
        self.tick, self.elapsed = 0, 0.0
        self.finished = False
        self.action_id = "straight_coast"
        self.next_checkpoint = 1
        self.checkpoints_passed = self.laps_completed = 0
        self.lap_times: list[float] = []
        self.offroad_time = self.distance_travelled = 0.0
        self.max_speed_seen = 0.0
        self.s, self.offset, _ = self.track.project(self.x, self.y)
        self.departure_s = self.s
        self.offroad_elapsed = 0.0
        self.last_reset_tick: int | None = None
        self.reset_events: list[dict] = []

    @classmethod
    def from_config(cls, config: dict, seed: int = 0) -> Simulation:
        """Reconstruct a declared course/handling configuration, rejecting drift."""
        try:
            sim = cls(seed=seed, laps=config["laps"], reset_after_s=config["rescue"]["after_s"],
                      course=config["track"].get("course", "winding"),
                      road_width=config["track"]["width"], max_speed=config["handling"]["max_speed"],
                      max_steering_angle=config["handling"]["max_steering_angle"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Saved simulation configuration is invalid") from exc
        if sim.config() != config:
            raise ValueError("Saved simulation configuration differs from supported physics")
        return sim

    @property
    def speed(self) -> float:
        return math.hypot(self.vx, self.vy)

    def set_control(self, action_id: str) -> None:
        if action_id not in ACTIONS:
            raise ValueError(f"unknown action: {action_id}")
        self.action_id = action_id

    def _check_progress(self, old_x: float, old_y: float) -> None:
        """Cross the next finite gate forward, and only on its road surface."""
        gx, gy, heading, _ = self.track.checkpoints[self.next_checkpoint]
        tx, ty = math.cos(heading), math.sin(heading)
        before = (old_x-gx)*tx + (old_y-gy)*ty
        after = (self.x-gx)*tx + (self.y-gy)*ty
        if not (before <= 0 < after):
            return
        fraction = -before / (after-before)
        cross_x = old_x + (self.x-old_x)*fraction
        cross_y = old_y + (self.y-old_y)*fraction
        lateral = -(cross_x-gx)*ty + (cross_y-gy)*tx
        if abs(lateral) > self.track.width/2:
            return
        self.checkpoints_passed += 1
        self.next_checkpoint = (self.next_checkpoint+1) % len(self.track.checkpoints)
        if self.checkpoints_passed % len(self.track.checkpoints) == 0:
            self.laps_completed += 1
            self.lap_times.append(self.elapsed - sum(self.lap_times))
            self.finished = self.laps_completed == self.laps

    def step(self, dt: float = DT) -> None:
        if dt <= 0 or dt > DT*1.000001:
            raise ValueError("physics step must be positive and no larger than DT")
        if self.finished:
            return
        old_x, old_y, old_s = self.x, self.y, self.s
        h, action = self.handling, ACTIONS[self.action_id]
        onroad = abs(self.offset) <= self.track.width/2
        if not onroad:
            self.offroad_time += dt
            self.offroad_elapsed += dt
        else:
            self.offroad_elapsed = 0.0
        self.steering += (action["steer"]*h.max_steering_angle-self.steering) * (1-math.exp(-dt/h.steering_response))
        speed = self.speed
        forward_speed = max(0.0, self.vx*math.cos(self.heading) + self.vy*math.sin(self.heading))
        grip = h.lateral_grip if onroad else h.grass_grip
        desired_yaw = forward_speed/h.wheelbase * math.tan(self.steering)
        max_yaw = grip/max(speed, 2.0)
        desired_yaw = clamp(desired_yaw, -max_yaw, max_yaw)
        self.yaw_rate += (desired_yaw-self.yaw_rate) * (1-math.exp(-dt/h.yaw_response))
        self.heading = wrap(self.heading + self.yaw_rate*dt)
        fx, fy = math.cos(self.heading), math.sin(self.heading)
        lateral = -self.vx*fy + self.vy*fx
        lateral_change = clamp(-lateral, -grip*dt, grip*dt)
        self.vx -= fy*lateral_change
        self.vy += fx*lateral_change
        speed = self.speed
        drag = h.rolling_drag + h.aerodynamic_drag*speed*speed
        if not onroad:
            drag += h.grass_drag*speed
        acceleration = (h.acceleration if onroad else h.grass_acceleration)*action["throttle"]
        acceleration -= h.braking*action["brake"] + drag
        if acceleration < 0:
            reduction = max(0.0, speed+acceleration*dt)/speed if speed else 0.0
            self.vx *= reduction
            self.vy *= reduction
        else:
            self.vx += fx*acceleration*dt
            self.vy += fy*acceleration*dt
        speed = self.speed
        if speed > h.max_speed:
            self.vx *= h.max_speed/speed
            self.vy *= h.max_speed/speed
        self.x += self.vx*dt
        self.y += self.vy*dt
        self.tick += 1
        self.elapsed += dt
        self.distance_travelled += math.dist((old_x, old_y), (self.x, self.y))
        self.max_speed_seen = max(self.max_speed_seen, self.speed)
        self.s, self.offset, _ = self.track.project(self.x, self.y)
        self._check_progress(old_x, old_y)
        if abs(self.offset) <= self.track.width/2:
            self.offroad_elapsed = 0.0
        elif onroad:
            # The last position on the road is a departure anchor, even if the
            # kart subsequently travels across grass to a different section.
            self.departure_s = old_s
        if (not self.finished and abs(self.offset) > self.track.width/2
                and self.reset_after_s is not None
                and self.offroad_elapsed + 1e-9 >= self.reset_after_s):
            self._rescue()

    def _rescue(self) -> None:
        """Respawn behind departure without advancing progress or moving time."""
        respawn_s = (self.departure_s - 1.0) % self.track.length
        self.x, self.y, self.heading, _ = self.track.at(respawn_s)
        self.heading = wrap(self.heading)
        self.vx = self.vy = self.yaw_rate = self.steering = 0.0
        previous_action = self.action_id
        self.action_id = "straight_coast"
        self.s, self.offset, _ = self.track.project(self.x, self.y)
        self.last_reset_tick = self.tick
        self.reset_events.append({
            "tick": self.tick, "time": self.elapsed,
            "departure_s": self.departure_s, "respawn_s": respawn_s,
            "x": self.x, "y": self.y, "heading": self.heading,
            "offroad_elapsed": self.offroad_elapsed,
            "previous_action": previous_action, "control": self.action_id,
        })
        self.offroad_elapsed = 0.0

    def observation(self) -> dict:
        _, _, track_heading, _ = self.track.at(self.s)
        fx, fy = math.cos(self.heading), math.sin(self.heading)
        lookahead = []
        for distance in (0, 3, 6, 10, 15, 22, 32, 45, 60):
            x, y, _, curvature = self.track.at(self.s+distance)
            dx, dy = x-self.x, y-self.y
            lookahead.append({"distance": distance, "x": round(dx*fx+dy*fy, 3),
                              "y": round(-dx*fy+dy*fx, 3), "curvature": round(curvature, 5)})
        return {"tick": self.tick, "time": round(self.elapsed, 4),
                "kart": {"x": round(self.x, 4), "y": round(self.y, 4),
                         "heading": round(self.heading, 5), "speed": round(self.speed, 4),
                         "vx": round(self.vx, 4), "vy": round(self.vy, 4),
                         "yaw_rate": round(self.yaw_rate, 5), "steering_angle": round(self.steering, 5)},
                "track": {"width": self.track.width, "offset": round(self.offset, 4),
                          "heading_error": round(wrap(track_heading-self.heading), 5),
                          "on_road": abs(self.offset) <= self.track.width/2,
                          "lookahead": lookahead},
                "progress": {"lap": min(self.laps_completed+1, self.laps),
                             "laps_completed": self.laps_completed, "laps": self.laps,
                             "checkpoint": self.next_checkpoint,
                             "checkpoints_passed": self.checkpoints_passed,
                             "checkpoints_per_lap": len(self.track.checkpoints),
                             "resets": len(self.reset_events),
                             "track_distance": round(self.s, 3), "finished": self.finished},
                "rescue": {"after_s": self.reset_after_s,
                           "offroad_elapsed": round(self.offroad_elapsed, 4),
                           "count": len(self.reset_events), "last_reset_tick": self.last_reset_tick},
                "control": self.action_id}

    def summary(self) -> dict:
        return {"seed": self.seed, "finished": self.finished, "elapsed": self.elapsed,
                "ticks": self.tick, "laps_completed": self.laps_completed,
                "checkpoints_passed": self.checkpoints_passed, "lap_times": self.lap_times[:],
                "offroad_time": self.offroad_time, "distance": self.distance_travelled,
                "max_speed": self.max_speed_seen, "resets": len(self.reset_events),
                "reset_events": [event.copy() for event in self.reset_events]}

    def config(self) -> dict:
        return {"version": VERSION, "dt": DT, "laps": self.laps,
                "handling": asdict(self.handling), "track": self.track.as_dict(),
                "actions": ACTIONS,
                "rescue": {"after_s": self.reset_after_s, "backtrack_m": 1.0,
                           "control_after": "straight_coast", "speed_after": 0.0,
                           "checkpoint_credit": False},
                "coordinates": "metres, seconds, radians; heading/steer positive left; ego x ahead y left",
                "start_conditions": {"lateral_uniform": [-0.35, 0.35], "heading_uniform": [-0.025, 0.025]}}


def scripted_action(observation: dict, *, max_steering_angle: float = 0.32) -> str:
    """Reference-only geometric driver, using the public telemetry and menu."""
    if not math.isfinite(max_steering_angle) or max_steering_angle <= 0:
        raise ValueError("Reference steering range must be finite and positive")
    kart, track = observation["kart"], observation["track"]
    speed = kart["speed"]
    target_distance = 4.0 + speed*0.5
    point = min(track["lookahead"], key=lambda p: abs(p["distance"]-target_distance))
    # A fixed short horizon anticipates steering/heading response. It uses only
    # the observed yaw and velocity; it neither reads simulation state nor
    # changes the kart's controls between the caller's action submissions.
    anticipation = 0.2
    rotation = kart["yaw_rate"]*anticipation
    px, py = point["x"]-speed*anticipation, point["y"]
    px, py = (px*math.cos(rotation)+py*math.sin(rotation),
              -px*math.sin(rotation)+py*math.cos(rotation))
    desired_angle = math.atan2(2*1.8*py, px*px + py*py)
    steer = clamp(desired_angle/max_steering_angle, -1, 1)
    steering_name = min(_STEERING, key=lambda item: abs(item[1]-steer))[0]
    target_speed = 24.0
    for point in track["lookahead"]:
        curve_speed_squared = 7.0 / max(abs(point["curvature"]), 0.0001)
        target_speed = min(target_speed, math.sqrt(curve_speed_squared + 2*13.0*max(0, point["distance"]-3)))
    if abs(track["offset"]) > track["width"]*0.35:
        target_speed = min(target_speed, 10.0)
    if speed > target_speed + 0.5:
        pedal = "brake"
    elif speed < target_speed - 0.2:
        pedal = "accelerate"
    else:
        pedal = "coast"
    return f"{steering_name}_{pedal}"
