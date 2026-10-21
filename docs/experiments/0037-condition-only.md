# Placing only eligibility conditions in the criteria

Status: complete, October 20, 2026. Final audit and separate collection-provenance
verification passed. Both arms scored 16/18 exact
native pairs; the candidate selected 17/18 wheels and 17/18 pedals, failing the
perfect-pilot gate. No broader validation or live race is admitted and no preset
is promoted. The original registration follows, with an immutable copy retained
under `artifacts/jev-condition-only-v1/prospective-design.md`.

The independently audited [0036 deadband-first test](0036-deadband-first.md)
failed its gate. Baseline scored 27/30 exact native pairs and the candidate
28/30, with two paired gains and one loss. Candidate wheel agreement was
29/30 but straight agreement remained 5/6; both arms selected 29/30 pedals.
The candidate's straight error was a stopped off-road case at +1.3084 degrees,
where it chose full left. Both arms also chose brake in a fast near-edge
inward-motion case whose policy guard was false and required acceleration.
Preserve those responses and the failed gate. No live race was admitted.

This pilot changes the placement of physical control descriptions. It asks
whether eligibility-only criteria improve compliance while preserving every
physical meaning elsewhere in the same component question. The experiment
tests a placement package, not an internal attention or reasoning mechanism.

## Fixed policy, facts and exact text relocation

Keep Python physics, the 24 m stadium, 12 m/s speed ceiling, 0.12 rad wheel
limit, three laps and three-second rescue unchanged. Preserve the joint
`damped` baseline and application defaults. The bearing `policy.py` remains
byte-identical to 0032, including canonical four-decimal point bearing,
thresholds -22/-7/+7/+22 degrees, inward ties, pedal guard and low-speed
acceleration priority.

Both arms receive the **exact 0034 `facts` projection**, including the same
factual bearing, original units and next-gate known status/signed plane. The
unchanged policy must return identical support status and labels on full and
projected observations. No evaluated guard, eligibility flag, branch, target
wheel, expected answer, example or recommendation enters the payload. Every
paid native choice remains Jev's own returned wheel/pedal pair; no control is
applied and no physics advances during this static pilot.

The baseline uses the exact 0036 deadband candidate questions. Preserve its
driving prefix, common definitions, wheel and pedal tasks, wheel-only deadband
addition, eligibility clauses, physical native descriptions, component IDs and
Cartesian inverse.

For the condition-only candidate, change both component questions as follows:

1. Each criterion value contains **only its unchanged eligibility clause**.
   Remove that criterion's physical description and the joining separator;
   do not reword the clause or change its ID.
2. Append each unchanged physical description exactly once to the end of its
   component instructions, under its original ID and in the same submitted
   order as that component's criteria. Construct the appended block exactly as:

```python
"\nPHYSICAL CONTROL DEFINITIONS:\n" + "\n".join(
    control_id + ": " + physical_description
    for control_id, physical_description in submitted_component_order
)
```

All pre-existing instruction bytes remain unchanged before the appended block.
In particular, the wheel keeps its complete 0036 deadband addition, and the
pedal keeps its original common definitions and task. Eligibility clauses stay
in the criteria and are not added to the definition list. Every physical
description appears once in that list, without a current-query evaluation.
Do not alter native meanings, controls, inverse mapping or response keys.

Local wire proofs must establish exact clause retention, exact physical-text
relocation, matching list/menu order, identical state and the absence of any
other question difference. Removing physical text from criteria and adding an
ID-labelled instruction list changes placement, reading order and question
structure together; a gain cannot identify one causal internal mechanism.

## Eighteen fresh cases covering every native target

Use fixed seed **2026102037** to generate nine fresh reflected pairs: one
pair for each wheel-magnitude x pedal combination. This yields six straight,
six moderate and six full wheel labels, with six cases per pedal. All fifteen
native targets appear: each of the three straight targets twice, and each
non-straight native target once. Match that coverage for held native inputs,
with no complete held-input copy of its target.

All six straight cases have fresh canonical **0.05 <= abs(theta) <= 1.5
degrees**, with both signs and every pedal represented. Other wheel targets
remain at least two degrees from every threshold. Use broad new track arcs,
offsets, speeds and road-left motion from the fixed geometry-only generator,
not small shifts of previous slots or paid answers.

Fix the three acceleration pairs to cover distinct policy branches:

- Straight acceleration: stopped off-road states.
- Moderate acceleration: slow outward states with the guard true and the
  speed-below-2 acceleration priority active.
- Full acceleration: fast near-edge inward-motion states with the guard false.

Include one off-road inward-motion coast pair, with its magnitude fixed in
the generator before freeze. The remaining coast and brake pairs exercise
on-road outward guards. Preserve protected predicate margins and explicit
synthetic-transient rules. Off-road states have zero rescue elapsed time and
no prior rescues; label compliance does not establish recovery effectiveness.

Require finite forward 15 m targets, finite positive squared range and no known
positive uncredited next-gate plane. Reconstruct full current observations
exactly through production renderers, including null velocity angles at rest.
Keep all eighteen rounded x/y pairs distinct and absent from prior static banks
and demonstrations. Full actual-wheel/yaw variations remain provenance because
the factual filter omits those fields; model-visible variation comes from
bearing, speed, surface, signed offset, clearances and road-left velocity.

This is a compact coverage pilot with one presentation per arm. It does not
estimate broad performance, natural driving robustness or within-arm stability.
Reflected states and paired arms are related observations.

## Ordered collection and perfect-score gate

Collect **36 calls maximum**: eighteen cases x baseline/condition-only framing.
Shuffle case units with seed `2026102037`. At shuffled index j, alternate the
first arm using j%2 and reverse both component menus using j//2%2. Match menu
order within each case, including the candidate's appended physical definitions.
Each arm occupies each request position nine times. The four first-arm/order
cells contain five, five, four and four units; normal/reversed menus therefore
cover ten/eight case units, rather than claiming exact equality.

There is no format gate or correctness stop. Retain every valid planned reply
regardless of score. Technical, identity, uncertain-accounting, hard-budget
or deadline failure stops admission and preserves every attempt and unrun entry.
Use the pinned dated Jev model at TypeSafe, one paid writer, one request in
flight, zero retries and no provider fallback.

The condition-only candidate must meet every requirement:

- **18/18 exact native pairs**, **18/18 wheels** and **18/18 pedals** correct.
- **Zero BRAKE selections below 2 m/s**.
- Complete collection, strictly typed atomic components, exact native inverse,
  zero endpoint/accounting errors and passing independent audit.

Report paired gains and losses descriptively, with component/magnitude/pedal
and signed-direction scores, each guard subtype, selected-input distributions
and source coverage. There is no separate comparative-gain admission threshold.
Passing capability without comparative gains does not establish improvement.
Do not claim an internal mechanism or general driver competence from this pilot.

## Resources, evidence and followup boundary

The completed 0036 boundary is **61,459 requests, $7.576862877999888 and
244,785,871 charged tokens**, leaving **5,214,129 tokens**, with 69 historical
uncertain requests and no pending reservations. Preserve all history and the
shared **75,000 requests / $10 / 250-million-token** limits. Retain the full
**16,384-input + 235,929-output = 252,313-token** reservation for every request.
The authorized session admission deadline remains **06:17:26 UTC**.

Before paid admission, freeze the exact relocation, questions, physical list
order, bank, generator, origin references, route, source, helpers and collection
order. Require actual-wire mocks with zero real calls and an unchanged shared
ledger, exact factual projection and label proofs, unchanged inherited
production decoding/accounting, immutable passing independent preflight and
timestamped root authorization. Final audit follows writer termination and
reconciles every response and ledger transition. Do not alter previous evidence
or rerun old audit CLIs against the advanced ledger.

A perfect passing pilot can motivate only a **new fresh sixty-case broader
native validation under unchanged 0035 thresholds**. It does not replace a
failed response, relax a previous gate, admit live use or promote a preset.
Do not promise a live race from a projected token estimate: read the actual
ledger after each phase, preserving the five-million-token race-admission
guard and all other resource/time conditions.

The new boot beginning `f534` invalidates earlier-boot clock qualification.
The complete fresh free clock gate is being run separately; this pilot does
not perform or qualify a timed race. Any eventual live attempt requires a
passing complete current-boot clock gate, exact serving-process identity,
applicable exact free control and all native-validation/admission requirements.

## Completed condition-only pilot

All **thirty-six planned calls** completed with no endpoint/accounting errors,
unrun entries, retries or replacements. Every valid planned answer was retained.
The eighteen fresh states form nine reflected pairs. Both arms kept the same
policy, exact selected factual inputs, eligibility clauses, native IDs and
atomic inverse. The candidate removed physical descriptions from criterion
values and placed those identical descriptions in component instruction lists,
matched to the submitted menu order. This was the complete registered placement
package; no rule or factual value was added or evaluated by the host. No paid
control was applied and no physics advanced.

| Measure | Baseline deadband questions | Condition-only criteria |
|---|---:|---:|
| Exact native pair | 16/18 | 16/18 |
| Wheel component | 16/18 | 17/18 |
| Straight wheel | 4/6 | 5/6 |
| Moderate wheel | 6/6 | 6/6 |
| Full wheel | 6/6 | 6/6 |
| ACCELERATE pedal | 6/6 | 5/6 |
| COAST pedal | 6/6 | 6/6 |
| BRAKE pedal | 6/6 | 6/6 |
| All pedals | 18/18 | 17/18 |
| BRAKE chosen below 2 m/s | 0/4 slow cases | 0/4 slow cases |

The candidate had **one paired gain and one loss**, with fifteen states correct
in both arms and one wrong in both. There was no net exact-pair gain. The
remaining outcomes were:

| Bearing | Expected | Baseline | Condition-only |
|---|---|---|---|
| −1.1383° | `straight_coast` | `hard_right_coast` | Correct |
| +1.1383° | `straight_coast` | `hard_left_coast` | `hard_left_coast` |
| +31.5406° | `hard_left_accelerate` | Correct | `hard_left_brake` |

The wheel gain on the negative small-bearing coast state was offset by a pedal
loss on a positive full-wheel, fast near-edge inward-motion state. That state's
policy guard was false and required ACCELERATE. The positive small-bearing
coast wheel error remained in both arms. All observations remain in the record.

The candidate failed **18/18 exact pairs, 18/18 wheels and 18/18 pedals**.
Its low-speed-brake and technical requirements passed; comparative gain was
descriptive and was not an admission threshold. The perfect gate was not
relaxed, so no new broader validation or live race is admitted. Retain joint
`damped` and unchanged application defaults.

These equal overall scores do not establish identical choices or equivalent
internal processing. This test measures supplied-rule compliance for the exact
placement package, not an attention mechanism, optimal actions or general
driver competence. Both component layouts changed as registered while physical
meanings and rules were preserved. Small counts, reflected states and one
presentation per case leave repeatability and generalization unresolved.

## Audit, runtime qualification and accounting

The final audit passed with **`complete=true` and no errors or warnings**.
It checked all eighteen factual states and policy labels, exact clause/physical-
definition relocation, matching submitted list/menu order, unchanged baseline
origin, native mapping, raw typed components, fixed request order and all
sequential budget transitions. Source inheritance and prospective wire/error
mocks passed before admission. The origin manifest checked sixty-four evidence
files and an exact policy copy; no old frozen CLI ran against a later ledger.
Production source, physics and handling remained unchanged. Inherited free
host-policy runs establish nominal tracking only: none triggered the pedal
guard or established physical recovery.
Separate collection-provenance verification passed all **49 checks**, including
immutable preflight/authorization chronology, all thirty-six wire payloads and
raw typed pairs, source identity, writer and full ledger chain. It confirmed
identical paired facts, physical definitions relocated exactly once in submitted
menu order, unchanged eligibility clauses and baseline questions identical to
the frozen 0036 deadband origin. Root tool chunk/session identifiers were checked
against preserved execution confirmation rather than independently queried from
tool infrastructure; actual writer and ledger records were independently verified.

The complete new-boot runtime clock gate passed at **04:09:25 UTC**, bound to
source `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`,
boot `f534ef07-e837-401d-bf64-a0fe7c51e3d3` and HTTP parent PID 1751/start ticks
85454. This qualifies runtime timing only. Exact candidate free control,
native gates and actual resource/time admission remain separate; this failed
static pilot does not admit live actuation.

Independent prospective preflight passed at 04:11:35 UTC. Root authorization
`15502c1e10c141498b5142c9798b1c32` at **04:12:01 UTC** preceded the sole writer's
**04:12:04.960187 UTC** start. Its session was
`3721b7b090db429abfee55c5adc22615`, PID 3135, with explicit collection enabled.
All thirty-six calls appear in the completion record; root confirmed exit zero.
Caps, conservative reservations, identity checks and no-fallback/no-retry
policies were retained.

The pilot used **thirty-six requests, $0.0027914040000007745 and 69,908 charged tokens**.
Its saved audited end boundary is **61,495 requests, $7.579654281999889 and
244,855,779 charged tokens**, with 69 historical uncertain charges unchanged
and pending empty. This report uses saved evidence and does not rerun an audit
against a later ledger.

The [machine-readable summary](0037-condition-only-summary.json) retains frozen
and completed evidence. The exact [prompt archive](0037-condition-only-prompts.json)
remains unchanged. A passing pilot would still require a new fresh broader
validation under unchanged 0035 gates; this pilot did not pass.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `98b87cb61a48c3121ce09d60343f11084febc9927a15221d841a1c47e0b621eb` |
| Exact prompt archive | `2d09d72dd2c7ea1c50f8f70838fff205fcd422e4a3dd1bf47804f5477c4bda6f` |
| Final audit | `e6b4d5b3be078445a6b2ed374afb8cd6caad0c68cb21866f85ed6a21adb2b686` |
| Audited report summary | `39edd4a3eaaadfb7e92c141c978aa91d84afd86660262ea1655bcae8e2eb6f0b` |
| Source-inheritance proof | `456ed9f37b1ed786cc3bdad166fa7bb96ef7c92c7fce12c56505405a1637faf2` |
| Frozen origin manifest | `886bc1ee5d65e87958d7f7259ee8330d1fa63f21161802d1e47784a4656f76f7` |
| Collection provenance | `45035256843dc3bcad55049fd720594dd68d32c29c518f9ceb752846263d37a6` |

Source remains `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
