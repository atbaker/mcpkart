"""Deterministic two-kart world with equal-mass circular contact.

No input is selected here. A shared tick integrates both karts, resolves their
contact, then credits finite gates and applies the ordinary rescue rule.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import asdict

from .sim import DT, Simulation, clamp, wrap

RACERS = ("red", "blue")
DUEL_VERSION = "duel-v1-discs"
CHECKPOINT_VERSION = "duel-checkpoint-v1"
WORLD_FIELDS = (
    "tick", "elapsed", "finish_ticks", "phase_until", "contacts", "contact_count", "events",
    "_touching", "_leader",
)
KART_FIELDS = (
    "x", "y", "heading", "vx", "vy", "steering", "yaw_rate", "tick", "elapsed", "finished",
    "action_id", "next_checkpoint", "checkpoints_passed", "laps_completed", "lap_times",
    "offroad_time", "distance_travelled", "max_speed_seen", "s", "offset", "departure_s",
    "offroad_elapsed", "last_reset_tick", "reset_events",
)


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


class DuelKart(Simulation):
    def __init__(self, *, radius: float, distance: float, offset: float, heading_error: float, **kwargs):
        self.radius = radius
        super().__init__(start_pose={"offset_m": offset, "heading_error_rad": heading_error}, **kwargs)
        x, y, heading, _ = self.track.at(distance)
        self.x, self.y = x - math.sin(heading) * offset, y + math.cos(heading) * offset
        self.heading = wrap(heading + heading_error)
        self.s, self.offset, _ = self.track.project(self.x, self.y)
        self.departure_s = self.s

    def _road_half_width(self):
        return self.track.width / 2 - self.radius


class DuelSimulation:
    def __init__(
        self,
        seed=0,
        *,
        course="stadium",
        road_width=24,
        max_speed=12,
        max_steering_angle=0.12,
        laps=3,
        reset_after_s=3.0,
        radius=1.0,
        restitution=0.15,
        phase_s=1.0,
        contact="solid",
        grid=None,
        checkpoint=None,
        episode=None,
    ):
        if not _finite(radius) or not 0 < radius <= 3 or not _finite(road_width) or road_width <= radius * 2:
            raise ValueError("Kart radius must fit inside the road")
        if not _finite(restitution) or not 0 <= restitution <= 1:
            raise ValueError("Contact restitution must be between zero and one")
        if not _finite(phase_s) or not 0 <= phase_s <= 5:
            raise ValueError("Rescue phase duration must be between zero and five seconds")
        if contact not in ("solid", "ghost"):
            raise ValueError("Contact must be solid or ghost")
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError("Seed must be an integer")
        if not isinstance(laps, int) or isinstance(laps, bool) or not 1 <= laps <= 10:
            raise ValueError("Laps must be an integer from one to ten")
        if grid is None:
            grid = [
                {"distance_m": 0.0, "offset_m": -2.0, "heading_error_rad": 0.0},
                {"distance_m": 0.0, "offset_m": 2.0, "heading_error_rad": 0.0},
            ]
        if not isinstance(grid, list) or len(grid) != 2:
            raise ValueError("Exactly two grid positions are required")
        self.grid = []
        for item in grid:
            if not isinstance(item, dict) or set(item) != {"distance_m", "offset_m", "heading_error_rad"}:
                raise ValueError("Grid requires distance, offset and heading error")
            if (
                not all(_finite(v) for v in item.values())
                or not -8 <= item["distance_m"] <= 0
                or abs(item["offset_m"]) > road_width / 2 - radius
                or abs(item["heading_error_rad"]) > math.pi
            ):
                raise ValueError("Grid must be finite, on-road and before the first gate")
            self.grid.append({key: float(value) for key, value in item.items()})
        self.seed, self.radius, self.restitution = seed, float(radius), float(restitution)
        self.contact, self.phase_s = contact, float(phase_s)
        self.karts = {
            rid: DuelKart(
                radius=self.radius,
                distance=g["distance_m"],
                offset=g["offset_m"],
                heading_error=g["heading_error_rad"],
                seed=seed + i,
                course=course,
                road_width=road_width,
                max_speed=max_speed,
                max_steering_angle=max_steering_angle,
                laps=laps,
                reset_after_s=reset_after_s,
            )
            for i, (rid, g) in enumerate(zip(RACERS, self.grid, strict=True))
        }
        self.track = self.karts["red"].track
        if math.dist(self._position("red"), self._position("blue")) < self.radius * 2:
            raise ValueError("Starting footprints must not overlap")
        self.tick, self.elapsed = 0, 0.0
        self.finish_ticks = {rid: None for rid in RACERS}
        self.phase_until = {rid: 0 for rid in RACERS}
        self.contacts: list[dict] = []
        self.contact_count = 0
        self.events: list[dict] = []
        self._touching = False
        self._leader = None
        self._checkpoint_input = None
        self.episode = None
        if checkpoint is not None:
            self._restore_checkpoint(checkpoint)
            self._checkpoint_input = copy.deepcopy(checkpoint)
        if episode is not None:
            if (
                not isinstance(episode, dict) or set(episode) != {"racer_id", "gate_credits"}
                or episode["racer_id"] not in RACERS
                or isinstance(episode["gate_credits"], bool)
                or not isinstance(episode["gate_credits"], int)
                or not 1 <= episode["gate_credits"] <= 5
            ):
                raise ValueError("Episode requires a racer and one to five new gate credits")
            if self.karts[episode["racer_id"]].finished:
                raise ValueError("Episode target must be unfinished")
            self.episode = copy.deepcopy(episode)
        self._episode_baseline = {
            r: (k.checkpoints_passed, len(k.reset_events)) for r, k in self.karts.items()
        }

    def _base_config_hash(self):
        config = self.config()
        config["parameters"].pop("checkpoint", None)
        config["parameters"].pop("episode", None)

        def canonical(value):
            if isinstance(value, dict):
                return {key: canonical(item) for key, item in value.items()}
            if isinstance(value, list):
                return [canonical(item) for item in value]
            if isinstance(value, float) and value.is_integer():
                return int(value)
            return value

        return hashlib.sha256(json.dumps(canonical(config), sort_keys=True, allow_nan=False).encode()).hexdigest()

    def checkpoint(self):
        """Full-precision physical state, including held inputs and contact/rescue memory."""
        return {
            "version": CHECKPOINT_VERSION,
            "base_config_sha256": self._base_config_hash(),
            "world": {key: copy.deepcopy(getattr(self, key)) for key in WORLD_FIELDS},
            "karts": {
                r: {key: copy.deepcopy(getattr(k, key)) for key in KART_FIELDS}
                for r, k in self.karts.items()
            },
        }

    def _restore_checkpoint(self, checkpoint):
        from .sim import ACTIONS

        try:
            if (
                not isinstance(checkpoint, dict)
                or set(checkpoint) != {"version", "base_config_sha256", "world", "karts"}
                or checkpoint["version"] != CHECKPOINT_VERSION
                or checkpoint["base_config_sha256"] != self._base_config_hash()
                or set(checkpoint["world"]) != set(WORLD_FIELDS)
                or set(checkpoint["karts"]) != set(RACERS)
                or len(json.dumps(checkpoint, allow_nan=False)) > 1024 * 1024
            ):
                raise ValueError("Checkpoint schema or game configuration differs")

            def integer(value):
                return isinstance(value, int) and not isinstance(value, bool) and value >= 0

            world = checkpoint["world"]
            if (
                not integer(world["tick"]) or not _finite(world["elapsed"])
                or abs(world["elapsed"] - world["tick"] * DT) > 1e-6
                or not isinstance(world["_touching"], bool) or world["_leader"] not in (*RACERS, None)
                or not integer(world["contact_count"])
                or not isinstance(world["contacts"], list) or not isinstance(world["events"], list)
                or set(world["finish_ticks"]) != set(RACERS) or set(world["phase_until"]) != set(RACERS)
            ):
                raise ValueError("Invalid checkpoint world clock or contact state")
            numeric = set(KART_FIELDS) - {
                "finished", "action_id", "lap_times", "last_reset_tick", "reset_events"
            }
            for r in RACERS:
                state = checkpoint["karts"][r]
                if set(state) != set(KART_FIELDS) or not all(_finite(state[key]) for key in numeric):
                    raise ValueError("Checkpoint kart fields must be complete and finite")
                if (
                    not all(integer(state[key]) for key in ("tick", "next_checkpoint", "checkpoints_passed", "laps_completed"))
                    or not isinstance(state["finished"], bool) or state["action_id"] not in ACTIONS
                    or not isinstance(state["lap_times"], list) or not all(_finite(t) and t >= 0 for t in state["lap_times"])
                    or not isinstance(state["reset_events"], list)
                    or state["last_reset_tick"] is not None and (
                        not integer(state["last_reset_tick"]) or state["last_reset_tick"] > state["tick"]
                    )
                    or state["tick"] > world["tick"]
                    or not state["finished"] and state["tick"] != world["tick"]
                    or abs(state["elapsed"] - state["tick"] * DT) > 1e-6
                    or state["checkpoints_passed"] > self.karts[r].laps * 40
                    or state["next_checkpoint"] != (state["checkpoints_passed"] + 1) % 40
                    or state["laps_completed"] != state["checkpoints_passed"] // 40
                    or state["finished"] != (state["laps_completed"] == self.karts[r].laps)
                    or any(state[key] < 0 for key in (
                        "offroad_time", "distance_travelled", "max_speed_seen", "offroad_elapsed"
                    ))
                    or abs(state["steering"]) > self.karts[r].handling.max_steering_angle + 1e-9
                    or math.hypot(state["vx"], state["vy"]) > self.karts[r].handling.max_speed + 1e-8
                    or not integer(world["phase_until"][r])
                    or world["finish_ticks"][r] is not None and (
                        not integer(world["finish_ticks"][r]) or world["finish_ticks"][r] > world["tick"]
                    )
                    or (world["finish_ticks"][r] is not None) != state["finished"]
                ):
                    raise ValueError("Incoherent checkpoint kart progress or dynamics")
                s, offset, _ = self.track.project(state["x"], state["y"])
                if abs(s - state["s"]) > 1e-8 or abs(offset - state["offset"]) > 1e-8:
                    raise ValueError("Checkpoint road projection differs from position")
            for key in WORLD_FIELDS:
                setattr(self, key, copy.deepcopy(world[key]))
            for r in RACERS:
                for key in KART_FIELDS:
                    setattr(self.karts[r], key, copy.deepcopy(checkpoint["karts"][r][key]))
        except (KeyError, TypeError, OverflowError) as error:
            raise ValueError("Malformed checkpoint") from error

    def episode_outcome(self):
        if self.episode is None:
            return None
        rid = self.episode["racer_id"]
        k = self.karts[rid]
        credit, resets = self._episode_baseline[rid]
        if len(k.reset_events) > resets:
            return "rescued"
        if k.checkpoints_passed - credit >= self.episode["gate_credits"]:
            return "credited"
        return None

    @classmethod
    def from_config(cls, config):
        if config.get("version") != DUEL_VERSION:
            raise ValueError("Unsupported duel configuration")
        sim = cls(**config["parameters"])
        if sim.config() != config:
            raise ValueError("Duel configuration differs from supported physics")
        return sim

    @property
    def finished(self):
        return all(k.finished for k in self.karts.values())

    def _position(self, rid):
        k = self.karts[rid]
        return k.x, k.y

    def phased(self, rid):
        return self.karts[rid].finished or self.phase_until[rid] > 0

    def set_control(self, rid, action_id):
        if rid not in RACERS:
            raise ValueError("Unknown racer")
        if self.karts[rid].finished:
            raise ValueError("Racer has already finished")
        self.karts[rid].set_control(action_id)

    def _contact(self, old):
        a, b = (self.karts[rid] for rid in RACERS)
        if self.contact == "ghost" or any(self.phased(rid) for rid in RACERS):
            self._touching = False
            return {}
        ax, ay = old["red"]
        bx, by = old["blue"]
        px, py = bx - ax, by - ay
        da, db = (a.x - ax, a.y - ay), (b.x - bx, b.y - by)
        dx, dy = db[0] - da[0], db[1] - da[1]
        radius = self.radius * 2
        aa, bb, cc = dx * dx + dy * dy, 2 * (px * dx + py * dy), px * px + py * py - radius * radius
        toi = None
        if cc < -1e-9:
            toi = 0.0
        elif aa > 1e-18 and bb < 0:
            discriminant = bb * bb - 4 * aa * cc
            if discriminant >= 0:
                root = (-bb - math.sqrt(discriminant)) / (2 * aa)
                if -1e-9 <= root <= 1 + 1e-9:
                    toi = clamp(root, 0.0, 1.0)
        distance = math.hypot(b.x - a.x, b.y - a.y)
        if toi is None:
            if distance > radius + 0.05:
                self._touching = False
            return {}
        ca, cb = (ax + da[0] * toi, ay + da[1] * toi), (bx + db[0] * toi, by + db[1] * toi)
        nx, ny = cb[0] - ca[0], cb[1] - ca[1]
        length = math.hypot(nx, ny)
        if length <= 1e-12:
            nx, ny = 1.0, 0.0
        else:
            nx, ny = nx / length, ny / length
        closing = (b.vx - a.vx) * nx + (b.vy - a.vy) * ny
        impulse = max(0.0, -(1 + self.restitution) * closing / 2)
        a.vx -= impulse * nx
        a.vy -= impulse * ny
        b.vx += impulse * nx
        b.vy += impulse * ny
        for kart in (a, b):
            if kart.speed > kart.handling.max_speed:
                scale = kart.handling.max_speed / kart.speed
                kart.vx *= scale
                kart.vy *= scale
        remaining = DT * (1 - toi)
        a.x, a.y = ca[0] + a.vx * remaining, ca[1] + a.vy * remaining
        b.x, b.y = cb[0] + b.vx * remaining, cb[1] + b.vy * remaining
        # Tiny solver overlap is separation only, never a progress-credit path.
        distance = math.hypot(b.x - a.x, b.y - a.y)
        correction = max(0.0, radius - distance) / 2
        end_a, end_b = (a.x, a.y), (b.x, b.y)
        a.x -= correction * nx
        a.y -= correction * ny
        b.x += correction * nx
        b.y += correction * ny
        record = {
            "tick": self.tick + 1,
            "time": (self.tick + 1) * DT,
            "toi_fraction": toi,
            "normal": [nx, ny],
            "closing_speed_m_s": max(0.0, -closing),
            "impulse_m_s": impulse,
            "onset": not self._touching,
            "positions_at_contact": {"red": list(ca), "blue": list(cb)},
            "separation_correction_m": correction,
        }
        if impulse > 1e-9 or correction > 1e-9:
            self.contacts.append(record)
            if not self._touching:
                self.contact_count += 1
                self.events.append({"type": "contact", **record})
            self._touching = True
        return {"red": [old["red"], ca, end_a], "blue": [old["blue"], cb, end_b]}

    def step(self):
        if self.finished:
            return
        separated = math.dist(self._position("red"), self._position("blue")) >= self.radius * 2 + 0.001
        for rid in RACERS:
            if self.phase_until[rid] and self.tick >= self.phase_until[rid] and separated:
                self.phase_until[rid] = 0
                self.events.append(
                    {"type": "phase_end", "racer_id": rid, "tick": self.tick, "time": self.elapsed}
                )
        old = {rid: self._position(rid) for rid in RACERS}
        resets = {rid: len(k.reset_events) for rid, k in self.karts.items()}
        contexts = {rid: k._advance_dynamics() for rid, k in self.karts.items()}
        paths = self._contact(old)
        self.tick += 1
        self.elapsed += DT
        for rid, k in self.karts.items():
            if contexts[rid] is None:
                continue
            k._complete_step(contexts[rid], paths.get(rid))
            if len(k.reset_events) != resets[rid]:
                self.phase_until[rid] = self.tick + math.ceil(self.phase_s / DT)
                self.events.append({"type": "rescue", "racer_id": rid, **k.reset_events[-1]})
            if k.finished and self.finish_ticks[rid] is None:
                self.finish_ticks[rid] = self.tick
                k.vx = k.vy = k.yaw_rate = 0.0
                k.action_id = "straight_coast"
                self.events.append(
                    {"type": "finish", "racer_id": rid, "tick": self.tick, "time": self.elapsed}
                )
        leader = self.leader()
        if leader is not None:
            if self._leader is not None and leader != self._leader:
                self.events.append(
                    {
                        "type": "lead_change",
                        "from": self._leader,
                        "to": leader,
                        "tick": self.tick,
                        "time": self.elapsed,
                        "rescue_this_tick": any(
                            len(k.reset_events) != resets[r] for r, k in self.karts.items()
                        ),
                    }
                )
            self._leader = leader

    def progress_m(self, rid):
        k = self.karts[rid]
        count = len(self.track.checkpoints)
        segment = self.track.length / count
        if k.finished:
            return k.laps * self.track.length
        previous = ((k.next_checkpoint - 1) % count) * segment
        delta = (k.s - previous + self.track.length / 2) % self.track.length - self.track.length / 2
        return (k.checkpoints_passed + clamp(delta / segment, 0.0, 0.999999)) * segment

    def leader(self):
        finished = [r for r in RACERS if self.finish_ticks[r] is not None]
        if finished:
            earliest = min(self.finish_ticks[r] for r in finished)
            winners = [r for r in finished if self.finish_ticks[r] == earliest]
            return winners[0] if len(winners) == 1 else None
        scores = {r: self.progress_m(r) for r in RACERS}
        return None if abs(scores["red"] - scores["blue"]) < 0.5 else max(scores, key=scores.get)

    def observation(self, rid):
        if rid not in RACERS:
            raise ValueError("Unknown racer")
        k = self.karts[rid]
        other_id = next(r for r in RACERS if r != rid)
        other = self.karts[other_id]
        raw = k.observation()
        raw.update(tick=self.tick, time=round(self.elapsed, 4), finished=k.finished)
        dx, dy = other.x - k.x, other.y - k.y
        fx, fy = math.cos(k.heading), math.sin(k.heading)
        dvx, dvy = other.vx - k.vx, other.vy - k.vy
        raw["body"] = {
            "radius_m": self.radius,
            "phased": self.phased(rid),
            "left_edge_clearance_m": round(self.track.width / 2 - k.offset - self.radius, 4),
            "right_edge_clearance_m": round(self.track.width / 2 + k.offset - self.radius, 4),
        }
        raw["competition"] = {
            "racer_id": rid,
            "leader": self.leader(),
            "progress_m": round(self.progress_m(rid), 4),
            "opponent": {
                "racer_id": other_id,
                "ego_x_m": round(dx * fx + dy * fy, 4),
                "ego_y_m": round(-dx * fy + dy * fx, 4),
                "relative_forward_velocity_m_s": round(dvx * fx + dvy * fy, 4),
                "relative_left_velocity_m_s": round(-dvx * fy + dvy * fx, 4),
                "speed_m_s": round(other.speed, 4),
                "heading_relative_rad": round(wrap(other.heading - k.heading), 5),
                "surface_gap_m": round(math.hypot(dx, dy) - 2 * self.radius, 4),
                "phased": self.phased(other_id),
                "finished": other.finished,
                "checkpoints_passed": other.checkpoints_passed,
                "progress_m": round(self.progress_m(other_id), 4),
            },
            "contact_count": self.contact_count,
        }
        return raw

    def state(self):
        return {
            "tick": self.tick,
            "time": self.elapsed,
            "racers": {r: self.observation(r) for r in RACERS},
            "leader": self.leader(),
            "finished": self.finished,
        }

    def summary(self):
        finished = [r for r in RACERS if self.finish_ticks[r] is not None]
        first = min((self.finish_ticks[r] for r in finished), default=None)
        return {
            "finished": self.finished,
            "elapsed": self.elapsed,
            "ticks": self.tick,
            "winner_ids": [r for r in finished if self.finish_ticks[r] == first],
            "finish_times_s": {r: self.finish_ticks[r] * DT if r in finished else None for r in RACERS},
            "racers": {r: k.summary() for r, k in self.karts.items()},
            "contacts": self.contact_count,
            "lead_changes": sum(e["type"] == "lead_change" for e in self.events),
        }

    def config(self):
        k = self.karts["red"]
        result = {
            "version": DUEL_VERSION,
            "dt": DT,
            "parameters": {
                "seed": self.seed,
                "course": self.track.course,
                "road_width": self.track.width,
                "max_speed": k.handling.max_speed,
                "max_steering_angle": k.handling.max_steering_angle,
                "laps": k.laps,
                "reset_after_s": k.reset_after_s,
                "radius": self.radius,
                "restitution": self.restitution,
                "phase_s": self.phase_s,
                "contact": self.contact,
                "grid": [g.copy() for g in self.grid],
            },
            "handling": asdict(k.handling),
            "track": self.track.as_dict(),
            "racer_ids": list(RACERS),
            "finish_ties": "same_physics_tick",
            "boundary": "full_circle",
            "contact_solver": "swept_equal_mass_normal_impulse",
            "speed_cap": "motor_and_after_contact_impulse",
        }
        if self._checkpoint_input is not None:
            result["parameters"]["checkpoint"] = copy.deepcopy(self._checkpoint_input)
        if self.episode is not None:
            result["parameters"]["episode"] = copy.deepcopy(self.episode)
        return result
