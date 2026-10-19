//! Deterministic port of `mcpkart.sim` using Python-exported geometry and starts.
//!
//! Track generation and seeded initial poses intentionally remain in Python for
//! this spike. Only stepping and state ownership move into the Rust worker.

use serde::Deserialize;
use serde_json::{json, Value};
use std::f64::consts::{PI, TAU};
use std::sync::Arc;

pub const DT: f64 = 1.0 / 60.0;

fn wrap(angle: f64) -> f64 {
    (angle + PI).rem_euclid(TAU) - PI
}

fn clamp(value: f64, lower: f64, upper: f64) -> f64 {
    value.max(lower).min(upper)
}

// Formatting uses ties-to-even and respects the original binary float, as does
// Python round(value, ndigits). Keep this presentation work off the clock thread.
fn rounded(value: f64, digits: usize) -> f64 {
    format!("{value:.digits$}").parse().unwrap()
}

#[derive(Clone, Deserialize)]
pub struct Handling {
    max_speed: f64,
    acceleration: f64,
    braking: f64,
    max_steering_angle: f64,
    wheelbase: f64,
    steering_response: f64,
    yaw_response: f64,
    lateral_grip: f64,
    rolling_drag: f64,
    aerodynamic_drag: f64,
    grass_acceleration: f64,
    grass_drag: f64,
    grass_grip: f64,
}

#[derive(Clone, Deserialize)]
pub struct Track {
    pub points: Vec<[f64; 2]>,
    pub segments: Vec<[f64; 7]>,
    pub lengths: Vec<f64>,
    pub length: f64,
    pub headings: Vec<f64>,
    pub curvatures: Vec<f64>,
    pub checkpoints: Vec<[f64; 4]>,
    pub width: f64,
}

impl Track {
    pub fn at(&self, distance: f64) -> (f64, f64, f64, f64) {
        let distance = distance.rem_euclid(self.length);
        let i = self
            .lengths
            .partition_point(|s| *s <= distance)
            .saturating_sub(1)
            .min(self.points.len() - 1);
        let [x, y, dx, dy, length, _, _] = self.segments[i];
        let t = (distance - self.lengths[i]) / length;
        let j = (i + 1) % self.points.len();
        let heading = self.headings[i] + wrap(self.headings[j] - self.headings[i]) * t;
        let curvature = self.curvatures[i] + (self.curvatures[j] - self.curvatures[i]) * t;
        (x + dx * t, y + dy * t, heading, curvature)
    }

    pub fn project(&self, x: f64, y: f64) -> (f64, f64, f64) {
        let mut best = f64::INFINITY;
        let mut nearest_s = 0.0;
        let mut offset = 0.0;
        for (i, &[ax, ay, dx, dy, length, tx, ty]) in self.segments.iter().enumerate() {
            let t = clamp(
                ((x - ax) * dx + (y - ay) * dy) / (length * length),
                0.0,
                1.0,
            );
            let ex = x - ax - dx * t;
            let ey = y - ay - dy * t;
            let squared = ex * ex + ey * ey;
            if squared < best {
                best = squared;
                nearest_s = self.lengths[i] + length * t;
                offset = squared.sqrt().copysign(tx * ey - ty * ex);
            }
        }
        (nearest_s.rem_euclid(self.length), offset, best.sqrt())
    }
}

#[derive(Deserialize)]
struct InitialState {
    seed: i64,
    laps: usize,
    reset_after_s: Option<f64>,
    x: f64,
    y: f64,
    heading: f64,
    vx: f64,
    vy: f64,
    steering: f64,
    yaw_rate: f64,
    tick: u64,
    elapsed: f64,
    finished: bool,
    action_id: String,
    next_checkpoint: usize,
    checkpoints_passed: usize,
    laps_completed: usize,
    lap_times: Vec<f64>,
    offroad_time: f64,
    distance_travelled: f64,
    max_speed_seen: f64,
    s: f64,
    offset: f64,
    departure_s: f64,
    offroad_elapsed: f64,
    last_reset_tick: Option<u64>,
    reset_events: Vec<Value>,
}

/// Immutable geometry/config are shared when handing a snapshot to the publisher.
#[derive(Clone)]
pub struct Simulation {
    pub track: Arc<Track>,
    handling: Arc<Handling>,
    config_value: Arc<Value>,
    pub seed: i64,
    pub laps: usize,
    pub reset_after_s: Option<f64>,
    pub x: f64,
    pub y: f64,
    pub heading: f64,
    pub vx: f64,
    pub vy: f64,
    pub steering: f64,
    pub yaw_rate: f64,
    pub tick: u64,
    pub elapsed: f64,
    pub finished: bool,
    pub action_id: String,
    pub next_checkpoint: usize,
    pub checkpoints_passed: usize,
    pub laps_completed: usize,
    pub lap_times: Vec<f64>,
    pub offroad_time: f64,
    pub distance_travelled: f64,
    pub max_speed_seen: f64,
    pub s: f64,
    pub offset: f64,
    pub departure_s: f64,
    pub offroad_elapsed: f64,
    pub last_reset_tick: Option<u64>,
    pub reset_events: Vec<Value>,
}

pub fn valid_action(action_id: &str) -> bool {
    action(action_id).is_some()
}

fn action(action_id: &str) -> Option<(f64, f64, f64)> {
    let (steering_name, pedal) = action_id.rsplit_once('_')?;
    let steer = match steering_name {
        "hard_right" => -1.0,
        "right" => -0.5,
        "straight" => 0.0,
        "left" => 0.5,
        "hard_left" => 1.0,
        _ => return None,
    };
    let (throttle, brake) = match pedal {
        "accelerate" => (1.0, 0.0),
        "coast" => (0.0, 0.0),
        "brake" => (0.0, 1.0),
        _ => return None,
    };
    Some((steer, throttle, brake))
}

impl Simulation {
    pub fn from_fixture(fixture: &Value) -> Result<Self, String> {
        let state_value = fixture
            .get("state")
            .or_else(|| fixture.get("initial_state"))
            .ok_or("fixture requires state or initial_state")?;
        let state: InitialState = serde_json::from_value(state_value.clone())
            .map_err(|e| format!("invalid initial state: {e}"))?;
        let track: Track = serde_json::from_value(fixture["track"].clone())
            .map_err(|e| format!("invalid track: {e}"))?;
        let handling: Handling = serde_json::from_value(fixture["handling"].clone())
            .map_err(|e| format!("invalid handling: {e}"))?;
        let config = fixture
            .get("config")
            .ok_or("fixture requires config")?
            .clone();
        let n = track.points.len();
        if n < 2
            || track.segments.len() != n
            || track.lengths.len() != n + 1
            || track.headings.len() != n
            || track.curvatures.len() != n
            || track.checkpoints.is_empty()
            || state.next_checkpoint >= track.checkpoints.len()
            || !track.length.is_finite()
            || track.length <= 0.0
            || state.laps < 1
        {
            return Err("inconsistent track or race geometry".to_string());
        }
        if let Some(after) = state.reset_after_s {
            if !after.is_finite() || after <= 0.0 {
                return Err("reset_after_s must be positive and finite, or null".to_string());
            }
        }
        if !valid_action(&state.action_id) {
            return Err(format!("unknown action: {}", state.action_id));
        }
        Ok(Self {
            track: Arc::new(track),
            handling: Arc::new(handling),
            config_value: Arc::new(config),
            seed: state.seed,
            laps: state.laps,
            reset_after_s: state.reset_after_s,
            x: state.x,
            y: state.y,
            heading: state.heading,
            vx: state.vx,
            vy: state.vy,
            steering: state.steering,
            yaw_rate: state.yaw_rate,
            tick: state.tick,
            elapsed: state.elapsed,
            finished: state.finished,
            action_id: state.action_id,
            next_checkpoint: state.next_checkpoint,
            checkpoints_passed: state.checkpoints_passed,
            laps_completed: state.laps_completed,
            lap_times: state.lap_times,
            offroad_time: state.offroad_time,
            distance_travelled: state.distance_travelled,
            max_speed_seen: state.max_speed_seen,
            s: state.s,
            offset: state.offset,
            departure_s: state.departure_s,
            offroad_elapsed: state.offroad_elapsed,
            last_reset_tick: state.last_reset_tick,
            reset_events: state.reset_events,
        })
    }

    pub fn speed(&self) -> f64 {
        self.vx.hypot(self.vy)
    }

    pub fn set_control(&mut self, action_id: &str) -> Result<(), String> {
        if !valid_action(action_id) {
            return Err(format!("unknown action: {action_id}"));
        }
        self.action_id.clear();
        self.action_id.push_str(action_id);
        Ok(())
    }

    fn check_progress(&mut self, old_x: f64, old_y: f64) {
        let [gx, gy, heading, _] = self.track.checkpoints[self.next_checkpoint];
        let tx = heading.cos();
        let ty = heading.sin();
        let before = (old_x - gx) * tx + (old_y - gy) * ty;
        let after = (self.x - gx) * tx + (self.y - gy) * ty;
        if !(before <= 0.0 && after > 0.0) {
            return;
        }
        let fraction = -before / (after - before);
        let cross_x = old_x + (self.x - old_x) * fraction;
        let cross_y = old_y + (self.y - old_y) * fraction;
        let lateral = -(cross_x - gx) * ty + (cross_y - gy) * tx;
        if lateral.abs() > self.track.width / 2.0 {
            return;
        }
        self.checkpoints_passed += 1;
        self.next_checkpoint = (self.next_checkpoint + 1) % self.track.checkpoints.len();
        if self
            .checkpoints_passed
            .is_multiple_of(self.track.checkpoints.len())
        {
            self.laps_completed += 1;
            self.lap_times
                .push(self.elapsed - self.lap_times.iter().sum::<f64>());
            self.finished = self.laps_completed == self.laps;
        }
    }

    pub fn step(&mut self, dt: f64) -> Result<(), String> {
        if dt <= 0.0 || dt > DT * 1.000001 {
            return Err("physics step must be positive and no larger than DT".to_string());
        }
        if self.finished {
            return Ok(());
        }
        let (old_x, old_y, old_s) = (self.x, self.y, self.s);
        let (steer, throttle, brake) = action(&self.action_id).unwrap();
        let h = &self.handling;
        let onroad = self.offset.abs() <= self.track.width / 2.0;
        if !onroad {
            self.offroad_time += dt;
            self.offroad_elapsed += dt;
        } else {
            self.offroad_elapsed = 0.0;
        }
        self.steering += (steer * h.max_steering_angle - self.steering)
            * (1.0 - (-dt / h.steering_response).exp());
        let speed = self.speed();
        let forward_speed = (self.vx * self.heading.cos() + self.vy * self.heading.sin()).max(0.0);
        let grip = if onroad { h.lateral_grip } else { h.grass_grip };
        let desired_yaw = forward_speed / h.wheelbase * self.steering.tan();
        let max_yaw = grip / speed.max(2.0);
        let desired_yaw = clamp(desired_yaw, -max_yaw, max_yaw);
        self.yaw_rate += (desired_yaw - self.yaw_rate) * (1.0 - (-dt / h.yaw_response).exp());
        self.heading = wrap(self.heading + self.yaw_rate * dt);
        let fx = self.heading.cos();
        let fy = self.heading.sin();
        let lateral = -self.vx * fy + self.vy * fx;
        let lateral_change = clamp(-lateral, -grip * dt, grip * dt);
        self.vx -= fy * lateral_change;
        self.vy += fx * lateral_change;
        let speed = self.speed();
        let mut drag = h.rolling_drag + h.aerodynamic_drag * speed * speed;
        if !onroad {
            drag += h.grass_drag * speed;
        }
        let mut acceleration = if onroad {
            h.acceleration
        } else {
            h.grass_acceleration
        } * throttle;
        acceleration -= h.braking * brake + drag;
        if acceleration < 0.0 {
            let reduction = if speed != 0.0 {
                (speed + acceleration * dt).max(0.0) / speed
            } else {
                0.0
            };
            self.vx *= reduction;
            self.vy *= reduction;
        } else {
            self.vx += fx * acceleration * dt;
            self.vy += fy * acceleration * dt;
        }
        let speed = self.speed();
        if speed > h.max_speed {
            self.vx *= h.max_speed / speed;
            self.vy *= h.max_speed / speed;
        }
        self.x += self.vx * dt;
        self.y += self.vy * dt;
        self.tick += 1;
        self.elapsed += dt;
        self.distance_travelled += (self.x - old_x).hypot(self.y - old_y);
        self.max_speed_seen = self.max_speed_seen.max(self.speed());
        (self.s, self.offset, _) = self.track.project(self.x, self.y);
        self.check_progress(old_x, old_y);
        if self.offset.abs() <= self.track.width / 2.0 {
            self.offroad_elapsed = 0.0;
        } else if onroad {
            self.departure_s = old_s;
        }
        if !self.finished
            && self.offset.abs() > self.track.width / 2.0
            && self
                .reset_after_s
                .is_some_and(|after| self.offroad_elapsed + 1e-9 >= after)
        {
            self.rescue();
        }
        Ok(())
    }

    fn rescue(&mut self) {
        let respawn_s = (self.departure_s - 1.0).rem_euclid(self.track.length);
        (self.x, self.y, self.heading, _) = self.track.at(respawn_s);
        self.heading = wrap(self.heading);
        self.vx = 0.0;
        self.vy = 0.0;
        self.yaw_rate = 0.0;
        self.steering = 0.0;
        let previous_action = self.action_id.clone();
        self.action_id.clear();
        self.action_id.push_str("straight_coast");
        (self.s, self.offset, _) = self.track.project(self.x, self.y);
        self.last_reset_tick = Some(self.tick);
        self.reset_events.push(json!({
            "tick": self.tick, "time": self.elapsed,
            "departure_s": self.departure_s, "respawn_s": respawn_s,
            "x": self.x, "y": self.y, "heading": self.heading,
            "offroad_elapsed": self.offroad_elapsed,
            "previous_action": previous_action, "control": self.action_id,
        }));
        self.offroad_elapsed = 0.0;
    }

    pub fn observation(&self) -> Value {
        let (_, _, track_heading, _) = self.track.at(self.s);
        let fx = self.heading.cos();
        let fy = self.heading.sin();
        let lookahead: Vec<Value> = [0, 3, 6, 10, 15, 22, 32, 45, 60]
            .iter()
            .map(|&distance| {
                let (x, y, _, curvature) = self.track.at(self.s + distance as f64);
                let dx = x - self.x;
                let dy = y - self.y;
                json!({"distance": distance, "x": rounded(dx * fx + dy * fy, 3),
                "y": rounded(-dx * fy + dy * fx, 3), "curvature": rounded(curvature, 5)})
            })
            .collect();
        json!({"tick": self.tick, "time": rounded(self.elapsed, 4),
            "kart": {"x": rounded(self.x, 4), "y": rounded(self.y, 4),
                "heading": rounded(self.heading, 5), "speed": rounded(self.speed(), 4),
                "vx": rounded(self.vx, 4), "vy": rounded(self.vy, 4),
                "yaw_rate": rounded(self.yaw_rate, 5), "steering_angle": rounded(self.steering, 5)},
            "track": {"width": self.track.width, "offset": rounded(self.offset, 4),
                "heading_error": rounded(wrap(track_heading - self.heading), 5),
                "on_road": self.offset.abs() <= self.track.width / 2.0, "lookahead": lookahead},
            "progress": {"lap": (self.laps_completed + 1).min(self.laps),
                "laps_completed": self.laps_completed, "laps": self.laps,
                "checkpoint": self.next_checkpoint, "checkpoints_passed": self.checkpoints_passed,
                "checkpoints_per_lap": self.track.checkpoints.len(), "resets": self.reset_events.len(),
                "track_distance": rounded(self.s, 3), "finished": self.finished},
            "rescue": {"after_s": self.reset_after_s, "offroad_elapsed": rounded(self.offroad_elapsed, 4),
                "count": self.reset_events.len(), "last_reset_tick": self.last_reset_tick},
            "control": self.action_id})
    }

    pub fn summary(&self) -> Value {
        json!({"seed": self.seed, "finished": self.finished, "elapsed": self.elapsed,
            "ticks": self.tick, "laps_completed": self.laps_completed,
            "checkpoints_passed": self.checkpoints_passed, "lap_times": self.lap_times,
            "offroad_time": self.offroad_time, "distance": self.distance_travelled,
            "max_speed": self.max_speed_seen, "resets": self.reset_events.len(),
            "reset_events": self.reset_events})
    }

    pub fn config(&self) -> Value {
        (*self.config_value).clone()
    }

    pub fn track_json(&self) -> Value {
        self.config_value["track"].clone()
    }

    pub fn raw_state(&self) -> Value {
        json!({"seed": self.seed, "laps": self.laps, "reset_after_s": self.reset_after_s,
            "x": self.x, "y": self.y, "heading": self.heading, "vx": self.vx, "vy": self.vy,
            "steering": self.steering, "yaw_rate": self.yaw_rate, "tick": self.tick,
            "elapsed": self.elapsed, "finished": self.finished, "action_id": self.action_id,
            "next_checkpoint": self.next_checkpoint, "checkpoints_passed": self.checkpoints_passed,
            "laps_completed": self.laps_completed, "lap_times": self.lap_times,
            "offroad_time": self.offroad_time, "distance_travelled": self.distance_travelled,
            "max_speed_seen": self.max_speed_seen, "s": self.s, "offset": self.offset,
            "departure_s": self.departure_s, "offroad_elapsed": self.offroad_elapsed,
            "last_reset_tick": self.last_reset_tick, "reset_events": self.reset_events})
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn only_the_fifteen_controls_are_valid() {
        let mut count = 0;
        for steering in ["hard_right", "right", "straight", "left", "hard_left"] {
            for pedal in ["accelerate", "coast", "brake"] {
                assert!(valid_action(&format!("{steering}_{pedal}")));
                count += 1;
            }
        }
        assert_eq!(count, 15);
        assert!(!valid_action("left"));
        assert!(!valid_action("straight_reverse"));
        assert!(!valid_action("soft_left_coast"));
    }

    #[test]
    fn wrap_and_presentation_match_python_edge_cases() {
        assert_eq!(wrap(PI), -PI);
        assert_eq!(wrap(-PI), -PI);
        assert_eq!(rounded(2.675, 2), 2.67);
        assert_eq!(rounded(1.125, 2), 1.12);
        assert_eq!(rounded(-1.125, 2), -1.12);
    }
}
