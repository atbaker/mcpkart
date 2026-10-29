# Goal-only driving with current wheel motion facts

The four-race comparison is **closed**. All four Jev runs finished all 120 gates
within the useful-finish limit; one finished cleanly. Added wheel motion facts
produced a clean clockwise run, but **did not solve initial recovery**. Each
recovery arm needed rescue before its first forward-preview query or gate.
One run per arm per start, with unequal natural API delays, is insufficient to
attribute the clockwise difference to the facts or establish broad reliability.

The user authorized a **100,000-request cumulative ceiling** before collection.
Only that ledger field changed; the $10 and 500-million-token caps, charges,
reservations and 70 historical uncertainties were preserved. The
[prospective budget amendment](0073-budget-ceiling-amendment.json) records the
instruction, before/after ledgers and hashes. The preparation had proposed
78,000 without approval; the user instead explicitly approved 100,000.

## Actual Jev results

| Start | Facts | Time | Gates | Rescues | Grass | Replies ≥1 s |
| --- | --- | --- | --- | --- | --- | --- |
| Recovery 201 | Minimal | 90.28 s | 120/120 | 1 | 3.00 s | 3 |
| Recovery 201 | Motion added | 96.15 s | 120/120 | 1 | 3.00 s | 2 |
| Larger-error 202 clockwise | Motion added | 83.12 s | 120/120 | 0 | 0.00 s | 0 |
| Larger-error 202 clockwise | Minimal | 94.63 s | 120/120 | 3 | 9.00 s | 12 |

All four were useful finishes (at most twice their frozen reference); only
the clockwise motion run was clean (no grass or rescue). Motion was 5.87 s
slower in recovery and 11.52 s faster clockwise. The three assisted runs
entered the extended query domain, producing 26, 33 and 22 queries respectively;
the clean motion run produced none. Finishing after an extended query does
not demonstrate unassisted recovery.

Raw trajectories and latency are plotted in ignored
`artifacts/jev-goal-wheel-motion-v1/wheel-motion-results.png` and `.svg`, with
source hashes in `plot-manifest.json`. Every plotted position comes from the
saved physics trace. Rescue teleport segments are omitted; X marks the last
position before rescue and an open circle marks the respawn.

## Recovery and latency evidence

| Recovery arm | First grass sample | First rescue | First forward-preview query | First gate |
| --- | --- | --- | --- | --- |
| Minimal | 4.42 s | 7.40 s | 7.53 s | 9.15 s |
| Motion added | 5.48 s | 8.47 s | 8.67 s | 13.63 s |

Neither arm earned a gate before rescue. Both began from exactly the same
raw stationary observation, with preview bearing −90.3115°. Minimal selected
`hard_right_accelerate`; motion selected `hard_left_accelerate`. These are
actual native replies, not a reconstruction of what either model should do.

The clockwise motion run stayed on-road and first credited a gate at 1.47 s.
Minimal first credited a gate at 1.52 s and earned 76 gates before its first
rescue at 55.88 s; later rescues occurred at 75.52 s and 84.88 s.

API round trips across 1,304 replies: p50 227 ms, p95 362 ms, p99 1,112 ms,
maximum 1,700 ms; 17 replies were at least one second. The clockwise minimal
run had 12 such replies, while its motion counterpart had none. Its longest
reply began at 50.57 s; the first off-road sample was at 52.90 s. Some later
long replies began while already off-road. This temporal association cannot
separate model choices from latency, identify network versus inference/queue
time, or establish a counterfactual result with equal timing.

Recovery motion's 1.70 s reply began at 19.35 s, **after** its initial rescue;
the next query was still on-road. Minimal's 1.13 s initial reply held a stopped,
coasting kart. Long replies alone do not explain the initial recovery failures.

## Exact factual treatment

The control was the existing goal-only packet with `extended_domain=True`.
The treatment enabled `include_wheel_motion=True` in projection, client and
recorded driver, adding only `wheel_facts.motion`:

- `speed_m_s`: current speed copied from the raw snapshot.
- `steering_angle_rad`: actual front-wheel angle, not the held input target.
- `yaw_rate_rad_s`: current heading rate.
- `held_input`: the native input currently applied.
- Descriptive units and sign conventions.

No prediction, recommendation, action threshold or recovery advice was added.
Both goal rules, physical menus, native decoding, empty shared state and the
entire pedal question stayed exact on matched observations. Removing the
motion group restores the prior questions. Actual first snapshots matched
within both pairs, and this exact question equality was verified there too.
The bundle cannot identify which individual measurement matters. Defaults and
the public CLI retain their prior behavior; this option requires goal mode.

Median input tokens were 1,573 versus 1,690 in recovery and 1,574 versus 1,690
clockwise: roughly 117 extra tokens per motion request, about 7.4%. Recovery
pedal counts were accelerate/brake/coast 327/4/6 (minimal) and 333/3/7 (motion).
Clockwise counts were 304/9/5 and 306/0/0 respectively. Both questions were
selected by Jev in each POST; no host policy chose or altered paid controls.

[Actual request/response excerpts](0073-goal-only-wheel-motion-responses.json)
include all four first requests, the moving motion observations and each
run's longest reply when at least one second. They retain the real question
objects, native response, identity, usage, application status and source hashes.
The earlier [prepared examples](0073-goal-only-wheel-motion-prepared-prompts.json)
are separately labeled constructed requests on old observations, with no new
model replies.

## Fixed protocol and qualification

Entry order was minimal/recovery201, motion/recovery201, motion/larger202,
minimal/larger202. Recovery started stationary at −10 m offset/+124° heading;
clockwise at +6 m/+35°. Reference times were 107.9833 s and 78.6500 s.
Both arms used the same Python process/asyncio engine at 60 Hz, 24 m stadium
or mirror, 12 m/s ceiling, 0.12 rad wheel limit, three laps of 40 finite ordered
gates and three-second off-road rescue. Every start had zero progress and
zero injected steering or yaw state. Jev resolved to
`typesafe/jev-1.14-20261014` through TypeSafe.

One POST was in flight, timeout five seconds, with full route reservations.
Each race had an 800-decision bound and deadline three times its reference.
The 90-minute paid window began at 19:58:46.824782 UTC on October 21, 2026;
the study closed early after its four entries. Admission retained the
1,000-request, five-million-token and 15-minute floors. There were no paid
native probes, retries, replacements, extra seeds, latency injection,
response repairs, fallback controls or host progress repair.

Before spending: **509 tests passed, three optional Rust skips; Ruff passed**.
All 4,249 prior question sets remained exact; treatment isolation was verified
on those observations. All 34 native mocks passed. Four new exact-interface,
real-MCP controls with mocked 200 ms replies qualified both matched pairs:

| Entry | Facts/start | Time | Rescues | Grass |
| --- | --- | --- | --- | --- |
| 0 | Minimal/recovery | 108.13 s | 0 | 2.93 s |
| 1 | Motion/recovery | 107.80 s | 0 | 2.95 s |
| 2 | Motion/clockwise | 78.62 s | 0 | 0.00 s |
| 3 | Minimal/clockwise | 78.68 s | 0 | 0.00 s |

These are feasibility controls, not Jev results. Recovery allowed grass but
required zero rescues; clockwise required no grass or rescue. Their 1,669
queries and 22,398 saved physics frames replayed exactly without changing the
shared ledger. The complete 0072 engine clock gate was **reused and reverified**
on unchanged core, boot and server, with new controller hashes separately
bound; it was not rerun. [Preparation evidence](0073-goal-only-wheel-motion-preparation.json)
preserves the earlier checkpoint and original unapproved ceiling proposal.

The original free plan and helper bytes remain frozen as evidence. Before
any paid outcome, only the admission guard's two occurrences of `78000` were
replaced with `100000`, preserving its old file and hashes. The additive paid
release bound that exact diff to the original free qualification and the new
protocol. No controller, physics, prompt, factual projection or free guide
changed for the budget amendment.

Root launched one paid race per explicit process, observed actual exit zero,
then confirmed and fully audited it before admitting the next. All **1,304
actual queries and 21,855 saved physics frames** reconstructed exactly, including
raw/native identity, facts, questions, applied control sequence, accounting,
runtime and timing. No request errors, domain stops or new uncertainty occurred.

## Findings and spending

The clean clockwise motion result is promising, while initial recovery remains
unsolved. The comparable minimal run saw substantially more long replies.
This pilot supports testing factual observations further, but does not justify
claiming that motion facts reliably improve driving. A future registered
comparison should repeat matched arms and quantify latency exposure; this
closed study authorizes no additional model calls or prompt tuning.

Added **1,304 requests, 2,252,320 charged tokens and $0.089324550**. The final
ledger is **75,525 requests, 275,095,989 tokens, $8.868089768002191**, all
70 uncertainties retained and pending empty. Caps are **$10 / 100,000 requests /
500 million tokens**. No charge or uncertain reservation was refunded.

- [Machine-readable result](0073-goal-only-wheel-motion-summary.json)
- [Paired recovery/latency analysis](0073-goal-only-wheel-motion-analysis.json)
- [Actual requests and native responses](0073-goal-only-wheel-motion-responses.json)
- [Prospective ceiling-only amendment](0073-budget-ceiling-amendment.json)

Raw races, HTTP bodies, gate evidence, original frozen helpers, admissions,
actual-exit confirmations, full audits and plot provenance remain in ignored
`artifacts/jev-goal-wheel-motion-v1/`. No new paid window is active.
