"""Pure alternative presentations of observed road geometry and vehicle physics.

These presentations never choose controls, a racing line, a speed, or a braking
point. ``raw`` preserves the supplied observation. Other variants express the
same road geometry in a local frame and discard redundant world coordinates.
The optional ``road_physics`` variant explicitly adds derived physical quantities.
"""

from __future__ import annotations

import bisect
import copy
import math
from functools import lru_cache

VARIANTS = (
    "raw",
    "road",
    "road_text",
    "road_physics",
    "kart_physics",
    "compact",
    "compact_text",
    "compact_inputs",
    "road_compass",
    "road_navigation",
    "compact_navigation",
    "road_history",
)
COMPACT_PATH_ARCS_M = (0, 3, 6, 10, 15, 22)
COMPACT_UNITS = (
    "m,s,deg; signed angles/yaw/curvature and road-lateral velocity are positive LEFT. "
    "PRESENT pose is kart versus current road; future bend direction is NOT kart heading. "
    "Negative edge clearance is off-road. Path bearing is from kart nose; range is Euclidean. "
    "Arc distances start at nearest road projection. "
    "Bend seconds=arc/current speed, not arrival prediction. Need=v²/r; grip ratio>1 exceeds current grip. "
    "Grip radius excludes steering/transients; wheel curvature=tan(angle)/wheelbase; yaw curvature=body yaw/speed."
)
NAVIGATION_UNITS = (
    "m,s; display angles deg, handling angles rad. Positive steering/yaw/curvature/ego y/offset are LEFT; "
    "ego x forward. Wheel angle is actual; control is held input. road_vs_kart=road tangent minus kart heading. "
    "road_turn=future tangent minus current ROAD tangent. Preview distances are centreline arc from nearest "
    "projection. Edge clearance<0 is outside. Need=v²×|curvature|; grip ratio>1 exceeds current surface grip. "
    "Grip radius excludes steering limits/transients."
)
# Numerical zero only, not a bend severity or driving-policy threshold.
ZERO_EPSILON = 1e-9
STATIONARY_SPEED_MPS = 1e-6  # Numerical guard for heading/curvature at effectively zero speed.
STEERING_SETTINGS = (-1.0, -0.5, 0.0, 0.5, 1.0)
BEND_SAMPLE_MAX_STEP_M = 1.0
BEND_HORIZON_M = 60.0
BEND_CURVATURE_THRESHOLD_RAD_PER_M = 0.004  # Radius >=250m is grouped as straight.
BEND_SUMMARY_LIMIT = 3
PREVIEW_COLUMNS = ("ahead_m", "ego_x_m", "ego_y_m", "road_turn_deg", "bend", "radius_m")
PHYSICS_COLUMNS = ("lateral_acceleration_needed_at_current_speed_mps2", "grip_usage_at_current_speed")
UNITS = (
    "Metres, seconds; speed m/s. Display angles degrees; handling constants retain radians. "
    "Positive steering/yaw is left. Ego x forward, y left. Offset positive left of road centre. "
    "Kart steering is the current wheel angle; control is the held input. "
    "Road tangent/curvature describe geometry, not a steering command. "
    "Edge clearance negative means outside. Road_vs_kart is road tangent minus kart heading. "
    "Road_turn is future tangent change from CURRENT ROAD tangent, not from kart heading. "
    "Ahead/bend distances are centreline arc length from the nearest road projection, "
    "not Euclidean distance forward from kart. Bend/radius describe local road curvature."
)


def _wrap(angle: float) -> float:
    return (angle + math.pi) % (2 * math.pi) - math.pi


def _number(value: float, digits: int = 3) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0 else rounded


def _direction(value: float, zero: str = "straight") -> str:
    return "left" if value > ZERO_EPSILON else "right" if value < -ZERO_EPSILON else zero


@lru_cache(maxsize=8)
def _geometry(points: tuple[tuple[float, float], ...]) -> tuple:
    """Reconstruct Track.at's interpolated centreline tangent, without a driver.

    Headings are unwrapped around the closed polyline so a long future left bend
    never becomes a right bend merely because its accumulated turn exceeds 180°.
    Central-neighbour tangents and their arc-length interpolation match the
    simulation's published track representation rather than noisy distant chords.
    """
    if len(points) > 1 and math.dist(points[0], points[-1]) <= ZERO_EPSILON:
        points = points[:-1]
    if len(points) < 3:
        raise ValueError("Road telemetry requires at least three closed-track centreline points")
    lengths = [0.0]
    headings = []
    count = len(points)
    for index, point in enumerate(points):
        next_point = points[(index + 1) % count]
        length = math.dist(point, next_point)
        if length <= ZERO_EPSILON:
            raise ValueError("Track centreline contains adjacent duplicate points")
        lengths.append(lengths[-1] + length)
        previous = points[(index - 1) % count]
        headings.append(math.atan2(next_point[1] - previous[1], next_point[0] - previous[0]))
    unwrapped = [headings[0]]
    for heading in headings[1:] + headings[:1]:
        unwrapped.append(unwrapped[-1] + _wrap(heading - unwrapped[-1]))
    winding = unwrapped[-1] - unwrapped[0]
    spacing = lengths[-1] / count
    # Same central difference and interpolation as the simulation's Track.at.
    curvatures = []
    for index in range(count):
        previous = unwrapped[index - 1] if index else unwrapped[count - 1] - winding
        following = unwrapped[index + 1]
        curvatures.append((following - previous) / (spacing * 2))
    return tuple(lengths), tuple(unwrapped), winding, tuple(curvatures)


def _heading(distance: float, geometry: tuple) -> float:
    lengths, headings, winding, _ = geometry
    circuits, position = divmod(distance, lengths[-1])
    index = min(bisect.bisect_right(lengths, position) - 1, len(lengths) - 2)
    fraction = (position - lengths[index]) / (lengths[index + 1] - lengths[index])
    return headings[index] + fraction * (headings[index + 1] - headings[index]) + circuits * winding


def _curvature(distance: float, geometry: tuple) -> float:
    lengths, _, _, curvatures = geometry
    position = distance % lengths[-1]
    index = min(bisect.bisect_right(lengths, position) - 1, len(lengths) - 2)
    fraction = (position - lengths[index]) / (lengths[index + 1] - lengths[index])
    return curvatures[index] + fraction * (curvatures[(index + 1) % len(curvatures)] - curvatures[index])


def _bends(position: float, geometry: tuple) -> tuple[list[dict], int]:
    """Summarize signed curve regions from dense immutable course geometry.

    Include every source vertex as well as a <=1m grid, so a curvature maximum
    between the original nine lookahead points cannot disappear through sampling.
    Threshold crossings are interpolated; bends are clipped to the visible arc.
    """
    lengths = geometry[0]
    samples = {0.0, BEND_HORIZON_M}
    steps = math.ceil(BEND_HORIZON_M / BEND_SAMPLE_MAX_STEP_M)
    samples.update(index * BEND_HORIZON_M / steps for index in range(steps + 1))
    for circuit in range(
        math.floor(position / lengths[-1]), math.floor((position + BEND_HORIZON_M) / lengths[-1]) + 1
    ):
        for source_distance in lengths[:-1]:
            ahead = source_distance + circuit * lengths[-1] - position
            if 0 < ahead < BEND_HORIZON_M:
                samples.add(ahead)
    samples = [(ahead, _curvature(position + ahead, geometry)) for ahead in sorted(samples)]
    threshold = BEND_CURVATURE_THRESHOLD_RAD_PER_M

    def sign(curvature):
        return 1 if curvature > threshold else -1 if curvature < -threshold else 0

    def crossing(previous, current, direction):
        distance, curvature = previous
        next_distance, next_curvature = current
        return distance + (direction * threshold - curvature) / (next_curvature - curvature) * (
            next_distance - distance
        )

    bends = []
    active = None

    def close(end):
        start, direction, tightest_distance, tightest_curvature = active
        bends.append(
            {
                "starts_in_road_m": _number(start),
                "ends_in_road_m": _number(end),
                "direction": "left" if direction > 0 else "right",
                "tightest_radius_m": _number(1 / abs(tightest_curvature)),
                "tightest_in_road_m": _number(tightest_distance),
                "heading_change_deg": _number(
                    math.degrees(_heading(position + end, geometry) - _heading(position + start, geometry))
                ),
            }
        )

    for index, sample in enumerate(samples):
        distance, curvature = sample
        direction = sign(curvature)
        if active is not None and direction != active[1]:
            close(crossing(samples[index - 1], sample, active[1]))
            active = None
        if direction and active is None:
            start = crossing(samples[index - 1], sample, direction) if index else distance
            active = (start, direction, distance, curvature)
        elif active is not None and abs(curvature) > abs(active[3]) + ZERO_EPSILON:
            active = (active[0], active[1], distance, curvature)
    if active is not None:
        close(BEND_HORIZON_M)
    return bends[:BEND_SUMMARY_LIMIT], len(bends)


def _road(observation: dict, config: dict) -> dict:
    track = observation["track"]
    width = float(track["width"])
    offset = float(track["offset"])
    heading_error = float(track["heading_error"])
    points = tuple(tuple(map(float, point)) for point in config["track"]["points"])
    geometry = _geometry(points)
    position = float(observation["progress"]["track_distance"])
    road_heading = _heading(position, geometry)
    bends, bend_count = _bends(position, geometry)
    rows = []
    for point in track["lookahead"]:
        distance = float(point["distance"])
        curvature = float(point["curvature"])
        turn = _heading(position + distance, geometry) - road_heading
        rows.append(
            [
                _number(distance),
                _number(point["x"]),
                _number(point["y"]),
                _number(math.degrees(turn)),
                _direction(curvature),
                _number(1 / abs(curvature)) if abs(curvature) > ZERO_EPSILON else None,
            ]
        )
    return {
        "width_m": _number(width),
        "offset_m": _number(offset),
        "kart_side": _direction(offset, "centre"),
        "left_edge_clearance_m": _number(width / 2 - offset),
        "right_edge_clearance_m": _number(width / 2 + offset),
        "on_road": bool(track.get("on_road", abs(offset) <= width / 2)),
        "road_vs_kart_deg": _number(math.degrees(heading_error)),
        "road_faces": _direction(heading_error, "aligned"),
        "preview_columns": list(PREVIEW_COLUMNS),
        "preview": rows,
        "bends": bends,
        "bend_sampling": {
            "horizon_road_m": BEND_HORIZON_M,
            "max_step_m": BEND_SAMPLE_MAX_STEP_M,
            "includes_all_source_vertices": True,
            "straight_threshold_rad_per_m": BEND_CURVATURE_THRESHOLD_RAD_PER_M,
            "total_regions": bend_count,
            "shown_limit": BEND_SUMMARY_LIMIT,
        },
    }


def _kart_physics(result: dict, observation: dict) -> None:
    """Add pose and nominal bicycle geometry; no driving policy is computed."""
    kart, track, handling = observation["kart"], observation["track"], result["handling"]
    wheelbase, max_angle = float(handling["wheelbase"]), float(handling["max_steering_angle"])
    if not math.isfinite(wheelbase) or wheelbase <= 0:
        raise ValueError("Wheelbase must be a finite positive distance")
    if not math.isfinite(max_angle) or not 0 <= max_angle < math.pi / 2:
        raise ValueError("Maximum steering angle must be finite and between zero and pi/2 radians")
    nose_angle = _wrap(-float(track["heading_error"]))
    road_heading = float(kart["heading"]) + float(track["heading_error"])
    velocity_angle = (
        _wrap(math.atan2(kart["vy"], kart["vx"]) - road_heading)
        if math.hypot(kart["vx"], kart["vy"]) >= STATIONARY_SPEED_MPS
        else None
    )
    result["current_alignment"] = {
        "metres_from_centre": _number(abs(track["offset"])),
        "side_of_centre": _direction(track["offset"], "centre"),
        "nose_vs_road_deg": _number(math.degrees(nose_angle)),
        "nose_points": _direction(nose_angle, "along road"),
        "velocity_vs_road_deg": _number(math.degrees(velocity_angle)) if velocity_angle is not None else None,
        "velocity_points": _direction(velocity_angle, "along road")
        if velocity_angle is not None
        else "stationary",
        "wheel_angle_deg": result["kart"]["steering_deg"],
        "wheel_points": result["kart"]["steering_direction"],
        "yaw_deg_s": result["kart"]["yaw_deg_s"],
        "yaw_direction": result["kart"]["yaw_direction"],
    }

    def nominal(wheel_angle):
        curvature = math.tan(wheel_angle) / wheelbase
        return [
            _number(math.degrees(wheel_angle)),
            _number(curvature, 6),
            _number(1 / abs(curvature)) if abs(curvature) > ZERO_EPSILON else None,
        ]

    result["steering_geometry"] = {
        "columns": [
            "normalized_setting",
            "wheel_angle_deg",
            "nominal_signed_curvature_rad_m",
            "nominal_radius_m",
        ],
        "rows": [[setting, *nominal(setting * max_angle)] for setting in STEERING_SETTINGS],
    }
    _, wheel_curvature, wheel_radius = nominal(float(kart["steering_angle"]))
    current_road = next(
        (point for point in track["lookahead"] if abs(float(point["distance"])) <= ZERO_EPSILON), None
    )
    if current_road is None:
        raise ValueError("Kart physics telemetry requires the zero-distance road preview")
    road_curvature = float(current_road["curvature"])
    speed = float(kart["speed"])
    result["physics"].update(
        {
            "current_wheel_nominal_curvature_rad_m": wheel_curvature,
            "current_wheel_nominal_radius_m": wheel_radius,
            "current_road_curvature_rad_m": road_curvature,
            "current_road_radius_m": _number(1 / abs(road_curvature))
            if abs(road_curvature) > ZERO_EPSILON
            else None,
            "current_yaw_curvature_rad_m": _number(float(kart["yaw_rate"]) / speed, 6)
            if speed >= STATIONARY_SPEED_MPS
            else None,
        }
    )
    result["units"] += (
        " Current_alignment describes KART nose/velocity relative to CURRENT ROAD; positive means left "
        "of road. Nominal steering curvature=tan(wheel angle)/wheelbase; positive is left, radius unsigned. "
        "Steering geometry excludes grip and response delays. Current yaw curvature=body yaw_rate/speed, "
        "not velocity-heading rate. Velocity angle/yaw curvature are null at effectively zero speed."
    )


def _compact_report(state: dict) -> str:
    """Render precisely the compact numeric facts, without duplicating their JSON."""
    pose, physics, path = state["present"], state["physics"], state["local_path"]

    def display(value):
        if value is None:
            return "null"
        return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)

    def angle(value):
        return "stationary (angle null)" if value is None else f"{display(value['deg'])}deg {value['side']}"

    def quantity(value, unit):
        return "null" if value is None else f"{display(value)}{unit}"

    def radius(value):
        return "radius null" if value is None else f"R{display(value)}m"

    local = "; ".join(
        f"arc {display(arc)}m: bearing {quantity(bearing, 'deg')}, range {display(distance)}m"
        for arc, bearing, distance in path["points"]
    )
    bends = (
        "; ".join(
            f"{bend['direction']} arc {display(bend['from_arc_m'])}–{display(bend['to_arc_m'])}m, "
            f"turn {display(bend['turn_deg'])}deg, tightest R{display(bend['min_radius_m'])}m "
            f"at arc {display(bend['peak_arc_m'])}m (arc/speed {quantity(bend['peak_seconds_at_current_speed'], 's')}), "
            f"peak need {display(bend['peak_need_m_s2'])}m/s², grip ratio {display(bend['peak_grip_ratio'])}"
            for bend in state["future_bends"]
        )
        or "none"
    )
    sampling = state["bend_sampling"]
    return (
        f"PRESENT: speed {display(pose['speed_m_s'])}m/s; kart {display(pose['offset']['m'])}m "
        f"{pose['offset']['side']} of centre; edge clearances left {display(pose['edges']['left_m'])}m, "
        f"right {display(pose['edges']['right_m'])}m. Nose versus CURRENT road: {angle(pose['nose_vs_road'])}; "
        f"velocity versus road: {angle(pose['velocity_vs_road'])}, road-lateral "
        f"{display(pose['road_lateral_m_s'])}m/s ({pose['road_lateral_side']}). "
        f"Wheel {display(pose['wheel_deg'])}deg; yaw {display(pose['yaw_deg_s'])}deg/s. "
        f"CURRENT PHYSICS: surface {physics['surface']}, grip {display(physics['grip_m_s2'])}m/s², "
        f"grip-limited radius {display(physics['grip_min_radius_m'])}m; "
        f"road curvature {display(physics['road_curve_rad_m'])}rad/m, {radius(physics['road_radius_m'])}; "
        f"nominal wheel curvature {display(physics['wheel_curve_rad_m'])}rad/m, {radius(physics['wheel_radius_m'])}; "
        f"body yaw/speed curvature {quantity(physics['yaw_curve_rad_m'], 'rad/m')}. "
        f"LOCAL PATH (arc from road projection; bearing from kart nose): {local}. "
        f"FUTURE ROAD GEOMETRY, independent of kart heading: {bends}. "
        f"Dense bend horizon {display(sampling['horizon_arc_m'])}m; max step {display(sampling['max_step_m'])}m "
        f"plus every source vertex; straight |curvature|≤{display(sampling['straight_rad_m'])}rad/m; "
        f"showing nearest {display(sampling['shown'])} of {display(sampling['regions'])} regions."
    )


def _compact(observation: dict, config: dict, *, text: bool) -> dict:
    rich = represent(observation, config, "kart_physics")
    alignment, road, physics = rich["current_alignment"], rich["road"], rich["physics"]
    kart, track = observation["kart"], observation["track"]
    road_heading = float(kart["heading"]) + float(track["heading_error"])
    lateral_velocity = -kart["vx"] * math.sin(road_heading) + kart["vy"] * math.cos(road_heading)

    def angle(degrees, side):
        return {"deg": _number(abs(degrees)), "side": side} if degrees is not None else None

    state = copy.deepcopy(
        {
            key: observation[key]
            for key in ("tick", "time", "progress", "rescue", "control")
            if key in observation
        }
    )
    state["units"] = COMPACT_UNITS
    state["present"] = {
        "speed_m_s": kart["speed"],
        "offset": {"m": alignment["metres_from_centre"], "side": alignment["side_of_centre"]},
        "edges": {"left_m": road["left_edge_clearance_m"], "right_m": road["right_edge_clearance_m"]},
        "nose_vs_road": angle(alignment["nose_vs_road_deg"], alignment["nose_points"]),
        "velocity_vs_road": angle(alignment["velocity_vs_road_deg"], alignment["velocity_points"]),
        "road_lateral_m_s": _number(lateral_velocity, 4),
        "road_lateral_side": _direction(lateral_velocity, "none"),
        "wheel_deg": rich["kart"]["steering_deg"],
        "yaw_deg_s": rich["kart"]["yaw_deg_s"],
    }
    state["physics"] = {
        "surface": physics["current_surface"],
        "grip_m_s2": physics["current_lateral_grip_mps2"],
        "grip_min_radius_m": physics["grip_limited_minimum_steady_turn_radius_m"],
        "road_curve_rad_m": physics["current_road_curvature_rad_m"],
        "road_radius_m": physics["current_road_radius_m"],
        "wheel_curve_rad_m": physics["current_wheel_nominal_curvature_rad_m"],
        "wheel_radius_m": physics["current_wheel_nominal_radius_m"],
        "yaw_curve_rad_m": physics["current_yaw_curvature_rad_m"],
    }
    path = []
    for point in track["lookahead"]:
        if point["distance"] not in COMPACT_PATH_ARCS_M:
            continue
        distance = math.hypot(point["x"], point["y"])
        bearing = (
            _number(math.degrees(math.atan2(point["y"], point["x"]))) if distance > ZERO_EPSILON else None
        )
        path.append([point["distance"], bearing, _number(distance)])
    state["local_path"] = {"columns": ["arc_m", "bearing_from_nose_deg", "range_m"], "points": path}
    speed = float(kart["speed"])
    state["future_bends"] = [
        {
            "direction": bend["direction"],
            "from_arc_m": bend["starts_in_road_m"],
            "to_arc_m": bend["ends_in_road_m"],
            "peak_arc_m": bend["tightest_in_road_m"],
            "min_radius_m": bend["tightest_radius_m"],
            "turn_deg": bend["heading_change_deg"],
            "peak_need_m_s2": bend[PHYSICS_COLUMNS[0]],
            "peak_grip_ratio": bend[PHYSICS_COLUMNS[1]],
            "peak_seconds_at_current_speed": _number(bend["tightest_in_road_m"] / speed)
            if speed >= STATIONARY_SPEED_MPS
            else None,
        }
        for bend in road["bends"][:2]
    ]
    sampling = road["bend_sampling"]
    state["bend_sampling"] = {
        "horizon_arc_m": sampling["horizon_road_m"],
        "max_step_m": sampling["max_step_m"],
        "straight_rad_m": sampling["straight_threshold_rad_per_m"],
        "shown": len(state["future_bends"]),
        "regions": sampling["total_regions"],
    }
    handling = observation.get("handling", config["handling"])
    state["handling"] = {
        target: handling[source]
        for source, target in (
            ("max_speed", "max_speed_m_s"),
            ("acceleration", "accel_m_s2"),
            ("braking", "brake_m_s2"),
            ("wheelbase", "wheelbase_m"),
            ("steering_response", "steer_response_s"),
            ("yaw_response", "yaw_response_s"),
            ("lateral_grip", "road_grip_m_s2"),
            ("grass_grip", "grass_grip_m_s2"),
            ("grass_acceleration", "grass_accel_m_s2"),
        )
        if source in handling
    }
    state["handling"]["max_wheel_deg"] = _number(math.degrees(handling["max_steering_angle"]))
    if "next_checkpoint" in rich:
        state["next_checkpoint"] = rich["next_checkpoint"]
    if text:
        report = _compact_report(state)
        for key in ("present", "physics", "local_path", "future_bends", "bend_sampling"):
            del state[key]
        state["road_report"] = report
    return state


def _road_report(road: dict) -> str:
    side = road["kart_side"]
    offset = f"{abs(road['offset_m']):g}m {side} of centre" if side != "centre" else "on centre"
    alignment = (
        f"{abs(road['road_vs_kart_deg']):g}deg {road['road_faces']} of kart"
        if road["road_faces"] != "aligned"
        else "aligned with kart"
    )
    preview = []
    for ahead, x, y, turn, bend, radius in road["preview"]:
        local_bend = "straight" if radius is None else f"{bend}, radius {radius:g}m"
        preview.append(f"{ahead:g}m: ego({x:g},{y:g})m; road turn {turn:+g}deg; {local_bend}")
    bends = [
        f"{bend['direction']} from {bend['starts_in_road_m']:g} to {bend['ends_in_road_m']:g}m, "
        f"tightest radius {bend['tightest_radius_m']:g}m at {bend['tightest_in_road_m']:g}m, "
        f"heading change {bend['heading_change_deg']:+g}deg"
        for bend in road["bends"]
    ]
    sampling = road["bend_sampling"]
    return (
        f"Road width {road['width_m']:g}m. Kart {offset}; "
        f"left edge clearance {road['left_edge_clearance_m']:g}m, "
        f"right {road['right_edge_clearance_m']:g}m; "
        f"{'on road' if road['on_road'] else 'off road'}. Road tangent {alignment}. "
        "Preview (distance along centreline; ego x forward/y left; tangent change from current ROAD): "
        + "; ".join(preview)
        + f". Dense bends over {sampling['horizon_road_m']:g}m arc from nearest projection "
        + f"(<= {sampling['max_step_m']:g}m sampling plus source vertices; "
        + f"straight |curvature| <= {sampling['straight_threshold_rad_per_m']:g}rad/m; "
        + f"showing first {len(bends)} of {sampling['total_regions']}): "
        + ("; ".join(bends) if bends else "none")
        + "."
    )


def _road_compass(observation: dict, config: dict) -> dict:
    """Describe where the road is from the kart, without proposing an input."""
    state = represent(observation, config, "compact_inputs")
    kart, track = observation["kart"], observation["track"]

    def word(degrees):
        return "LEFT" if degrees > ZERO_EPSILON else "RIGHT" if degrees < -ZERO_EPSILON else "AHEAD"

    def point_values(point):
        distance = math.hypot(point["x"], point["y"])
        bearing = math.degrees(math.atan2(point["y"], point["x"])) if distance > ZERO_EPSILON else None
        return [
            point["distance"],
            _number(point["x"]),
            _number(point["y"]),
            _number(distance),
            _number(bearing) if bearing is not None else None,
            word(bearing) if bearing is not None else None,
        ]

    points = [point_values(point) for point in track["lookahead"] if point["distance"] in COMPACT_PATH_ARCS_M]
    current = next((point for point in points if abs(float(point[0])) <= ZERO_EPSILON), None)
    if current is None:
        raise ValueError("Road compass requires the zero-distance centreline point")
    heading = float(kart["heading"])
    cosine, sine = math.cos(heading), math.sin(heading)
    old_pose = state.pop("present")
    state["kart"] = {
        "speed_m_s": kart["speed"],
        "velocity_forward_m_s": _number(kart["vx"] * cosine + kart["vy"] * sine, 4),
        "velocity_left_m_s": _number(-kart["vx"] * sine + kart["vy"] * cosine, 4),
        "wheel_deg": old_pose["wheel_deg"],
        "yaw_deg_s": old_pose["yaw_deg_s"],
    }
    tangent = math.degrees(float(track["heading_error"]))
    state["road_here"] = {
        "centre": dict(zip(("ego_x_m", "ego_y_m", "range_m", "bearing_deg", "direction"), current[1:])),
        "forward_tangent": {"deg": _number(abs(tangent)), "direction": word(tangent)},
        "edge_clearance_m": {
            "road_left": old_pose["edges"]["left_m"],
            "road_right": old_pose["edges"]["right_m"],
        },
    }
    state["local_path"] = {
        "columns": ["arc_m", "ego_x_m", "ego_y_m", "range_m", "bearing_deg", "direction"],
        "points": points,
    }
    bends = [bend for bend in state["future_bends"] if bend["from_arc_m"] <= 22][:2]
    for bend in bends:
        bend["end_beyond_window"] = bend["to_arc_m"] > 22
        bend["peak_beyond_window"] = bend["peak_arc_m"] > 22
    state["future_bends"] = bends
    source_sampling = state.pop("bend_sampling")
    state["bend_window"] = {
        "starts_within_arc_m": 22,
        "max_step_m": source_sampling["max_step_m"],
        "straight_rad_m": source_sampling["straight_rad_m"],
    }
    state["units"] = (
        "m,s,deg; signed angles/yaw/curvature and ego lateral velocity positive LEFT. Ego x forward,y left. "
        "ROAD centre/tangent are relative to KART, not steering commands. Edges use road frame; negative=outside. "
        "Bends start within22m projection arc; flagged ends/peaks can extend beyond. "
        "Need=v²/r; ratio>1 exceeds current grip; seconds=arc/speed. "
        "Nominal wheel/grip radii exclude response delays. held_input is the held absolute normalized wheel target and pedals."
    )
    return state


def _next_gate(observation: dict, config: dict) -> dict:
    """Finite gate geometry in two separate frames: kart view and gate plane."""
    index = observation.get("progress", {}).get("checkpoint")
    checkpoints = config.get("track", {}).get("checkpoints", ())
    gate = checkpoints[index] if isinstance(index, int) and 0 <= index < len(checkpoints) else None
    if gate is None:
        candidate = observation.get("next_checkpoint")
        if isinstance(candidate, dict) and all(key in candidate for key in ("x", "y", "forward_heading")):
            gate = {"x": candidate["x"], "y": candidate["y"], "heading": candidate["forward_heading"]}
    if gate is None:
        return {"known": False, "index": index, "reason": "next gate geometry unavailable"}
    kart = observation["kart"]
    gate_heading = float(gate["heading"])
    gate_dx, gate_dy = float(gate["x"]) - kart["x"], float(gate["y"]) - kart["y"]
    cosine, sine = math.cos(kart["heading"]), math.sin(kart["heading"])
    ego_x, ego_y = gate_dx * cosine + gate_dy * sine, -gate_dx * sine + gate_dy * cosine
    distance = math.hypot(gate_dx, gate_dy)
    forward_x, forward_y = math.cos(gate_heading), math.sin(gate_heading)
    plane = -gate_dx * forward_x - gate_dy * forward_y
    lateral = gate_dx * forward_y - gate_dy * forward_x
    width = float(config.get("track", {}).get("width", observation["track"]["width"]))
    return {
        "known": True,
        "index": index,
        "centre_ego_m": [_number(ego_x), _number(ego_y)],
        "range_m": _number(distance),
        "bearing_to_centre_deg": _number(math.degrees(math.atan2(ego_y, ego_x)))
        if distance > ZERO_EPSILON
        else None,
        "forward_heading_vs_kart_deg": _number(math.degrees(_wrap(gate_heading - kart["heading"]))),
        "behind_kart_nose": ego_x < 0,
        "signed_plane_m": _number(plane, 4),
        "signed_lateral_m": _number(lateral, 4),
        "gate_forward_velocity_m_s": _number(kart["vx"] * forward_x + kart["vy"] * forward_y, 4),
        "half_width_m": width / 2,
        "within_span_now": abs(lateral) <= width / 2,
        "crossing_rule": (
            "Next gate only: step crosses plane<=0 to>0 and interpolated |lateral|<=half_width. "
            "Plane positive=gate forward side; lateral positive=gate left. Bearing points to centre; forward heading orients gate. "
            "Within_span_now is not credit. Uncredited gate remains required; reverse crossings and rescue give no credit."
        ),
    }


def _navigation(observation: dict, config: dict, variant: str, context: dict | None) -> dict:
    compact = variant == "compact_navigation"
    state = represent(observation, config, "compact" if compact else "road_physics")
    state.pop("next_checkpoint", None)
    state["next_gate"] = _next_gate(observation, config)
    if compact:
        state["units"] += (
            " present.offset.m and pose angles paired with side are MAGNITUDES; side gives direction. "
            "Wheel/yaw, road-lateral velocity, curvature, local bearings and gate frame coordinates stay SIGNED."
        )
    else:
        state["units"] = NAVIGATION_UNITS
    if variant == "road_history":
        context = context or {}
        recent, clock = context.get("recent_motion"), context.get("checkpoint_clock")
        recent = copy.deepcopy(recent) if isinstance(recent, dict) and recent else None
        clock = copy.deepcopy(clock) if isinstance(clock, dict) and clock else None
        state["history"] = {
            "recent_motion": recent,
            "checkpoint_clock": clock,
            "status": "available"
            if recent is not None and clock is not None
            else "partial"
            if recent is not None or clock is not None
            else "not_known",
        }
        state["units"] += (
            " History offset/nose_vs_road/velocity_vs_road/road_lateral positive=road LEFT; "
            "nose sign opposes road_vs_kart. Null history=not known."
        )
    return state


def represent(observation: dict, config: dict, variant: str = "road", *, context: dict | None = None) -> dict:
    """Return an independent JSON-serializable presentation without mutating inputs.

    ``config.track.points`` are the published centreline polyline. Geometry-only
    variants do not derive capability, speed targets, or recommended controls.
    ``road_physics`` additionally reports speed² × |curvature| and its ratio to
    the *current surface's* grip, without accounting for future surface changes,
    steering limits, or transient vehicle response.
    """
    if variant not in VARIANTS:
        raise ValueError(f"Unknown telemetry variant: {variant}")
    if variant == "raw":
        return copy.deepcopy(observation)
    if variant in {"road_navigation", "compact_navigation", "road_history"}:
        return _navigation(observation, config, variant, context)
    if variant == "road_compass":
        return _road_compass(observation, config)
    if variant in {"compact", "compact_text", "compact_inputs"}:
        compact = _compact(observation, config, text=variant == "compact_text")
        if variant == "compact_inputs":
            action = config.get("actions", {}).get(observation.get("control"))
            if not isinstance(action, dict) or any(
                key not in action for key in ("steer", "throttle", "brake")
            ):
                raise ValueError(
                    "Held input requires the current control's physical config.actions definition"
                )
            del compact["control"]
            compact["held_input"] = {key: action[key] for key in ("steer", "throttle", "brake")}
            compact["units"] += (
                " held_input describes held controls, not a next choice; "
                "steer is the absolute normalized target wheel setting."
            )
        return compact
    result = copy.deepcopy(
        {k: v for k, v in observation.items() if k not in {"kart", "track", "next_checkpoint", "units"}}
    )
    result["units"] = UNITS
    result.setdefault("handling", copy.deepcopy(config["handling"]))
    kart = observation["kart"]
    heading = float(kart["heading"])
    cosine, sine = math.cos(heading), math.sin(heading)
    result["kart"] = {
        "speed_m_s": kart["speed"],
        "velocity_forward_m_s": _number(kart["vx"] * cosine + kart["vy"] * sine, 4),
        "velocity_left_m_s": _number(-kart["vx"] * sine + kart["vy"] * cosine, 4),
        "yaw_deg_s": _number(math.degrees(kart["yaw_rate"])),
        "yaw_direction": _direction(kart["yaw_rate"]),
        "steering_deg": _number(math.degrees(kart["steering_angle"])),
        "steering_direction": _direction(kart["steering_angle"]),
    }
    checkpoint = observation.get("next_checkpoint")
    if checkpoint is not None:
        result["next_checkpoint"] = {
            "ego_x_m": checkpoint["ego_x"],
            "ego_y_m": checkpoint["ego_y"],
            "forward_vs_kart_deg": _number(math.degrees(_wrap(checkpoint["forward_heading"] - heading))),
        }
    road = _road(observation, config)
    if variant in {"road_physics", "kart_physics"}:
        handling = result["handling"]
        grip = float(handling["lateral_grip"] if road["on_road"] else handling["grass_grip"])
        if not math.isfinite(grip) or grip <= 0:
            raise ValueError("Current surface grip must be a finite positive acceleration")
        speed_squared = float(kart["speed"]) ** 2
        road["preview_columns"].extend(PHYSICS_COLUMNS)
        for row, point in zip(road["preview"], observation["track"]["lookahead"]):
            acceleration = speed_squared * abs(float(point["curvature"]))
            row.extend([_number(acceleration), _number(acceleration / grip, 4)])
        for bend in road["bends"]:
            acceleration = speed_squared / bend["tightest_radius_m"]
            bend[PHYSICS_COLUMNS[0]] = _number(acceleration)
            bend[PHYSICS_COLUMNS[1]] = _number(acceleration / grip, 4)
        result["physics"] = {
            "current_surface": "road" if road["on_road"] else "grass",
            "current_lateral_grip_mps2": grip,
            "grip_limited_minimum_steady_turn_radius_m": _number(speed_squared / grip),
        }
        result["units"] += (
            " Physics preview acceleration is speed²×|curvature| in m/s²; grip usage >1 means it exceeds "
            "current surface grip. Grip-limited radius excludes steering limits and transient response."
        )
        if variant == "kart_physics":
            _kart_physics(result, observation)
    if variant == "road_text":
        result["road_report"] = _road_report(road)
    else:
        result["road"] = road
    return result
