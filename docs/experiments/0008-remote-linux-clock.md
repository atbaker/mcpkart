# Remote Linux timing comparison

October 18, 2026. Status: all free controls passed; one timing-valid Jev screen
failed driving. Results were downloaded and the temporary VM was deleted.
After [Rust also exceeded the local timing limit](0007-rust-race-engine.md), the
user approved a temporary four-vCPU VM in GCP project `gator-works-dev`, with a
$1 infrastructure cap and deletion after downloading results. The existing
$10 model ledger is separate. This remote bundle makes no model requests.

## Declared protocol

Use an on-demand `c2d-highcpu-4` VM (four vCPUs, 8 GiB) with Ubuntu 24.04 and a
20 GiB automatically deleted boot disk. Prefer `us-west1` where available.
Do not attach a service account or provide model credentials. Only SSH is
needed externally; the game binds localhost through Docker. Configure a
one-hour maximum runtime with automatic VM deletion and explicitly delete the
VM immediately after collecting evidence. No persistent disk, reserved IP or
snapshot is required.

Google's [compute-optimized price table](https://cloud.google.com/products/compute/pricing/compute-optimized)
lists $0.149924/hour for this machine in its default US table; disk/IP charges
are additional. The short runtime and small automatically deleted disk keep
the experiment below the authorized $1 cap. Preserve timestamps and actual
resource configuration; the final bill may arrive later.

Package only the current source, locked Python/Rust dependencies, tests,
control tools, the existing 56.7 s seed-zero reference, and selected free
helpers. Exclude `.env`, credentials, Git/history, host virtual environments,
legacy code, build outputs and unrelated recordings. Verify the archive's
SHA-256 manifest on the VM before building. Build the native Linux release
there, before timed trials; this changes CPU architecture from the M1's ARM64
to x86-64 and must be recorded rather than treated as an isolated OS change.

Run the Rust server and MCP driver inside the same init-enabled container.
Use Linux monotonic timestamps for physics, commands and the verified HTTP
parent pause. The host and container record kernel, CPU, affinity, memory,
Docker, package versions, source/binary hashes and cgroup limits/counters.

Before the first timed race, finish tests, lint, deterministic replay parity,
and exact reference-configuration checks. If another architecture changes
reference geometry/configuration, stop and document it before considering a
separately labelled reference; do not silently change physics or thresholds.
Freeze code/image and avoid parallel compilation or heavy analysis while
clocks run.

Run one batch of three scripted three-lap controls through real MCP, with
the same spectator load and `scripts/validate_clock.py`. Each must finish
120 ordered gates and satisfy maximum lateness <=100 ms, p95 <=25 ms and
absolute final drift <=100 ms. On control two, pause only the verified HTTP
parent for approximately 350 ms around 20 race seconds; require at least
twelve actual child samples within that interval. Resume the parent in cleanup.
Stop at the first failed control and preserve it; do not retry until a pass.

Only if all three pass, run the existing 170.1 s neutral-input clock check,
through MCP at about 5 Hz, with its independent client heartbeat. Preserve
the same clock mode, physics, handling, track, rescue rules, seed, reference
and limits. Record live p95 histogram approximations separately from the exact
final p95 used for scoring. Model viability remains unproven by free controls.

The runner must preserve logs, every failed attempt, runtime provenance and
individual recordings, collect results locally, then remove its own container
and VM. Source and binary identity must match across the batch. After clocks
stop, independently replay applied inputs and validate recorded samples.
No Jev call belongs to this credential-free remote runner; any subsequent
screen must use the existing shared model budget and already agreed route,
telemetry and instructions after the free gate passes.

If that gate passes, the already authorized next step is one seed-zero Jev
`road_navigation` screen with numeric controls, original instructions, pinned
TypeSafe route, the same release image and 170.1 s deadline. The source bundle
and free runner stay credential-free. Supply the OpenRouter key only in the
paid driver process environment over SSH, without storing it on disk or in
the server environment. Transfer the existing budget under its local lock,
retrieve/merge its updates before VM deletion, and retain interrupted attempts.
Run no other ledger writer concurrently. This one trajectory does not qualify
eight-of-ten success or isolate language, telemetry, hosting and model latency.

## Tools

`scripts/package_remote_clock.py --output /path/to/bundle.tar.gz` creates an
allowlisted archive and manifest without connecting or deploying.
On the prepared Linux host, extract it and run
`bash scripts/run_remote_clock.sh /path/to/results`. It builds, validates,
runs the gate and archives results, including failures. Its cleanup resumes
the verified parent and removes only its own uniquely named container.

GCP provisioning, SSH transport, result download and VM deletion are tracked
separately in the ignored local `artifacts/remote-clock-v1/` directory.

## Results

Compute Engine was enabled in the user-selected project, which already had
billing. The temporary on-demand C2D VM ran in `us-west1-a` on AMD Milan, with
four vCPUs and 8 GiB RAM, Ubuntu 24.04.5 LTS, kernel `7.0.0-1014-gcp`, and Docker
29.1.3. It had no service account. Its 20 GiB boot disk was automatically deleted
with the VM; a one-hour automatic DELETE limit backed up explicit cleanup.
No firewall changes, reserved IPs, snapshots or additional disks were needed.

The source bundle was 234,145 bytes, 43 regular files, SHA-256
`e1843972c9fd6953ff586d347b15cb1a67e3f3fe8a494d72dacc29e0030f8f95`.
Its 42 content hashes were verified before Docker built the native x86-64
release. The application fingerprint matches the local Rust experiment:
`79752a5d5c50eca99d5feefa9e34360e161feb581a4c47ec001be196a03cc9a8`.
The x86-64 binary hash is
`e5379c719e3bef2b571b1d268ba269e33b8cc52768cc8b73059bee522c998a19`;
it appropriately differs from the ARM64 binary. All controls and the model
screen used this same source and binary.

Preflight passed **276 tests**, Ruff, and 17 deterministic parity scenarios
with 1,418,439 comparisons. The saved reference configuration matched exactly
despite the architecture change; no recalibration or physics change occurred.
The existing seed-zero reference remains 56.7 s.

### Free clock controls

| Metric | Race 1 | Race 2, parent paused | Race 3 | Neutral clock |
| --- | ---: | ---: | ---: | ---: |
| Simulation duration | 56.667 s | 56.633 s | 56.667 s | 170.100 s |
| Ordered gates | 120 | 120 | 120 | stationary |
| Maximum lateness | 0.862 ms | 0.083 ms | 0.149 ms | 0.144 ms |
| Exact final p95 lateness | 0.066 ms | 0.066 ms | 0.066 ms | 0.066 ms |
| Final world/wall drift | 0.079 ms | 0.079 ms | 0.041 ms | 0.077 ms |
| Realtime-valid | yes | yes | yes | yes |

All three races finished with zero off-road time and zero rescues. The verified
HTTP-parent pause lasted 350.10 ms around 20 s. The child recorded **21 actual
physics samples during that interval**, with maximum lateness 0.064 ms. Host
spectator polling made 1,790 successful requests and no errors, retaining the
294.42 ms maximum round trip during the interruption. The longer check made
neutral MCP calls about 5 Hz and retained its independent client heartbeat.
Cgroup counters recorded no CPU throttling or memory/OOM events.

The batch satisfies the unchanged 100/25/100 ms limits. This provides a useful
working environment for this frozen solo workload. It does not isolate Mac
hardware age, OS behavior, Docker's VM, CPU architecture or other environment
differences; it also does not establish sustained reliability or multiplayer
capacity. Python physics was not tested in this batch. The subsequent
[Python comparison](0009-python-on-gcp.md) passed the same gate on a fresh VM
of the same type, supporting retention of Python for the current solo PoC.

### Jev screen

After all free gates passed and their archive was downloaded, one fresh server
used the same release image/binary for the declared Jev screen. The pinned
TypeSafe route resolved to `typesafe/jev-1.14-20261014`; telemetry was
`road_navigation`, with original instructions, numeric controls and seed zero.
The key was sent over SSH stdin into the driver process environment; it was
not included in the bundle, stored on the VM filesystem, or added to the
server's environment. The local budget lock was held while its existing
ledger was used remotely, then the updated ledger was retrieved and atomically
restored locally. No other writer ran concurrently.

| Metric | Jev on GCP / Rust |
| --- | ---: |
| Ordered gates | **50/120** |
| Completed laps | 1 |
| First lap | 156.583 s |
| Trial duration / deadline | 170.100 s |
| Off-road time | 73.317 s |
| Rescues | 24 |
| Requests / API errors | 866 / 0 |
| Applied controls | 843 |
| Replies rejected after rescue / after race end | 22 / 1 |
| Median / p95 API latency | 156.00 / 227.59 ms |
| Maximum API latency | 1,709.61 ms |
| Median / p95 observation age at application | 166.66 / 248.48 ms |
| Maximum physics lateness | **1.204 ms** |
| Exact final p95 physics lateness | 0.066 ms |
| Final world/wall drift | 0.073 ms |
| Realtime-valid / driving completion | **yes / no** |
| Model charge | $0.088287486 |

The clock stayed comfortably within its limits while Jev drove, so this screen
can inform the next driving investigation. It does not demonstrate a three-lap
model completion, eight-of-ten qualification, or an improvement over earlier
Jev runs: hosting, language and telemetry differ across some earlier screens.
The large local clock stalls no longer confound this particular trajectory.

### Evidence and cleanup

The free archive, individual recordings, hashes, logs, model archive and budget
transfer evidence are saved under `artifacts/remote-clock-v1/`. After every
clock stopped, all five recordings passed independent replay: **30,615 samples**,
826,949 Python comparisons, 4,649,238 native Rust replay comparisons, and
83,304 recording-invariant checks. Maximum numeric difference was 2.27e-13.
Ticks, command/acknowledgement ordering, stale-observation rejection, rescues,
timing recomputation and source/GCP-binary identity checks passed. The native
offline replay ran on ARM64 locally, with its different binary explicitly
labelled; it was not another timed GCP trial.

The persistent
model ledger is **$0.914245672 of $10**, with no pending reservations.
The VM was deleted after collection, along with its boot disk, and its temporary
local SSH private key was removed. Independent API lookups confirmed both VM
and boot disk absent. Provisioning-to-deletion took about 14.56
minutes: roughly **$0.036 compute**, plus small disk/IP charges, below the
authorized $1 infrastructure budget. This is an estimate, not a final invoice.
Compute Engine remains enabled in the project.
