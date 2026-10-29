"""Physics and course validity, without model requests or network access."""

import math

import pytest

from mcpkart.sim import ACTIONS, DT, Simulation, scripted_action


def cross_gate(sim, gate, *, forward=True, lateral=0.0):
    """Move a short segment through a gate to isolate checkpoint accounting."""
    x, y, heading, _ = sim.track.checkpoints[gate]
    tx, ty = math.cos(heading), math.sin(heading)
    sign = 1 if forward else -1
    old_x, old_y = x-sign*tx-lateral*ty, y-sign*ty+lateral*tx
    sim.x, sim.y = x+sign*tx-lateral*ty, y+sign*ty+lateral*tx
    sim._check_progress(old_x, old_y)


def test_fifteen_direct_joint_actions():
    assert len(ACTIONS) == 15
    assert {a["steer"] for a in ACTIONS.values()} == {-1, -0.5, 0, 0.5, 1}
    assert {(a["throttle"], a["brake"]) for a in ACTIONS.values()} == {(0, 0), (1, 0), (0, 1)}
    sim = Simulation()
    with pytest.raises(ValueError):
        sim.set_control("follow_racing_line")
    sim.set_control("straight_accelerate")
    for _ in range(30):
        sim.step()
    assert sim.speed > 4
    assert sim.action_id == "straight_accelerate"
    assert sim.tick == 30
    assert sim.elapsed == pytest.approx(0.5)


def test_ordered_gates_reject_shortcuts_reverse_and_offroad_crossings():
    sim = Simulation(laps=1)
    cross_gate(sim, 2)  # Skipping the next gate earns nothing.
    assert sim.checkpoints_passed == 0
    cross_gate(sim, 1, forward=False)
    assert sim.checkpoints_passed == 0
    cross_gate(sim, 1, lateral=sim.track.width/2+0.5)
    assert sim.checkpoints_passed == 0
    cross_gate(sim, 0)  # The finish line is gated by the rest of the course.
    assert not sim.finished
    for index in list(range(1, 40)) + [0]:
        cross_gate(sim, index)
    assert sim.finished
    assert sim.checkpoints_passed == 40
    assert sim.laps_completed == 1


def test_grass_slows_motion_without_reset_or_steering_assistance():
    road, grass = Simulation(seed=0), Simulation(seed=0)
    for sim, offset in ((road, 0.0), (grass, 7.0)):
        x, y, heading, _ = sim.track.at(0)
        sim.x, sim.y = x-math.sin(heading)*offset, y+math.cos(heading)*offset
        sim.heading = heading
        sim.vx, sim.vy = math.cos(heading)*20, math.sin(heading)*20
        sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)
        sim.set_control("straight_coast")
        for _ in range(30):
            sim.step()
        assert sim.heading == heading
        assert sim.summary()["resets"] == 0
    assert grass.speed < road.speed*0.75
    assert grass.offroad_time == pytest.approx(0.5)
    assert grass.offset > grass.track.width/2


def test_replaying_actions_reproduces_every_state_exactly():
    original, replay = Simulation(seed=7), Simulation(seed=7)
    for _ in range(900):
        action = scripted_action(original.observation())
        original.set_control(action)
        replay.set_control(action)
        original.step()
        replay.step()
        assert original.observation() == replay.observation()
    assert original.summary() == replay.summary()
    assert original.config() == replay.config()
    assert Simulation(seed=8).observation() != Simulation(seed=7).observation()


def test_declared_start_pose_roundtrips_without_progress_or_runtime_assistance():
    pose = {"offset_m": -4.0, "heading_error_rad": math.radians(110)}
    sim = Simulation(seed=201, course="stadium", road_width=24, max_speed=12,
                     max_steering_angle=.12, start_pose=pose)
    pose["offset_m"] = 9  # The caller cannot change the recorded contract.
    assert sim.offset == pytest.approx(-4)
    assert sim.speed == sim.steering == sim.yaw_rate == 0
    assert sim.next_checkpoint == 1 and sim.checkpoints_passed == sim.tick == 0
    assert sim.action_id == "straight_coast" and not sim.reset_events
    target = next(p for p in sim.observation()["track"]["lookahead"] if p["distance"] == 15)
    assert target["x"] < 0
    replay = Simulation.from_config(sim.config(), seed=201)
    for _ in range(90):
        sim.set_control("hard_right_accelerate")
        replay.set_control("hard_right_accelerate")
        sim.step()
        replay.step()
        assert sim.observation() == replay.observation()
    assert sim.config() == replay.config()
    assert sim.config()["start_conditions"]["pose"]["offset_m"] == -4


@pytest.mark.parametrize("pose", [
    {}, {"offset_m": 0, "heading_error_rad": 0, "speed": 12},
    {"offset_m": 13, "heading_error_rad": 0},
    {"offset_m": 0, "heading_error_rad": math.pi+.01},
    {"offset_m": math.nan, "heading_error_rad": 0},
    {"offset_m": 0, "heading_error_rad": True},
    {"offset_m": "0", "heading_error_rad": 0},
])
def test_start_pose_rejects_invalid_or_outside_road_values(pose):
    with pytest.raises(ValueError, match="start_pose"):
        Simulation(course="stadium", road_width=24, start_pose=pose)


@pytest.mark.parametrize("seed", range(10))
def test_reference_completes_three_laps_and_uses_brakes(seed):
    sim = Simulation(seed=seed)
    brake_steps = 0
    for _ in range(60*65):
        action = scripted_action(sim.observation())
        brake_steps += action.endswith("_brake")
        sim.set_control(action)
        sim.step()
        if sim.finished:
            break
    assert sim.finished, sim.summary()
    assert 30 < sim.elapsed < 60
    assert sim.checkpoints_passed == 120
    assert sim.offroad_time == 0
    assert brake_steps > 30
    assert sim.max_speed_seen > 22


@pytest.mark.parametrize("delay_ticks", (6, 12))
def test_reference_handles_stale_observation_and_held_controls(delay_ticks):
    # Unlike merely running a lower update rate, each action here was computed
    # from an observation captured a full 100 or 200 ms before application.
    sim = Simulation(seed=0)
    due_tick, pending_action = delay_ticks, scripted_action(sim.observation())
    for _ in range(60*110):
        if sim.tick == due_tick:
            sim.set_control(pending_action)
            due_tick, pending_action = sim.tick+delay_ticks, scripted_action(sim.observation())
        sim.step()
        if sim.finished:
            break
    assert sim.finished, sim.summary()
    assert sim.summary()["resets"] == 0
    assert sim.elapsed < 100


def test_lookahead_coordinates_and_handling_are_explicit():
    sim = Simulation()
    observation = sim.observation()
    assert observation["tick"] == 0
    assert observation["progress"]["lap"] == 1
    assert len(observation["track"]["lookahead"]) == 9
    assert observation["track"]["lookahead"][3]["x"] > 0
    assert sim.config()["handling"]["lateral_grip"] > 0
    assert sim.config()["dt"] == DT
    with pytest.raises(ValueError):
        sim.step(DT*2)


def place_kart(sim, distance, lateral=0.0):
    """Place a stationary kart to isolate rescue state accounting."""
    x, y, heading, _ = sim.track.at(distance)
    sim.x, sim.y = x-math.sin(heading)*lateral, y+math.cos(heading)*lateral
    sim.heading = heading
    sim.vx = sim.vy = sim.yaw_rate = sim.steering = 0.0
    sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)


@pytest.mark.parametrize("threshold", (0, -1, math.inf, -math.inf, math.nan, True))
def test_rescue_threshold_must_be_positive_finite_or_disabled(threshold):
    with pytest.raises(ValueError):
        Simulation(reset_after_s=threshold)


def test_rescue_needs_continuous_offroad_time_and_preserves_cumulative_time():
    sim = Simulation(reset_after_s=0.2)
    place_kart(sim, 0, lateral=-8)
    for _ in range(6):
        sim.step()
    assert sim.offroad_elapsed == pytest.approx(0.1)
    place_kart(sim, 0)
    sim.step()
    assert sim.offroad_elapsed == 0
    place_kart(sim, 0, lateral=-8)
    for _ in range(11):
        sim.step()
    assert sim.summary()["resets"] == 0
    sim.step()
    assert sim.summary()["resets"] == 1
    assert sim.offroad_elapsed == 0
    assert sim.offroad_time == pytest.approx(0.3)
    assert sim.tick == 19
    assert sim.elapsed == pytest.approx(19*DT)


def test_default_rescue_has_visible_evidence_and_leaves_neutral_stationary_kart():
    sim = Simulation()
    place_kart(sim, 0, lateral=-8)
    sim.set_control("hard_left_brake")
    for _ in range(179):
        sim.step()
    assert sim.summary()["resets"] == 0
    sim.step()
    observation = sim.observation()
    event = sim.reset_events[0]
    assert observation["rescue"] == {
        "after_s": 3.0, "offroad_elapsed": 0.0, "count": 1, "last_reset_tick": 180,
    }
    assert observation["progress"]["resets"] == sim.summary()["resets"] == 1
    assert event["tick"] == sim.last_reset_tick == 180
    assert event["time"] == pytest.approx(3.0)
    assert event["offroad_elapsed"] == pytest.approx(3.0)
    assert event["previous_action"] == "hard_left_brake"
    assert event["respawn_s"] == pytest.approx((event["departure_s"]-1) % sim.track.length)
    assert sim.action_id == event["control"] == "straight_coast"
    assert sim.speed == sim.yaw_rate == sim.steering == 0
    assert abs(sim.offset) < 1e-8
    _, _, expected_heading, _ = sim.track.at(event["respawn_s"])
    assert math.remainder(sim.heading-expected_heading, math.tau) == pytest.approx(0)
    rescued_position = sim.x, sim.y
    for _ in range(60):
        sim.step()
    assert (sim.x, sim.y) == rescued_position
    assert sim.speed == 0  # No automatic throttle or steering after a reset.


def test_rescue_uses_departure_anchor_and_teleport_never_credits_a_gate():
    sim = Simulation(reset_after_s=3*DT)
    place_kart(sim, 18)
    sim.heading += math.pi/2
    sim.vx, sim.vy = math.cos(sim.heading)*10, math.sin(sim.heading)*10
    for _ in range(120):
        sim.step()
        if abs(sim.offset) > sim.track.width/2:
            break
    assert abs(sim.offset) > sim.track.width/2
    departure = sim.departure_s
    # Drift can carry a kart closer to another track section. The reset must
    # return to its original departure rather than award forward teleportation.
    sim.x = sim.y = 1000
    sim.vx = sim.vy = 0
    sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)
    previous_tick, previous_time = sim.tick, sim.elapsed
    previous_progress = sim.checkpoints_passed, sim.next_checkpoint, sim.laps_completed
    for _ in range(3):
        sim.step()
    assert sim.summary()["resets"] == 1
    assert sim.reset_events[0]["departure_s"] == departure
    assert (sim.checkpoints_passed, sim.next_checkpoint, sim.laps_completed) == previous_progress
    assert sim.tick == previous_tick+3
    assert sim.elapsed == pytest.approx(previous_time+3*DT)
    assert sim.distance_travelled < 20  # The long teleport is not driven distance.


def test_strict_mode_disables_rescue_without_hiding_offroad_evidence():
    sim = Simulation(reset_after_s=None)
    place_kart(sim, 0, lateral=-8)
    for _ in range(240):
        sim.step()
    assert sim.offroad_elapsed == pytest.approx(4.0)
    assert sim.offroad_time == pytest.approx(4.0)
    assert sim.summary()["resets"] == 0
    assert sim.reset_events == []
    assert sim.last_reset_tick is None
    assert sim.observation()["rescue"]["after_s"] is None
    assert sim.config()["rescue"]["after_s"] is None
    assert abs(sim.offset) > sim.track.width/2
    assert sim.config()["version"] == "solo-v2-rescue"
