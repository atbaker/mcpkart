# Rust race-engine experiment

October 18, 2026. Status: implemented; the Linux timing batch failed control two.
The protocol below was written before timed Rust trials.
The user asked whether Rust is worth trying for the game engine while retaining
Python and FastMCP for the platform. The recommendation is a bounded race-worker
experiment before choosing a production implementation language.

Implementation uses a standalone `rust-race` release binary and an optional
`RustRaceRuntime` Python adapter, selected with `--race-engine rust`. Python
remains the default. Results use the fresh `artifacts/rust-clock-v1/` directory.
Before timed trials, replay comparison uses absolute numeric tolerance 1e-8
with exact discrete outcomes. Build/test/parity work must finish before the
first declared control; no concurrent compilation or parity analysis.

## Evidence and hypothesis

The [Linux control](0006-linux-docker-clock.md) completed three laps, but failed
the unchanged maximum-lateness gate: 104.26 ms versus 100 ms. Its maximum
physics-step duration was only 0.81 ms, well below a 16.67 ms tick budget. A
102 ms state-publication span coincided with the worst delayed wake and
substantial process CPU. Process CPU covers all child threads; neither that
function nor the GIL is established as the cause. Earlier low-CPU macOS gaps
remain a separate clue. Linux runs in Docker's VM on the same Mac.

Inferred from current source, not checkpoint history: the isolated Python
worker still runs physics, observation construction and its 20 Hz state
publisher on one asyncio loop. IPC serialization runs on a separate Python
thread in that same process. Porting only the vehicle equations would leave
these possible sources of delay in place.

Rust offers a useful alternative implementation for the entire clock-owning
worker: compiled code, explicit memory ownership, and OS threads without
Python's GIL. Rust ownership avoids tracing garbage collection, but GC was
short in the failed Linux control, so that benefit alone is not an explanation.
Rust is not a realtime scheduling guarantee; its documented sleep behavior
permits oversleep because of OS scheduling. See the official
[ownership chapter](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html)
and [thread sleep documentation](https://doc.rust-lang.org/std/thread/fn.sleep.html).

## Smallest useful boundary

Keep Python for FastMCP, the model driver, benchmark scoring, HTTP/SVG
spectating, and eventual platform orchestration. Replace the race-worker
process behind the existing runtime interface with a standalone Rust binary.
Do not introduce an embedded Python extension or a new physics library for
this comparison.

The Rust clock thread owns simulation state and absolute 60 Hz deadlines.
It applies bounded, validated commands at tick boundaries and produces compact
snapshots. Other threads encode responses and write transport messages.
Snapshot publication must be bounded and nonblocking, with older spectator
snapshots replaceable; applied-command acknowledgements remain lossless or
fail explicitly. A blocked Python parent must not block the clock thread.
Preallocate trial recording capacity and export it after stop. Keep variable
work, formatting, transport writes, and cumulative percentile calculations
off the tick thread; changing language does not make that work harmless.

Preserve the current handling equations, track, 15 controls, checkpoint rules,
three-second rescue at zero speed, stale-command rejection, and observation
semantics. Supply exact track geometry and initial state from Python fixtures
so RNG or spline implementations cannot silently change the course. Keep
the existing telemetry candidate and model instructions fixed.

## Evaluation order

1. Port deterministic simulation and replay saved applied inputs at their
   recorded ticks. Declare numerical tolerances before comparison; require
   exact discrete outcomes (controls, gates, laps, rescue ticks). Preserve the
   Python reference. Investigate divergent boundary events before live trials;
   do not silently recalibrate handling to make a run pass.
2. Run a headless Rust clock with stationary state, then the scripted driver
   through Python/FastMCP with spectator polling. Record release-build and
   dependency identity, per-thread CPU, tick lateness, action age, snapshots
   and backpressure. Include a deliberately paused Python parent.
3. Use the existing gate: three consecutive valid scripted three-lap controls,
   then the 170.1 s neutral-input check. Keep maximum lateness <=100 ms,
   p95 <=25 ms, and absolute final drift <=100 ms; stop and preserve the first
   failed control. Compare in the same Docker VM/resources first, with native
   macOS as a separately labelled check. Finish builds and analysis before
   timed runs.
4. Only after the free gate passes, resume one Jev screen with the existing
   reference, telemetry, route and shared $10 budget. Free Rust experiments
   require no API credentials.

A pass establishes that this Rust worker architecture can support the current
local workload. It does not prove that Python is inherently too slow: language,
threading and publication design changed together. A failure keeps host/VM
scheduling and transport design in scope. Multiplayer collisions, power-ups,
framework adoption and production hosting follow the solo driving milestone.

## Results

The optional Rust worker is implemented behind the existing Python/FastMCP API.
Python remains the default engine. The release uses Rust 1.96.0, with locked
Serde/JSON/libc dependencies; the final image includes the binary, not the Rust
compiler. The simulation thread uses bounded command/reply channels and
replaceable spectator snapshots. JSON encoding, road-preview formatting and
pipe writes run on a separate writer thread. Immutable geometry/configuration
are shared, and recording capacity is reserved before the epoch. Small string
allocations and rare rescue-event allocations remain; this is not a claim of
zero allocation or hard realtime scheduling.

Validation passed **276 Python tests on macOS and 276 inside Linux**, two Rust
unit tests, Ruff, Rustfmt and Clippy. Offline parity passed 18 scenarios and
**1,793,663 comparisons** on each platform, including a prior Python Linux
recording. Maximum Linux numeric error was below 1e-8; discrete outcomes match.
Initial fixture/type-check failures are preserved separately. A preflight
found that macOS `CLOCK_MONOTONIC` has a different epoch from Python's clock;
the Rust macOS path uses `CLOCK_UPTIME_RAW`, with receive-time brackets tested.
Linux uses `CLOCK_MONOTONIC`. This was corrected before timing trials.

The Linux VM has the same four CPUs and 8,320,299,008 bytes RAM as the Python
Docker comparison, kernel `7.0.14-linuxkit`, and Python 3.14.8. The earlier idle
Python Docker container was stopped for this batch. No credentials entered
the Rust container. Image `sha256:d912f9d7d37fe1c6f330eb1e23261992144f8b1c65f04a4682f5809f6478c05c`,
source `79752a5d5c50eca99d5feefa9e34360e161feb581a4c47ec001be196a03cc9a8`,
and Linux binary `29183addca3a9bfcf9a64a902ad0f9bd00fe54e73c03a031ec42d0ffd724f10b`
are recorded with selected environment metadata under `artifacts/rust-clock-v1/`.
The paired seed-zero reference remains 56.7 s.

The preliminary three-second stationary check passed (4.14 ms maximum
lateness). The declared real-MCP controls then produced:

| Metric | Control 1 | Control 2, parent paused |
| --- | ---: | ---: |
| Three-lap duration | 56.700 s | 56.850 s |
| Ordered gates | 120 | 120 |
| Off-road time / rescues | 0 / 0 | 0 / 0 |
| Maximum physics lateness | 47.83 ms | **117.09 ms** |
| p95 physics lateness | 2.73 ms | 2.74 ms |
| Final world/wall drift | 2.48 ms | 2.12 ms |
| Realtime-valid | yes | **no** |

The second control paused the HTTP parent for 353.49 ms around 20 s. The Rust
child recorded **21 actual samples during the pause**, with maximum lateness
3.99 ms. The worst delayed wake occurred at tick 1,427, about 23.90 s into the
race: a 128.53 ms wake gap, with 60.40 ms recorded simulation-thread CPU and
60.70 ms process CPU. That gap began 3.40 s after the parent pause ended.
The pause itself therefore demonstrates clock independence and does not
overlap the failed wake.

Maximum physics step, sampling and snapshot-capture spans in the failed control
were only 0.40, 0.08 and 0.07 ms. Request/acknowledgement/channel paths are not
individually profiled, so the thread CPU does not identify a function or exclude
the runtime/allocator. VM accounting and scheduling remain possible factors.
Cgroup counters show no CPU throttling or memory/OOM events; this does not
measure every host/VM scheduling effect. Absolute-deadline catch-up kept all
ticks and retained the failure, rather than resetting the epoch.

After stop, independent replay verified all **6,815 samples / 6,720 applied
controls** against Python: 184,039 recording comparisons and 751,659 Rust replay
comparisons passed, with maximum replay error 3.70e-13. Source and binary hashes
match both controls. In-container polling made 2,264 successful requests; the
Mac-side spectator made 698 without errors, including setup/collection time.

The batch stopped on its first failure. **Control three, the 170.1 s check and
Jev did not run.** No API spending occurred; the ledger remains $0.825958186 of
$10 with no pending reservations. The Rust spectator remains on localhost:8767.
This spike did not establish reliable timing or prove that the Mac is the
cause. The user has authorized exploring a separate Linux host as the next
environment comparison; preserve the same gate and keep model calls held.

Follow-up: [the temporary GCP comparison](0008-remote-linux-clock.md) passed the
full free gate and produced a timing-valid Jev screen. This does not qualify
local Mac timing or establish that Python would fail on the remote host.
