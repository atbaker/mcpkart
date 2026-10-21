# Applying the bearing policy from a smaller factual state

Status: complete, October 20, 2026. Final audit and separate collection-provenance
verification passed. The fixed factual projection
scored 30/30 exact native pairs versus 25/30 from full state, meeting every
registered gate. This motivates fresh broader native validation, not live
admission or promotion. The original prospective registration follows, with
an immutable copy retained under `artifacts/jev-policy-facts-v1/prospective-design.md`.

The independently audited [0033 bridge](0033-native-policy-bridge.md) failed
its driving gate. Both static and driving framing selected 26/30 exact native
pairs and 30/30 pedals. Driving wheel scores were 5/6 straight, 9/12 moderate
and 12/12 full; the paired framing contrast had one gain and one loss. The
27/30 pair, 6/6 straight and 11/12 moderate requirements were not met. No live
race was admitted. Preserve that outcome and its failed gate.

This comparison asks whether Jev applies the same supplied bearing policy more
reliably when the state contains the facts needed by that policy and its domain,
instead of the full driving observation. It is a static diagnostic. Removing
motion, control, progress and recovery facts changes the information available;
any gain does not identify an internal distraction or attention mechanism, or
establish that the smaller state is suitable for general driving.

## Fixed policy and exact driving questions

Keep Python physics, the 24 m stadium, 12 m/s ceiling, 0.12 rad maximum wheel,
three laps and three-second rescue unchanged. Preserve the joint `damped`
baseline and application defaults. No controls are applied and no physics
advances during paid collection.

Copy the 0032/0033 bearing `policy.py` byte-for-byte. The canonical current
15 m point bearing remains `round(degrees(atan2(y,x)),4)` from the same
three-decimal preview x/y facts. Its thresholds -22, -7, +7 and +22 degrees
select the five native wheel angles, with boundary ties choosing the smaller
absolute angle. Keep the complete pedal guard and speed-below-2 acceleration
priority unchanged. These are supplied engineering rules, not optimal controls
or a rewrite of the earlier pursuit formula.

Both arms use the **exact 0033 driving questions**: the same prefix, common
definitions, component tasks, criterion-local eligibility clauses, physical
native descriptions, IDs and Cartesian inverse. The prefix remains
`"DRIVING POLICY. Choose the next native input by executing the supplied policy exactly. "`,
including its trailing space. No `damped` guide or explanation is added.
The only designed arm difference is a fixed state projection.

## One fixed factual projection

Construct `full` from the complete current `road_navigation` observation plus
the same current road-frame facts and canonical
`road.preview_15m_bearing_deg` used in 0033. Construct `facts` only by
projecting that already-complete state. Retain exactly these paths:

- Top-level `units`, with its original complete string unchanged.
- `kart.speed_m_s`.
- `road.on_road`, `road.offset_m`, `road.left_edge_clearance_m`,
  `road.right_edge_clearance_m` and `road.preview_15m_bearing_deg`.
- `road.preview_columns`, restricted to the original first three entries:
  `ahead_m`, `ego_x_m`, `ego_y_m`.
- `road.preview`, restricted to the unique ahead-15 row and that row's first
  three original values, in the same order.
- `current_road_frame.velocity_left_m_s` and the original complete
  `current_road_frame.units` string, unchanged.
- `next_gate.known` and `next_gate.signed_plane_m`.

Omit every other field, including handling, held control, actual wheel, yaw,
other pose/velocity facts, time/tick, progress, rescue, and all other road rows
and columns. Do not rename retained hierarchy paths, rewrite unit strings,
recalculate retained values, add fields or substitute descriptions. This is a
key, row and column projection of current facts. The remaining units strings
retain their original conventions even where other described fields have
been omitted. The physical action menus are unchanged and remain tied to the
fixed original handling contract; dropping handling from state does not change
the actual controls or their question descriptions.

All retained scalar leaves, table cells and unit strings must have exactly the
same JSON representation as their full-state source. Every projected key must
be on this whitelist, every required path must be present, and the 15 m row
must remain unique. No evaluated guard B, steering angle, eligible branch,
wheel target, expected answer or recommendation enters either payload.
The supplied bearing is the same factual geometric angle in both arms.

The two retained next-gate fields preserve the policy's label/admission domain.
Independently verify that the unchanged policy returns the same support status
and exact label on full and projected states. Supported cases require finite
forward 15 m coordinates, finite positive squared range and no known positive
uncredited gate plane. Reject unsupported cases without inventing recovery
labels. No scoring or projection code may choose paid controls.

This is distinct from [0022's full/raw comparison](0022-observation-context.md).
That study asked Jev to execute pursuit arithmetic from full telemetry versus
isolated raw coordinates and changed answer-menu representations. Here the
questions and native physical choices are identical, both states already
contain the same factual bearing, and neither arm needs that pursuit
calculation. A gain concerns this fixed factual projection and supplied policy.

## Fresh bank and ordered collection

Generate thirty fresh synthetic current states in fifteen reflected pairs.
All fifteen prescribed native wheel/pedal targets occur exactly twice, and
each held native input occurs twice with no complete target copy. Balance
six straight, twelve moderate and twelve full wheel labels, with ten cases per
pedal. Require at least two degrees from every bearing threshold. Retain the
prior pedal/rest coverage and predicate margins: two stationary near-off-road
acceleration cases, four slow outward acceleration cases, four fast cases
without the guard, ten guarded coast cases and ten guarded brake cases.

Vary actual wheel, yaw and motion in the full observations. These factual
variations are omitted by the fixed projection, not altered or counterfactually
replaced. Stationary velocity angles in the full state must be null. All
rounded 15 m x/y pairs must be distinct and absent from earlier static banks
and demonstrations. Generate geometry using declared coverage constraints,
never model answers. Reflections and synthetic transients are correlated
constructed cases rather than recorded driving or recovery episodes.

Collect **60 calls maximum**: thirty cases x full/facts, one presentation
each. Shuffle case units with seed `2026102034`. At shuffled index j, alternate
the first arm using j%2 and reverse both wheel and pedal menus using j//2%2.
Match menu order within each case. Each arm occupies each request position
fifteen times; the four first-arm/order cells contain seven or eight units.

There is no format gate or correctness stop. Retain all valid planned responses
regardless of correctness. Technical, identity, uncertain-accounting, budget
or deadline failures stop admission, preserving every attempt and unrun entry.
Use one paid writer, one request in flight, zero retries, no provider fallback
and the pinned dated Jev model at TypeSafe.

## Gate, interpretation and resource boundary

The `facts` arm must meet every descriptive requirement:

- At least 27/30 exact native pairs correct.
- Wheel agreement 6/6 straight, at least 11/12 moderate and 11/12 full.
- At least 9/10 correct in each pedal class.
- Zero BRAKE selections when speed is below 2 m/s.
- At least three net additional correct pairs over the concurrent full arm.
- Complete collection, strictly typed atomic component answers, exact native
  inverse mapping, zero endpoint/accounting errors and passing independent audit.

Report component and pair agreement, magnitude, pedal class, signed direction,
paired gains/losses, chosen-input distributions and source-case coverage.
Retain the complete full-state case provenance even though the smaller payload
omits those fields. One presentation supplies no within-arm repeatability
estimate. A strong full arm is reported separately without claiming a projection
gain.

Passing can motivate only a separately frozen fresh native bridge before any
live use. That bridge must make its proposed live information contract explicit;
this diagnostic does not silently establish adequacy of omitted motion,
progress or recovery facts. No live race, qualification or promotion follows
automatically. The failed 0033 gate remains a failed gate.

The completed 0033 boundary is **61,279 requests, $7.561810875999882 and
244,410,246 charged tokens**, with 69 historical uncertain requests and no
pending reservations. Preserve all history and the shared **75,000 requests /
$10 / 250-million-token** caps. Each call retains the conservative
**16,384-input + 235,929-output = 252,313-token** reservation. The session
admission deadline remains **06:17:26 UTC**.

The policy is unchanged, so bind the existing verified free-policy evidence
through an origin manifest rather than tuning or rerunning old audit CLIs
against an advanced ledger. Before paid admission, freeze exact questions,
projection whitelist, bank, origin references, order, route, source and helper
hashes. Actual-wire local mocks must verify full/projected payloads, unchanged
retained JSON leaves, equal policy labels, inherited production decoding and
accounting, and zero real model calls or shared-ledger changes. Require an
immutable passing independent preflight and timestamped root authorization.
Final audit follows writer termination and reconciles every saved response and
ledger transition. Keep raw evidence ignored and preserve exact versioned
prompts and audited result summaries.

## Completed observations

All **sixty planned calls** completed, with zero endpoint/accounting errors,
no retries or replacements and no unrun entries. Every valid answer was
retained. Both arms used the exact frozen 0033 driving questions, unchanged
0032 bearing policy, component menus and atomic native inverse. The only
registered difference was the fixed factual state projection. All retained
leaves and unit strings were copied unchanged, with identical policy support
and labels; neither arm received an evaluated guard, target or eligibility
flag. No paid controls were applied and no physics advanced.

| Measure | Full state | Fixed facts projection |
|---|---:|---:|
| Exact native pair | 25/30 | 30/30 |
| Wheel component | 25/30 | 30/30 |
| Straight wheel | 3/6 | 6/6 |
| Moderate wheel | 10/12 | 12/12 |
| Full wheel | 12/12 | 12/12 |
| ACCELERATE pedal | 10/10 | 10/10 |
| COAST pedal | 10/10 | 10/10 |
| BRAKE pedal | 10/10 | 10/10 |
| BRAKE chosen below 2 m/s | 0 | 0 |

The facts arm produced **five paired gains and no losses**. Twenty-five states
were correct in both arms, and no state was wrong in both. All five gains were
wheel corrections: three straight and two moderate targets. Every pedal was
correct in both contexts. The facts arm met every overall, wheel, pedal,
low-speed-brake and paired-gain requirement.

This supports execution of the supplied bearing policy from the fixed factual
projection on this fresh bank. It does not identify an internal distraction or
attention mechanism: dropping other fields changes available information as
well as serialization. The factual bearing is still a geometric observation,
not an encoded wheel command. No field selection, policy, question, threshold
or rounding convention was tuned after observing these responses.

A separately frozen **fresh broader native validation** is required before
any live consideration. The reduced state omits facts that could matter to
general driving and recovery; this perfect static score does not establish
that those capabilities are preserved. Reflected states, components and paired
contexts are related observations, with one presentation per state and no
within-arm repeatability estimate. Retain joint `damped` and unchanged
application defaults. No live race is admitted and no preset is promoted.

## Validation and accounting

The final audit passed with **`complete=true` and no errors or warnings**.
It independently reconstructed all thirty states and labels, verified the
fixed projection whitelist and exact retained-leaf copies, checked unchanged
questions, policy support, labels and native inverse, and reconciled raw typed
wheel/pedal answers, order and every budget transition. Source inheritance and
local wire/error mocks passed before admission. Production source, handling
and physics remained unchanged.

The frozen origin manifest checked thirty-one evidence files, with the policy
copy exact. The audit did not run an old frozen CLI against a later ledger.
Inherited free host-policy evidence remains nominal tracking only: no complete
free race triggered the pedal guard, so edge braking, coasting and recovery
remain physically unvalidated. Those free runs are not Jev attempts.
Separate collection-provenance verification passed all **47 checks**, including
the immutable preflight/authorization chronology, all sixty wire payloads, raw
typed native pairs, source identity, writer and the entire ledger chain. It
confirmed exact copied current leaves and table cells, identical support and
policy labels, and question bytes identical to the frozen 0033 driving origin.
Root tool chunk/session identifiers were checked against preserved execution
confirmation rather than queried independently from tool infrastructure; actual
writer and ledger records were independently verified.

Root authorization at **03:32:12.637275 UTC** preceded the single writer's
**03:32:17.635772 UTC** start. Its session was
`520c36b333e4412b9e6bd1b55930bdf2`, PID 39494, with explicit collection enabled.
The completion record contains all sixty calls, and root confirmed exit zero.
No fallback, retry, cap or conservative reservation was relaxed.

The screen used **sixty requests, $0.006046236000003979 and 149,705 charged tokens**.
Its saved audited end boundary is **61,339 requests, $7.567857111999886 and
244,559,951 charged tokens**, with 69 historical uncertain charges unchanged
and pending empty. This report uses saved evidence and does not rerun an
audit against a later ledger.

The [machine-readable summary](0034-results-summary.json) retains the frozen
protocol and completed evidence. The exact [prompt archive](0034-policy-facts-prompts.json)
remains unchanged.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `d33ad23e345e3a8dac09a4293ede866dc6b726cfc9fb1d8abd3d2bcad56f764b` |
| Exact prompt archive | `0fcae7cec4218702c107f563521203eae583acfd272981753dea71abe279a046` |
| Final audit | `c6718533f30b2c6e069bff9343ac4e87211a4665d02c337c02c0116d512e811a` |
| Audited report summary | `096ff594e34ce42f39ecd98e18abb6311abacf67d263e8eab28e046c32ab4a25` |
| Source-inheritance proof | `ece1e0b6d84170ac16be0e45f94ca78ca1e494fd5562cbbf0a8e75cd2387f568` |
| Frozen origin manifest | `c3434c69b3794b5100afbf3f3182a3e3b6c1c8b592b621664bc3c025ad8dfa87` |
| Collection provenance | `370c673d56d2123d6578a1faf7713f31287e5da4d7cf12a661bc502267fae2de` |

Source remains `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
