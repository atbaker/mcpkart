# Current road-frame motion and present surface labels

Status: complete and independently audited, October 20, 2026. All 96 calls
completed. Current-motion answers improved from 14/16 to 16/16 with added
road-frame facts, but all four forecast profiles remained 8/16 with every
answer mapped to `stays_on_road`. No forecast replication signal was met.
The original prospective design is retained below.

In [0027](0027-risk-context.md), all sixteen prescribed-format controls passed,
but every forecast profile selected the physical `stays_on_road` outcome:
16/32 overall and 0/16 hazards. Removing the quoted guide and changing semantic
IDs to opaque IDs did not repair that pattern. Prescribed category mapping is
distinct from interpreting motion or predicting its consequences. The saved
0027 final audit and corrected separate provenance verification pass. The
initial failed fingerprint check and its correction remain preserved in that
study; this comparison does not replace that historical evidence.

The current `road_navigation` observation expresses velocity in the kart frame,
while road offset and edge clearances use the road frame. This comparison adds
factual current motion in the road frame and separately removes two redundant
present-surface labels. It supplies no evaluated future motion or control advice.

## Frozen physical task and fresh states

Keep Python physics, the 24 m stadium, 12 m/s speed ceiling, 0.12 rad maximum
wheel angle, three laps and three-second rescue unchanged. The forecast holds
the factual current native input fixed for exactly thirty 60 Hz physics steps,
or 0.5 seconds. Predict whether the kart centre is strictly outside the road
at any of those future frames. A centre touching an edge remains on-road.
This asks for the consequence of a held input, not an optimal driving action.

Use sixteen fresh synthetic states in eight reflected pairs. There are eight
safe and eight hazardous states, eight on current straight regions and eight
on current curves, with four states per risk × region cell. Current region
need not describe every future frame. All current centres are on-road, with
no previous or active rescue. Exact private offline simulations provide labels;
safe states must retain at least 0.5 m future centre clearance, and hazardous
states must reach at least 0.5 m beyond an edge. Achieved margins belong in the
frozen fixture evidence after local verification, not in forecast payloads.

The complete held-command distribution is matched between risk classes and
covers all five wheel settings and all three pedals. The generator checks that
requested road positions and rounded 15 m preview coordinate pairs are fresh
relative to the prior fixture banks and demonstrations it records. It reads
prior geometry rather than model responses. These are constructed transients,
not recorded racing trajectories or independent new tracks.

Require absolute current road-lateral velocity of at least 1 m/s. Reflection
gives eight currently leftward and eight currently rightward states, with four
of each direction within each risk class and each region. Current direction
is not a safety label. Expected answers, risk classes, future traces, clearance
proofs and reconstruction metadata remain outside submitted payloads.

## Motion facts × explicit present-surface labels

| Condition | Factual state | Explicit present-surface labels |
|---|---|---|
| A | Existing complete `road_navigation` | Retained |
| B | A plus `current_road_frame` | Retained |
| C | A with only the two specified labels removed | Removed |
| D | B with only the two specified labels removed | Removed |

The added `current_road_frame` object contains only:

- `nose_vs_road_deg`, signed nose orientation relative to the current road.
- `velocity_vs_road_deg`, signed current velocity direction relative to that road.
- `velocity_left_m_s`, current velocity projected onto the road's left normal.
- `velocity_forward_m_s`, current velocity projected onto the road tangent.

Use three decimal places for angles and four for velocities, plus fixed unit
text defining positive left and forward. The angles match existing
`kart_physics.current_alignment` facts; lateral velocity matches existing
`compact.present.road_lateral_m_s`. Forward velocity is the corresponding
current velocity dot product with the current road tangent. Derive these from
the same rounded current raw observation used by the existing renderers;
do not add hidden pose precision. Keep all original body-frame motion facts.

C and D remove exactly `road.on_road` and `physics.current_surface`. All other
facts, including centre offset, both edge clearances, current grip, held input,
actual wheel, yaw, progress, rescue and runtime `finished`, remain unchanged.
B and D append the fixed motion-unit explanation and four current quantities;
they do not replace the observation with the whole compact renderer. No
time-to-edge, closing-risk annotation, predicted position, future clearance,
action ranking or calculated control is supplied.

Every forecast uses the identical quoted `damped` guide, required forecast
question and semantic criteria from 0027's `guide_semantic` condition. The
answer instruction includes “Answer YES or NO using the criteria.” The physical answer
IDs remain `leaves_road` and `stays_on_road`. Only the registered state additions,
two label removals and their fixed unit text vary. Match criterion order within
each state; submitted order does not establish provider-internal ordering.

This factorial separates the added current-motion presentation from those two
explicit surface labels. It cannot hide current on-road status: positive
clearances and other retained physical facts still reveal it. An effect of
label removal concerns these redundant labels, not every possible current-state
cue. Added motion also changes redundancy and payload length, so a gain would
not identify an internal coordinate or attention mechanism.

## Collection and supplementary current-motion checks

Collect all **64 forecasts first**: sixteen states × four conditions, with one
presentation each. Shuffle states with seed `2026102028` and use a Latin
rotation of condition order. Balance physical criterion order, matching it
within each state. Each condition occupies every request position four times.
Freeze the complete ordered request list before collection.

Then collect **32 supplementary current-motion checks**: the same sixteen
states under A and B, with both present-surface labels retained. Ask only
whether the CURRENT velocity points leftward or rightward relative to the
CURRENT road tangent. Do not ask whether absolute offset is increasing, which
edge is approached, whether the input is good, or whether departure will occur.
Use the same fixed current-motion question and physical criterion meanings
under A and B. Shuffle states and alternate A/B presentation and criterion
order; freeze that order with the forecast order.

The maximum is **96 paid calls**, with no additional prescribed-format stage
and no repetitions. Collect every structurally valid planned answer regardless
of correctness; do not stop or select a candidate from partial responses.
Stop only for the registered technical, accounting, admission or deadline
conditions. No controls are applied and no race or server is started.

The motion checks are not forecasts. Success under B can reflect reading an
explicit current velocity component; it does not demonstrate prediction of
lag, grip or future curvature. Their placement after all forecasts prevents
their answers from being used to adapt this round. Contexts share states, and
reflected pairs are correlated rather than sixteen independent situations.

## Prespecified analysis and continuation limits

For each forecast condition, report overall accuracy, safe/hazard and
straight/curve results, confusion counts and selected physical outcomes.
Report matched gains/losses for motion additions B−A and D−C, label removals
C−A and D−B, and the combined D−A contrast. Report the motion and label main
effects and their interaction as descriptive matched differences. Mirror
agreement alone is not forecast accuracy or a repeatability estimate.

The descriptive forecast benchmarks are **15/16 overall** and **at least 7/8
within each risk class and each region**. For the separate current-motion
checks, use **15/16 overall** and **at least 7/8 in each leftward/rightward
class**. Report motion-check results by future risk and region as well, without
using those future metadata in the question.

An added-motion forecast condition must meet every forecast benchmark and gain
at least **four net correct responses out of sixteen** over its matched state
without added motion, B−A or D−C, before that motion presentation can motivate
a separately frozen fresh replication. These are small-screen benchmarks, not
statistical significance or driving qualification. A label-only improvement is
not credited as a motion-coordinate improvement. Accurate current-motion
answers alongside poor forecasts would leave the failure in future prediction
or task interpretation, rather than establish inability to read the current
motion. Poor current-motion answers would not establish a unique cause either.

No result automatically triggers replication, native-command validation, a live
race, qualification or promotion. Any subsequent comparison needs its own
fresh cases, frozen protocol and budget/deadline admission. Forecasting one
held input does not show that the model can choose a better input or maintain
checkpoint progress. Retain the joint `damped` baseline and application defaults.

## Admission and evidence contract

The saved end boundary after 0027 is **60,963 requests, $7.523178561999893 and
243,467,657 charged tokens**, with 69 historical uncertain requests and no
pending reservations. Preserve all historical spending and the shared
**75,000-request / $10 / 250-million-token** limits. Do not weaken the existing
conservative input/output reservation to extend collection. The authorized
[session](2026-10-20-six-hour-session.md) admission deadline remains
**06:17:26 UTC**.

Pin the same dated Jev model and TypeSafe provider, use one paid writer and one
request in flight, and retain zero automatic retries and no fallback. Before
paid admission, freeze the actual source identity, fixture bank, fields,
questions, menus, order, route and every helper hash. Retain an immutable
passing independent preflight and timestamped root authorization preceding
the actual writer start. Attribute every record and the completion marker to
that writer and protocol. A prior source or audit does not substitute for this
round's source and provenance checks. The current source fingerprint is
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`;
the 0028 protocol was frozen at 01:51:58 UTC before collection.

An endpoint, identity, malformed-response or uncertain-accounting failure stops
collection immediately, retaining the attempt, charge and explicit unrun
entries. Hard budget and deadline stops admit no additional request. Final audit
follows collection termination and reconstructs all current observations,
road-frame facts, independent direction labels, thirty-frame forecasts, exact
ordered wire bodies, field additions/removals and the complete ledger chain.
No older audit is rerun against an advanced ledger. Keep raw evidence under
ignored `artifacts/jev-road-motion-v1/`. The unchanged
[exact prompt archive](0028-road-motion-prompts.json) preserves the frozen
protocol; the [results summary](0028-results-summary.json) preserves completed
audit, subgroup, paired, mirror, gate and exact accounting evidence.


## Completed forecasts and current-motion checks

All 64 forecasts were collected before the 32 current-motion questions. No
supplementary answer was fed into a forecast request or used to adapt collection.

| Forecast condition | Overall | Safe | Hazard | Straight region | Curve region |
|---|---:|---:|---:|---:|---:|
| A: `road` | 8/16 | 8/8 | 0/8 | 4/8 | 4/8 |
| B: `road_frame` | 8/16 | 8/8 | 0/8 | 4/8 | 4/8 |
| C: `road_no_badges` | 8/16 | 8/8 | 0/8 | 4/8 | 4/8 |
| D: `road_frame_no_badges` | 8/16 | 8/8 | 0/8 | 4/8 | 4/8 |

Every forecast selected the physical `stays_on_road` category: 32 false-safe
answers and zero false-hazard answers across the four contexts. All five simple
forecast contrasts and their interaction were zero, with no paired gains or
losses. Motion and label main effects were also zero. All 32 forecast mirror
comparisons agreed, which follows from the constant safe answer rather than
useful forecast sensitivity.

| Current-motion condition | Overall | Leftward | Rightward | Straight region | Curve region |
|---|---:|---:|---:|---:|---:|
| A: `road` | 14/16 | 6/8 | 8/8 | 6/8 | 8/8 |
| B: `road_frame` | 16/16 | 8/8 | 8/8 | 8/8 | 8/8 |

Added current facts gave **two gains and zero losses**, correcting
`road-motion-00-b` and `road-motion-02-b`. Both were safe, straight-region,
leftward cases with nose/motion conflict. Thus safe-case motion readback
improved 6/8→8/8 while hazardous-case readback stayed 8/8. Mirror-direction
relations improved from 6/8 to 8/8. Each context was sampled once per state;
there is no within-context repetition estimate.

Only B met the separate current-motion benchmark. No forecast condition met
15/16 overall or 7/8 within hazards and either region, and neither added-motion
comparison achieved the required four net forecast gains. No fresh-replication
signal or live-qualification claim follows. No replication, native validation,
live comparison or preset promotion was triggered; the joint `damped` baseline
and application defaults remain unchanged.

These current-motion gains support the usefulness of the explicit facts for
literal reading on this bank. They did not transfer to the future forecast.
Removing the two present-surface labels also gave no forecast change; retained
clearances and other facts still reveal current on-road status. The experiment
does not identify the model's internal coordinate or attention mechanism.

These synthetic transients are related through mirrors and shared contexts,
not independent driving starts. Labels describe only the currently held input
over half a second, not optimal control. The supplied state includes the full
handling dictionary, but **full simulator update equations and the complete
track representation were not supplied**. Disagreement with exact offline
physical ground truth does not establish a particular internal mechanism or
general driving incapacity. Added facts are current projections, not a supplied
future trajectory or control recommendation.

## Completed audit, provenance and fixed boundary

All **96 requests** completed with zero endpoint errors, no retries or
replacements, no new uncertain charges and no unrun entries. The final audit
passed with no errors or warnings. It reconstructed all sixteen current states,
480 exact future physics steps, road-frame additions, two-field removals,
current-direction labels, exact wire bodies, writer attribution and accounting.
No controls were applied. The actual writer execution session was
`c86791f3521747c3b9bcd2169dc2798d`, with explicit collection enabled.

Separate collection-provenance verification passed all **31 checks**; its
immutable preflight/authorization timestamps and actual writer identity are
preserved in the results summary.

The phase used **96 requests, $0.010682699999997602 and 258,176 charged tokens**.
The saved audited end boundary is **61,059 requests, $7.533861261999891 and
243,725,833 charged tokens**, with 69 historical uncertain requests unchanged
and pending empty. Shared caps and conservative reservations remain unchanged.
This report uses saved completed evidence; it does not rerun audits or inspect
a later ledger.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `cab051e6cc0373f195adda776de0c24eb902c45e56dd0616701dba12fa96af6d` |
| Exact prompt archive | `e10662021d9074d2cf9a67b40449fc2ce031cab4e204084cf55bdec393665676` |
| Final audit | `8ddc7c59f2e54cb70f0b7694891270e5285b958093ab9c8c44245de64d67e05c` |
| Audited report summary | `0d0df914cb28ae28de72c709a6523da7815aab0167e9e3b08bfbeb837e159de0` |
| Collection provenance verification | `fa74f476ab157985844768e884fdda6ed921f787e421a9f5a79c57d0795f4cce` |
