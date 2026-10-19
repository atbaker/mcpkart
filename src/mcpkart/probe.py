"""Paired static telemetry probes; diagnostic action agreement is not ground truth.

These requests freeze each input snapshot. They do not drive a realtime race.
All variants retain the production instructions, action menu, and pinned routes.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import math
import os
import re
import statistics
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

from .bench import POC_MODELS, driving_evidence, percentiles, simulation_contract
from .decisions import (
    CONTROL_LANGUAGES,
    DRIVING_INSTRUCTIONS,
    INSTRUCTION_STYLES,
    Budget,
    BudgetExceeded,
    DecisionClient,
    discover_routes,
)
from .sim import ACTIONS, DT, Simulation, scripted_action
from .telemetry import VARIANTS, represent

REFERENCE_TICKS = {0: "rest", 60: "straight", 114: "first_bend_approach",
                   317: "left_before_right", 396: "left_to_right_transition",
                   434: "tight_right_approach", 527: "right_to_left_transition"}
DEFAULT_RECORDS = Path("artifacts/rescue-v1")
CORRECTION_LOOKBACK_TICKS = 12


def atomic_json(path: Path, value: Any, *, replace: bool = False) -> None:
    """Publish a complete JSON file; never truncate the preceding checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise FileExistsError(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def source_fingerprint() -> str:
    digest = hashlib.sha256()
    for name in ("sim.py", "decisions.py", "runtime.py", "bench.py", "telemetry.py", "observations.py", "probe.py"):
        digest.update(name.encode())
        digest.update(Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


def frozen_context(observation: dict, prior: list[dict]) -> dict:
    """Build history from past observations only; the target remains current."""
    from .observations import ObservationHistory

    history = ObservationHistory()
    for previous in sorted(prior, key=lambda item: item["tick"]):
        if previous["tick"] >= observation["tick"]:
            raise ValueError("Frozen history must contain only observations before the target")
        history.observe(previous)
    return history.observe(observation)


def fixture(name: str, observation: dict, source: dict, *, context: dict | None = None) -> dict:
    # Diagnostics stay beside the state; they are never passed to represent/decide.
    raw = driving_evidence(observation, variant="raw")
    return {"id": name, "observation": raw, "source": source,
            "context": copy.deepcopy(context if context is not None else frozen_context(observation, [])),
            "diagnostic_reference_action": scripted_action(raw)}


def collect_fixtures(records: Path = DEFAULT_RECORDS, driving_record: Path | None = None,
                     navigation_record: Path | None = None) -> list[dict]:
    """Reference/synthetic cases plus available historical and replayed cases."""
    snapshots = []
    observed = []
    sim = Simulation(seed=0)
    while sim.tick <= max(REFERENCE_TICKS):
        observation = sim.observation()
        if sim.tick in REFERENCE_TICKS:
            snapshots.append(fixture(REFERENCE_TICKS[sim.tick], observation,
                                     {"kind": "scripted_reference", "seed": 0, "tick": sim.tick,
                                      "history": {"kind": "scripted_fixed_observation_cadence", "cadence_ticks": 12,
                                                  "prior_ticks": [item["tick"] for item in observed]}},
                                     context=frozen_context(observation, observed)))
        if sim.tick % 12 == 0:
            observed.append(copy.deepcopy(observation))
        sim.set_control(scripted_action(observation))
        sim.step()
    for model, name in (("typesafe--jev-1.14", "jev_first_curve_pre_exit"),
                        ("openai--gpt-6-luna-decisions", "luna_first_curve_pre_exit")):
        path = records / f"{model}--seed-0.json"
        if not path.exists():
            continue
        document = json.loads(path.read_text())
        requests = document["requests"]
        chosen = None
        for index in range(1, len(requests)):
            before, after = requests[index-1]["observation"], requests[index]["observation"]
            if (before["track"]["on_road"] and not after["track"]["on_road"]
                    and before["kart"]["speed"] >= 18):
                chosen = index-1
                break
        if chosen is None:
            raise ValueError(f"No fast first-departure approach found in {path}")
        record = requests[chosen]
        snapshots.append(fixture(name, record["observation"], {
            "kind": "recorded_model_before_first_fast_exit", "path": str(path),
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "request_index": chosen, "recorded_action": record["action"],
            "recorded_latency_ms": record.get("latency_ms"),
            "history": {"kind": "actual_saved_driver_requests", "prior_ticks": [r["observation"]["tick"] for r in requests[:chosen]
                                                                                   if r["observation"]["tick"] < record["observation"]["tick"]]},
        }, context=frozen_context(record["observation"], [r["observation"] for r in requests[:chosen]
                                                         if r["observation"]["tick"] < record["observation"]["tick"]])))
    sim = Simulation(seed=0)
    x, y, heading, _ = sim.track.at(8)
    sim.x, sim.y = x-math.sin(heading)*2, y+math.cos(heading)*2
    sim.heading = heading+math.radians(10)
    sim.vx, sim.vy = 12*math.cos(sim.heading), 12*math.sin(sim.heading)
    sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)
    sim.set_control("straight_accelerate")
    snapshots.append(fixture("left_drift_correction", sim.observation(), {
        "kind": "synthetic_physical_state", "seed": 0, "centreline_s_m": 8,
        "offset_m": 2, "kart_heading_relative_road_deg": 10, "speed_m_s": 12,
        "history": {"kind": "current_synthetic_state_only", "prior_ticks": []},
    }))
    if driving_record is not None:
        snapshots.extend(correction_fixtures(driving_record))
    if navigation_record is not None:
        snapshots.extend(navigation_fixtures(navigation_record))
    return snapshots


def replay_observations(document: dict, ticks: set[int]) -> dict[int, dict]:
    """Replay applied commands against identical physics, including real rescues."""
    if not ticks or any(isinstance(tick, bool) or not isinstance(tick, int) or tick < 0 for tick in ticks):
        raise ValueError("Replay requires nonnegative integer observation ticks")
    race = document["race"]
    config = race["config"]
    sim = Simulation(seed=race["seed"], laps=config["laps"],
                     reset_after_s=config["rescue"]["after_s"])
    if sim.config() != config:
        raise ValueError("Driving record physics/configuration differs from the current simulator")
    commands = race["commands"]
    previous_tick = 0
    for command in commands:
        applied_tick = command["applied_tick"]
        if (isinstance(applied_tick, bool) or not isinstance(applied_tick, int)
                or applied_tick <= previous_tick or command["action_id"] not in ACTIONS):
            raise ValueError("Driving record commands must have unique increasing applied ticks and valid actions")
        previous_tick = applied_tick
    states = {0: sim.observation()} if 0 in ticks else {}
    command_index = 0
    while sim.tick < max(ticks):
        if sim.finished:
            raise ValueError("Driving record observation occurs after simulation completion")
        if command_index < len(commands) and commands[command_index]["applied_tick"] == sim.tick+1:
            sim.set_control(commands[command_index]["action_id"])
            command_index += 1
        sim.step()
        if sim.tick in ticks:
            states[sim.tick] = sim.observation()
    return states


def replay_contexts(document: dict, targets: set[int], states: dict[int, dict] | None = None) -> tuple:
    """Use the actual prior request cadence, validating every reconstructed pose."""
    if any(r.get("observation_tick", r["observation"]["tick"]) != r["observation"]["tick"] for r in document["requests"]):
        raise ValueError("Driving record observation tick identities disagree")
    requested = sorted({r.get("observation_tick", r["observation"]["tick"]) for r in document["requests"]
                        if r["observation"]["tick"] <= max(targets)})
    required = targets | set(requested)
    states = replay_observations(document, required) if states is None else states
    samples = {sample["tick"]: sample for sample in document["race"]["samples"]}
    for tick in required:
        if tick not in samples:
            raise ValueError(f"Driving record lacks runtime sample at history/target tick {tick}")
        validate_runtime_sample(states[tick], samples[tick])
    contexts, provenance = {}, {}
    for tick in targets:
        prior_ticks = [previous for previous in requested if previous < tick]
        contexts[tick] = frozen_context(states[tick], [states[previous] for previous in prior_ticks])
        provenance[tick] = {"kind": "actual_prior_driver_request_ticks", "prior_ticks": prior_ticks,
                            "target_was_recorded_request": tick in requested,
                            "all_prior_poses_validated_against_runtime_samples": True}
    return states, contexts, provenance


def validate_replay(raw: dict, saved: dict, config: dict, sample: dict | None = None) -> dict:
    """Reject a reconstruction whose pose/progress differs from saved evidence."""
    road = represent(driving_evidence(raw, variant="raw"), config, "road_physics")
    checks = {
        "time_s": (raw["time"], saved["time"], .00011),
        "offset_m": (road["road"]["offset_m"], saved["road"]["offset_m"], .002),
        "road_vs_kart_deg": (road["road"]["road_vs_kart_deg"], saved["road"]["road_vs_kart_deg"], .002),
        "speed_m_s": (raw["kart"]["speed"], saved["kart"]["speed_m_s"], .0002),
        "yaw_deg_s": (road["kart"]["yaw_deg_s"], saved["kart"]["yaw_deg_s"], .002),
        "steering_deg": (road["kart"]["steering_deg"], saved["kart"]["steering_deg"], .002),
        "track_distance_m": (raw["progress"]["track_distance"], saved["progress"]["track_distance"], .002),
    }
    if sample is not None:
        for key in ("x", "y", "heading", "vx", "vy", "yaw_rate", "steering_angle"):
            checks[f"sample_{key}"] = (raw["kart"][key], sample["kart"][key], .0002)
    errors = {key: abs(float(actual)-float(expected)) for key, (actual, expected, _) in checks.items()}
    if any(not math.isfinite(error) or error > checks[key][2] for key, error in errors.items()):
        raise ValueError(f"Driving record replay pose validation failed at tick {raw['tick']}: {errors}")
    if (raw["tick"] != saved["tick"] or road["road"]["on_road"] != saved["road"]["on_road"]
            or raw["rescue"] != saved["rescue"]
            or any(raw["progress"][key] != saved["progress"][key] for key in
                   ("checkpoint", "checkpoints_passed", "laps_completed", "resets"))):
        raise ValueError(f"Driving record replay progress/rescue validation failed at tick {raw['tick']}")
    return {"validated": True, "absolute_errors": errors,
            "runtime_pose_sample_checked": sample is not None}


def correction_fixtures(path: Path) -> list[dict]:
    """Select earliest left/right inside-drift states and reconstruct exact raw inputs."""
    source_bytes = path.read_bytes()
    document = json.loads(source_bytes)
    selected: dict[str, tuple[int, dict]] = {}
    requests = sorted(enumerate(document["requests"]), key=lambda item: item[1]["observation"]["tick"])
    for index, record in requests:
        observation = record["observation"]
        road = observation.get("road")
        if road is None:
            continue
        if not road["on_road"] or observation["kart"]["speed_m_s"] >= 20:
            continue
        side = ("left" if road["offset_m"] > 1 and road["road_vs_kart_deg"] < -15 else
                "right" if road["offset_m"] < -1 and road["road_vs_kart_deg"] > 15 else None)
        if side is not None and side not in selected:
            if record.get("observation_tick", observation["tick"]) != observation["tick"]:
                raise ValueError("Driving record observation tick identities disagree")
            selected[side] = index, record
    if not selected:
        return []
    ticks = {record["observation"]["tick"] for _, record in selected.values()}
    ticks.update(max(0, tick-CORRECTION_LOOKBACK_TICKS) for tick in list(ticks))
    raw, contexts, history = replay_contexts(document, ticks)
    samples = {sample["tick"]: sample for sample in document["race"].get("samples", [])}
    snapshots = []
    for side in ("left", "right"):
        if side not in selected:
            continue
        index, record = selected[side]
        tick = record["observation"]["tick"]
        validation = validate_replay(raw[tick], record["observation"], document["race"]["config"],
                                     samples.get(tick))
        snapshots.append(fixture(f"recorded_{side}_oversteer_correction", raw[tick], {
            "kind": "replayed_model_inside_oversteer", "path": str(path),
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "model": document.get("model"), "request_index": index, "observation_tick": tick,
            "recorded_action": record.get("action"), "seed": document["race"]["seed"],
            "replay": "Original commands applied before their applied_tick step; original rescue policy retained.",
            "pose_validation": validation,
            "history": history[tick],
        }, context=contexts[tick]))
        early_tick = max(0, tick-CORRECTION_LOOKBACK_TICKS)
        sample = samples.get(early_tick)
        if sample is None:
            raise ValueError(f"Driving record lacks runtime sample for fixed early tick {early_tick}")
        early_validation = validate_runtime_sample(raw[early_tick], sample)
        snapshots.append(fixture(f"recorded_{side}_oversteer_early", raw[early_tick], {
            "kind": "replayed_model_inside_oversteer_fixed_lookback", "path": str(path),
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(), "model": document.get("model"),
            "request_index": index, "selected_observation_tick": tick, "observation_tick": early_tick,
            "lookback_ticks": CORRECTION_LOOKBACK_TICKS, "seed": document["race"]["seed"],
            "selection": "Fixed 12-tick lookback; no controller or action-quality selection.",
            "replay": "Original commands and original rescue policy; validated against saved runtime sample.",
            "pose_validation": early_validation,
            "history": history[early_tick],
        }, context=contexts[early_tick]))
    return snapshots


def navigation_fixtures(path: Path) -> list[dict]:
    """Paired valid-behind-nose and missed-gate states from actual requests."""
    source_bytes = path.read_bytes()
    document = json.loads(source_bytes)
    requested = sorted({r.get("observation_tick", r["observation"]["tick"]) for r in document["requests"]})
    if not requested:
        raise ValueError("Navigation record has no driver observations")
    raw = replay_observations(document, set(requested))
    config = document["race"]["config"]

    def gate_facts(state):
        gate = config["track"]["checkpoints"][state["progress"]["checkpoint"]]
        kart = state["kart"]
        dx, dy = kart["x"]-gate["x"], kart["y"]-gate["y"]
        gate_plane = dx*math.cos(gate["heading"])+dy*math.sin(gate["heading"])
        gate_ego_x = -dx*math.cos(kart["heading"])-dy*math.sin(kart["heading"])
        return gate_plane, gate_ego_x

    early = next((raw[tick] for tick in requested if raw[tick]["track"]["on_road"]
                  and gate_facts(raw[tick])[0] > 0 and gate_facts(raw[tick])[1] < 0), None)
    if early is None:
        raise ValueError("Navigation record has no on-road required-gate-behind observation")
    later = [raw[tick] for tick in requested if raw[tick]["time"] >= early["time"]+2
             and raw[tick]["progress"]["checkpoints_passed"] == early["progress"]["checkpoints_passed"]
             and raw[tick]["progress"]["checkpoint"] == early["progress"]["checkpoint"]]
    if not later:
        raise ValueError("Navigation record lacks a >=2-second later observation with the same required gate")
    stalled = next((state for state in later if state["track"]["on_road"]), later[0])
    samples = {sample["tick"]: sample for sample in document["race"]["samples"]}
    approach, credit_tick = None, None
    for tick in requested:
        state = raw[tick]
        plane, ego_x = gate_facts(state)
        if not state["track"]["on_road"] or not (plane < 0 and ego_x < 0):
            continue
        credited = next((future for future in range(tick+1, tick+13) if future in samples
                         and samples[future]["progress"]["checkpoints_passed"] > state["progress"]["checkpoints_passed"]), None)
        if credited is not None:
            approach, credit_tick = state, credited
            break
    if approach is None:
        raise ValueError("Navigation record has no behind-nose approach credited within 12 physics ticks")
    after_credit = next((raw[tick] for tick in requested if tick >= credit_tick), None)
    if after_credit is None:
        raise ValueError("Navigation record has no driver observation after the selected gate credit")
    credit_state = replay_observations(document, {credit_tick})[credit_tick]
    credit_validation = validate_runtime_sample(credit_state, samples[credit_tick])
    selected = (("recorded_missed_gate_early", early), ("recorded_missed_gate_stalled", stalled),
                ("recorded_gate_approach_behind_nose", approach), ("recorded_gate_after_credit", after_credit))
    targets = {state["tick"] for _, state in selected}
    raw, contexts, history = replay_contexts(document, targets, states=raw)
    return [fixture(name, state, {
        "kind": "replayed_model_required_gate_navigation", "path": str(path),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(), "model": document.get("model"),
        "observation_tick": state["tick"], "seed": document["race"]["seed"],
        "selection": ("First on-road state with positive required-gate plane distance and negative gate ego_x; "
                      "then first on-road observation >=2s later with unchanged required gate (off-road fallback)."
                      if name.startswith("recorded_missed") else
                      "First on-road actual request with gate ego_x<0, gate-plane<0, and credit within next 12 physics ticks; "
                      "after-credit target is the first actual driver observation after that credit."),
        "first_missed_gate_tick": early["tick"], "minimum_later_seconds": 2,
        "first_missed_gate_time_s": early["time"],
        "actual_seconds_after_first_target": state["time"]-early["time"],
        "gate_plane_m": gate_facts(state)[0], "gate_ego_x_m": gate_facts(state)[1],
        "valid_approach_tick": approach["tick"], "valid_approach_credit_tick": credit_tick,
        "valid_approach_credit_time_s": credit_state["time"], "valid_approach_credit_validation": credit_validation,
        "pose_validation": validate_runtime_sample(state, samples[state["tick"]]),
        "history": history[state["tick"]],
    }, context=contexts[state["tick"]]) for name, state in selected]


def validate_runtime_sample(raw: dict, sample: dict) -> dict:
    """Validate a replay at a physics sample with no model request at that tick."""
    errors = {key: abs(float(raw["kart"][key])-float(sample["kart"][key])) for key in raw["kart"]}
    errors["time_s"] = abs(float(raw["time"])-float(sample["time"]))
    if (any(not math.isfinite(error) or error > .0002 for error in errors.values())
            or raw["tick"] != sample["tick"] or raw["progress"] != sample["progress"]
            or raw["rescue"] != sample["rescue"] or raw["control"] != sample["control"]):
        raise ValueError(f"Driving record runtime sample validation failed at tick {raw['tick']}")
    return {"validated": True, "absolute_errors": errors, "runtime_pose_sample_checked": True,
            "progress_rescue_control_checked": True, "request_at_tick_required": False}


def select_fixtures(fixtures: list[dict], selection: str | None) -> list[dict]:
    """Keep explicit user ordering and fail before paid work on bad selections."""
    if selection is None:
        return fixtures
    names = [name.strip() for name in selection.split(",")]
    if not names or any(not name for name in names) or len(set(names)) != len(names):
        raise ValueError("Fixtures must be a nonempty comma-separated list of unique IDs")
    available = {snapshot["id"]: snapshot for snapshot in fixtures}
    unknown = [name for name in names if name not in available]
    if unknown:
        raise ValueError(f"Unknown fixture IDs: {unknown}; available: {list(available)}")
    return [available[name] for name in names]


def schedule(fixtures: list[dict], routes: list[dict], variants: list[str],
             repeats: int = 1) -> list[tuple[dict, dict, str, int]]:
    """Rotate paired model/profile blocks across deterministic, 1-based repeats."""
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("repeats must be an integer >= 1")
    if not fixtures or not routes or not variants:
        raise ValueError("Probes require at least one fixture, route, and variant")
    order = []
    for repeat in range(1, repeats+1):
        for index, snapshot in enumerate(fixtures):
            for round_index in range(len(variants)):
                for model_index in range(len(routes)):
                    route_index = (model_index+index+round_index+repeat-1) % len(routes)
                    route = routes[route_index]
                    variant = variants[(round_index+index+route_index+repeat-1) % len(variants)]
                    order.append((snapshot, route, variant, repeat))
    return order


def restore_snapshot(observation: dict) -> Simulation:
    """Approximate state from rounded public telemetry, with rescue disabled."""
    sim = Simulation(reset_after_s=None)
    kart, progress = observation["kart"], observation["progress"]
    for attribute in ("x", "y", "heading", "vx", "vy", "yaw_rate"):
        setattr(sim, attribute, float(kart[attribute]))
    sim.steering = float(kart["steering_angle"])
    sim.tick, sim.elapsed = observation["tick"], observation["time"]
    sim.laps_completed = progress["laps_completed"]
    sim.checkpoints_passed = progress["checkpoints_passed"]
    sim.next_checkpoint = progress["checkpoint"]
    sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)
    sim.set_control(observation["control"])
    return sim


def action_effect(observation: dict, action: str, *, age_s: float = .2, hold_s: float = .3) -> dict:
    """Fixed-age/open-loop diagnostic, not a prediction of closed-loop driving."""
    sim = restore_snapshot(observation)
    for _ in range(round(age_s/DT)):
        sim.step()
    applied_heading_error = abs(sim.observation()["track"]["heading_error"])
    initial_s, initial_offroad = sim.s, sim.offroad_time
    initial_checkpoints = sim.checkpoints_passed
    minimum_margin = sim.track.width/2-abs(sim.offset)
    progress = 0.0
    sim.set_control(action)
    for _ in range(round(hold_s/DT)):
        previous_s = sim.s
        sim.step()
        progress += (sim.s-previous_s+sim.track.length/2) % sim.track.length-sim.track.length/2
        minimum_margin = min(minimum_margin, sim.track.width/2-abs(sim.offset))
    final_heading_error = abs(sim.observation()["track"]["heading_error"])
    return {"fixed_observation_age_s": age_s, "held_action_s": hold_s,
            "rescue_enabled": False, "minimum_road_margin_m": minimum_margin,
            "offroad_time_s": sim.offroad_time-initial_offroad,
            "absolute_heading_error_change_deg": math.degrees(final_heading_error-applied_heading_error),
            "centreline_progress_m": progress, "checkpoints_crossed": sim.checkpoints_passed-initial_checkpoints,
            "end_speed_m_s": sim.speed, "application_centreline_s_m": initial_s,
            "limitation": "Rounded public state; fixed delay/hold; no subsequent driver decisions."}


def diagnostics(snapshot: dict, action: str | None) -> dict:
    reference = snapshot["diagnostic_reference_action"]
    if action not in ACTIONS:
        return {"exact_agreement": None, "steer_agreement": None, "pedal_agreement": None,
                "heading_error_direction": None, "selected_steering_direction": None,
                "action_effect": None}
    selected, expected = ACTIONS[action], ACTIONS[reference]
    heading_error = snapshot["observation"]["track"]["heading_error"]
    heading_direction = "left" if heading_error > 0 else "right" if heading_error < 0 else "aligned"
    steering_direction = "left" if selected["steer"] > 0 else "right" if selected["steer"] < 0 else "straight"
    return {"exact_agreement": action == reference,
            "heading_error_direction": heading_direction, "selected_steering_direction": steering_direction,
            "steer_agreement": selected["steer"] == expected["steer"],
            "pedal_agreement": (selected["throttle"], selected["brake"]) ==
                               (expected["throttle"], expected["brake"]),
            "action_effect": action_effect(snapshot["observation"], action)}


def summarize(records: list[dict], *, planned: int, status: str, budget: dict,
              repeats: int = 1, control_language: str = "numeric", instruction_style: str = "original") -> dict:
    groups = sorted({(record["model"], record["variant"]) for record in records})
    rows = []
    for model, variant in groups:
        group = [record for record in records if record["model"] == model and record["variant"] == variant]
        successes = [record for record in group if record["decision"]["ok"]]
        diagnostic = [record["diagnostics"] for record in successes]
        rows.append({"model": model, "variant": variant, "requests": len(group), "successes": len(successes),
                     "errors": len(group)-len(successes),
                     "latency_ms": percentiles([record["decision"]["latency_ms"] for record in group
                                                 if record["decision"].get("latency_ms") is not None]),
                     "encoded_bytes": percentiles([record["encoded_bytes"] for record in group
                                                    if record.get("encoded_bytes") is not None]),
                     "cost_usd": sum(record["decision"].get("cost") or 0 for record in group),
                     "diagnostic_denominator": len(diagnostic),
                     **{key: sum(bool(d[key]) for d in diagnostic) for key in
                        ("exact_agreement", "steer_agreement", "pedal_agreement")},
                     "median_diagnostic_road_margin_m": statistics.median(
                         d["action_effect"]["minimum_road_margin_m"] for d in diagnostic) if diagnostic else None})
    fixture_rows = []
    for name, model, variant in sorted({(r["fixture"], r["model"], r["variant"]) for r in records}):
        group = [r for r in records if (r["fixture"], r["model"], r["variant"]) == (name, model, variant)]
        successes = [r for r in group if r["decision"]["ok"]]
        directions = Counter(f"road_faces_{r['diagnostics']['heading_error_direction']}__steer_{r['diagnostics']['selected_steering_direction']}"
                             for r in successes)
        fixture_rows.append({"fixture": name, "model": model, "variant": variant,
                             "requests": len(group), "successes": len(successes), "errors": len(group)-len(successes),
                             "action_counts": dict(sorted(Counter(r["decision"]["action"] for r in successes).items())),
                             "direction_counts": dict(sorted(directions.items()))})
    return {"status": status, "planned_requests": planned, "completed_requests": len(records),
            "repeats": repeats, "control_language": control_language, "fixture_groups": fixture_rows,
            "instruction_style": instruction_style,
            "complete": len(records) == planned and status == "complete", "budget": budget, "groups": rows,
            "interpretation": "Static pilot only. Scripted agreement is diagnostic, not ground truth or race viability."
            " Effects use rounded public states and fixed 200ms age/300ms action hold without rescue."
            " Direction counts compare current road-vs-kart heading with selected steering, not a recommended action."}


class WireCapture:
    """Record bodies only; request headers and credentials are never persisted."""

    def __init__(self) -> None:
        self.secret = ""
        self.exchanges: list[dict] = []

    def redact(self, value: str) -> str:
        if self.secret:
            value = value.replace(self.secret, "[REDACTED]")
        value = re.sub(r"(?i)bearer\s+[^\s\"\\]+", "Bearer [REDACTED]", value)
        return re.sub(r"sk-or-v1-[A-Za-z0-9_-]+", "[REDACTED]", value)

    async def request(self, request: httpx.Request) -> None:
        body = request.content
        self.exchanges.append({"request_body_utf8": self.redact(body.decode("utf-8")),
                               "request_bytes": len(body)})

    async def response(self, response: httpx.Response) -> None:
        await response.aread()
        body = self.redact(response.content.decode("utf-8", errors="replace"))
        try:
            parsed = json.loads(body)
        except ValueError:
            parsed = None
        self.exchanges[-1].update(response_body_utf8=body, response_json=parsed,
                                  http_status=response.status_code)


async def run_probes(client: Any, budget: Any, routes: list[dict], fixtures: list[dict],
                     variants: list[str], output: Path, capture: WireCapture | None = None,
                     repeats: int = 1, control_language: str = "numeric", instruction_style: str = "original") -> dict:
    """Run in a fresh directory and atomically checkpoint every completed call."""
    from .observations import HISTORY_PRIOR_LIMIT, HISTORY_WINDOW_S

    order = schedule(fixtures, routes, variants, repeats=repeats)
    output.mkdir(parents=True, exist_ok=False)
    control_language = getattr(client, "control_language", control_language)
    instruction_style = getattr(client, "instruction_style", instruction_style)
    instructions = getattr(client, "instructions", DRIVING_INSTRUCTIONS)
    question_contract = {"control": {"type": "choice", "instructions": instructions,
                                    "criteria": copy.deepcopy(getattr(client, "criteria", {
                                        action: value["description"] for action, value in ACTIONS.items()}))}}
    atomic_json(output / "manifest.json", {
        "created_at": time.time(), "fingerprint": source_fingerprint(), "routes": routes,
        "variants": variants, "fixtures": fixtures, "simulation_config": simulation_contract(),
        "planned_requests": len(order), "repeats": repeats, "control_language": control_language,
        "instruction_style": instruction_style,
        "question_contract": question_contract, "instructions_changed": instructions != DRIVING_INSTRUCTIONS,
        "history_contract": {"window_s": HISTORY_WINDOW_S, "maximum_prior_observations": HISTORY_PRIOR_LIMIT,
                             "timing": "Driver-observed credit times; no invented credit time before tracking starts.",
                             "rescue": "Clears recent motion; preserves checkpoint progress clock.",
                             "provenance": "Recorded fixtures use actual prior request ticks; scripted fixtures use fixed12tick cadence; "
                                           "synthetic drift has no invented prior observations. Current targets are not history samples."},
        "variant_information": {"raw": "Original sparse ego geometry.",
                                "road": "Readable structured geometry plus dense course bends.",
                                "road_text": "Same enriched geometry as prose.",
                                "road_physics": "Enriched geometry plus derived lateral-grip quantities.",
                                "kart_physics": "Road physics plus kart/velocity alignment and steering physics.",
                                "compact": "Compact factual navigation telemetry.",
                                "compact_text": "Compact factual navigation telemetry as prose.",
                                "road_navigation": "Road geometry with explicit ordered-gate facts.",
                                "compact_navigation": "Compact motion with explicit ordered-gate facts.",
                                "road_history": "Road navigation plus factual prior observations and progress clock."},
        "reference_action_effects": {snapshot["id"]: action_effect(snapshot["observation"],
                                                                  snapshot["diagnostic_reference_action"])
                                     for snapshot in fixtures},
        "request_order": [{"fixture": snapshot["id"], "model": route["model"], "variant": variant, "repeat": repeat}
                          for snapshot, route, variant, repeat in order],
    })
    records, status = [], "running"
    try:
        for index, (snapshot, route, variant, repeat) in enumerate(order):
            evidence = represent(snapshot["observation"], simulation_contract(), variant, context=snapshot.get("context"))
            if capture is not None:
                capture.exchanges = []
            try:
                decision = await client.decide(route, evidence)
            except BudgetExceeded:
                status = "budget_exhausted"
                break
            except Exception as exc:  # noqa: BLE001 — preserve results and never retry a paid call.
                decision = {"ok": False, "action": None, "cost": 0, "latency_ms": None,
                            "error": f"client_exception:{type(exc).__name__}"}
            exchanges = copy.deepcopy(capture.exchanges) if capture is not None else []
            wire_questions = json.loads(exchanges[0]["request_body_utf8"]).get("questions") if exchanges else None
            record = {"index": index, "fixture": snapshot["id"], "model": route["model"],
                      "repeat": repeat, "control_language": control_language,
                      "instruction_style": instruction_style,
                      "request_questions": wire_questions,
                      "admissible_choice_ids": list(wire_questions.get("control", {}).get("criteria", {})) if wire_questions else None,
                      "variant": variant, "route": route, "state": evidence, "decision": decision,
                      "encoded_bytes": exchanges[0]["request_bytes"] if exchanges else decision.get("payload_bytes"),
                      "wire": exchanges, "diagnostics": diagnostics(snapshot, decision.get("action"))}
            if capture is not None:
                record = json.loads(capture.redact(json.dumps(record, ensure_ascii=False)))
            name = f"{index:04d}--repeat-{repeat:02d}--{snapshot['id']}--{route['model'].replace('/', '--')}--{variant}.json"
            atomic_json(output / "calls" / name, record)
            records.append(record)
            atomic_json(output / "summary.json", summarize(records, planned=len(order), status="running",
                                                            budget=budget.summary(), repeats=repeats,
                                                            control_language=control_language,
                                                            instruction_style=instruction_style), replace=True)
            print(json.dumps({"index": index, "fixture": snapshot["id"], "model": route["model"],
                              "variant": variant, "repeat": repeat, "control_language": control_language,
                              "instruction_style": instruction_style,
                              "ok": decision["ok"], "action": decision.get("action"),
                              "latency_ms": decision.get("latency_ms"), "error": decision.get("error")}), flush=True)
        else:
            status = "complete"
    except BaseException:
        status = "interrupted"
        raise
    finally:
        summary = summarize(records, planned=len(order), status=status, budget=budget.summary(),
                            repeats=repeats, control_language=control_language, instruction_style=instruction_style)
        atomic_json(output / "summary.json", summary, replace=True)
    return summary


async def command(args: argparse.Namespace) -> dict:
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing probe directory: {output}")
    variants = args.variants.split(",")
    if not variants or len(set(variants)) != len(variants) or any(v not in VARIANTS for v in variants):
        raise ValueError(f"Variants must be unique members of {VARIANTS}")
    if isinstance(args.repeats, bool) or not isinstance(args.repeats, int) or args.repeats < 1:
        raise ValueError("repeats must be an integer >= 1")
    snapshots = select_fixtures(collect_fixtures(Path(args.records), Path(args.driving_record) if args.driving_record else None,
                                               Path(args.navigation_record) if getattr(args, "navigation_record", None) else None), args.fixtures)
    route_path = Path(args.routes)
    routes = json.loads(route_path.read_text()) if route_path.exists() else await discover_routes()
    if args.models:
        models = args.models.split(",")
        available = {route["model"]: route for route in routes}
        if len(set(models)) != len(models) or any(model not in available for model in models):
            raise ValueError("Requested models must be unique aliases present in pinned routes")
        routes = [available[model] for model in models]
    if not routes:
        raise ValueError("No routes selected")
    budget = Budget(path=Path("artifacts/budget.json"), cap_usd=10)
    capture = WireCapture()
    async with (
        httpx.AsyncClient(timeout=5, follow_redirects=False,
                          transport=httpx.AsyncHTTPTransport(retries=0),
                          event_hooks={"request": [capture.request], "response": [capture.response]}) as http,
        DecisionClient(budget=budget, actions=ACTIONS, http_client=http,
                       control_language=args.control_language, instruction_style=args.instruction_style) as decisions,
    ):
        capture.secret = decisions.api_key
        return await run_probes(decisions, budget, routes, snapshots, variants, output, capture,
                                repeats=args.repeats, control_language=args.control_language,
                                instruction_style=args.instruction_style)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/telemetry-probes-v1")
    parser.add_argument("--models", default=POC_MODELS,
                        help="Comma-separated exact aliases; the initial PoC defaults to Jev")
    parser.add_argument("--variants", default=",".join(VARIANTS))
    parser.add_argument("--routes", default=str(DEFAULT_RECORDS / "routes.json"))
    parser.add_argument("--records", default=str(DEFAULT_RECORDS),
                        help="Optional raw-telemetry screen directory; missing historical files are skipped")
    parser.add_argument("--driving-record", help="Append exactly replayed inside-oversteer cases and fixed lookbacks")
    parser.add_argument("--navigation-record", help="Append validated missed-gate and valid-behind-nose navigation cases")
    parser.add_argument("--fixtures", help="Comma-separated fixture IDs in desired order; defaults to every fixture")
    parser.add_argument("--repeats", type=int, default=1, help="Repeated paired blocks; integer >= 1")
    parser.add_argument("--control-language", choices=CONTROL_LANGUAGES, default="numeric",
                        help="Criterion-description experiment; same controls and action IDs")
    parser.add_argument("--instruction-style", choices=INSTRUCTION_STYLES, default="original",
                        help="Explicit question phrasing experiment; same physical controls")
    args = parser.parse_args()
    try:
        summary = asyncio.run(command(args))
    except (FileExistsError, ValueError, OSError) as exc:
        parser.exit(2, f"{exc}\n")
    except KeyboardInterrupt:
        parser.exit(130, "Interrupted; completed calls remain saved.\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
