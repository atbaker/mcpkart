# Placing fixed-policy clauses beside their criteria

Status: complete, October 20, 2026. Final audit and separate collection-provenance
verification passed. Shared rules scored 15/30 exact
native pairs; criterion-local rules scored 12/30. Both arms selected every pedal
correctly, but the wheel and pair requirements failed. No candidate qualified.
The original prospective design follows; its immutable copy is retained under
`artifacts/jev-criterion-policy-v1/prospective-design.md`.

The preceding 0030 diagnostic ended after seven of eight prescribed-format
controls were correct. Its registered gate withheld all forecasts, so it
produced no question-name forecast comparison. Retain that stop and its
unrun entries. The next comparison changes the placement of a complete supplied
control policy: can the model execute it more reliably when each eligibility
clause appears beside the criterion it governs?

## One fixed policy in both arms

Both arms ask for the same prescribed mathematical policy, not an optimal
driving input. Neither is the ordinary `damped` baseline, and neither includes
that guide. Keep Python physics, the 24 m stadium, 12 m/s speed ceiling,
0.12 rad maximum wheel angle, three laps and three-second rescue unchanged.

The wheel policy uses the actual `ego_x_m = x` and `ego_y_m = y` in the
15 m preview row. Its nominal target is
`delta = atan(3.6*y / (x*x + y*y))` radians. Quantize to the nearest of
`-0.12, -0.06, 0, +0.06, +0.12` radians, breaking an exact tie toward the
smaller absolute angle. Negative wheel angles mean right; positive mean left.

The prompts express that same quantizer as cross-multiplied eligibility
clauses. Define `D = x*x + y*y`, `z = 3.6*y`, `T3 = tan(0.03)` and
`T9 = tan(0.09)`. The five disjoint clauses are:

- Full right when `z < -T9*D`.
- Moderate right when `-T9*D <= z < -T3*D`.
- Straight when `-T3*D <= z <= T3*D`.
- Moderate left when `T3*D < z <= T9*D`.
- Full left when `z > T9*D`.

These definitions and fixed constants do not evaluate a current query. The
host supplies no computed `D`, `z`, ratio, angle, chosen magnitude or eligibility
flag in a paid payload. The frozen prompt archive will preserve the exact
constant representations and clause strings, and independent verification
must establish their agreement with the fixed policy on all screened cases.
The atan-nearest implementation uses a numerical distance tie tolerance of
`1e-12`; the equivalence claim therefore concerns the margin-protected bank,
not arbitrary floating-point points in the narrow threshold strips.

The pedal policy first releases braking at low speed: if speed is below
2 m/s, choose ACCELERATE. Otherwise guard `B` is true if `road.on_road` is false,
or either of these directional conditions holds: positive road offset with
left clearance at most 3 m and road-left velocity at least +0.5 m/s; negative
road offset with right clearance at most 3 m and road-left velocity at most
−0.5 m/s. At zero offset neither directional condition applies. When `B`
holds, choose BRAKE above 6 m/s and COAST from 2 through 6 m/s inclusive.
Otherwise choose ACCELERATE. Both arms share these exact definitions;
no evaluated `B` or prescribed pedal is submitted.

The supported label domain requires finite 15 m `x` and `y`, `x > 0`, finite
`D > 0`, and no known next gate with positive uncredited signed plane. Off-road
states remain supported when those conditions hold. Behind-target, nonfinite
and known positive uncredited-gate-plane states stop the free policy and are
excluded from this static bank. No recovery policy or invented answer is
supplied for those unsupported states.

## Free physical upper bound and its limits

Before model collection, the fixed policy was run as an offline controller,
with no network calls or budget charges. Under the declared 250 ms request
cadence and 250 ms control-set delay, starts 13 and 14 finished in 78.60 and
78.7333 seconds. Their first effective control-frame observation age was
266.7 ms. The zero-delay versions finished in 77.45 and 77.50 seconds. All
four completed 120 gates with zero grass and zero rescues; there was no tuning
between these cases.

Those races never triggered the pedal guard. They support nominal tracking
by this fixed policy under these declared delays, not the effectiveness of its
edge braking, coasting or off-road behaviour. Separate at-rest and slow-edge
fixtures verify the intended release/selection logic; they do not demonstrate
that braking can prevent a departure or recover progress. The exact policy,
free scripts and results must be frozen and independently reproduced before
paid admission. This offline upper bound never chooses a paid model's input.

## Fresh static bank and clause placement

Use thirty fresh, margin-separated synthetic poses in fifteen reflected pairs.
All fifteen native wheel × pedal target combinations occur exactly twice.
This yields six straight-wheel, twelve moderate-wheel and twelve full-wheel
labels, with ten cases for each pedal. Vary actual wheels, yaw and held input
to include conflicts with the prescribed target, plus rest and outward-motion
cases. Reflections are constructed static counterparts, not independent live
trajectories. These labels score policy compliance, not steering optimality.

Both arms receive the identical complete factual `road_navigation` state plus
current road-frame motion. Preserve the same four current quantities and unit
conventions used in earlier diagnostics. No computed denominator, ratio, angle,
guard value, target, expected answer or eligibility flag enters the state.
Ground-truth labels and proofs remain outside model payloads.

The two-question factored interface returns one wheel choice and one pedal
choice in one response. It maps their Cartesian pair exactly to one of the
existing fifteen native commands. Common definitions, component tasks,
component IDs, physical input descriptions and that inverse mapping remain
unchanged between arms:

- `shared`: wheel instructions list all five exact wheel eligibility clauses;
  pedal instructions list all three exact pedal eligibility clauses. Criteria
  retain their unchanged physical descriptions.
- `local`: remove those clause lists from the component instructions. Append
  each exact clause once beside its own criterion, after that criterion's
  unchanged physical description. Keep the common definitions and component
  task text identical.

This compares placement of the same fixed rules. It does not add a query-specific
recommendation, change the policy or let the host choose between controls.
Different serialization and reading order accompany placement, so a score
change does not identify a particular internal reasoning mechanism.

## Ordered collection and prespecified gate

Collect **60 paid calls**: thirty cases × shared/local placement, one
presentation each. Shuffle cases with seed `2026102031`. At shuffled case
index `j`, alternate first context using `j % 2` and reverse both wheel and
pedal menu orders using `j // 2 % 2`. Match both menu orders within each case.
The four first-context/order cells contain seven or eight units each; each
context occupies each request position fifteen times. Submitted insertion
order is not evidence of provider-internal ordering.

There is no format gate, performance stop or adaptive prompt change. Collect
all structurally valid planned responses regardless of correctness; technical,
identity, uncertain-accounting, hard-budget or deadline failures stop admission
and preserve every attempt and unrun entry. There are no retries or replacement
cases. During this screen no paid command is applied and no race advances.

Report wheel, pedal and exact native-pair agreement separately, with each
wheel magnitude, pedal class and signed direction. Report paired gains/losses,
chosen-input distributions and source-case coverage. The local arm must meet
all these descriptive requirements:

- At least **27/30 exact native pairs** correct.
- Wheel agreement **6/6 straight**, **at least 11/12 moderate** and
  **at least 11/12 full**.
- Pedal agreement **at least 9/10 in each pedal class**.
- **Zero BRAKE selections when speed is below 2 m/s**.
- At least **three net additional correct pairs out of thirty** over shared.
- Complete collection, zero endpoint/accounting errors and a passing
  independent audit.

A capable shared arm is reported separately without claiming a local-placement
gain. Both components within a response, reflected poses and paired arms are
related observations. One presentation per case/context supplies no within-arm
repeatability estimate. High scores establish execution of this supplied rule,
not general driving competence or a good recovery policy.

A passing local screen can only motivate a separately frozen fresh native
compatibility/physical-choice bridge, followed by a separately frozen live
comparison if budget and time permit. Neither is automatic, and no result
promotes a preset. Preserve the joint `damped` baseline and application defaults.

## Client inheritance, admission and evidence

Use an ignored artifact subclass overriding only the question property.
Production `decide`, atomic factored decoding, native inverse mapping, identity
validation, proxy-aware transport, error handling and accounting are inherited
unchanged. No response-key rewriting or host policy selection occurs. One
request returns the two components under one reservation and commit. Freeze
source-inheritance proof, helper identity checks and local wire/error mocks
before paid collection; all local checks must make zero model calls and leave
the ledger unchanged.

The completed 0030 boundary is **61,099 requests, $7.538698821999888 and
243,842,702 charged tokens**, with 69 historical uncertain requests and no
pending reservations. Preserve all historical charges and the shared
**75,000-request / $10 / 250-million-token** caps. Each request retains the
**16,384-input plus 235,929-output-token** conservative reservation. The
[authorized session](2026-10-20-six-hour-session.md) admission deadline remains
**06:17:26 UTC**. No limit or reservation is relaxed to finish this screen.

Use the pinned dated Jev model and TypeSafe provider, one paid writer and one
request in flight, zero automatic retries and no fallback. Current production
source remains
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
Before paid admission, freeze the exact policy, constants, free evidence,
fixture bank, prompts, component menus, order, route, source and helper hashes.
Retain an immutable passing independent preflight, timestamped root authorization
and actual writer identity preceding collection; bind every call and completion
record to that protocol and writer.

After collection terminates, the independent audit must reconstruct policy
labels from factual states, verify mathematical equivalence and unsupported
domain exclusions, reproduce free evidence, check exact clause relocation and
unchanged native mapping, validate raw component responses, and reconcile every
ledger transition. Preserve failures and unrun entries. Do not rerun older
audits against an advanced ledger. Keep raw evidence under ignored `artifacts/`,
freeze a separate exact prompt archive before collection, and publish results
only after the completed audit.

## Completed observations

All **60 planned calls** completed, with no endpoint or accounting errors,
no replacements and no unrun entries. The frozen rule, cases and prompts were
unchanged during collection. These are supplied-policy compliance scores;
no paid controls were applied and no race advanced.

| Measure | Shared instructions | Criterion-local rules |
|---|---:|---:|
| Exact native pair | 15/30 | 12/30 |
| Wheel component | 15/30 | 12/30 |
| Straight wheel | 3/6 | 2/6 |
| Moderate wheel | 2/12 | 2/12 |
| Full wheel | 10/12 | 8/12 |
| ACCELERATE pedal | 10/10 | 10/10 |
| COAST pedal | 10/10 | 10/10 |
| BRAKE pedal | 10/10 | 10/10 |
| BRAKE chosen below 2 m/s | 0 | 0 |

Local placement produced **one paired gain and four losses**, a net loss of
three correct pairs. Eleven pairs were correct in both arms and fourteen were
wrong in both. Because every pedal was correct, all pair errors were wheel
errors. Moderate-left targets were 0/6 in both arms. Both contexts selected
full wheel angles frequently: shared chose hard right eleven times and hard
left nine times; local chose them twelve and seven times respectively.

The local arm failed the exact-pair, every wheel-magnitude and paired-gain
requirements. Pedal-class and low-speed-brake requirements passed. The shared arm
also fell below each of those wheel thresholds.
This result does not support criterion-local placement for this policy, and
neither context qualifies for a native bridge or live trial. Retain joint
`damped` and unchanged application defaults.

The perfect pedal results establish execution of this supplied pedal rule on
this bank, including rest and slow cases. They do not establish successful
edge braking or recovery. All complete free host-policy races remained near
the centre and never triggered that guard. Those free runs are nominal tracking
evidence, not Jev driving attempts. Related reflected states, paired contexts
and a single presentation per state also limit generalization.

## Validation and retained correction

The final audit passed with **`complete=true` and no errors or warnings**.
It reconstructed all thirty policy labels, checked the raw wheel/pedal heads
and their atomic native inverse, verified exact clause relocation, and
reconciled every sequential budget transition. Independent free-policy review
reproduced **18,741 physics samples, 1,250 policy observations and sixteen
guard fixtures**. The source-inheritance proof and prospective local wire/error
mocks preceded paid admission. Production source and physics were unchanged.
Separate collection-provenance verification passed all **37 checks**, including
the immutable preflight/authorization chronology, source, exact payload and
order, raw typed component pairs, actual writer and complete ledger chain.
Root tool chunk/session identifiers were checked against the preserved execution
confirmation, rather than independently queried from tool infrastructure.
The actual writer and accounting records were independently verified.

Before freezing or any paid call, independent review found that the free
observer used an angle for zero velocity where the production renderer uses
`None`. The free observer was corrected, all free evidence was reproduced,
and the original scripts/evidence plus the initial failed check were retained.
Only ten undefined stationary-angle observations changed. The wheel and pedal
policies do not read that angle, and the physical commands and trajectories
remained identical. The paid case bank and final frozen evidence use the
correct production convention. This was a precollection formatter correction,
not a paid rerun or policy adjustment.

Root authorization at **03:10:21.295107 UTC** preceded the single writer's
**03:10:25.644022 UTC** start. Its session was
`99a507649d174bda80d85b999b8f190f`, PID 37195, with explicit collection enabled.
The completion record contains all sixty calls; root confirmed process exit
zero. Each request retained the existing conservative input/output reservation.

The screen used **60 requests, $0.007817039999998165 and 191,879 charged tokens**.
The saved audited end boundary is **61,159 requests, $7.546515861999886 and
244,034,581 charged tokens**, with 69 historical uncertain charges unchanged
and pending empty. No cap, retry policy or reservation was relaxed. This report
uses saved evidence and does not rerun an audit against a later ledger.

The [machine-readable summary](0031-results-summary.json) retains the frozen
protocol, audited results, writer, accounting and evidence hashes. The exact
[prompt archive](0031-criterion-policy-prompts.json) remains frozen unchanged.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `f836e2428fa283ac4a7e648ba46df057e62a06b9fef3f2da58b6cd51e7e98cb3` |
| Exact prompt archive | `3e10b2be4880f39b5ac8deb1797fe48c8222dec786cb2bd5de8f6053aeb32562` |
| Final audit | `b3a8f18396eb5d405925d45e48cd4e46cd5bd122f393d4793873fb09a785046a` |
| Audited report summary | `a25502787ecfe7e57d3d7ca1e1dfab83f9ba787f439aaba98df03e516cf1d9ce` |
| Source-inheritance proof | `007aa11e3e61e5e809a05c9444604d3001bb0d454819ab586fbb90a7c48d90af` |
| Independent free-policy review | `4fd04e5e42c7f41d7ce16ffab25f59867223ef0d151f1aa63521db195b915265` |
| Precollection formatter correction | `fe9fc5db57a926df261407c7c412dc9673a5aae92bab8707d18705b60522144b` |
| Collection provenance | `bff825a2e6966d5b0e5dcd4f8d56dfc79eec9d8f3c29baad107dd1004350fb40` |

Source remains `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
