import copy
import json
import math

import pytest

from mcpkart import telemetry
from mcpkart.decisions import DRIVING_INSTRUCTIONS, explicit_control_description
from mcpkart.observations import ObservationHistory
from mcpkart.sim import ACTIONS, Simulation
from mcpkart.telemetry import VARIANTS, represent

DISTANCES = (0, 3, 6, 10, 15, 22, 32, 45, 60)


def circle(radius=20.0, offset=1.0, road_distance=0.0):
    count = 256
    points = [
        [radius * math.cos(index * 2 * math.pi / count), radius * math.sin(index * 2 * math.pi / count)]
        for index in range(count)
    ]
    theta = road_distance / radius
    heading = theta + math.pi / 2 - 0.1
    x, y = (radius - offset) * math.cos(theta), (radius - offset) * math.sin(theta)
    cosine, sine = math.cos(heading), math.sin(heading)
    lookahead = []
    for distance in DISTANCES:
        px = radius * math.cos(theta + distance / radius) - x
        py = radius * math.sin(theta + distance / radius) - y
        lookahead.append(
            {
                "distance": distance,
                "x": px * cosine + py * sine,
                "y": -px * sine + py * cosine,
                "curvature": 1 / radius,
            }
        )
    observation = {
        "tick": 100,
        "time": 1.6667,
        "kart": {
            "x": x,
            "y": y,
            "heading": heading,
            "speed": 10.0,
            "vx": 10 * cosine - sine,
            "vy": 10 * sine + cosine,
            "yaw_rate": 0.2,
            "steering_angle": 0.15,
        },
        "track": {
            "width": 9,
            "offset": offset,
            "heading_error": 0.1,
            "on_road": abs(offset) <= 4.5,
            "lookahead": lookahead,
        },
        "progress": {"lap": 1, "track_distance": road_distance, "checkpoint": 2},
        "rescue": {"after_s": 3, "count": 0, "offroad_elapsed": 0},
        "control": "straight_accelerate",
        "next_checkpoint": {"x": 0, "y": 0, "ego_x": 5, "ego_y": 1, "forward_heading": heading + 0.3},
        "units": "Original raw units",
    }
    config = {
        "track": {"points": points, "width": 9},
        "actions": ACTIONS,
        "handling": {"lateral_grip": 13.0, "grass_grip": 8.0, "max_steering_angle": 0.32, "wheelbase": 1.8},
    }
    observation["handling"] = copy.deepcopy(config["handling"])
    return observation, config


def rigid_transform(observation, config, angle, dx, dy):
    observation, config = copy.deepcopy(observation), copy.deepcopy(config)
    cosine, sine = math.cos(angle), math.sin(angle)

    def transform(x, y):
        return x * cosine - y * sine + dx, x * sine + y * cosine + dy

    config["track"]["points"] = [transform(x, y) for x, y in config["track"]["points"]]
    for gate in config["track"].get("checkpoints", []):
        gate["x"], gate["y"] = transform(gate["x"], gate["y"])
        gate["heading"] += angle
    kart = observation["kart"]
    kart["x"], kart["y"] = transform(kart["x"], kart["y"])
    kart["vx"], kart["vy"] = (
        kart["vx"] * cosine - kart["vy"] * sine,
        kart["vx"] * sine + kart["vy"] * cosine,
    )
    kart["heading"] += angle
    checkpoint = observation["next_checkpoint"]
    checkpoint["x"], checkpoint["y"] = transform(checkpoint["x"], checkpoint["y"])
    checkpoint["forward_heading"] += angle
    return observation, config


def test_raw_is_an_independent_unchanged_observation():
    observation, config = circle()
    result = represent(observation, config, "raw")
    assert result == observation
    result["track"]["lookahead"][0]["x"] = 999
    assert observation["track"]["lookahead"][0]["x"] != 999


@pytest.mark.parametrize("variant", VARIANTS[1:])
def test_road_presentations_are_invariant_to_world_rotation_and_translation(variant):
    observation, config = circle(road_distance=23)
    transformed, transformed_config = rigid_transform(observation, config, 2.1, 101, -33)
    assert represent(observation, config, variant) == represent(transformed, transformed_config, variant)


def test_left_alignment_bend_offset_and_edge_clearance_are_distinct_facts():
    observation, config = circle(offset=1)
    result = represent(observation, config)
    road = result["road"]
    assert road["kart_side"] == "left"
    assert road["left_edge_clearance_m"] == 3.5
    assert road["right_edge_clearance_m"] == 5.5
    assert road["road_faces"] == "left"
    assert road["road_vs_kart_deg"] == pytest.approx(math.degrees(0.1), abs=0.001)
    assert road["preview"][0][3] == 0  # Current road tangent, not heading error.
    assert all(row[4] == "left" and row[5] == 20 for row in road["preview"])
    assert result["kart"]["velocity_forward_m_s"] == 10
    assert result["kart"]["velocity_left_m_s"] == 1
    assert result["kart"]["yaw_direction"] == "left"


def test_mirrored_road_reverses_left_right_without_recommending_controls():
    observation, config = circle()
    config["track"]["points"] = [[x, -y] for x, y in config["track"]["points"]]
    kart = observation["kart"]
    for name in ("y", "heading", "vy", "yaw_rate", "steering_angle"):
        kart[name] *= -1
    observation["track"]["offset"] *= -1
    observation["track"]["heading_error"] *= -1
    for point in observation["track"]["lookahead"]:
        point["y"] *= -1
        point["curvature"] *= -1
    result = represent(observation, config)
    assert result["road"]["kart_side"] == result["road"]["road_faces"] == "right"
    assert result["road"]["preview"][-1][3] < 0
    assert all(row[4] == "right" for row in result["road"]["preview"])
    assert result["kart"]["yaw_direction"] == result["kart"]["steering_direction"] == "right"


def test_straight_has_no_finite_curve_radius_and_no_future_tangent_turn():
    observation, config = circle(offset=0)
    config["track"]["points"] = [[x, 0] for x in range(0, 201, 25)] + [[200, 100], [0, 100]]
    observation["progress"]["track_distance"] = 75
    for point in observation["track"]["lookahead"]:
        point.update(x=point["distance"], y=0, curvature=0)
    rows = represent(observation, config)["road"]["preview"]
    assert all(row[3] == 0 and row[4] == "straight" and row[5] is None for row in rows)


def test_tangent_is_unwrapped_across_finish_line_and_more_than_half_circle():
    observation, config = circle(radius=12, road_distance=70)
    rows = represent(observation, config)["road"]["preview"]
    assert [row[0] for row in rows] == list(DISTANCES)
    for row in rows:
        assert row[3] == pytest.approx(math.degrees(row[0] / 12), abs=0.02)
    assert rows[-1][3] > 180


def test_offroad_edge_clearance_is_negative_not_an_instruction():
    observation, config = circle(offset=5)
    road = represent(observation, config)["road"]
    assert road["left_edge_clearance_m"] == -0.5
    assert road["right_edge_clearance_m"] == 9.5
    assert road["on_road"] is False


@pytest.mark.parametrize("variant", VARIANTS)
def test_presentations_do_not_mutate_kinematics_inputs_or_config(variant):
    observation, config = circle()
    before_observation, before_config = copy.deepcopy(observation), copy.deepcopy(config)
    result = represent(observation, config, variant)
    json.dumps(result, allow_nan=False)
    assert observation == before_observation
    assert config == before_config
    if variant in {"compact_inputs", "road_compass"}:
        assert result["held_input"] == {
            key: config["actions"][observation["control"]][key] for key in ("steer", "throttle", "brake")
        }
    else:
        assert result["control"] == observation["control"]
    assert result["progress"] == observation["progress"]
    assert result["rescue"] == observation["rescue"]
    if variant in {"compact", "compact_text", "compact_inputs", "road_compass", "compact_navigation"}:
        assert result["handling"]["road_grip_m_s2"] == config["handling"]["lateral_grip"]
        assert result["handling"]["wheelbase_m"] == config["handling"]["wheelbase"]
    else:
        assert result["handling"] == config["handling"]
    if variant != "raw":
        generated_geometry = json.dumps(
            result
            if variant in {"compact", "compact_text", "compact_inputs", "road_compass"}
            else result.get("road", result.get("road_report"))
        )
        for hidden_policy in ("target_speed", "safe_speed", "recommended", "braking_point", "racing_line"):
            assert hidden_policy not in generated_geometry


def test_text_contains_same_road_facts_and_separates_road_from_kart_heading():
    observation, config = circle()
    text = represent(observation, config, "road_text")
    assert "road" not in text
    assert "Road width 9m" in text["road_report"]
    assert "1m left of centre" in text["road_report"]
    assert "left edge clearance 3.5m, right 5.5m" in text["road_report"]
    assert "0m: ego" in text["road_report"] and "60m: ego" in text["road_report"]
    assert "radius 20m" in text["road_report"]
    assert "tangent change from current ROAD" in text["road_report"]


def test_physics_ratios_scale_with_speed_squared_and_current_grip():
    observation, config = circle()
    original = represent(observation, config, "road_physics")
    assert original["physics"]["current_lateral_grip_mps2"] == 13
    row = original["road"]["preview"][0]
    assert row[-2] == 5  # 10² / radius20.
    assert row[-1] == pytest.approx(5 / 13, abs=0.0001)
    observation["kart"]["speed"] *= 2
    faster = represent(observation, config, "road_physics")
    assert faster["road"]["preview"][0][-2] == row[-2] * 4
    assert faster["road"]["preview"][0][-1] == pytest.approx(row[-1] * 4, abs=0.0003)
    assert faster["physics"]["grip_limited_minimum_steady_turn_radius_m"] == pytest.approx(
        400 / 13, abs=0.001
    )
    assert "grip usage >1" in faster["units"]
    observation["track"]["on_road"] = False
    grass = represent(observation, config, "road_physics")
    assert grass["physics"]["current_surface"] == "grass"
    assert grass["physics"]["current_lateral_grip_mps2"] == 8
    assert grass["road"]["preview"][0][-1] == 20 / 8


def test_default_road_has_no_physics_ratios_or_control_policy():
    observation, config = circle()
    result = represent(observation, config)
    assert "physics" not in result
    assert "grip_usage_at_current_speed" not in result["road"]["preview_columns"]


def test_dense_bends_capture_narrow_curve_between_sparse_preview_points():
    sim = Simulation()
    sim.s, sim.offset = 50, 0
    sim.x, sim.y, sim.heading, _ = sim.track.at(sim.s)
    observation = sim.observation()
    road = represent(observation, sim.config())["road"]
    sparse_tightest = min(row[5] for row in road["preview"] if row[5] is not None)
    narrow_bend = next(bend for bend in road["bends"] if bend["direction"] == "right")
    assert narrow_bend["tightest_radius_m"] == pytest.approx(3.8, abs=0.01)
    assert 37 < narrow_bend["tightest_in_road_m"] < 39  # Between the 32/45m preview points.
    assert narrow_bend["tightest_radius_m"] < sparse_tightest / 2
    assert narrow_bend["heading_change_deg"] < 0
    assert road["bend_sampling"]["includes_all_source_vertices"]


def test_dense_bend_limit_preserves_nearest_and_reports_omitted_regions(monkeypatch):
    sim = Simulation()
    sim.s, sim.offset = 50, 0
    sim.x, sim.y, sim.heading, _ = sim.track.at(sim.s)
    monkeypatch.setattr(telemetry, "BEND_SUMMARY_LIMIT", 1)
    road = represent(sim.observation(), sim.config())["road"]
    assert len(road["bends"]) == 1
    assert road["bends"][0]["starts_in_road_m"] == 0
    assert road["bend_sampling"]["total_regions"] == 3
    assert road["bend_sampling"]["shown_limit"] == 1


def test_invalid_variants_and_track_geometry_are_explicit_errors():
    observation, config = circle()
    with pytest.raises(ValueError, match="Unknown telemetry variant"):
        represent(observation, config, "autopilot")
    config["track"]["points"] = [[0, 0], [1, 0]]
    with pytest.raises(ValueError, match="at least three"):
        represent(observation, config)


@pytest.mark.parametrize("nose_deg,velocity_deg,side", [(41, 20, "left"), (-41, -20, "right")])
def test_kart_alignment_uses_kart_relative_to_road_and_separate_velocity_heading(
    nose_deg, velocity_deg, side
):
    observation, config = circle(offset=3.8 if side == "left" else -3.8)
    kart, track = observation["kart"], observation["track"]
    road_heading = kart["heading"] + track["heading_error"]
    kart["heading"] = road_heading + math.radians(nose_deg)
    track["heading_error"] = -math.radians(nose_deg)
    velocity_heading = road_heading + math.radians(velocity_deg)
    kart["vx"], kart["vy"] = 10 * math.cos(velocity_heading), 10 * math.sin(velocity_heading)
    alignment = represent(observation, config, "kart_physics")["current_alignment"]
    assert alignment["metres_from_centre"] == 3.8
    assert alignment["side_of_centre"] == side
    assert alignment["nose_vs_road_deg"] == nose_deg
    assert alignment["nose_points"] == side
    assert alignment["velocity_vs_road_deg"] == velocity_deg
    assert alignment["velocity_points"] == side


@pytest.mark.parametrize("speed", [0.0, 1e-9])
def test_kart_velocity_heading_and_yaw_curvature_are_null_at_near_zero_speed(speed):
    observation, config = circle()
    observation["kart"].update(speed=speed, vx=speed, vy=0)
    result = represent(observation, config, "kart_physics")
    assert result["current_alignment"]["velocity_vs_road_deg"] is None
    assert result["current_alignment"]["velocity_points"] == "stationary"
    assert result["physics"]["current_yaw_curvature_rad_m"] is None
    assert result["current_alignment"]["nose_vs_road_deg"] is not None


@pytest.mark.parametrize("wheel_angle", [-0.16, 0.16])
def test_steering_geometry_table_and_current_wheel_are_consistent_without_grip_or_policy(wheel_angle):
    observation, config = circle()
    observation["kart"]["steering_angle"] = wheel_angle
    result = represent(observation, config, "kart_physics")
    rows = result["steering_geometry"]["rows"]
    assert [row[0] for row in rows] == [-1, -0.5, 0, 0.5, 1]
    wheelbase, maximum = config["handling"]["wheelbase"], config["handling"]["max_steering_angle"]
    for setting, wheel_deg, curvature, radius in rows:
        assert wheel_deg == pytest.approx(math.degrees(setting * maximum), abs=0.001)
        assert curvature == pytest.approx(math.tan(setting * maximum) / wheelbase, abs=1e-6)
        if setting == 0:
            assert radius is None
        else:
            assert abs(curvature) * radius == pytest.approx(1, abs=0.0001)
    current = result["physics"]
    assert current["current_wheel_nominal_curvature_rad_m"] == pytest.approx(
        math.tan(wheel_angle) / wheelbase, abs=1e-6
    )
    assert current["current_wheel_nominal_radius_m"] == pytest.approx(
        wheelbase / abs(math.tan(wheel_angle)), abs=0.001
    )
    assert current["current_road_curvature_rad_m"] == observation["track"]["lookahead"][0]["curvature"]
    assert current["current_road_radius_m"] == 20
    assert current["current_yaw_curvature_rad_m"] == 0.02
    assert result["current_alignment"]["wheel_points"] == ("left" if wheel_angle > 0 else "right")
    assert "excludes grip and response delays" in result["units"]


def test_zero_wheel_angle_and_straight_road_have_no_finite_nominal_radius():
    observation, config = circle()
    observation["kart"]["steering_angle"] = 0
    observation["track"]["lookahead"][0]["curvature"] = 0
    physics = represent(observation, config, "kart_physics")["physics"]
    assert physics["current_wheel_nominal_curvature_rad_m"] == 0
    assert physics["current_wheel_nominal_radius_m"] is None
    assert physics["current_road_curvature_rad_m"] == 0
    assert physics["current_road_radius_m"] is None


def test_kart_profile_retains_road_and_grip_facts_without_changing_other_variants():
    observation, config = circle()
    road = represent(observation, config, "road_physics")
    kart = represent(observation, config, "kart_physics")
    assert kart["road"] == road["road"]
    assert kart["kart"] == road["kart"]
    assert all(kart["physics"][key] == value for key, value in road["physics"].items())
    assert "current_alignment" not in road
    assert "steering_geometry" not in road


def test_compact_present_pose_distinguishes_nose_velocity_lateral_motion_and_future_bend():
    observation, config = circle(offset=3.8)
    kart, track = observation["kart"], observation["track"]
    road_heading = kart["heading"] + track["heading_error"]
    kart["heading"] = road_heading + math.radians(41)
    track["heading_error"] = -math.radians(41)
    kart["vx"], kart["vy"] = (
        10 * math.cos(road_heading + math.radians(20)),
        10 * math.sin(road_heading + math.radians(20)),
    )
    result = represent(observation, config, "compact")
    pose = result["present"]
    assert pose["offset"] == {"m": 3.8, "side": "left"}
    assert pose["edges"] == {"left_m": 0.7, "right_m": 8.3}
    assert pose["nose_vs_road"] == {"deg": 41, "side": "left"}
    assert pose["velocity_vs_road"] == {"deg": 20, "side": "left"}
    assert pose["road_lateral_m_s"] == pytest.approx(10 * math.sin(math.radians(20)), abs=0.0001)
    assert pose["road_lateral_side"] == "left"
    assert result["future_bends"][0]["direction"] == "left"
    assert "future bend direction is NOT kart heading" in result["units"]


def test_compact_local_path_uses_six_projection_arcs_and_kart_frame_polar_coordinates():
    observation, config = circle()
    result = represent(observation, config, "compact")
    assert [row[0] for row in result["local_path"]["points"]] == [0, 3, 6, 10, 15, 22]
    for row, point in zip(result["local_path"]["points"], observation["track"]["lookahead"]):
        assert row[1] == pytest.approx(math.degrees(math.atan2(point["y"], point["x"])), abs=0.001)
        assert row[2] == pytest.approx(math.hypot(point["x"], point["y"]), abs=0.001)


def test_compact_keeps_nearest_two_dense_bends_and_labels_constant_speed_arc_time():
    sim = Simulation()
    sim.s, sim.offset = 50, 0
    sim.x, sim.y, sim.heading, _ = sim.track.at(sim.s)
    sim.vx = 10
    observation, config = sim.observation(), sim.config()
    result = represent(observation, config, "compact")
    rich = represent(observation, config, "kart_physics")
    assert len(result["future_bends"]) == 2
    assert result["bend_sampling"]["regions"] == 3
    for bend, original in zip(result["future_bends"], rich["road"]["bends"]):
        assert bend["direction"] == original["direction"]
        assert bend["peak_arc_m"] == original["tightest_in_road_m"]
        assert bend["min_radius_m"] == original["tightest_radius_m"]
        assert bend["peak_seconds_at_current_speed"] == pytest.approx(bend["peak_arc_m"] / 10, abs=0.001)
        assert bend["peak_need_m_s2"] == original[telemetry.PHYSICS_COLUMNS[0]]
        assert bend["peak_grip_ratio"] == original[telemetry.PHYSICS_COLUMNS[1]]


@pytest.mark.parametrize("variant", ["compact", "compact_text"])
def test_compact_zero_speed_and_zero_range_have_explicit_nulls(variant):
    observation, config = circle()
    observation["kart"].update(speed=0, vx=0, vy=0)
    observation["track"]["lookahead"][0].update(x=0, y=0)
    result = represent(observation, config, variant)
    json.dumps(result, allow_nan=False)
    if variant == "compact":
        assert result["present"]["velocity_vs_road"] is None
        assert result["present"]["road_lateral_m_s"] == 0
        assert result["present"]["road_lateral_side"] == "none"
        assert result["physics"]["yaw_curve_rad_m"] is None
        assert result["local_path"]["points"][0] == [0, None, 0]
        assert all(bend["peak_seconds_at_current_speed"] is None for bend in result["future_bends"])
    else:
        assert "stationary (angle null)" in result["road_report"]
        assert "body yaw/speed curvature null" in result["road_report"]
        assert "arc/speed null" in result["road_report"]
        assert "arc 0m: bearing null, range 0m" in result["road_report"]


def test_compact_text_keeps_identical_metadata_and_reports_facts_without_duplicate_structures():
    observation, config = circle()
    structured = represent(observation, config, "compact")
    text = represent(observation, config, "compact_text")
    formatted = {"present", "physics", "local_path", "future_bends", "bend_sampling"}
    assert {key: value for key, value in structured.items() if key not in formatted} == {
        key: value for key, value in text.items() if key != "road_report"
    }
    assert not formatted.intersection(text)
    assert text["road_report"] == telemetry._compact_report(structured)
    assert "PRESENT:" in text["road_report"]
    assert "Nose versus CURRENT road:" in text["road_report"]
    assert "FUTURE ROAD GEOMETRY, independent of kart heading" in text["road_report"]


@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("language", ["numeric", "explicit"])
def test_profiles_fit_existing_decision_request_guard_for_full_real_track_states(variant, language):
    for position in (0, 50, 100):
        sim = Simulation(reset_after_s=3)
        sim.s, sim.offset = position, 0
        sim.x, sim.y, sim.heading, _ = sim.track.at(position)
        sim.vx = 24
        observation, config = sim.observation(), sim.config()
        observation["handling"] = config["handling"]
        observation["next_checkpoint"] = {"ego_x": 30.123, "ego_y": -30.123, "forward_heading": 1.23}
        state = represent(observation, config, variant)
        payload = {
            "model": "typesafe/jev-1.14",
            "state": state,
            "questions": {
                "control": {
                    "type": "choice",
                    "instructions": DRIVING_INSTRUCTIONS,
                    "criteria": {
                        key: explicit_control_description(value)
                        if language == "explicit"
                        else value["description"]
                        for key, value in ACTIONS.items()
                    },
                }
            },
            "provider": {"only": ["typesafe"], "allow_fallbacks": False},
        }
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
        assert len(encoded) + 512 <= 8192
        if variant in {"compact", "compact_text", "compact_inputs", "road_compass"}:
            assert len(json.dumps(state, separators=(",", ":"), ensure_ascii=False).encode()) <= 2500


def test_compact_inputs_removes_current_answer_label_but_keeps_exact_physical_input():
    observation, config = circle()
    observation["control"] = "hard_left_brake"
    baseline = represent(observation, config, "compact")
    result = represent(observation, config, "compact_inputs")
    assert "control" not in result
    assert observation["control"] not in json.dumps(result)
    assert result["held_input"] == {"steer": 1.0, "throttle": 0.0, "brake": 1.0}
    assert {key: value for key, value in result.items() if key not in {"held_input", "units"}} == {
        key: value for key, value in baseline.items() if key not in {"control", "units"}
    }
    assert result["units"].startswith(baseline["units"])
    assert "absolute normalized target wheel setting" in result["units"]
    assert "not a next choice" in result["units"]


def test_compact_inputs_requires_a_real_physical_definition_without_substituting_controls():
    observation, config = circle()
    observation["control"] = "unknown"
    with pytest.raises(ValueError, match="physical config.actions"):
        represent(observation, config, "compact_inputs")


@pytest.mark.parametrize("offset,nose_deg,road_direction", [(3.8, 41, "RIGHT"), (-3.8, -41, "LEFT")])
def test_road_compass_real_track_pose_reports_road_opposite_to_kart_deviation(
    offset, nose_deg, road_direction
):
    sim = Simulation()
    road_x, road_y, road_heading, _ = sim.track.at(50)
    sim.s, sim.offset = 50, offset
    sim.x = road_x - math.sin(road_heading) * offset
    sim.y = road_y + math.cos(road_heading) * offset
    sim.heading = road_heading + math.radians(nose_deg)
    sim.vx, sim.vy = 10 * math.cos(sim.heading), 10 * math.sin(sim.heading)
    result = represent(sim.observation(), sim.config(), "road_compass")
    here = result["road_here"]
    assert here["centre"]["direction"] == road_direction
    assert here["forward_tangent"] == {"deg": 41, "direction": road_direction}
    assert here["centre"]["range_m"] == pytest.approx(abs(offset), abs=0.001)
    assert (here["centre"]["ego_y_m"] < 0) == (road_direction == "RIGHT")
    assert result["kart"]["velocity_forward_m_s"] == 10
    assert result["kart"]["velocity_left_m_s"] == 0
    assert "present" not in result and "current_alignment" not in result
    assert all(isinstance(value, (int, float)) for value in result["kart"].values())


def test_road_compass_path_bearing_words_and_window_flags_describe_real_geometry():
    sim = Simulation()
    sim.s, sim.offset = 50, 0
    sim.x, sim.y, sim.heading, _ = sim.track.at(sim.s)
    result = represent(sim.observation(), sim.config(), "road_compass")
    for arc, x, y, distance, bearing, direction in result["local_path"]["points"]:
        assert arc in [0, 3, 6, 10, 15, 22]
        assert distance == pytest.approx(math.hypot(x, y), abs=0.001)
        if distance == 0:
            assert bearing is None and direction is None
        else:
            assert bearing == pytest.approx(math.degrees(math.atan2(y, x)), abs=0.001)
            assert direction == ("LEFT" if bearing > 0 else "RIGHT" if bearing < 0 else "AHEAD")
    assert len(result["future_bends"]) <= 2
    assert all(bend["from_arc_m"] <= 22 for bend in result["future_bends"])
    assert result["future_bends"][0]["end_beyond_window"] is True
    assert result["future_bends"][0]["peak_beyond_window"] is True
    assert result["bend_window"]["starts_within_arc_m"] == 22


def test_road_compass_stationary_zero_range_retains_defined_geometry_without_inventing_a_bearing():
    observation, config = circle(offset=0)
    observation["kart"].update(speed=0, vx=0, vy=0)
    result = represent(observation, config, "road_compass")
    json.dumps(result, allow_nan=False)
    assert result["road_here"]["centre"]["range_m"] == 0
    assert result["road_here"]["centre"]["bearing_deg"] is None
    assert result["road_here"]["centre"]["direction"] is None
    assert result["kart"]["velocity_forward_m_s"] == result["kart"]["velocity_left_m_s"] == 0
    assert result["physics"]["yaw_curve_rad_m"] is None


def gate_fixture(x=-2, y=1, heading=math.pi):
    observation, config = circle()
    observation["kart"].update(x=x, y=y, heading=heading)
    observation["progress"]["checkpoint"] = 0
    config["track"]["checkpoints"] = [{"x": 0, "y": 0, "heading": 0}]
    return observation, config


@pytest.mark.parametrize("variant", ["road_navigation", "compact_navigation", "road_history"])
def test_gate_plane_is_distinct_from_bearing_orientation_and_whether_behind_nose(variant):
    observation, config = gate_fixture()
    gate = represent(observation, config, variant)["next_gate"]
    assert gate["known"]
    assert gate["centre_ego_m"] == [-2, 1]
    assert gate["range_m"] == pytest.approx(math.sqrt(5), abs=0.001)
    assert gate["bearing_to_centre_deg"] == pytest.approx(153.435, abs=0.001)
    assert gate["forward_heading_vs_kart_deg"] == -180
    assert gate["behind_kart_nose"] is True
    assert gate["signed_plane_m"] == -2  # Behind nose, yet still on the approach side.
    assert gate["signed_lateral_m"] == 1
    assert gate["half_width_m"] == 4.5
    assert gate["within_span_now"] is True
    assert "interpolated |lateral|<=half_width" in gate["crossing_rule"]
    assert "Within_span_now is not credit" in gate["crossing_rule"]
    assert (
        "Uncredited gate remains required; reverse crossings and rescue give no credit"
        in gate["crossing_rule"]
    )
    assert "on_road" not in gate["crossing_rule"]


def test_uncredited_gate_beyond_plane_and_outside_span_is_reported_without_awarding_credit():
    observation, config = gate_fixture(x=2, y=-5, heading=0)
    original_progress = copy.deepcopy(observation["progress"])
    gate = represent(observation, config, "road_navigation")["next_gate"]
    assert gate["behind_kart_nose"] is True
    assert gate["signed_plane_m"] == 2
    assert gate["signed_lateral_m"] == -5
    assert gate["within_span_now"] is False
    assert observation["progress"] == original_progress
    assert "credited" not in gate


def test_gate_forward_velocity_uses_gate_orientation_not_nose_or_bearing():
    observation, config = gate_fixture()
    observation["kart"].update(vx=3, vy=4)
    assert represent(observation, config, "road_navigation")["next_gate"]["gate_forward_velocity_m_s"] == 3
    config["track"]["checkpoints"][0]["heading"] = math.pi / 2
    assert represent(observation, config, "road_navigation")["next_gate"]["gate_forward_velocity_m_s"] == 4


def test_gate_geometry_is_invariant_to_rigid_world_transformations():
    observation, config = gate_fixture()
    transformed, transformed_config = rigid_transform(observation, config, 1.7, -100, 233)
    assert (
        represent(observation, config, "road_navigation")["next_gate"]
        == represent(transformed, transformed_config, "road_navigation")["next_gate"]
    )


def test_gate_at_kart_has_no_invented_bearing_and_missing_gate_is_explicit_unknown():
    observation, config = gate_fixture(x=0, y=0, heading=0)
    gate = represent(observation, config, "road_navigation")["next_gate"]
    assert gate["range_m"] == 0
    assert gate["bearing_to_centre_deg"] is None
    assert gate["signed_plane_m"] == 0
    del config["track"]["checkpoints"]
    observation.pop("next_checkpoint")
    gate = represent(observation, config, "road_navigation")["next_gate"]
    assert gate == {"known": False, "index": 0, "reason": "next gate geometry unavailable"}


@pytest.mark.parametrize("context", [None, {}, {"recent_motion": {}, "checkpoint_clock": {}}])
def test_road_history_missing_context_is_unknown_without_fabricated_motion_or_clock(context):
    observation, config = gate_fixture()
    history = represent(observation, config, "road_history", context=context)["history"]
    assert history == {"recent_motion": None, "checkpoint_clock": None, "status": "not_known"}


def test_road_history_copies_supplied_factual_context_without_changing_navigation_only():
    sim = Simulation()
    tracker = ObservationHistory()
    for _ in range(4):
        observation = sim.observation()
        context = tracker.observe(observation)
        sim.set_control("straight_accelerate")
        for _ in range(10):
            sim.step()
    original = copy.deepcopy(context)
    result = represent(observation, sim.config(), "road_history", context=context)
    assert result["history"]["status"] == "available"
    assert result["history"]["recent_motion"] == original["recent_motion"]
    assert result["history"]["checkpoint_clock"] == original["checkpoint_clock"]
    assert "nose sign opposes road_vs_kart" in result["units"]
    assert "target_speed" not in json.dumps(result["history"])
    result["history"]["recent_motion"]["samples"][0]["offset_m"] = 999
    assert context == original
    assert represent(observation, sim.config(), "road_navigation", context=context) == represent(
        observation, sim.config(), "road_navigation"
    )


def test_compact_navigation_clarifies_magnitudes_and_retains_old_compact_facts():
    observation, config = gate_fixture()
    compact = represent(observation, config, "compact")
    navigation = represent(observation, config, "compact_navigation")
    assert {key: value for key, value in navigation.items() if key not in {"next_gate", "units"}} == {
        key: value for key, value in compact.items() if key not in {"next_checkpoint", "units"}
    }
    assert "MAGNITUDES; side gives direction" in navigation["units"]
    assert "stay SIGNED" in navigation["units"]
    assert "MAGNITUDES" not in compact["units"]


@pytest.mark.parametrize("language", ["numeric", "explicit"])
def test_navigation_and_full_three_sample_history_fit_request_guard(language):
    sim = Simulation(reset_after_s=3)
    tracker = ObservationHistory()
    for position in (0, 50, 100):
        sim.s = position
        sim.x, sim.y, sim.heading, _ = sim.track.at(position)
        sim.vx = 24
        for index in range(4):
            sim.tick = 3900 + index * 12
            sim.elapsed = 65 + index * 0.2
            observation = sim.observation()
            context = tracker.observe(observation)
        for variant in ("road_navigation", "compact_navigation", "road_history"):
            state = represent(observation, sim.config(), variant, context=context)
            payload = {
                "model": "typesafe/jev-1.14",
                "state": state,
                "questions": {
                    "control": {
                        "type": "choice",
                        "instructions": DRIVING_INSTRUCTIONS,
                        "criteria": {
                            key: explicit_control_description(value)
                            if language == "explicit"
                            else value["description"]
                            for key, value in ACTIONS.items()
                        },
                    }
                },
                "provider": {"only": ["typesafe"], "allow_fallbacks": False},
            }
            assert len(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()) + 512 <= 8192
