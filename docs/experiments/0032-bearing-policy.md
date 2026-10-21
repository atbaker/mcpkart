# A fixed bearing policy with factual angle telemetry

Status: complete, October 20, 2026. Final audit and separate collection-provenance
verification passed. Factual bearing telemetry scored
28/30 exact native pairs versus 10/30 from the raw-coordinate state, meeting
all registered screening requirements. This motivates a separately frozen fresh
native bridge; it does not establish driving qualification or promote a preset.
The original prospective design follows, with an immutable copy retained under
`artifacts/jev-bearing-policy-v1/prospective-design.md`.

The independently audited [0031 comparison](0031-criterion-policy.md) produced
15/30 exact native pairs under shared rules and 12/30 under criterion-local
rules. Wheel agreement determined those pair scores: both arms chose all thirty
pedals correctly, including every pedal class and the low-speed release cases.
Criterion placement did not qualify that supplied pursuit policy for followup.
This experiment changes the wheel policy to a direct signed-bearing rule and
asks whether factual angle telemetry makes that new rule executable.

## One new policy and a free admission gate

Keep Python physics, the 24 m stadium, 12 m/s speed ceiling, 0.12 rad maximum
wheel, three laps and three-second rescue unchanged. Preserve the joint
`damped` baseline and application defaults. Neither static arm uses that guide.

From the actual 15 m preview row, let x be `ego_x_m`, y be `ego_y_m`, and
theta be `round(degrees(atan2(y,x)),4)`: the centreline point's bearing from
the kart nose. Use the same three-decimal preview x/y facts and this four-decimal
canonical bearing in labels, free policy and any supplied factual scalar. This
definition was fixed before the first free run. Positive means left. Apply
these disjoint fixed wheel rules:

- Full right when theta < -22 degrees.
- Moderate right when -22 <= theta < -7 degrees.
- Straight when -7 <= theta <= +7 degrees.
- Moderate left when +7 < theta <= +22 degrees.
- Full left when theta > +22 degrees.

Exact boundary ties choose the smaller absolute wheel angle. These thresholds
define a different engineering policy from 0031's pursuit equation. They are
not an algebraic rewrite, an optimal-control label or evidence of better
driving. The host may execute this policy only in free offline evidence; every
paid native input remains the model's own returned wheel/pedal pair.

Retain 0031's pedal rule exactly. Speed below 2 m/s requires ACCELERATE even
off-road. Otherwise B is true when currently off-road, or when positive road
offset, left clearance <=3 m and road-left velocity >=+0.5 m/s coincide, or
when negative offset, right clearance <=3 m and road-left velocity <=-0.5 m/s
coincide. At zero offset neither directional condition applies. B with speed
above 6 m/s requires BRAKE; B from 2 through 6 m/s requires COAST; no B
requires ACCELERATE. No evaluated B enters model state.

The supported domain remains finite x/y, x>0, finite positive x*x+y*y, and
no known uncredited next gate with positive signed plane. Off-road current
states are supported when those conditions hold. Behind-target, nonfinite and
missed-gate states stop free execution rather than receiving invented recovery
labels, and are excluded from the static bank.

Freeze the policy before free checks on seeds 15 and 16, each at zero and
250 ms control-set delay with a 250 ms request cadence. The delayed condition
evolves the old input for fifteen physics ticks before setting the new one;
the first affected frame ends at observation age 266.7 ms. Require **all four
runs to finish three laps and 120 gates, with zero grass, zero rescues and no
unsupported-domain stop**. Preserve every outcome. No threshold or distance
search, seed replacement or selective rerun is permitted. A failed requirement
ends this experiment free-only. A pass establishes nominal tracking under these
declared conditions; any unexercised edge/pedal or recovery branches remain
physically unvalidated.

## Fresh paired factual representation screen

Prepare thirty fresh synthetic snapshots in fifteen reflected pairs. Case
preparation may proceed alongside independent verification. The free gate must
pass before the paid protocol is frozen, and both free evidence and the complete
bank must pass independent verification before any paid admission. Each of
the fifteen prescribed native wheel/pedal combinations occurs exactly twice;
each native held input also occurs twice, with no complete held-input copy of
its target. Wheel labels comprise six straight, twelve moderate and twelve
full cases; each pedal has ten cases. Retain varied actual wheel, yaw and
motion facts, stopped near-off-road cases, low-speed outward cases, and the
speed/clearance/outward-velocity guard margins used in 0031. Stationary velocity
angles must be null, matching the production renderer. Require at least
**2 degrees from every wheel threshold**, exceeding the initial 0.5-degree
minimum proposal. Record actual minimum margins before freezing.

Before freezing or paid collection, the initial wording requiring independent
verification before case preparation was corrected to match this preparation
sequence. That wording overstated a dependency; no paid admission requirement
changed.

All rounded 15 m x/y pairs must be distinct and absent from the earlier static
banks and worked examples. State generation may use declared geometry and
coverage constraints, never model answers. Reflections and synthetic transients
are related constructed cases, not natural recorded recovery trajectories.
Labels score this supplied policy rather than optimal driving.

Both arms retain the identical complete `road_navigation` state plus current
road-frame motion and use identical criterion-local policy clauses, component
questions, physical descriptions, IDs and native Cartesian mapping:

- `xy`: the 15 m x/y facts are present; Jev evaluates theta from them.
- `bearing`: add `road.preview_15m_bearing_deg`, calculated from those same
  rounded x/y values with the canonical four-decimal formula. Retain the full
  x/y preview and all other state facts.

Use identical common instructions explaining the bearing definition, degree
units and positive-left sign. Read the scalar when present; otherwise compute
atan2 from the preview values and round to four decimal places. The added
field is the sole designed arm difference. Independently verify the canonical
calculation and protected margins on every case. Supply no query-specific
wheel, evaluated steering angle, eligibility flag, selected branch or
recommendation. A geometric point bearing is an observation; the
model still applies the fixed thresholds and chooses every native component.
This contrast concerns a factual representation and duplicated information;
it does not isolate an internal arithmetic or attention mechanism.

## Collection, gate and limits

Collect **60 calls maximum**: thirty cases x two arms, one presentation each.
Shuffle case units with seed 2026102032. At shuffled index j, alternate the
first arm using j%2 and reverse both component-menu orders using j//2%2;
match menu orders within a case. Record four first-arm/order cells of seven
or eight units, with each arm occupying each request position fifteen times.

There is no format gate or performance stop. Retain all valid planned answers
regardless of correctness. Stop on technical, identity, uncertain-accounting,
hard-budget or deadline failure, preserving every attempt and unrun entry.
Use one paid writer, one request in flight, no retries, no fallback and the
pinned dated Jev model at TypeSafe. No paid command is applied in this screen.

The `bearing` arm must meet every descriptive requirement:

- At least 27/30 exact native pairs correct.
- Wheel agreement 6/6 straight, at least 11/12 moderate and 11/12 full.
- At least 9/10 correct in each pedal class.
- Zero BRAKE selections when speed is below 2 m/s.
- At least three net additional correct pairs over `xy`.
- Complete collection, zero endpoint/accounting errors and a passing
  independent audit.

Report each component, magnitude, pedal class and signed direction; paired
gains/losses; chosen-input distributions; and source-case coverage. One
presentation supplies no within-arm repeatability estimate. A capable `xy`
arm is reported separately without claiming a factual-bearing gain. Passing
can motivate only a separately frozen fresh native compatibility/physical-choice
bridge; live use, qualification and promotion remain separate decisions.

The completed 0031 boundary is **61,159 requests, $7.546515861999886 and
244,034,581 charged tokens**, with 69 historical uncertain charges and no
pending reservations. Preserve the shared **75,000 requests / $10 /
250-million-token** caps and every historical charge. Each request retains
the conservative **16,384-input + 235,929-output = 252,313-token** reservation.
The authorized session admission deadline remains **06:17:26 UTC**.

Before any paid admission, freeze the exact policy, four-run free evidence,
fresh bank, prompts, arm-only state difference, menus, order, route, production
source and helper hashes. Require actual-wire local mocks, unchanged inherited
production decoding/accounting, an immutable passing independent preflight,
and timestamped root authorization binding the protocol, preflight and shared
ledger. Final independent audit follows writer termination and reconciles every
saved raw typed response and ledger transition. Keep raw evidence under ignored
`artifacts/`; preserve exact versioned prompt and audited result summaries.

## Completed observations

All **sixty planned calls** completed with no endpoint or accounting errors,
no replacements and no unrun entries. Policy, thresholds, canonical rounding,
cases and prompt strings remained frozen. No paid control was applied and
no race advanced.

| Measure | Raw coordinates (`xy`) | Added factual bearing |
|---|---:|---:|
| Exact native pair | 10/30 | 28/30 |
| Wheel component | 10/30 | 28/30 |
| Straight wheel | 3/6 | 6/6 |
| Moderate wheel | 0/12 | 11/12 |
| Full wheel | 7/12 | 11/12 |
| ACCELERATE pedal | 10/10 | 10/10 |
| COAST pedal | 10/10 | 10/10 |
| BRAKE pedal | 10/10 | 10/10 |
| BRAKE chosen below 2 m/s | 0 | 0 |

The bearing arm had **eighteen paired gains and no losses**, a net gain of
eighteen correct pairs. Ten states were correct in both arms and two were
wrong in both. Every pedal was correct in both contexts, so wheel agreement
determined pair agreement. The bearing arm met every frozen predicate,
including the overall, wheel-magnitude, pedal-class, low-speed and gain gates.

The two bearing-arm errors were both rightward targets. At −14.5107 degrees,
`right_brake` was answered `hard_right_brake`; at −34.9410 degrees,
`hard_right_accelerate` was answered `straight_accelerate`. Both were well
clear of a threshold, with margins of 7.4893 and 12.9410 degrees. They remain
in the results and are not rerun or replaced.

This is a clear gain in executing the **new supplied bearing policy** from a
factual scalar. The scalar describes a road point's angle; it is not an
encoded wheel command or an evaluated policy label. This policy differs from
0031's pursuit equation, so the result does not repair or establish equivalence
to that earlier formula. The four-decimal bearing convention was fixed before
the free checks and used consistently for labels, free execution and model
telemetry, with no tuning after outcomes.

The result motivates only a separately frozen **fresh native compatibility and
physical-choice bridge**. Reflected synthetic states, related component and
paired observations, and a single presentation per state limit generalization.
The policy's guard/recovery branches remain physically unvalidated: all four
free host-policy races tracked cleanly without ever triggering the guard.
Neither a clean Jev race nor reliable live latency tails have been established.
Retain the joint `damped` baseline and unchanged application defaults.

## Audit and accounting

The final audit passed with **`complete=true` and no errors or warnings**.
It independently reconstructed all thirty labels and canonical bearings,
verified the factual-scalar-only payload difference, raw typed component heads,
atomic native inverse, balanced order and every sequential budget transition.
The independent free review reproduced **18,731 physics samples, 1,250 policy
observations and sixteen guard fixtures**. All four free races completed 120
gates with zero grass, rescues or unsupported-domain stops. Those are free
host-policy tracking results, not paid model races or recovery evidence.
Starts 15 and 16 finished in 78.4500 and 78.5833 seconds at 250 ms
control-set delay; their zero-delay versions finished in 77.5000 and 77.5833
seconds. No free threshold, distance or seed search was performed.

Source inheritance and prospective wire/error mocks passed before collection;
production source and physics were unchanged. Separate collection-provenance
verification passed all **42 checks**, including immutable preflight and
authorization chronology, all sixty actual payloads, raw typed pairs, order,
writer and the full ledger chain. Every matched state pair differed only by
the canonical four-decimal bearing scalar; question bytes and menu orders
matched. Root tool chunk/session identifiers were checked against the preserved
execution confirmation rather than queried independently from tool infrastructure;
the actual writer and ledger records were independently verified.

Root authorization at **03:17:30.085884 UTC** preceded the single writer's
**03:17:35.503066 UTC** start. The writer session was
`92c82644baa648be8314ddfacca0bbf9`, PID 38188, with explicit collection enabled.
The completion record contains all sixty calls and root confirmed exit zero.
No retry, fallback, cap or conservative reservation was relaxed.

The screen used **sixty requests, $0.0076398419999987865 and 187,650 charged tokens**.
Its saved audited end boundary is **61,219 requests, $7.554155703999885 and
244,222,231 charged tokens**, with 69 historical uncertain charges unchanged
and pending empty. This report uses saved evidence only and does not rerun
an audit against a later ledger.

The [machine-readable summary](0032-results-summary.json) retains the frozen
protocol, audited results, writer, accounting and evidence hashes. The exact
[prompt archive](0032-bearing-policy-prompts.json) remains frozen unchanged.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `ea0352640a8ba2c04c8788f8202091f76e6d5079d8f1c7cf96627cd219096027` |
| Exact prompt archive | `399a6b4e2c9ea2e90a200754eea1b7e36834aac3f48266f8c26b385879d3cae4` |
| Final audit | `507f82dd0f440f8fc9f73c1e9aa848721139b2f0207f402928753a41c992a828` |
| Audited report summary | `8dbeed311e6892c3f073e027acfbf81fd988e314e80e4a3450e01e941f6ded30` |
| Source-inheritance proof | `26619eb8e66c3d05509f896d9eb71acc2ff92fb76fff394242f0ce6a844b1809` |
| Independent free-policy review | `a16ec5a8eaf5981178b2a535f10b22257837144eb585b3f4e689284dc250d1c0` |
| Collection provenance | `d7e28229d03369c60bbc945b6122cdc7e5f506da354aea0e05de6c70aacea634` |

Source remains `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
