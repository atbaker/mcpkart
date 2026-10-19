//! Clock ownership stays on one dedicated native thread (the process main thread).
//! NDJSON parsing and writing run on separate threads. The clock never serializes
//! JSON, writes a pipe, or waits for a snapshot lock or reply consumer.

use crate::sim::{self, Simulation, DT};
use serde_json::{json, Value};
use std::collections::VecDeque;
use std::io::{self, BufRead, BufWriter, Write};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    mpsc, Arc, Mutex,
};
use std::thread;
use std::time::Duration;

pub const CLOCK_MODE: &str = "rust_fixed_step_wall_clock";
const QUEUE_LIMIT: usize = 128;

fn clock_ns(clock: libc::clockid_t) -> u64 {
    let mut value = libc::timespec {
        tv_sec: 0,
        tv_nsec: 0,
    };
    // These clocks are supported on the macOS and Linux targets of this spike.
    let result = unsafe { libc::clock_gettime(clock, &mut value) };
    assert_eq!(result, 0, "clock_gettime failed");
    value.tv_sec as u64 * 1_000_000_000 + value.tv_nsec as u64
}

pub fn monotonic_ns() -> u64 {
    // CPython uses mach_absolute_time on macOS: CLOCK_UPTIME_RAW shares that
    // epoch and suspend behavior. CLOCK_MONOTONIC there includes sleep and is
    // not interchangeable with Python monotonic timestamps. Linux uses the
    // same CLOCK_MONOTONIC as CPython.
    #[cfg(target_os = "macos")]
    {
        clock_ns(libc::CLOCK_UPTIME_RAW)
    }
    #[cfg(not(target_os = "macos"))]
    {
        clock_ns(libc::CLOCK_MONOTONIC)
    }
}
fn process_ns() -> u64 {
    clock_ns(libc::CLOCK_PROCESS_CPUTIME_ID)
}
fn thread_ns() -> u64 {
    clock_ns(libc::CLOCK_THREAD_CPUTIME_ID)
}
fn rounded(value: f64, digits: usize) -> f64 {
    format!("{value:.digits$}").parse().unwrap()
}

#[derive(Clone)]
struct Command {
    race_id: String,
    action_id: String,
    observation_tick: u64,
    command_seq: u64,
    queued_ns: u64,
    applied_ns: Option<u64>,
    applied_tick: Option<u64>,
    reset_during_step: bool,
}
impl Command {
    fn value(&self) -> Value {
        let mut value = json!({"race_id":self.race_id,"action_id":self.action_id,
            "observation_tick":self.observation_tick,"command_seq":self.command_seq,"queued_ns":self.queued_ns});
        if let Some(applied_ns) = self.applied_ns {
            value["applied_ns"] = json!(applied_ns);
            value["applied_tick"] = json!(self.applied_tick);
            value["reset_during_step"] = json!(self.reset_during_step);
        }
        value
    }
}

struct Pending {
    identity: Value,
    command: Command,
}

#[derive(Clone)]
struct Rejected {
    command: Command,
    reason: String,
    rejected_ns: u64,
}
impl Rejected {
    fn value(&self) -> Value {
        let mut result = self.command.value();
        result["applied"] = json!(false);
        result["reason"] = json!(self.reason);
        result["rejected_ns"] = json!(self.rejected_ns);
        result
    }
}

struct Sample {
    tick: u64,
    elapsed: f64,
    wall_ns: u64,
    lateness_ms: f64,
    x: f64,
    y: f64,
    heading: f64,
    speed: f64,
    vx: f64,
    vy: f64,
    yaw_rate: f64,
    steering: f64,
    s: f64,
    control: String,
    laps: usize,
    laps_completed: usize,
    next_checkpoint: usize,
    checkpoints_passed: usize,
    checkpoints_per_lap: usize,
    finished: bool,
    resets: usize,
    reset_after_s: Option<f64>,
    offroad_elapsed: f64,
    last_reset_tick: Option<u64>,
}
impl Sample {
    fn capture(sim: &Simulation, wall_ns: u64, lateness_ms: f64) -> Self {
        Self {
            tick: sim.tick,
            elapsed: sim.elapsed,
            wall_ns,
            lateness_ms,
            x: sim.x,
            y: sim.y,
            heading: sim.heading,
            speed: sim.speed(),
            vx: sim.vx,
            vy: sim.vy,
            yaw_rate: sim.yaw_rate,
            steering: sim.steering,
            s: sim.s,
            control: sim.action_id.clone(),
            laps: sim.laps,
            laps_completed: sim.laps_completed,
            next_checkpoint: sim.next_checkpoint,
            checkpoints_passed: sim.checkpoints_passed,
            checkpoints_per_lap: sim.track.checkpoints.len(),
            finished: sim.finished,
            resets: sim.reset_events.len(),
            reset_after_s: sim.reset_after_s,
            offroad_elapsed: sim.offroad_elapsed,
            last_reset_tick: sim.last_reset_tick,
        }
    }
    fn value(&self) -> Value {
        json!({"tick":self.tick,"time":self.elapsed,"wall_ns":self.wall_ns,"lateness_ms":self.lateness_ms,
            "kart":{"x":rounded(self.x,4),"y":rounded(self.y,4),"heading":rounded(self.heading,5),
                "speed":rounded(self.speed,4),"vx":rounded(self.vx,4),"vy":rounded(self.vy,4),
                "yaw_rate":rounded(self.yaw_rate,5),"steering_angle":rounded(self.steering,5)},
            "progress":{"lap":(self.laps_completed+1).min(self.laps),"laps_completed":self.laps_completed,
                "laps":self.laps,"checkpoint":self.next_checkpoint,"checkpoints_passed":self.checkpoints_passed,
                "checkpoints_per_lap":self.checkpoints_per_lap,"resets":self.resets,"track_distance":rounded(self.s,3),"finished":self.finished},
            "rescue":{"after_s":self.reset_after_s,"offroad_elapsed":rounded(self.offroad_elapsed,4),"count":self.resets,"last_reset_tick":self.last_reset_tick},
            "control":self.control})
    }
}

#[derive(Clone)]
struct Span {
    count: u64,
    total_ms: f64,
    max_ms: f64,
    max_process_cpu_ms: f64,
    max_thread_cpu_ms: f64,
}
impl Span {
    fn new() -> Self {
        Self {
            count: 0,
            total_ms: 0.0,
            max_ms: 0.0,
            max_process_cpu_ms: 0.0,
            max_thread_cpu_ms: 0.0,
        }
    }
    fn record(&mut self, wall: u64, process: u64, thread: u64) {
        let ms = wall as f64 / 1e6;
        self.count += 1;
        self.total_ms += ms;
        self.max_ms = self.max_ms.max(ms);
        self.max_process_cpu_ms = self.max_process_cpu_ms.max(process as f64 / 1e6);
        self.max_thread_cpu_ms = self.max_thread_cpu_ms.max(thread as f64 / 1e6);
    }
    fn value(&self) -> Value {
        json!({"count":self.count,"total_ms":self.total_ms,"max_ms":self.max_ms,
            "max_process_cpu_ms":self.max_process_cpu_ms,"max_thread_cpu_ms":self.max_thread_cpu_ms})
    }
}

#[derive(Clone)]
struct LateWake {
    tick: u64,
    wake_ns: u64,
    lateness_ms: f64,
    previous_wake_ns: u64,
    wall_gap_ms: f64,
    process_cpu_ms: f64,
    thread_cpu_ms: f64,
}
impl LateWake {
    fn value(&self) -> Value {
        json!({"tick":self.tick,"wake_ns":self.wake_ns,"lateness_ms":self.lateness_ms,
        "previous_wake_ns":self.previous_wake_ns,"wall_since_previous_wake_ms":self.wall_gap_ms,
        "process_cpu_since_previous_wake_ms":self.process_cpu_ms,"thread_cpu_since_previous_wake_ms":self.thread_cpu_ms})
    }
}

#[derive(Clone)]
struct Diagnostics {
    physics: Span,
    sampling: Span,
    publication: Span,
    late_wake_count: u64,
    late_wakes: VecDeque<LateWake>,
    largest: Option<LateWake>,
    previous_wake: (u64, u64, u64),
    dropped_snapshots: u64,
}
impl Diagnostics {
    fn new(started: u64) -> Self {
        Self {
            physics: Span::new(),
            sampling: Span::new(),
            publication: Span::new(),
            late_wake_count: 0,
            late_wakes: VecDeque::with_capacity(64),
            largest: None,
            previous_wake: (started, process_ns(), thread_ns()),
            dropped_snapshots: 0,
        }
    }
    fn wake(&mut self, tick: u64, wake_ns: u64, lateness_ms: f64) {
        let process = process_ns();
        let thread = thread_ns();
        let previous = self.previous_wake;
        self.previous_wake = (wake_ns, process, thread);
        if lateness_ms <= 25.0 {
            return;
        }
        let event = LateWake {
            tick,
            wake_ns,
            lateness_ms,
            previous_wake_ns: previous.0,
            wall_gap_ms: (wake_ns - previous.0) as f64 / 1e6,
            process_cpu_ms: (process - previous.1) as f64 / 1e6,
            thread_cpu_ms: (thread - previous.2) as f64 / 1e6,
        };
        self.late_wake_count += 1;
        if self
            .largest
            .as_ref()
            .map(|e| e.lateness_ms < lateness_ms)
            .unwrap_or(true)
        {
            self.largest = Some(event.clone());
        }
        if self.late_wakes.len() == 64 {
            self.late_wakes.pop_front();
        }
        self.late_wakes.push_back(event);
    }
    fn value(&self, running: bool, detail: bool) -> Value {
        let mut value = json!({"active":running,"event_limit":64,"slow_span_threshold_ms":5.0,
            "late_wake_threshold_ms":25,"gc_count":0,"gc_max_ms":0.0,"slow_span_count":0,
            "late_wake_count":self.late_wake_count,"spans":{"physics_step":self.physics.value(),
                "physics_sample":self.sampling.value(),"snapshot_capture":self.publication.value()},
            "largest_late_wake":self.largest.as_ref().map(LateWake::value),"dropped_snapshots":self.dropped_snapshots,
            "watchdog":{"enabled":false,"sample_interval_ms":16,"stall_threshold_ms":50,
                "sample_count":0,"stall_sample_count":0,"max_sample_gap_ms":0.0,"largest_sample_gap":null,"last_sample_ns":null,
                "note":"Rust clock records process and dedicated simulation thread CPU at physics wakes."},
            "cpu_note":"Process CPU includes serialization and IPC threads; thread CPU is the simulation thread only.",
            "gc_note":"Rust worker has no tracing garbage collector; per-step allocations are not claimed to be zero."});
        if detail {
            value["gc_events"] = json!([]);
            value["slow_spans"] = json!([]);
            value["late_wakes"] =
                Value::Array(self.late_wakes.iter().map(LateWake::value).collect());
            value["watchdog"]["stall_samples"] = json!([]);
        }
        value
    }
}

#[derive(Clone)]
struct Snapshot {
    sim: Simulation,
    race_id: String,
    label: String,
    status: String,
    reason: Option<String>,
    deadline: f64,
    started_ns: u64,
    finished_ns: Option<u64>,
    captured_ns: u64,
    last_observed_ns: Option<u64>,
    command_count: usize,
    pending: bool,
    max_lateness_ms: f64,
    p95_lateness_ms: f64,
    diagnostics: Diagnostics,
    trail: Vec<[f64; 2]>,
}
impl Snapshot {
    fn observation(&self, observed_ns: Option<u64>) -> Value {
        let mut value = self.sim.observation();
        value["race_id"] = json!(self.race_id);
        value["status"] = json!(self.status);
        value["finished"] = json!(self.sim.finished);
        if let Some(now) = observed_ns {
            value["observed_ns"] = json!(now);
        }
        value
    }
    fn timing(&self, detail: bool) -> Value {
        let now = self.finished_ns.unwrap_or(self.captured_ns);
        let wall_elapsed = (now - self.started_ns) as f64 / 1e9;
        let drift_ms = (wall_elapsed - self.sim.elapsed) * 1000.0;
        let valid = self.max_lateness_ms <= 100.0
            && self.p95_lateness_ms <= 25.0
            && drift_ms.abs() <= 100.0
            && !self
                .reason
                .as_deref()
                .unwrap_or("")
                .starts_with("runtime_error");
        json!({"wall_elapsed":wall_elapsed,"simulation_elapsed":self.sim.elapsed,"drift_ms":drift_ms,
            "max_lateness_ms":self.max_lateness_ms,"p95_lateness_ms":self.p95_lateness_ms,
            "physics_hz":60,"physics_steps":self.sim.tick,"clock_mode":CLOCK_MODE,
            "pacing":{"native_sleeper_ready_ns":null,"native_sleeper_thread_alive":false,
                "dedicated_simulation_thread":true,"absolute_epoch":true},
            "diagnostics":self.diagnostics.value(self.status=="running",detail),"infrastructure_valid":valid,
            "validity_limits_ms":{"max_lateness":100,"p95_lateness":25,"absolute_drift":100}})
    }
    fn state(&self) -> Value {
        let config = self.sim.config();
        json!({"status":self.status,"race_id":self.race_id,"label":self.label,"reason":self.reason,
            "seed":self.sim.seed,"deadline":self.deadline,"observation":self.observation(None),
            "track":self.sim.track_json(),"actions":config["actions"],"timing":self.timing(false),
            "command_count":self.command_count,"waiting_for_reply":self.status=="running"&&!self.pending,
            "observation_age_ms":self.last_observed_ns.map(|n|(self.captured_ns-n)as f64/1e6),
            "trail":self.trail.iter().map(|p|[rounded(p[0],4),rounded(p[1],4)]).collect::<Vec<_>>()})
    }
}

struct Recording {
    snapshot: Snapshot,
    samples: Vec<Sample>,
    commands: Vec<Command>,
    rejected: Vec<Rejected>,
}
impl Recording {
    fn value(&self) -> Value {
        let timing = self.snapshot.timing(true);
        let mut summary = self.snapshot.sim.summary();
        summary["deadline"] = json!(self.snapshot.deadline);
        summary["realtime_valid"] = timing["infrastructure_valid"].clone();
        let commands = Value::Array(self.commands.iter().map(Command::value).collect());
        json!({"race_id":self.snapshot.race_id,"seed":self.snapshot.sim.seed,"label":self.snapshot.label,
            "status":self.snapshot.status,"reason":self.snapshot.reason,"deadline":self.snapshot.deadline,
            "started_ns":self.snapshot.started_ns,"finished_ns":self.snapshot.finished_ns,"summary":summary,
            "config":self.snapshot.sim.config(),"track":self.snapshot.sim.track_json(),"timing":timing,
            "runtime_info":{"backend":"rust","protocol_version":1,"watchdog_enabled":false,
                "clock_mode":CLOCK_MODE,"physics_hz":60,"process_pid":std::process::id()},
            "samples":self.samples.iter().map(Sample::value).collect::<Vec<_>>(),
            "commands":commands,"controls":commands,"realtime_valid":timing["infrastructure_valid"],
            "rejected_commands":self.rejected.iter().map(Rejected::value).collect::<Vec<_>>(),
            "reset_events":self.snapshot.sim.reset_events})
    }
}

enum Payload {
    Json(Value),
    Observation(Snapshot),
    Ack(Command, Snapshot),
    Rejection(Rejected, Snapshot),
    Ended(Value, Snapshot),
    Recording(Box<Recording>),
}
struct Reply {
    identity: Value,
    payload: Result<Payload, String>,
    state: Option<Snapshot>,
    terminal: bool,
}
enum Output {
    Ready(Value),
    Reply(Box<Reply>),
}
struct Outbox {
    tx: mpsc::SyncSender<Output>,
    latest: Arc<Mutex<Option<Snapshot>>>,
    failed: Arc<AtomicBool>,
}
impl Outbox {
    fn reply(
        &self,
        identity: Value,
        payload: Result<Payload, String>,
        state: Option<Snapshot>,
        terminal: bool,
    ) -> Result<(), String> {
        self.tx
            .try_send(Output::Reply(Box::new(Reply {
                identity,
                payload,
                state,
                terminal,
            })))
            .map_err(|_| "Worker RPC reply queue exhausted or writer disconnected".to_string())
    }
    fn publish(&self, snapshot: Snapshot) -> bool {
        if let Ok(mut latest) = self.latest.try_lock() {
            *latest = Some(snapshot);
            true
        } else {
            false
        }
    }
}

fn write_output(writer: &mut impl Write, session: &str, output: Output) -> io::Result<()> {
    let message = match output {
        Output::Ready(value) => value,
        Output::Reply(reply) => {
            let mut value = match reply.payload {
                Err(error) => {
                    json!({"type":"reply","id":reply.identity,"ok":false,"error_type":"ValueError","error":error})
                }
                Ok(payload) => {
                    let result = match payload {
                        Payload::Json(value) => value,
                        Payload::Observation(snapshot) => {
                            snapshot.observation(Some(snapshot.captured_ns))
                        }
                        Payload::Ack(command, snapshot) => {
                            let mut value = command.value();
                            value["applied"] = json!(true);
                            value["observation"] = snapshot.observation(Some(snapshot.captured_ns));
                            value
                        }
                        Payload::Rejection(rejected, snapshot) => {
                            let mut value = rejected.value();
                            value["observation"] = snapshot.observation(Some(snapshot.captured_ns));
                            value
                        }
                        Payload::Ended(mut value, snapshot) => {
                            value["observation"] = snapshot.observation(Some(snapshot.captured_ns));
                            value
                        }
                        Payload::Recording(recording) => recording.value(),
                    };
                    json!({"type":"reply","id":reply.identity,"ok":true,"value":result})
                }
            };
            if let Some(snapshot) = reply.state {
                value["state"] = snapshot.state();
                value["captured_ns"] = json!(snapshot.captured_ns);
                if reply.terminal {
                    value["terminal_observation"] =
                        snapshot.observation(Some(snapshot.captured_ns));
                }
            }
            value
        }
    };
    let mut message = message;
    message["session_id"] = json!(session);
    serde_json::to_writer(&mut *writer, &message)?;
    writer.write_all(b"\n")?;
    writer.flush()
}

struct Race {
    sim: Simulation,
    race_id: String,
    label: String,
    status: String,
    reason: Option<String>,
    deadline: f64,
    started_ns: u64,
    finished_ns: Option<u64>,
    last_command_seq: Option<u64>,
    pending: Option<Pending>,
    last_observed_ns: Option<u64>,
    samples: Vec<Sample>,
    commands: Vec<Command>,
    rejected: Vec<Rejected>,
    lateness: Vec<f64>,
    histogram: [u64; 1002],
    max_lateness_ms: f64,
    diagnostics: Diagnostics,
    recording_taken: bool,
}
impl Race {
    fn new(sim: Simulation, deadline: f64, label: String, session: &str) -> Result<Self, String> {
        let capacity = (deadline / DT).ceil() as usize + 2;
        let mut samples = Vec::new();
        samples
            .try_reserve_exact(capacity)
            .map_err(|e| format!("Cannot reserve race recording: {e}"))?;
        let mut lateness = Vec::new();
        lateness
            .try_reserve_exact(capacity)
            .map_err(|e| format!("Cannot reserve clock recording: {e}"))?;
        let mut commands = Vec::new();
        commands
            .try_reserve_exact(capacity)
            .map_err(|e| format!("Cannot reserve control recording: {e}"))?;
        let mut diagnostics = Diagnostics::new(0);
        let started_ns = monotonic_ns();
        diagnostics.previous_wake = (started_ns, process_ns(), thread_ns());
        let mut race = Self {
            sim,
            race_id: format!("{session}-{started_ns}"),
            label,
            status: "running".into(),
            reason: None,
            deadline,
            started_ns,
            finished_ns: None,
            last_command_seq: None,
            pending: None,
            last_observed_ns: None,
            samples,
            commands,
            rejected: Vec::new(),
            lateness,
            histogram: [0; 1002],
            max_lateness_ms: 0.0,
            diagnostics,
            recording_taken: false,
        };
        race.samples
            .push(Sample::capture(&race.sim, started_ns, 0.0));
        Ok(race)
    }
    fn snapshot(&self, exact: bool) -> Snapshot {
        let p95 = if exact {
            let mut ordered = self.lateness.clone();
            ordered.sort_by(f64::total_cmp);
            if ordered.is_empty() {
                0.0
            } else {
                ordered[((ordered.len() as f64 * 0.95).ceil() as usize).saturating_sub(1)]
            }
        } else {
            let rank = (self.lateness.len() as f64 * 0.95).ceil() as u64;
            let mut count = 0;
            let mut result = 0.0;
            if rank > 0 {
                for (i, &n) in self.histogram.iter().enumerate() {
                    count += n;
                    if count >= rank {
                        result = i as f64 / 10.0;
                        break;
                    }
                }
            }
            result
        };
        let last_reset = self.sim.last_reset_tick.unwrap_or(0);
        let start = self.samples.len().saturating_sub(600);
        let trail = self.samples[start..]
            .iter()
            .step_by(3)
            .filter(|s| s.tick >= last_reset)
            .map(|s| [s.x, s.y])
            .collect();
        Snapshot {
            sim: self.sim.clone(),
            race_id: self.race_id.clone(),
            label: self.label.clone(),
            status: self.status.clone(),
            reason: self.reason.clone(),
            deadline: self.deadline,
            started_ns: self.started_ns,
            finished_ns: self.finished_ns,
            captured_ns: monotonic_ns(),
            last_observed_ns: self.last_observed_ns,
            command_count: self.commands.len(),
            pending: self.pending.is_some(),
            max_lateness_ms: self.max_lateness_ms,
            p95_lateness_ms: p95,
            diagnostics: self.diagnostics.clone(),
            trail,
        }
    }
    fn end(&mut self, reason: &str, outbox: &Outbox) -> Result<(), String> {
        self.status = if reason == "completed" {
            "completed"
        } else if reason == "deadline" || reason.starts_with("runtime_error") {
            "failed"
        } else {
            "stopped"
        }
        .into();
        self.reason = Some(reason.into());
        self.finished_ns = Some(monotonic_ns());
        if let Some(pending) = self.pending.take() {
            outbox.reply(
                pending.identity,
                Err(format!("Race ended before input application: {reason}")),
                None,
                false,
            )?;
        }
        Ok(())
    }
    fn require(&self, args: &Value) -> Result<(), String> {
        if let Some(race_id) = args["race_id"].as_str() {
            if race_id != self.race_id {
                return Err("Stale race_id; the command belongs to a different race".into());
            }
        }
        Ok(())
    }
    fn recording(&mut self) -> Result<Recording, String> {
        if self.status == "running" {
            return Err("Stop the race before transferring its full recording".into());
        }
        if self.recording_taken {
            return Err("Race recording has already been transferred".into());
        }
        self.recording_taken = true;
        Ok(Recording {
            snapshot: self.snapshot(true),
            samples: std::mem::take(&mut self.samples),
            commands: std::mem::take(&mut self.commands),
            rejected: std::mem::take(&mut self.rejected),
        })
    }
    fn tick(&mut self, outbox: &Outbox) -> Result<(), String> {
        let target = self.started_ns + ((self.sim.tick + 1) as f64 * DT * 1e9).round() as u64;
        let wake = monotonic_ns();
        let late = wake.saturating_sub(target) as f64 / 1e6;
        self.diagnostics.wake(self.sim.tick + 1, wake, late);
        let pending = self.pending.take();
        let reset_before = self.sim.last_reset_tick;
        let stale = pending
            .as_ref()
            .map(|p| {
                reset_before
                    .map(|t| p.command.observation_tick < t)
                    .unwrap_or(false)
            })
            .unwrap_or(false);
        if let Some(pending) = pending.as_ref().filter(|_| !stale) {
            self.sim.set_control(&pending.command.action_id)?;
        }
        let before = (monotonic_ns(), process_ns(), thread_ns());
        self.sim.step(DT)?;
        let applied_ns = monotonic_ns();
        self.diagnostics.physics.record(
            applied_ns - before.0,
            process_ns() - before.1,
            thread_ns() - before.2,
        );
        self.lateness.push(late);
        self.max_lateness_ms = self.max_lateness_ms.max(late);
        self.histogram[((late * 10.0).ceil() as usize).min(1001)] += 1;
        let before = (monotonic_ns(), process_ns(), thread_ns());
        self.samples
            .push(Sample::capture(&self.sim, applied_ns, late));
        self.diagnostics.sampling.record(
            monotonic_ns() - before.0,
            process_ns() - before.1,
            thread_ns() - before.2,
        );
        if self.sim.finished {
            self.end("completed", outbox)?;
        } else if self.sim.elapsed >= self.deadline {
            self.end("deadline", outbox)?;
        }
        if let Some(mut pending) = pending {
            self.last_observed_ns = Some(monotonic_ns());
            if stale {
                let rejected = Rejected {
                    command: pending.command,
                    reason: "observation_before_rescue".into(),
                    rejected_ns: monotonic_ns(),
                };
                self.rejected.push(rejected.clone());
                outbox.reply(
                    pending.identity,
                    Ok(Payload::Rejection(rejected, self.snapshot(false))),
                    None,
                    false,
                )?;
            } else {
                pending.command.applied_ns = Some(applied_ns);
                pending.command.applied_tick = Some(self.sim.tick);
                pending.command.reset_during_step =
                    self.sim.last_reset_tick.is_some() && self.sim.last_reset_tick != reset_before;
                self.last_command_seq = Some(pending.command.command_seq);
                self.commands.push(pending.command.clone());
                outbox.reply(
                    pending.identity,
                    Ok(Payload::Ack(pending.command, self.snapshot(false))),
                    None,
                    false,
                )?;
            }
        }
        if self.sim.tick.is_multiple_of(3) || self.status != "running" {
            let before = (monotonic_ns(), process_ns(), thread_ns());
            if !outbox.publish(self.snapshot(false)) {
                self.diagnostics.dropped_snapshots += 1;
            }
            self.diagnostics.publication.record(
                monotonic_ns() - before.0,
                process_ns() - before.1,
                thread_ns() - before.2,
            );
        }
        Ok(())
    }
}

fn required_race(race: &mut Option<Race>) -> Result<&mut Race, String> {
    race.as_mut().ok_or_else(|| "No race has started".into())
}

fn request(
    message: Value,
    race: &mut Option<Race>,
    outbox: &Outbox,
    session: &str,
) -> Result<bool, String> {
    if message["session_id"].as_str() != Some(session) {
        return Ok(false);
    }
    let identity = message["id"].clone();
    let method = message["method"].as_str().unwrap_or("");
    let args = &message["arguments"];
    let mut state = None;
    let mut terminal = false;
    let mut stopping = false;
    let result = (|| -> Result<Option<Payload>, String> {
        match method {
            "start" => {
                if race
                    .as_ref()
                    .map(|r| r.status == "running")
                    .unwrap_or(false)
                {
                    return Err(
                        "A race is already running; finish it before starting another".into(),
                    );
                }
                let deadline = args["deadline"].as_f64().unwrap_or(120.0);
                if !deadline.is_finite() || deadline <= 0.0 || deadline > 86400.0 {
                    return Err(
                        "deadline must be a positive number of seconds, at most 86400".into(),
                    );
                }
                let sim = Simulation::from_fixture(&args["fixture"])?;
                if sim.tick != 0 || sim.elapsed != 0.0 || sim.finished {
                    return Err("Live races must start at tick and elapsed zero".into());
                }
                let mut next = Race::new(
                    sim,
                    deadline,
                    args["label"].as_str().unwrap_or("").into(),
                    session,
                )?;
                next.last_observed_ns = Some(monotonic_ns());
                let snapshot = next.snapshot(false);
                state = Some(snapshot.clone());
                *race = Some(next);
                Ok(Some(Payload::Observation(snapshot)))
            }
            "observe" => {
                let race = required_race(race)?;
                race.require(args)?;
                race.last_observed_ns = Some(monotonic_ns());
                Ok(Some(Payload::Observation(race.snapshot(false))))
            }
            "drive" => {
                let race = required_race(race)?;
                race.require(args)?;
                let action = args["action_id"]
                    .as_str()
                    .ok_or("action_id must be a string")?;
                if race.status != "running" {
                    race.last_observed_ns = Some(monotonic_ns());
                    return Ok(Some(Payload::Ended(
                        json!({"race_id":race.race_id,
                "command_seq":args["command_seq"],"action_id":action,"applied":false,"reason":"race_already_ended"}),
                        race.snapshot(false),
                    )));
                }
                if !sim::valid_action(action) {
                    return Err(format!("Unknown action_id: {action}"));
                }
                let seq = args["command_seq"]
                    .as_u64()
                    .ok_or("command_seq must be a nonnegative integer")?;
                let tick = args["observation_tick"]
                    .as_u64()
                    .ok_or("observation_tick must refer to an existing physics tick")?;
                if tick > race.sim.tick {
                    return Err("observation_tick must refer to an existing physics tick".into());
                }
                let command = Command {
                    race_id: race.race_id.clone(),
                    action_id: action.into(),
                    observation_tick: tick,
                    command_seq: seq,
                    queued_ns: monotonic_ns(),
                    applied_ns: None,
                    applied_tick: None,
                    reset_during_step: false,
                };
                if race.sim.last_reset_tick.map(|t| tick < t).unwrap_or(false) {
                    let rejected = Rejected {
                        command,
                        reason: "observation_before_rescue".into(),
                        rejected_ns: monotonic_ns(),
                    };
                    race.rejected.push(rejected.clone());
                    race.last_observed_ns = Some(monotonic_ns());
                    return Ok(Some(Payload::Rejection(rejected, race.snapshot(false))));
                }
                if race
                    .last_command_seq
                    .map(|last| seq <= last)
                    .unwrap_or(false)
                {
                    return Err("Duplicate or out-of-order command_seq".into());
                }
                if race.pending.is_some() {
                    return Err("A command is already waiting for its physics step".into());
                }
                race.pending = Some(Pending {
                    identity: identity.clone(),
                    command,
                });
                Ok(None)
            }
            "finish" | "result" => {
                let race = required_race(race)?;
                race.require(args)?;
                if method == "finish" && race.status == "running" {
                    race.end(args["reason"].as_str().unwrap_or("cancelled"), outbox)?;
                }
                let recording = race.recording()?;
                state = Some(recording.snapshot.clone());
                terminal = true;
                Ok(Some(Payload::Recording(Box::new(recording))))
            }
            "shutdown" => {
                if let Some(race) = race.as_mut().filter(|r| r.status == "running") {
                    race.end("server_shutdown", outbox)?;
                }
                stopping = true;
                Ok(Some(Payload::Json(json!({"closed":true}))))
            }
            _ => Err(format!("Unknown worker method: {method}")),
        }
    })();
    match result {
        Ok(None) => {}
        Ok(Some(value)) => outbox.reply(identity, Ok(value), state, terminal)?,
        Err(error) => outbox.reply(identity, Err(error), None, false)?,
    }
    Ok(stopping)
}

pub fn run(session: String, idle: Value) -> Result<(), String> {
    let (tx, rx) = mpsc::sync_channel::<Value>(QUEUE_LIMIT);
    let reader_session = session.clone();
    thread::Builder::new()
        .name("kart-ndjson-reader".into())
        .spawn(move || {
            for line in io::stdin().lock().lines() {
                let value = match line {
                    Ok(line) => match serde_json::from_str::<Value>(&line) {
                        Ok(value) => value,
                        Err(_) => continue,
                    },
                    Err(_) => break,
                };
                if value["session_id"].as_str() != Some(reader_session.as_str()) {
                    continue;
                }
                if tx.send(value).is_err() {
                    return;
                }
            }
        })
        .map_err(|e| e.to_string())?;
    let (output_tx, output_rx) = mpsc::sync_channel::<Output>(QUEUE_LIMIT);
    let latest = Arc::new(Mutex::new(None::<Snapshot>));
    let failed = Arc::new(AtomicBool::new(false));
    let writer_latest = latest.clone();
    let writer_failed = failed.clone();
    let writer_session = session.clone();
    let writer=thread::Builder::new().name("kart-ndjson-writer".into()).spawn(move|| {
        let stdout=io::stdout();let mut writer=BufWriter::new(stdout.lock());
        loop {
            match output_rx.recv_timeout(Duration::from_millis(5)) {
                Ok(output)=>if write_output(&mut writer,&writer_session,output).is_err() {writer_failed.store(true,Ordering::Relaxed);break;},
                Err(mpsc::RecvTimeoutError::Disconnected)=>break,
                Err(mpsc::RecvTimeoutError::Timeout)=>{},
            }
            let snapshot=writer_latest.lock().unwrap().take();
            if let Some(snapshot)=snapshot {
                let state=json!({"type":"state","session_id":writer_session,"captured_ns":snapshot.captured_ns,"state":snapshot.state()});
                if serde_json::to_writer(&mut writer,&state).is_err()||writer.write_all(b"\n").is_err()||writer.flush().is_err() {
                    writer_failed.store(true,Ordering::Relaxed);break;
                }
            }
        }
    }).map_err(|e|e.to_string())?;
    let outbox = Outbox {
        tx: output_tx,
        latest,
        failed,
    };
    outbox
        .tx
        .try_send(Output::Ready(
            json!({"type":"ready","pid":std::process::id(),"ready_ns":monotonic_ns(),"state":idle,
        "entrypoint":"mcpkart-rust-worker","clock_mode":CLOCK_MODE,"web_modules_loaded":[]}),
        ))
        .map_err(|e| e.to_string())?;
    let mut race: Option<Race> = None;
    let result = (|| -> Result<(), String> {
        loop {
            if outbox.failed.load(Ordering::Relaxed) {
                return Err("Worker output disconnected".into());
            }
            let wait = if let Some(active) = race.as_ref().filter(|r| r.status == "running") {
                let target =
                    active.started_ns + ((active.sim.tick + 1) as f64 * DT * 1e9).round() as u64;
                let now = monotonic_ns();
                if now >= target {
                    let tick_result = race_tick(&mut race, &outbox);
                    if let Err(error) = tick_result {
                        if let Some(race) = race.as_mut() {
                            race.end(&format!("runtime_error:{error}"), &outbox)?;
                        }
                        return Err(error);
                    }
                    continue;
                }
                Duration::from_nanos(target - now)
            } else {
                Duration::from_millis(100)
            };
            match rx.recv_timeout(wait) {
                Ok(message) => {
                    if request(message, &mut race, &outbox, &session)? {
                        return Ok(());
                    }
                }
                Err(mpsc::RecvTimeoutError::Timeout) => {}
                Err(mpsc::RecvTimeoutError::Disconnected) => {
                    if let Some(race) = race.as_mut().filter(|r| r.status == "running") {
                        race.end("server_shutdown", &outbox)?;
                    }
                    return Ok(());
                }
            }
        }
    })();
    drop(outbox);
    let _ = writer.join();
    result
}

fn race_tick(race: &mut Option<Race>, outbox: &Outbox) -> Result<(), String> {
    required_race(race)?.tick(outbox)
}
