# A physics scaffold on naturally reached states

Status: complete and independently audited, October 20, 2026. All 32 calls
completed and separate collection-provenance verification passed. Baseline and
scaffold each scored 8/16, always predicting `stays_on_road`; no forecast gain
or fresh-replication signal was met. The registered design and achieved fixture
constraints are retained below.

The completed 0028 diagnostic found 14/16 correct current-motion answers from
the existing observation and 16/16 with explicit road-frame facts. All four
forecast conditions nevertheless scored 8/16 by always predicting that the
kart stays on-road; removing two present-surface labels had no effect. Reading
current motion therefore does not establish integration of its future effects.
The next comparison holds that explicit current-motion representation constant
and tests one fixed explanation of the simulation's physical updates.

## Natural current states and hypothetical continuations

Keep Python, the 24 m stadium, 12 m/s speed ceiling, 0.12 rad maximum wheel
angle, three laps and three-second rescue unchanged. The selection pool is
27 existing races compatible with that exact physical setup. Use sixteen
actual recorded current states, without perturbation or artificial reflection.
They must precede any rescue, have speed at least 2 m/s, and have between
0.5 m and 3.0 m current centre clearance under the final frozen selection rule.

The bank targets eight safe and eight hazardous states, eight on current
straight regions and eight on current curves: four per risk × region cell,
with two near each physical edge in every cell. Current region need not
describe every future frame. Select unsent ticks on a 0.1-second grid, use
distinct hazard episodes, prefer one selected state per race, and exclude
overlapping forecast windows. Do not pad the bank with many adjacent ticks
from a small number of departures. The final frozen bank matches complete held-input frequencies between risk
classes within each region. A stronger same-input pairing within physical side
was infeasible in the registered pool; its failed feasibility search remains
recorded. The original risk × region × side quotas and sixteen distinct-race
requirement were retained. Achieved coverage and remaining imbalances are
reported below.

Each current state is naturally reached under its recorded control prefix.
Its forecast then holds the current factual native input fixed for thirty
exact 60 Hz simulation steps, or 0.5 seconds. That continuation is hypothetical:
the original racer may have issued different later commands. Exact private
offline replay supplies labels. A safe continuation must retain at least
0.5 m centre clearance at every future frame; a hazard must reach at least
0.5 m beyond an edge. Touching an edge counts as on-road. Future traces, margins,
risk labels, expected answers and reconstruction metadata remain outside all
submitted query states and instructions.

Selection uses recorded states and offline physics, never model answers.
Unsent ticks can still be temporally related to earlier submitted observations;
they are not proof of an unseen track or independent driving situations.
Natural-state provenance does not make the hypothetical continuation a recorded
future trajectory.

## One fixed prompt intervention

Both arms receive exactly 0028 condition B: the complete factual
`road_navigation` observation plus four current road-frame facts and fixed unit
text, with `road.on_road` and `physics.current_surface` retained. Keep original
body-frame facts, runtime `finished`, handling, progress and rescue fields.
The added facts are current nose/velocity road-relative angles to three decimal
places and leftward/forward road-relative velocities to four decimal places.
They contain no evaluated future risk, edge-closing quantity or control advice.

The baseline uses the exact 0028 quoted `damped` guide, forecast question and
semantic criteria, with `leaves_road` and `stays_on_road` as the physical answer
IDs. The candidate inserts only the following fixed scaffold after
`END REFERENCE DRIVING GUIDE` and before the unchanged `REQUIRED TASK:`:

> PHYSICS OF THE REQUIRED FORECAST. Holding the current input fixed does NOT freeze position, velocity, nose, yaw or actual wheels. Positive clearance and on-road labels describe NOW; the answer concerns future frames.
>
> Start from actual current velocity, nose, yaw and wheel angle. Wheels approach the held target with steering-response lag. Yaw approaches a target determined by nonnegative forward speed times tan(actual wheel angle) divided by wheelbase, capped in magnitude by grip divided by max(speed, 2). Yaw-response lag applies before the nose rotates.
>
> Turning the nose does not instantly turn velocity. Each frame, grip reduces sideways velocity relative to the NEW NOSE by at most grip times DT. Net acceleration is throttle acceleration minus braking and drag. A positive net value adds velocity along the new nose; a negative value scales down the whole velocity vector, stopping rather than reversing it. The speed ceiling applies. The centre advances with that resulting velocity, while road geometry can change around a curve.
>
> Follow successive future positions and compare them with the road edges. Existing outward motion can cross an edge before wheel or yaw changes correct it. Inward motion, slowing or a corrective wheel target alone does not determine the outcome. Answer YES if the centre is outside at ANY required future frame, even if it could return later; otherwise answer NO. Return only the requested binary choice.

This is a qualitative account of the actual update order. The grip statement
concerns removal of slip sideways relative to the nose; it is not a bound on
total acceleration sideways relative to the road. In particular, positive net
acceleration adds velocity along the evolving nose, whereas negative net
acceleration scales the velocity vector. The scaffold does not provide the
complete exponential update equations, a complete track map, an evaluated query
forecast or a recommended input. It is not a guarantee that exact prediction
is identifiable or easy from the rendered current state.

No worked examples, alternative guide, answer-ID change, new question or
query-specific calculation accompanies the scaffold. Its content and extra
length change together; any effect concerns this complete fixed prompt addition.
No prediction or intermediate calculation from another model call is supplied.

## Ordered comparison and technical stops

Collect **32 paid forecasts**: sixteen current states × baseline/scaffold,
one presentation each. Shuffle states with seed `2026102029`. At shuffled
state index `j`, alternate the first context using `j % 2` and the first physical
criterion using `j // 2 % 2`. Match criterion order within each state. Each arm
occupies each request position eight times and sees each criterion first eight
times. Submitted order does not establish the provider's internal option order.

Freeze the entire order and collect all structurally valid planned answers
regardless of correctness. There is no performance stop, adaptive prompt change,
retry, replacement case, additional format gate or few-shot stage. Technical,
identity, uncertain-accounting, hard-budget and deadline stops retain every
attempt and explicit unrun entry. No control is applied and no live race starts.

Shared states, same-course races, event selection and the fixed model create
related observations. One presentation per arm/state provides no within-arm
repeatability estimate. The comparison does not establish broader physical
forecasting or driving capacity.

## Prespecified analysis and continuation limits

Report each arm's overall accuracy, safe/hazard, straight/curve and physical-edge
subgroups, confusion counts and chosen physical outcomes. Report paired gains,
losses and net differences, with source-race and hazard-episode coverage.
Distinguish valid constant-safe answers from endpoint or response-format errors.

The scaffold must reach **15/16 overall**, **at least 7/8 in each risk class
and each region**, and **at least four net additional correct responses out
of sixteen** relative to its matched baseline, with clean technical execution
and a passing independent audit, before it can motivate a separately frozen
fresh 32-state paired replication. Report a capable baseline separately without
crediting it as a candidate gain. These small-screen benchmarks are descriptive,
not statistical significance or driving qualification.

No result automatically triggers replication, native-command validation,
a live race, qualification or promotion. Forecasting one held input does not
show selection of a better alternative, useful checkpoint progress or safe
pedal planning. Retain the joint `damped` baseline and application defaults.

## Admission and evidence contract

The completed 0028 boundary is **61,059 requests, $7.533861261999891 and
243,725,833 charged tokens**, with 69 historical uncertain requests and no
pending reservations. Preserve the actual shared ledger and all historical
charges. The limits remain **75,000 requests / $10 / 250 million charged
tokens**, with the existing conservative per-request input/output reservation.
The authorized [session](2026-10-20-six-hour-session.md) admission deadline
remains **06:17:26 UTC**. No guard is raised to finish this comparison.

Use the pinned dated Jev model and TypeSafe provider, one paid writer and one
request in flight, zero automatic retries and no fallback. The fixed current
source fingerprint is
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
Freeze the actual fixture bank, source provenance, questions, scaffold bytes,
state fields, order, route and helper hashes before paid admission. Retain an
immutable passing independent preflight, timestamped root authorization and
the actual writer identity preceding collection; match every record and
completion marker to that protocol and writer.

After collection terminates, the independent audit must reconstruct each
recorded current prefix, current observation and road-frame facts, all thirty
hypothetical future steps and risk labels, source-event and freshness contracts,
exact ordered wire bodies, unchanged baseline, sole fixed scaffold insertion,
route identity and every ledger transition. Preserve failures and unrun cases.
Do not rerun older audits against a later ledger. Raw evidence remains under
ignored `artifacts/jev-natural-forecast-v1/`. The unchanged
[exact prompt archive](0029-natural-forecast-prompts.json) preserves the frozen
protocol and questions; the [results summary](0029-results-summary.json)
preserves completed audit, source coverage, selection constraints, subgroup
results, paired comparisons and exact budget boundaries.


## Achieved natural-state bank and replay

The frozen bank contains sixteen different recorded races across **ten starting
seeds**, one selected state per race, without perturbation or artificial
reflection. All selected ticks were unsent, precede the first rescue and lie on
the six-tick grid. All sixteen rendered 15 m coordinate pairs were fresh against
the recorded submissions and registered earlier banks. There are two states in
every risk × current-region × physical-side cell.

The full compatible pool contains **27 races, 188,381 exactly replayed physics
samples and 11,134 applied commands**, yielding 571 eligible candidate ticks.
Independent selected-prefix verification covered **29,968 recorded samples and
1,756 applied commands**, followed by **480 hypothetical future steps**. The
recorded command prefix establishes how each current state was naturally
reached. Later recorded commands were not used in its held-input forecast.

Current clearance was 0.6837–2.9525 m in safe states and 0.8239–2.9563 m in
hazards, under the common 0.5–3.0 m selection bound. The weakest safe future
clearance was +0.5437 m; the closest hazardous future minimum was −0.7287 m.
Complete held-input frequencies match between risk classes within region:
all curve states hold `left_accelerate`; each class's four straight states use
one `right_accelerate`, one `right_coast` and two `straight_accelerate`.
Within-side pairing was not feasible and is not claimed.

Fourteen states were at 12 m/s within floating-point tolerance. The coast pair
was 8.0796 m/s for the hazard and 11.7201 m/s for the safe state, so speed is not
perfectly matched. All selected states have zero observed body slip. These
constraints make a small stratified diagnostic bank, not a representative sample
of natural hazards or independent tracks and starts.

## Completed results and decision

| Prompt | Overall | Safe | Hazard | Straight region | Curve region |
|---|---:|---:|---:|---:|---:|
| Baseline | 8/16 | 8/8 | 0/8 | 4/8 | 4/8 |
| Fixed physics scaffold | 8/16 | 8/8 | 0/8 | 4/8 | 4/8 |

All **32 answers** mapped to `stays_on_road`: sixteen false-safe forecasts and
zero false-hazard forecasts. All sixteen paired physical choices agreed,
producing **zero gains, zero losses and zero net improvement**. Both prompts
also scored 4/8 on each physical-edge subgroup. There is one presentation per
prompt/state and no within-prompt repeatability estimate.

The scaffold failed 15/16 overall, 7/8 hazardous and each-region benchmarks,
and the required four net gains. The baseline also failed its capability
benchmark. No fresh-replication signal was met; no replication, native
validation, live race or promotion was triggered. Retain joint `damped` and
unchanged application defaults.

Constant safe forecasts persisted on this selected natural-state bank, and the
fixed qualitative physics explanation did not resolve them. Natural prefixes
and hypothetical futures must remain distinct: these are not labels of what
actually happened under the source racer's later commands. Comparing this bank
with earlier synthetic banks does not isolate a causal effect of naturalness.
The scaffold explains update order but does not supply complete exponential
update equations, a complete track map or evaluated query-specific integration.
Exact-ground-truth errors do not identify an internal mechanism or prove general
driving incapacity. Forecasting, choosing a better input and live checkpoint
progress remain separate tasks.

## Completed audit, wire-order correction and provenance

All 32 requests completed with zero endpoint errors, no retries or replacements,
no new uncertain charges and no unrun entries. The final audit passed with no
errors or warnings. It checked current recorded prefixes and exact observations,
road-frame facts, all future steps, fixture freshness/matching, scaffold content
against source, ordered payloads, route identity and accounting. No controls
were applied. The actual writer execution session was
`70baa53d35bc4834821de9f48e3599bd`, with explicit collection enabled.

Separate collection-provenance verification passed all **32 checks**, including
immutable preflight/authorization chronology, complete source fingerprint,
all 32 writer/response/wire identities and the exact sequential budget chain.
Its complete saved result and timestamps are retained in the results summary.

Before protocol freeze, canonical case-JSON serialization preserved semantic
values but changed state insertion order and actual wire bytes. The earlier
free mock proof was retained; all 33 wire mocks were refreshed before freezing
and paid admission. This is recorded in the canonical-order preflight amendment.
It did not change selected states, make paid requests or rerun any paid call.
Both preserved proof hashes and the frozen final proof are referenced in the
results summary.

The phase used **32 requests, $0.003948839999997844 and 95,364 charged tokens**.
Its saved audited end boundary is **61,091 requests, $7.537810101999889 and
243,821,197 charged tokens**, with 69 historical uncertain requests unchanged
and pending empty. All **75,000-request / $10 / 250-million-token** caps and
conservative reservations remain unchanged. This report uses completed saved
evidence; it does not rerun audits or inspect a later ledger.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `f75d9eb2248b504f16e794060aa36fabd166d8b3849a02db4a8723ce3dfce3f0` |
| Exact prompt archive | `f733bdf0eac52a8c0b0609fecff5bb8bbd48ced963b0990dcf9a5dde7e0d2449` |
| Final audit | `77b9436be52883469ed87a8f0213036e3ae09dc0e836078975c08aef62747fd8` |
| Audited report summary | `3444cfb569032607efb07a1d9f137bc1c93eec8057af52770130e334d940c6ad` |
| Collection provenance verification | `a7969262f1acb5a8be6d56b552ed1b975554ab71519a3d45ee1a1b3271285eb9` |

Source remains `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
