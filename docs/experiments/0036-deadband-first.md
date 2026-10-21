# Checking the straight-wheel deadband first

Status: complete, October 20, 2026. Final audit and separate collection-provenance
verification passed. Baseline scored 27/30 exact
pairs and deadband-first wording 28/30; the candidate still failed its overall,
straight-wheel and perfect-pedal requirements. No new broader validation or
live race is admitted. The original prospective design follows, with an
immutable copy retained under `artifacts/jev-deadband-first-v1/prospective-design.md`.

The independently audited [0035 broader validation](0035-broader-native-validation.md)
passed its technical audit but failed native qualification. Natural observations
scored 28/30 exact pairs, below their 29/30 requirement, with 8/10 straight
wheels. Synthetic states scored 29/30 pairs but failed their required 6/6
straight-wheel score at 5/6. All sixty pedals and every non-straight target
were correct. The three
errors had small positive canonical bearings, +0.2522, +0.5731 and +1.3782
degrees: the supplied policy required straight, but replies chose left or full
left. This motivates a focused rule-order check; it does not establish why the
model made those errors. Preserve the failed 0035 gate and every response.
No live race follows that outcome.

## One wheel-only instruction addition

Keep Python physics, the 24 m stadium, 12 m/s ceiling, 0.12 rad wheel limit,
three laps and three-second rescue unchanged. Preserve the joint `damped`
baseline and application defaults. The fixed bearing policy is copied
byte-for-byte from 0032: canonical bearing
`round(degrees(atan2(y,x)),4)` from the same three-decimal preview coordinates,
thresholds -22, -7, +7 and +22 degrees with inward boundary ties, and the
unchanged pedal guard and low-speed acceleration priority.

Both arms receive the **exact 0034 `facts` state** with the same factual bearing
and the same next-gate support facts. Both use the existing 0033 driving prefix,
common definitions, component tasks, physical descriptions, criterion-local
eligibility clauses, native IDs and Cartesian inverse. Neither arm adds a guide,
example, query-specific label, selected branch, guard value or host recommendation.
No command is applied and no physics advances during paid collection.

- `baseline`: exact existing 0033 driving questions.
- `deadband`: append the following exact text after the existing `WHEEL_TASK`
  in the wheel instructions only:

```text
First read b=road.preview_15m_bearing_deg. If -7<=b<=+7 degrees, choose straight, including small positive or negative bearings. Only outside this interval select the eligible non-straight wheel using the existing rules.
```

Freeze the exact joining whitespace and complete question bytes before calls.
The entire pedal question, including its instructions and criteria, remains
byte-identical within each paired presentation. All common definitions and
wheel eligibility/physical criteria are unchanged. Local wire proofs must
establish that only this fixed addition changes the wheel question.

This is a wording package combining an explicit factual-field reference and
deadband-first decision order. An advantage cannot be assigned to either
element separately or treated as proof of an internal reasoning mechanism.
The mathematical policy and its labels do not change. The host never applies
the deadband to choose a paid input; Jev chooses both native components.

## Fresh focused cases with broad guard coverage

Generate thirty fresh synthetic current states in fifteen reflected pairs,
using fixed seed **2026102036**. Each of the fifteen prescribed native
wheel/pedal targets occurs twice, and every held native input also occurs
twice with no complete held-input copy of its target. Labels comprise six
straight, twelve moderate and twelve full wheels, with ten cases per pedal.

All **six straight targets must have 0.05 <= abs(theta) <= 1.5 degrees**,
with both signs and all pedal classes represented through their mirror pairs.
Use fresh bearings rather than reusing the three observed error values or
earlier states. Other wheel targets remain at least two degrees from every
threshold. Choose broad new track arcs, offsets, speeds and road-left motion
using geometry and fixed coverage constraints, never paid answers. Do not
return to small arc shifts of the older slot families.

Retain the broader synthetic guard/rest coverage from 0035. Acceleration has
two stopped off-road cases, four slow outward guard-true cases, two fast
near-edge but inward-motion guard-false cases and two fast farther-inside
guard-false cases. Coast includes two off-road inward-motion cases, where
surface status makes the guard true; the other coast and brake cases use
outward motion near an on-road edge. Preserve the existing protected predicate
margins and explicit synthetic-transient exceptions. Off-road states begin
with zero rescue elapsed time and no prior rescues; they do not demonstrate
physical recovery effectiveness.

All targets must be finite and forward, with finite positive squared range
and no known positive uncredited next-gate plane. Full observation primitives
must reconstruct exactly through production renderers, including null velocity
angles at rest. Require all thirty rounded 15 m x/y pairs to be distinct and
absent from earlier static banks and demonstrations. The complete full states
remain provenance; only their unchanged factual projection enters model state.
Actual-wheel/yaw variation is not variation in the submitted filtered state.

Keep the exact 0034 hierarchy and projection: original top-level units; kart
speed; road status, offset, both clearances, bearing, original first three
preview columns and first three cells of its sole 15 m row; road-left velocity
and original frame units; and next-gate known status and signed plane. Retained
JSON leaves/table cells must be unchanged. Independently verify that the
unchanged policy's support status and labels agree on full and projected states.
Expected answers and all proof stay outside paid payloads.

## Ordered collection and absolute gate

Collect **60 calls maximum**: thirty cases x baseline/deadband, one presentation
each. Shuffle case units with seed `2026102036`. At shuffled index j, alternate
the first context using j%2 and reverse both wheel and pedal menu orders using
j//2%2. Match menu orders within each pair. Each context occupies each request
position fifteen times; the four first-context/order cells contain seven or
eight units.

There is no format gate or correctness stop. Retain every valid planned
response regardless of score. Technical, identity, uncertain-accounting,
hard-budget or deadline failure stops admission and preserves all attempts and
unrun entries. Use the pinned dated Jev model at TypeSafe, one paid writer,
one request in flight, zero retries and no provider fallback.

The `deadband` candidate must meet every absolute requirement:

- At least **29/30 exact native pairs** correct.
- Wheel agreement **6/6 straight**, **at least 11/12 moderate and 11/12 full**.
- **30/30 pedals** correct.
- **Zero BRAKE selections below 2 m/s**.
- Complete collection, strictly typed atomic components, exact native inverse,
  zero endpoint/accounting errors and passing independent audit.

Paired gains and losses are descriptive rather than a separate qualification
threshold. Report them, including straight cases by sign and pedal, magnitude
and signed-direction scores, chosen-input distributions and source coverage.
A capable candidate can motivate fresh broader validation even if the concurrent
baseline also performs well; that outcome does not establish improvement.
Do not claim a gain without comparative gains, or general driving competence
from this focused synthetic bank. One presentation provides no within-arm
repeatability estimate, and reflected states remain related observations.

## Evidence, resource boundary and followup limit

The completed 0035 boundary is **61,399 requests, $7.572323853999888 and
244,672,055 charged tokens**, leaving **5,327,945 tokens** under the unchanged
250-million-token cap, with 69 historical uncertain requests and no pending
reservations. Preserve every charge and the shared **75,000 requests / $10 /
250-million-token** limits. Each request retains the conservative
**16,384-input + 235,929-output = 252,313-token** reservation. The authorized
session admission deadline remains **06:17:26 UTC**.

Before paid admission, freeze exact questions and the wheel-only contrast,
bank, generation constraints, origin references, menus, order, route, production
source and helper hashes. Require actual-wire mocks with zero real calls and
an unchanged shared ledger, exact state/projection and inherited-client proofs,
an immutable passing independent preflight and timestamped root authorization.
The final audit follows writer termination and reconciles every saved response
and ledger transition. Do not alter prior evidence or rerun old audit CLIs
against the advanced ledger.

A passing candidate can motivate only a **new fresh broader native validation
under the unchanged 0035 natural and synthetic thresholds**. That is a new
case distribution check, not a replacement or relaxation of the failed 0035
attempt. Passing this focused experiment does not admit a live race, qualify
the driver or promote a preset.

The environment rebooted onto a new boot beginning `f534`; the old serving
process is gone. The unchanged source passed 445 tests, with three optional
Rust skips, and Ruff at 03:48:39 UTC. Those checks do not qualify realtime
timing. Any eventual live attempt still requires a **complete fresh clock gate
on the new boot**, exact current server identity, applicable free control and
the existing five-million-token race-admission guard, in addition to all other
limits. Earlier-boot clock evidence cannot qualify the rebuilt environment.

## Completed wording comparison

All **sixty planned calls** completed with zero endpoint/accounting errors,
no unrun entries, retries or replacement trials. Every valid planned answer
was retained. The only registered arm change was one fixed wheel instruction;
the complete pedal question, factual state, policy, thresholds, native menus
and atomic inverse remained unchanged. No paid command was applied and no
physics advanced.

| Measure | Baseline | Deadband-first |
|---|---:|---:|
| Exact native pair | 27/30 | 28/30 |
| Wheel component | 28/30 | 29/30 |
| Straight wheel | 4/6 | 5/6 |
| Moderate wheel | 12/12 | 12/12 |
| Full wheel | 12/12 | 12/12 |
| ACCELERATE pedal | 9/10 | 9/10 |
| COAST pedal | 10/10 | 10/10 |
| BRAKE pedal | 10/10 | 10/10 |
| All pedals | 29/30 | 29/30 |
| BRAKE chosen below 2 m/s | 0/6 slow cases | 0/6 slow cases |

The candidate produced **two paired gains and one loss**, a net gain of one
correct pair. Twenty-six states were correct in both arms and one was wrong
in both. Paired gain was descriptive, not a gate requirement. The candidate
failed **29/30 exact pairs, 6/6 straight wheels and 30/30 pedals**; all other
predicates passed. No gate was relaxed and no state was rerun or replaced.

The changes and shared error were:

| Bearing | Expected | Baseline | Deadband-first |
|---|---|---|---|
| +0.1285° | `straight_coast` | `left_coast` | Correct |
| +0.5367° | `straight_brake` | `hard_left_brake` | Correct |
| +1.3084° | `straight_accelerate` | Correct | `hard_left_accelerate` |
| +15.1753° | `left_accelerate` | `left_brake` | `left_brake` |

The candidate's remaining wheel error was a stationary off-road state whose
small positive bearing lies inside the straight interval. The same pedal
error occurred in both arms on a fast near-right-edge state moving inward:
speed 11.197 m/s, right clearance 1.035 m and road-left velocity +7.4651 m/s.
It was currently on-road; the outward right-edge condition was false, so the
supplied policy required ACCELERATE. Both responses chose BRAKE instead.
The complete pedal question was unchanged. These observations do not establish
that the wheel text caused the pedal error or that historical pedal performance
changed because of it; the earlier banks differ.

This is a small descriptive wording gain with a **failed candidate gate**.
No new broader validation or live race is admitted and no preset is promoted.
Labels score the supplied rule, not optimal actions or race competence. The
fresh bank contains related reflected states and one presentation per state,
so neither repeatability nor a general small-angle mechanism is established.
Retain joint `damped` and unchanged application defaults.

## Validation, environment and accounting

The final audit passed with **`complete=true` and no errors or warnings**.
It reconstructed all thirty labels and copied factual states, verified the
exact wheel-only contrast and byte-identical pedal question, native component
menus/inverse, raw typed answers, balanced order and every ledger transition.
Source inheritance and prospective wire/error mocks passed before admission.
The origin manifest checked fifty-three evidence files and an exact policy
copy, without running an old frozen CLI against a later ledger. Production
source, handling and physics remained unchanged.

Inherited free rollout evidence remains nominal tracking only: no complete
free rollout triggered the guard, leaving physical recovery unvalidated.
This collection ran on boot `f534ef07-e837-401d-bf64-a0fe7c51e3d3`. The old
boot's clock qualification does not qualify this one. At this completed
collection boundary, a replacement server
(PID 1751, start ticks 85454) and new-boot timing helpers have been prepared,
but preparation is not a timing measurement. The full new-boot free clock
gate remains required before any paid actuation. These static calls applied
no controls and advanced no race.
Separate collection-provenance verification passed all **51 checks**, including
immutable preflight/authorization chronology, all sixty exact wire payloads and
raw typed answers, order, source, actual writer and the complete ledger chain.
It confirmed identical facts, byte-identical pedal questions, baseline questions
matching the frozen 0035 origin, and only the registered wheel-instruction
suffix changing. Root tool chunk/session identifiers were checked against
preserved execution confirmation rather than independently queried from tool
infrastructure; actual writer and ledger records were independently verified.

Root authorization at **03:54:17.510192 UTC** preceded the sole writer's
**03:54:22.445680 UTC** start. Its session was
`3407c5f6851946ad98fe84b9428720eb`, PID 2023, with explicit collection enabled.
All sixty calls are in the completion record and root confirmed process exit
zero. Conservative reservations, caps, identity checks and no-fallback/no-retry
policies were unchanged.

The comparison used **sixty requests, $0.004539024000000502 and 113,816 charged tokens**.
Its saved audited end boundary is **61,459 requests, $7.576862877999888 and
244,785,871 charged tokens**, with 69 historical uncertain charges unchanged
and pending empty. This report uses saved evidence and does not rerun an audit
against a later ledger.

The [machine-readable summary](0036-results-summary.json) retains the frozen
protocol and completed evidence. The exact [prompt archive](0036-deadband-first-prompts.json)
remains unchanged.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `7b1c863006de759bf764e3b1d6525008a2b4d02b85c287094f843ac2a5598cef` |
| Exact prompt archive | `c7b4e7f801dee666807e54c1808dc9ab24587680d73180b1d9e6992c53b976a7` |
| Final audit | `be0a59e705d3387dd06590839357e884ab4e135b9aee9a335654dd5862caaa4a` |
| Audited report summary | `98282d2607d2b328b7844954655348470d8151b0adf551b62a4f15f872371af7` |
| Source-inheritance proof | `9cd0a6caee0e6bc0e88cd3daa4c8814242768fc092c12c32172cda407a076abd` |
| Frozen origin manifest | `fe67693b2858418f29a96cf90fbef9da1f0b061a4e5668a16d2fb314865eb6c4` |
| Collection provenance | `433e01e35f09070b81f6b88ab24ccb6c76fd1b136a942321b7e4c7a8ed5c1dfa` |

Source remains `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
