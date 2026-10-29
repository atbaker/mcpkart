# Goal-only wheel-local road geometry comparison

The four-race study is **closed**. Added road heading and edge clearances did
**not** demonstrate better recovery: **0/2 geometry races and 0/2 baselines
earned a gate before rescue**. All four eventually finished all 120 gates
within the useful-finish limit, with assistance; none was clean. This small
pilot does not establish that the facts are harmful or explain the failure.

## Actual results

| Run | Facts | Finish | Rescues | Grass | First gate before rescue |
| --- | --- | --- | --- | --- | --- |
| 1 | Minimal | 89.30 s | 1 | 3.00 s | No |
| 2 | Road geometry | 95.55 s | 2 | 6.00 s | No |
| 3 | Road geometry | 89.57 s | 1 | 3.00 s | No |
| 4 | Minimal | 90.60 s | 1 | 3.00 s | No |

The paired geometry-minus-minimal time differences were +6.25 s and −1.03 s;
rescue differences were +1 and zero. There is no consistent improvement in
elapsed time, rescues or the predeclared primary endpoint. Median finish times
were 89.95 s minimal and 92.56 s geometry. Motion facts were disabled in both
arms. No physics, track, action, goal-rule or pedal-question change was made.

## Initial recovery timeline

| Run | First off-road sample | First rescue | First forward-preview query | First gate credit |
| --- | --- | --- | --- | --- |
| 1 minimal | 4.00 s | 6.98 s | 2.12 s | 8.40 s |
| 2 geometry | 4.23 s | 7.22 s | 7.23 s | 11.35 s |
| 3 geometry | 3.55 s | 6.53 s | 0.95 s | 8.22 s |
| 4 minimal | 3.92 s | 6.90 s | 6.98 s | 8.93 s |

A forward preview alone does not count as successful recovery. Runs 1 and 3
obtained it before rescue, yet neither earned a gate beforehand. Every run
selected `hard_right_accelerate` on its first actual request. All four started
from the same raw stationary observation. Removing only the geometry group
restores the exact baseline questions on both matched initial snapshots.

## Latency and cost of the extra facts

| Run | API p50 | API p95 | Maximum | Replies ≥1 s | Median input tokens |
| --- | --- | --- | --- | --- | --- |
| 1 minimal | 215 ms | 354 ms | 1,575 ms | 2 | 1,573 |
| 2 geometry | 216 ms | 330 ms | 2,197 ms | 4 | 1,677 |
| 3 geometry | 201 ms | 264 ms | 2,194 ms | 1 | 1,677 |
| 4 minimal | 217 ms | 293 ms | 1,190 ms | 1 | 1,573 |

Across 1,425 replies: p50 212 ms, p95 310 ms, p99 553 ms, max 2,197 ms.
Geometry added roughly 104 median input tokens per request (6.6%). Extra facts
could affect model choices and latency; this cohort cannot separate those effects
or identify which individual field matters.

The first geometry run's 2.197 s reply began at 0.68 s while the previous input
was `hard_left_accelerate`; the newly returned choice was `hard_right_accelerate`.
It later had a 1.719 s reply at observation 40.42 s; its second off-road interval
began at 42.53 s and ended in rescue at 45.52 s. This sequence is recorded, not
proof of latency causality. Another long reply began while already off-road.

The second geometry run's sole ≥1 s reply began at 80.57 s, long after initial
rescue at 6.53 s. The final baseline's sole such reply began at 7.48 s, also
after rescue at 6.90 s. Those initial failures did not require a ≥1 s reply.
No saved action or response was retimed to assert a counterfactual finish.

## Exact factual change

The goal-only option `include_wheel_road_frame=True` adds only
`wheel_facts.road_frame`. At the initial pose it contains:

```json
{
  "road_minus_kart_heading_rad": -2.16421,
  "left_edge_clearance_m": 22.0,
  "right_edge_clearance_m": 2.0,
  "units": "road_minus_kart_heading_rad: current road tangent minus kart heading in radians; positive means the road tangent is left of the kart nose. Edge clearances are metres; negative is outside that edge."
}
```

Heading is copied from raw `track.heading_error`; edge values equal the current
pedal road measurements. There is no target, prediction, risk predicate,
threshold, worked example or suggested input. Both goal-rule strings, full
pedal question, menus, inverse, empty shared state and native actions remain
exact on a matched snapshot. The actual first geometry reply selected wheel
`hard_right` and pedal `accelerate`, yielding the unchanged native input above.
[Actual requests and replies](0075-goal-only-wheel-road-geometry-responses.json)
retain real wire payloads, identities, usage, application status and source hashes.

Projection, validation, question construction, client and recorded driver carry
the new flag. It defaults false and requires goal mode. Missing/nonfinite/boolean/
string raw measurements, inconsistent edge values, altered units and extra
advisory fields are rejected before budget reservation or POST. Existing motion
and policy profiles retain their exact old questions; the public CLI is unchanged.
The full game engine, handling and defaults remain unchanged.

## Qualification and execution

**534 tests passed, three optional Rust skips; Ruff passed.** The initial test
fixture tried a forbidden off-road start; it was corrected to move the running
kart outside after a legal start, without changing simulation rules. All
8,237 previous question sets matched their original facts and questions exactly,
including the old motion runs. On every saved observation the new treatment
added only the road-frame group and preserved goal rules, menus and the entire
pedal question. All three earlier proposed examples matched the implementation.
All 34 new mocked native checks passed (15 controls plus prior stopped/passed-gate
poses for both profiles); no paid native probe was made.

Four fresh exact-interface real-MCP free controls used 200 ms mocked replies
and the unchanged feasibility guide, which was never sent to Jev:

| Entry | Profile | Time | Rescues | Grass |
| --- | --- | --- | --- | --- |
| 0 | Minimal | 108.07 s | 0 | 2.93 s |
| 1 | Geometry | 108.25 s | 0 | 2.93 s |
| 2 | Geometry | 107.88 s | 0 | 2.93 s |
| 3 | Minimal | 107.75 s | 0 | 2.93 s |

Each passed useful-finish/zero-rescue qualification and full replay. Their
1,950 queries and 25,921 saved physics frames reconstructed exactly without
changing the shared ledger. They establish feasibility, not Jev performance.
The complete 0072 engine clock gate was reused and reverified on unchanged
core, boot and server; new controller hashes were bound separately. It was not
rerun. A transient Cloud execution disconnect occurred before preflight and any
paid use; after recovery the same runtime gate and untouched budget verified.

Root launched one paid race per explicit process, observed each actual exit
zero, confirmed it and fully audited before the next admission. All **1,425
actual queries and 21,905 saved physics frames** reconstructed exactly, including
raw native replies, identities, facts/questions, applied controls, timing,
runtime and complete ledger transitions. No request error, invalid domain stop,
retry, replacement, host control or new uncertainty occurred.

The fixed order, stationary recovery201 pose (−10 m/+124°), 24 m stadium,
Python process/asyncio 60 Hz engine, 12 m/s ceiling, .12 rad wheel, three laps,
120 finite ordered gates and three-second rescue were registered before paid
outcomes. Jev resolved to `typesafe/jev-1.14-20261014` via TypeSafe. Per race:
800-decision bound, 3x reference deadline (reference 107.9833333333 s), 5 s HTTP
timeout, one POST in flight and full reservations. A 90-minute paid window
was frozen after qualification, with 1,000-request/5-million-token/15-minute
admission floors; it closed early after exactly the four entries.

## Findings and spending

This factual bundle did not solve the initial recovery problem. Keep it as an
explicit experimental option rather than promoting it as a proven improvement.
The result narrows our next investigation: additional state alone has not made
this start reliable. No further model, seed, prompt tuning or paid race is
admitted by this closed study.

Added **1,425 requests, 2,453,676 charged tokens and $0.097304718**. Final ledger:
**79,634 requests, 282,185,152 tokens and $9.149239028003063**, pending empty,
all 70 uncertainties retained. Caps stay **$10 / 100,000 requests / 500 million
tokens**. No charge, reservation or uncertainty was reset or refunded.

- [Prospective registration and qualification](0075-goal-only-wheel-road-geometry-registration.json)
- [Actual race summary](0075-goal-only-wheel-road-geometry-summary.json)
- [Primary endpoints and paired differences](0075-goal-only-wheel-road-geometry-outcomes.json)
- [Recovery/latency analysis](0075-goal-only-wheel-road-geometry-analysis.json)
- [Actual native request/response examples](0075-goal-only-wheel-road-geometry-responses.json)
- [Archived original proposal](0075-wheel-road-geometry-proposal.md)

Raw evidence, frozen source/helpers, actual-exit confirmations, audits and
plot provenance remain under ignored `artifacts/jev-goal-wheel-road-geometry-v1/`.
`wheel-road-geometry-results.png` and `.svg` plot actual saved trajectories
with rescue jumps omitted and rescue positions marked. A metadata-only export
correction renamed the legacy `motion_index` key to `geometry_index`; original
helper output and hashes are preserved, with no outcome or numerical change.
There is no active paid window.
