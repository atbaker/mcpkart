"""Goal-only multiplayer facts, strict native replies and shared accounting."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import time
from pathlib import Path

from .decisions import DecisionClient
from .duel import RACERS, DuelSimulation
from .question_context import GOAL_COMPONENT_DEFINITIONS, PromptDomainError, project_facts
from .question_context_driver import _number, _read, _safe, _write_new, encoded
from .sim import ACTIONS

DUEL_RULES = (
    "This is a two-kart race. Finish three laps, crossing all 120 required checkpoint gates in order, "
    "before the opponent and as quickly as possible while staying on the road. "
    "Gates require a forward crossing with the whole circular kart inside the road span. "
    "Each kart has a 1 metre radius. Physical contact between equal-mass karts slows or deflects them "
    "with normal restitution 0.15; speed is capped at 12 m/s, including after contact. "
    "Physics continues at 60 Hz while each driver independently requests decisions. "
    "Both selected settings form one direct input held until another input is applied. "
    "Wheel settings are absolute angles, not increments. After three continuous seconds with the "
    "body outside the road, rescue returns the kart near its departure point, stopped and coasting, "
    "with no checkpoint credit. Rescued karts are non-colliding for at least one second and until "
    "separated. Finished karts stop and become non-colliding. Same-tick finishes tie. "
    "Edge clearances refer to the body boundary. Opponent ego_x_m is forward and ego_y_m is left "
    "of your current nose; relative velocities are opponent minus your velocity in that same frame. "
    "A negative surface_gap_m means overlap; phased means non-colliding. "
    "Choose the next input using the current measurements and physical control descriptions. "
)
PROMPT_VERSION = "duel_goal_only_v1"


GATE_GEOMETRY_UNITS = (
    "Coordinates [x,y] are metres from the current kart centre: x forward along its nose, y left. "
    "Endpoints are the road edges at the required gate; left/right follow the gate's forward direction. "
    "forward_normal_ego is the dimensionless unit normal in the gate's forward crossing direction."
)


CONTROL_TIMING_UNITS = (
    "post_response_wait_s: fixed seconds between receiving a native reply and submitting it. "
    "Native request/response time is additional and variable; the current response time is unknown. "
    "physics_hz: simulation steps per second. Physics and the held input continue during both intervals."
)


def control_timing_facts(post_response_wait_s, config):
    if (
        isinstance(post_response_wait_s, bool)
        or not isinstance(post_response_wait_s, (int, float))
        or not math.isfinite(post_response_wait_s)
        or not 0 <= post_response_wait_s <= 2
        or config.get("dt") != 1 / 60
    ):
        raise PromptDomainError("Invalid declared control timing")
    return {
        "post_response_wait_s": float(post_response_wait_s),
        "physics_hz": 60,
        "units": CONTROL_TIMING_UNITS,
    }


def gate_geometry(raw, config):
    """Rigidly transform the required finite gate, without choosing a crossing point or input."""
    try:
        index = raw["progress"]["checkpoint"]
        gates = config["track"]["checkpoints"]
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(gates):
            raise PromptDomainError("Invalid required gate index")
        gate, kart = gates[index], raw["kart"]
        values = [gate[k] for k in ("x", "y", "heading")]
        values += [kart[k] for k in ("x", "y", "heading")]
        width = config["track"]["width"]
        values.append(width)
        if not all(
            isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
            for v in values
        ) or width <= 0:
            raise PromptDomainError("Invalid required gate measurement")
        c, s = math.cos(kart["heading"]), math.sin(kart["heading"])
        nx, ny = math.cos(gate["heading"]), math.sin(gate["heading"])

        def point(x, y):
            dx, dy = x - kart["x"], y - kart["y"]
            return [round(dx * c + dy * s, 4), round(-dx * s + dy * c, 4)]

        return {
            "index": index,
            "centre_ego_m": point(gate["x"], gate["y"]),
            "left_endpoint_ego_m": point(gate["x"] - ny * width / 2, gate["y"] + nx * width / 2),
            "right_endpoint_ego_m": point(gate["x"] + ny * width / 2, gate["y"] - nx * width / 2),
            "forward_normal_ego": [round(nx * c + ny * s, 6), round(-nx * s + ny * c, 6)],
            "units": GATE_GEOMETRY_UNITS,
        }
    except (KeyError, TypeError, IndexError) as error:
        raise PromptDomainError("Missing required gate geometry") from error


def duel_facts(
    raw, config, racer_id, *, include_gate_geometry=False, include_wheel_motion=False,
    control_timing_s=None, include_pedal_timing=False,
):
    if not isinstance(include_gate_geometry, bool):
        raise TypeError("Gate geometry requires an explicit boolean profile")
    if not isinstance(include_wheel_motion, bool):
        raise TypeError("Wheel motion requires an explicit boolean profile")
    if not isinstance(include_pedal_timing, bool):
        raise TypeError("Pedal timing requires an explicit boolean profile")
    if include_pedal_timing and control_timing_s is None:
        raise PromptDomainError("Pedal timing requires declared control timing")
    timing = control_timing_facts(control_timing_s, config) if control_timing_s is not None else None
    for key, expected in {
        "radius": 1.0,
        "road_width": 24,
        "max_speed": 12,
        "max_steering_angle": 0.12,
        "laps": 3,
        "reset_after_s": 3.0,
        "restitution": 0.15,
        "phase_s": 1.0,
        "contact": "solid",
    }.items():
        if config["parameters"].get(key) != expected:
            raise PromptDomainError("Game configuration differs from the declared multiplayer rules")
    if racer_id not in RACERS or raw.get("competition", {}).get("racer_id") != racer_id:
        raise PromptDomainError("Observation belongs to another racer")
    solo_config = DuelSimulation.from_config(config).karts[racer_id].config()
    facts = project_facts(
        raw, config=solo_config, extended_domain=True, include_wheel_motion=include_wheel_motion,
    )
    if include_wheel_motion:
        facts["wheel_facts"]["current_road_frame"] = copy.deepcopy(
            facts["pedal_facts"]["current_road_frame"]
        )
    if timing is not None:
        facts["wheel_facts"]["control_timing"] = timing
        if include_pedal_timing:
            facts["pedal_facts"]["control_timing"] = copy.deepcopy(timing)
    try:
        body, competition = copy.deepcopy(raw["body"]), copy.deepcopy(raw["competition"])
        if body["radius_m"] != config["parameters"]["radius"] or not isinstance(body["phased"], bool):
            raise PromptDomainError("Invalid kart footprint")
        for key in ("left_edge_clearance_m", "right_edge_clearance_m"):
            expected = round(
                raw["track"]["width"] / 2
                + (-1 if key.startswith("left") else 1) * raw["track"]["offset"]
                - body["radius_m"],
                4,
            )
            if not _number(abs(body[key])) or abs(body[key] - expected) > 0.0002:
                raise PromptDomainError("Invalid body edge measurement")
            facts["pedal_facts"]["road"][key] = body[key]
        opponent = competition["opponent"]
        if opponent["racer_id"] != next(r for r in RACERS if r != racer_id):
            raise PromptDomainError("Invalid opponent identity")
        if competition["leader"] not in (*RACERS, None):
            raise PromptDomainError("Invalid leader")

        def finite_tree(value):
            if isinstance(value, float) and not math.isfinite(value):
                raise PromptDomainError("Nonfinite opponent measurement")
            if isinstance(value, dict):
                for item in value.values():
                    finite_tree(item)

        finite_tree(competition)
        for key in (
            "ego_x_m",
            "ego_y_m",
            "relative_forward_velocity_m_s",
            "relative_left_velocity_m_s",
            "speed_m_s",
            "heading_relative_rad",
            "surface_gap_m",
            "progress_m",
        ):
            if not isinstance(opponent[key], (float, int)) or isinstance(opponent[key], bool):
                raise PromptDomainError("Invalid opponent geometry")
        for head in ("wheel", "pedal"):
            facts[head + "_facts"]["body"] = copy.deepcopy(body)
            facts[head + "_facts"]["competition"] = copy.deepcopy(competition)
            facts[head + "_facts"]["race"] = {**copy.deepcopy(raw["progress"]), "time_s": raw["time"]}
    except (KeyError, TypeError) as error:
        raise PromptDomainError("Missing multiplayer facts") from error
    if include_gate_geometry:
        facts["wheel_facts"]["next_gate"]["geometry"] = gate_geometry(raw, config)
    return facts


class DuelDecisionClient(DecisionClient):
    def __init__(self, *, facts, handling, **kwargs):
        self.facts = copy.deepcopy(facts)
        super().__init__(
            actions=ACTIONS,
            handling=handling,
            max_input_tokens=16384,
            control_language="geometry",
            decision_layout="factored",
            **kwargs,
        )
        self.instruction_style = PROMPT_VERSION
        self.instructions = DUEL_RULES

    @property
    def questions(self):
        return {
            head: {
                "type": "choice",
                "instructions": {
                    "rules": DUEL_RULES + GOAL_COMPONENT_DEFINITIONS[head],
                    "current_facts": {head + "_facts": copy.deepcopy(self.facts[head + "_facts"])},
                },
                "criteria": copy.deepcopy(self.component_criteria[head]),
            }
            for head in ("wheel", "pedal")
        }


class BudgetJournal:
    """Synchronous transitions form one chain across two asynchronous drivers."""

    def __init__(self, budget, path):
        self.budget, self.path = budget, Path(path)
        self.expected = _read(budget.path)
        if self.expected["pending"]:
            raise ValueError("Pending reservations forbid a new duel")
        self.events, self.owners = [], {}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("x")

    def view(self, racer_id):
        return RacerBudget(self, racer_id)

    def check(self):
        current = _read(self.budget.path)
        if current != self.expected:
            raise RuntimeError("Shared ledger changed outside this duel writer")
        return current

    def append(self, kind, racer_id, reservation, before, after, **details):
        event = {
            "index": len(self.events),
            "kind": kind,
            "racer_id": racer_id,
            "reservation_id": reservation,
            "wall_ns": time.monotonic_ns(),
            "before": before,
            "after": after,
            **details,
        }
        self.stream.write(json.dumps(event, allow_nan=False) + "\n")
        self.stream.flush()
        self.events.append(event)
        self.expected = after

    def close(self):
        self.stream.close()


class RacerBudget:
    def __init__(self, journal, racer_id):
        self.journal, self.racer_id = journal, racer_id
        self.path = journal.budget.path

    def reserve(self, cost, tokens, *, model, provider):
        j = self.journal
        before = j.check()
        if self.racer_id in j.owners.values():
            raise RuntimeError("One reservation per racer is allowed")
        reservation = j.budget.reserve(cost, tokens, model=model, provider=provider)
        j.owners[reservation] = self.racer_id
        j.append(
            "reserve",
            self.racer_id,
            reservation,
            before,
            _read(self.path),
            cost=cost,
            tokens=tokens,
            model=model,
            provider=provider,
        )
        return reservation

    def commit(self, reservation, *, cost=None, tokens=None):
        j = self.journal
        before = j.check()
        if j.owners.get(reservation) != self.racer_id:
            raise RuntimeError("Reservation belongs to another racer")
        charged = j.budget.commit(reservation, cost=cost, tokens=tokens)
        del j.owners[reservation]
        j.append("commit", self.racer_id, reservation, before, _read(self.path), cost=cost, tokens=tokens)
        return charged


class DuelDriver:
    def __init__(
        self,
        *,
        racer_id,
        config,
        route,
        budget,
        http,
        capture,
        output,
        api_key=None,
        admission=None,
        seen_ids=None,
        include_gate_geometry=False,
        include_wheel_motion=False,
        control_timing_s=None,
        include_pedal_timing=False,
    ):
        self.racer_id, self.config, self.route = racer_id, copy.deepcopy(config), copy.deepcopy(route)
        self.budget, self.http, self.capture, self.output = budget, http, capture, Path(output)
        self.api_key, self.admission = api_key, admission
        self.count, self.busy, self.stopped = 0, False, False
        self.seen_ids = seen_ids if seen_ids is not None else set()
        if not isinstance(include_gate_geometry, bool):
            raise TypeError("Gate geometry requires an explicit boolean profile")
        self.include_gate_geometry = include_gate_geometry
        if not isinstance(include_wheel_motion, bool):
            raise TypeError("Wheel motion requires an explicit boolean profile")
        if not isinstance(include_pedal_timing, bool):
            raise TypeError("Pedal timing requires an explicit boolean profile")
        if include_pedal_timing and control_timing_s is None:
            raise PromptDomainError("Pedal timing requires declared control timing")
        if control_timing_s is not None:
            control_timing_facts(control_timing_s, self.config)
        self.include_wheel_motion = include_wheel_motion
        self.control_timing_s = control_timing_s
        self.include_pedal_timing = include_pedal_timing

    async def decide(self, observation):
        if self.busy or self.stopped:
            raise RuntimeError("Driver already active or stopped")
        self.busy = True
        try:
            return await self._decide(observation)
        except BaseException:
            self.stopped = True
            raise
        finally:
            self.busy = False

    async def _decide(self, observation):
        facts = duel_facts(
            observation, self.config, self.racer_id, include_gate_geometry=self.include_gate_geometry,
            include_wheel_motion=self.include_wheel_motion, control_timing_s=self.control_timing_s,
            include_pedal_timing=self.include_pedal_timing,
        )
        if self.admission:
            self.admission()
        api = DuelDecisionClient(
            facts=facts,
            handling=self.config["handling"],
            budget=self.budget,
            http_client=self.http,
            api_key=self.api_key,
        )
        self.api_key = api.api_key
        payload = {
            "model": self.route["model"],
            "state": {},
            "questions": api.questions,
            "provider": {"only": [self.route["provider"]], "allow_fallbacks": False},
        }
        query = {
            "index": self.count,
            "racer_id": self.racer_id,
            "raw_observation": observation,
            "facts": facts,
            "payload": payload,
        }
        _write_new(self.output / f"query-{self.count:05d}.json", _safe(query, self.api_key))
        self.capture.clear()
        try:
            record = await api.decide(self.route, {})
        except BaseException:
            self.stopped = True
            _write_new(
                self.output / f"interrupted-{self.count:05d}.json",
                {"wire": self.capture.evidence(self.api_key)},
            )
            raise
        failures = []
        wire = self.capture.evidence(self.api_key)
        if len(self.capture.requests) != 1 or self.capture.requests[0]["body"] != encoded(payload):
            failures.append("wire_request_mismatch")
        if not wire["saved_unmodified"]:
            failures.append("unsafe_wire")
        response = self.capture.responses[0] if len(self.capture.responses) == 1 else {}
        raw = response.get("json")
        if not isinstance(raw, dict):
            failures.append("missing_single_raw_reply")
        else:
            if (
                response["status"] != 200
                or raw.get("model") != self.route["resolved_model"]
                or raw.get("provider") != self.route["provider_name"]
            ):
                failures.append("route_identity")
            identity = raw.get("id")
            if not isinstance(identity, str) or not identity.strip() or identity in self.seen_ids:
                failures.append("response_identity")
            else:
                self.seen_ids.add(identity)
            answers = raw.get("answers")
            if not isinstance(answers, dict) or set(answers) != {"wheel", "pedal"}:
                failures.append("answer_heads")
            else:
                choices = {}
                for head in ("wheel", "pedal"):
                    answer = answers[head]
                    if (
                        not isinstance(answer, dict)
                        or answer.get("type") != "choice"
                        or answer.get("refusal")
                        or not isinstance(answer.get("choice"), str)
                        or answer["choice"] not in api.component_criteria[head]
                    ):
                        failures.append("invalid_native_" + head)
                    else:
                        choices[head] = answer["choice"]
                if len(choices) == 2 and (
                    choices != record["component_choices"]
                    or api._component_actions[(choices["wheel"], choices["pedal"])] != record["action"]
                ):
                    failures.append("native_inverse")
            if raw.get("usage") != record.get("usage"):
                failures.append("usage_identity")
        usage = record.get("usage") or {}
        if (
            record.get("cost_source") != "reported"
            or not _number(record.get("cost"))
            or not _number(usage.get("cost"))
            or usage["cost"] != record["cost"]
            or not all(
                isinstance(usage.get(k), int) and not isinstance(usage[k], bool) and usage[k] >= 0
                for k in ("input_tokens", "output_tokens")
            )
        ):
            failures.append("uncertain_accounting")
        if failures:
            record.update(
                unapplied_reply_action=record.get("action"),
                ok=False,
                action=None,
                error="duel_guard_failure",
                wrapper_failures=failures,
            )
        if not record["ok"]:
            self.stopped = True
        record.update(
            racer_id=self.racer_id,
            query_index=self.count,
            wire_payload_sha256=hashlib.sha256(encoded(payload)).hexdigest(),
        )
        _write_new(
            self.output / "calls" / f"{self.count:05d}.json",
            _safe({"query": query, "wire": wire, "record": record}, self.api_key),
        )
        self.count += 1
        return record
