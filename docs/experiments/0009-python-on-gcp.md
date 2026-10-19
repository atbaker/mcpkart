# Python race engine on GCP

October 18, 2026. Status: all three scripted races and the long clock check
passed. Results were downloaded; the VM and boot disk were deleted.
The user requested a Python comparison after [Rust passed on GCP](0008-remote-linux-clock.md),
preferring to retain Python if its remote performance is sufficient.

## Declared comparison

Use another temporary on-demand `c2d-highcpu-4` in `gator-works-dev`,
`us-west1-a`: four vCPUs, 8 GiB RAM, Ubuntu 24.04, 20 GiB automatically deleted
boot disk, no service account or model credentials. Retain the $1 infrastructure
cap, one-hour automatic DELETE limit and explicit deletion after evidence is
downloaded. This is the same VM type/region as the Rust experiment, not the
same physical host. Record actual CPU, kernel, Docker and container metadata.

Keep the same pinned Docker base images, Python 3.14.8, `uv.lock`, source,
handling, track, 15 controls, seed zero, three laps and zero-speed rescue rules.
Select the existing **Python process backend with asyncio pacing**:
`--race-engine python --clock-backend process --clock-pacing asyncio`, watchdog
disabled. Do not modify physics or timing code. The image contains the unused
Rust binary for an otherwise comparable environment; its presence is not
execution. Prove each actual child's entrypoint is `mcpkart.physics_worker`,
clock mode is `fixed_step_wall_clock`, child/parent PIDs differ, and no web/MCP
framework modules were loaded by the child. Reject a Rust or native-sleeper
fallback.

Package the same allowlisted source and locked dependencies with an explicit
Python manifest and fresh `artifacts/remote-python-clock-v1/` output. Preserve
original helper hashes and declare engine/path/label substitutions. Exclude
`.env`, credentials, Git, legacy files, host tooling and unrelated recordings.
Verify the bundle on the VM. Before timing, finish tests, lint, reference
configuration checks and any shared image parity checks; freeze code/image.
The paired seed-zero reference remains 56.7 s unless an explicitly documented
configuration mismatch blocks the test.

Run **three consecutive real-MCP scripted races**, with about 20 Hz container
spectator polling and 5 Hz VM-host polling. Each must complete all 120 ordered
gates and meet the unchanged limits: maximum physics lateness <=100 ms, exact
final p95 <=25 ms, absolute final drift <=100 ms. During race two, pause only
the verified HTTP parent for about 350 ms around 20 race seconds. Require at
least twelve actual child samples during that Linux monotonic interval and
always resume the parent in cleanup. Stop at the first failed control, retain
the attempt, and do not retry until a pass.

Only if all three pass, run the same **170.1 s neutral-input check** through
MCP at about 5 Hz, with an independent client heartbeat and the same spectator
load. Stationary progress is expected; timing/duration and provenance determine
this check's result. No builds or heavy analysis run alongside a live clock.
After stop, independently replay recorded applied-tick inputs, recompute timing
metrics, and verify source, Python worker identity, command ordering and pause
samples. Preserve all logs and failures and retrieve results before deletion.

This comparison makes **no model calls**, and must leave the shared $10 model
ledger unchanged at $0.914245672 with no pending reservations. A pass supports
keeping the current Python process architecture for solo development on GCP;
Python need not match Rust's sub-millisecond jitter to satisfy this workload.
It does not establish multiplayer capacity, sustained production reliability,
Temporal overhead, or a specific cause for the local Mac stalls.

## Results

The fresh `c2d-highcpu-4` in `us-west1-a` used AMD Milan, four vCPUs and
8 GiB RAM, Ubuntu 24.04.5 LTS, kernel `7.0.0-1014-gcp` and Docker 29.1.3.
The container used Python 3.14.8 and `EpollSelector`, the same pinned base
images and locked dependencies as the preceding Rust comparison. No physics,
handling, timing thresholds or reference configuration changed. The application
fingerprint remains
`79752a5d5c50eca99d5feefa9e34360e161feb581a4c47ec001be196a03cc9a8`.

The 235,399-byte allowlisted source bundle contained 43 regular files, with
42 content hashes verified before building. Its SHA-256 was
`e51ad1e8c56be9bd09eb145399b064c1dd48c73776d021194dbead33fb2ea2d9`.
Preflight passed **276 tests**, Ruff, exact reference configuration checks,
and the shared image's 17 parity scenarios with 1,418,439 comparisons.
Parity was completed before timing; every timed race used only the Python
worker. The seed-zero reference remains 56.7 s.

| Metric | Race 1 | Race 2, parent paused | Race 3 | Neutral clock |
| --- | ---: | ---: | ---: | ---: |
| Simulation duration | 56.667 s | 56.633 s | 56.667 s | 170.100 s |
| Ordered gates | 120 | 120 | 120 | stationary |
| Maximum lateness | 2.094 ms | 2.224 ms | 2.078 ms | 3.276 ms |
| Exact final p95 lateness | 1.146 ms | 1.394 ms | 1.305 ms | 1.297 ms |
| Final world/wall drift | 0.776 ms | 1.196 ms | 0.844 ms | 0.367 ms |
| Realtime-valid | yes | yes | yes | yes |

All three races completed three laps with zero off-road time and zero rescues.
The HTTP-parent pause lasted **350.114 ms** around 20 s. The child recorded
**21 actual physics samples** during that interval, with maximum lateness
1.707 ms. It continued running while the HTTP process was stopped.
The long check submitted 849 neutral MCP commands. Independent VM-host
spectator polling made 1,804 successful requests with zero errors; its maximum
round trip was 403.69 ms. The batch retains the deliberate parent interruption
and final recording collection.
Physics timing is measured in the worker, separately from HTTP responsiveness.
The independent client heartbeat peaked at 2.24 ms during the long race.
Its raw 382.99 ms maximum occurred after the race ended, during final collection;
the replay proof records both intervals separately.

Across the batch, the longest measured physics step was 0.524 ms and the
longest state-publication span was 5.226 ms. The largest GC event was 4.295 ms;
there were no late-wake events above the 25 ms diagnostic threshold. Cgroup
counters recorded no CPU throttling or memory/OOM events. No GC, scheduler,
affinity or native-sleeper tuning was needed.

## Evidence and cleanup

All four final recordings identify `mcpkart.physics_worker`, process isolation,
`fixed_step_wall_clock`, asyncio pacing and separate child/parent PIDs. The
children loaded no web/MCP framework modules and used no Rust binary or native
sleeper. Independent offline Python replay passed for **20,408 samples** and
11,014 applied commands: 551,081 replay comparisons, 159,711 recording-invariant
checks and 304,168 acknowledgement/observation checks. Maximum numeric
difference was 2.27e-13. Exact timing recomputation, source identity, track and
configuration checks, command ordering and actual parent-pause samples passed.

The bundle, downloaded archive, recordings, environment/build/test logs,
provisioning metadata and replay proof are retained under the ignored
`artifacts/remote-python-clock-v1/`. The model ledger is byte-for-byte unchanged:
**$0.914245672 of $10**, with no pending reservations and no model calls in
this experiment. No API credentials were copied to the VM.

After collection, explicit deletion removed the VM and its automatically
deleted boot disk. Independent API lookups confirmed both absent; temporary
SSH private/public keys were removed locally. Provisioning-to-deletion took
about 11.18 minutes: approximately **$0.028 compute** using the price recorded
in the preceding experiment, plus small disk/IP charges. This is an estimate,
not a final invoice, and remains below the $1 infrastructure cap.

## Decision

**Retain the process-isolated Python engine with asyncio pacing for the
current solo PoC.** Python passed the unchanged 100/25/100 ms gate on GCP with
substantial margin: even its worst 3.28 ms wake lateness is below one 16.67 ms
physics tick. Rust has lower jitter in the preceding test, but this workload
does not require that difference. The optional Rust spike remains available.

Resume Jev navigation experiments using this qualified GCP/Python environment
and keep the timing gate in place. This experiment makes no new claim about
Jev's driving performance. Multiplayer capacity, longer production runs and
Temporal integration still require measurement. These results also do not
identify which local hardware, OS or container behavior caused the Mac stalls.

## Reproduce the free batch

`scripts/package_remote_clock.py --engine python --output /path/to/bundle.tar.gz`
creates the allowlisted package. On a prepared Linux host, extract it and run
`bash scripts/run_remote_clock.sh --engine python /path/to/results`.
The runner preserves the existing protocol, worker-identity checks, failures
and cleanup. Omitting `--engine` retains the earlier Rust runner's behavior.
Provisioning, infrastructure limits and VM deletion are managed separately.
