# Answer IDs and descriptions

Status: completed and independently audited, October 19, 2026 (client date). The user approved a four-menu
comparison after [six worked examples](0020-worked-examples.md) produced only a
6.25-point gain, with no correct full-left answers. Test whether answer IDs,
descriptions or their combination affect the supplied-formula task. This is a
presentation experiment, not a claim that a particular internal bias exists.

## Prospective comparison

All conditions use the same literal-expression question, full observation, named
copy of the raw 15 m coordinates and five absolute angles: -0.12, -0.06, 0,
+0.06 and +0.12 radians. No worked examples or current-query calculated
intermediates are supplied. Only the choice IDs and description strings change:

| Context | IDs | Descriptions |
|---|---|---|
| `semantic_physical` (A, control) | Existing `wheel_*` IDs | Existing absolute-wheel text with direction |
| `opaque_physical` (B) | `option_a` through `option_e` | Existing absolute-wheel text with direction |
| `semantic_numeric` (C) | Existing `wheel_*` IDs | Signed radians only |
| `opaque_numeric` (D) | `option_a` through `option_e` | Signed radians only |

The semantic IDs contain `full`, `half`, `left` and `right`. Numeric descriptions
are exactly `-0.12 radians.`, `-0.06 radians.`, `0 radians.`, `+0.06 radians.`
and `+0.12 radians.`. Each menu still means the same physical angles. Opaque
IDs rotate across angles independently of the matched physical option order;
the same mapping is used in B and D within a case/repetition. Host decoding
changes an answer identifier into its already declared angle, not into a newly
calculated control recommendation. No control is applied.

Use 24 fresh synthetic snapshots, twelve mirrored pairs, twelve straight-region
and twelve curve. Targets balance eight per magnitude, with both nonzero
directions represented. All actual rounded 15 m x/y pairs and requested road
positions are absent from studies 0016–0020; the six prior demonstration pairs
are excluded too. Deterministic selection reads prior geometry fields only,
never prior responses. Minimum quantization margin is 0.006993 rad. Four cases
distinguish actual x from x=15, and fourteen oppose the current heading-sign cue.
Coarse labels still do not identify exact atan execution. Retain the Python
simulation, 24 m stadium, 12 m/s ceiling and 0.12 rad wheel limit. Fixture speed
is 8 m/s, with the existing balanced held-wheel and yaw transients. No physics
is advanced and these are not driving trajectories or optimal-action labels.

Four menus × 24 cases × two repetitions yield **192 planned requests**. Shuffle
cases with seed 2026101921. Rotate the four condition request orders evenly,
then reverse cases and condition order for repetition two. Within each case
and repetition, all four menus share the same physical angle order. Five cyclic
angle orders and separate opaque-ID rotations make every angle occupy each
position and opaque ID nine or ten times across the 48 case/repetition units.
Each context occupies each request position exactly twelve times. This tests
five cyclic physical orders, not all 120 permutations. The control retains the
prior IDs/descriptions but also receives this counterbalanced order.

Report overall, magnitude, full-left/full-right, region and heading-conflict
scores. Decode answers to physical angles for all comparisons, including
repetition stability; opaque IDs change their meanings between some requests.
Repetitions and mirrored fixtures are correlated. Differences in string form,
semantic cues and description length are bundled within each factor; an effect
does not establish an internal psychological or arithmetic mechanism.
Matched submitted option order does not establish which order the provider
exposes internally. The opaque condition also changes the stability of ID-to-angle
assignments across requests; it tests that defined presentation package.

## Prespecified comparisons and continuation

Prespecify the four simple contrasts: B−A and D−C for opaque IDs, and C−A and
D−B for numeric descriptions. Also report combined D−A. The descriptive ID
main effect is the average of B−A and D−C; the description main effect averages
C−A and D−B. Report their interaction rather than interpreting either average
as constant across the other factor. No independent-sample significance claim
or posthoc choice of the most favorable contrast is planned.

Each of B, C and D must independently reach **90% overall**, **85% within every
magnitude** and **ten percentage points over A**, with zero endpoint errors and
a passing audit, to qualify for fresh validation. Report every candidate,
including regressions. If several qualify, select highest minimum-magnitude
accuracy, then overall accuracy, then fixed tie priority B, C, D. Any selected
candidate must pass a separately frozen fresh native-menu static check, bounded
to 192 additional calls, before considering promotion. If none qualify, finish
without further paid calls. No live race or preset promotion is automatic.

## Verification and spending

Freshly discover `typesafe/jev-1.14`, resolved to
`typesafe/jev-1.14-20261014` at `TypeSafe`, with unchanged prices. Use one
request in flight, zero retries and no provider fallback. Save exact
credential-free payloads, responses and ledger boundaries. Stop on the first
endpoint or identity error; retain failures and unrun cases without replacements.

Starting ledger: **58,648 requests / $7.260116644 / 236,960,024 charged tokens**,
69 historical uncertain requests and no pending reservations. Preserve the
shared **75,000-request / $10 / 250,000,000-token** limits. The existing Budget
reserves 16,384 input tokens plus the advertised output ceiling for each call.
No guard increase or historical charge reset is part of this experiment.

The local mock captures all 192 actual wire bodies plus a deliberate503, with
zero model calls and no ledger change. It verifies unchanged state/question,
physical-angle equivalence, option insertion order, opaque mappings and exclusion
of oracle metadata. The independent audit reconstructs poses and labels, exact
menu text and mappings, order balance and serialized payload order, then checks
all route identities, request IDs and accounting transitions. Freeze helper,
fixture, order and route hashes before collection. Run final audit only after
runner exit, the completion marker, all records and empty pending reservations.

Ignored evidence: `artifacts/jev-menu-v1/`. Versioned summaries and the exact
generator/prompt archive preserve handoff context without publishing raw runs.

## Results

All 192 requests completed with the pinned dated model/provider, zero endpoint
errors and no new uncertain charges. After runner exit, 192 saved records, the
completion marker and empty pending reservations were verified, the final audit
passed independent geometry/math, every ordered payload and physical mapping,
frozen helper hashes, route identities, request IDs and all ledger transitions.
All new experiment and plot helpers passed Ruff. Production source and runtime
dependencies were unchanged.

Every overall cell contains 48 responses (24 fixtures repeated twice); magnitude
cells contain sixteen and each nonzero direction within a magnitude contains eight.

| Menu | Overall | Straight | Moderate | Full | Full-left | Full-right |
|---|---:|---:|---:|---:|---:|---:|
| A: Current IDs + physical descriptions | 37/48 (77.1%) | 15/16 | 15/16 | 7/16 | 0/8 | 7/8 |
| B: Neutral IDs + physical descriptions | 36/48 (75.0%) | 15/16 | 13/16 | 8/16 | 0/8 | 8/8 |
| C: Current IDs + numeric descriptions | 34/48 (70.8%) | 13/16 | 15/16 | 6/16 | 0/8 | 6/8 |
| D: Neutral IDs + numeric descriptions | 40/48 (83.3%) | 16/16 | 11/16 | 13/16 | 5/8 | 8/8 |

The combined menu restores some full-left answers, while neither single change
does so on this bank. Its three-answer net overall gain hides a steering-magnitude
tradeoff: full targets improve 7/16→13/16, but moderate targets regress 15/16→11/16.
Full-left remains only 5/8, and moderate-right falls 7/8→4/8. The combined
condition is not a uniformly better formula executor.

## Prespecified contrasts

| Contrast | Wrong→correct | Correct→wrong | Net answers | Accuracy change |
|---|---:|---:|---:|---:|
| B−A: neutral IDs with physical descriptions | 2 | 3 | -1/48 | -2.08 pp |
| D−C: neutral IDs with numeric descriptions | 10 | 4 | +6/48 | +12.50 pp |
| C−A: numeric descriptions with current IDs | 1 | 4 | -3/48 | -6.25 pp |
| D−B: numeric descriptions with neutral IDs | 7 | 3 | +4/48 | +8.33 pp |
| D−A: both changes against control | 7 | 4 | +3/48 | +6.25 pp |

The ID effect depends on the description condition. The prespecified matched
difference of differences is +7/48, or **14.58 percentage points**. Averaged
across the other factor, the descriptive ID main effect is +5.21 points and the
description main effect +1.04 points. These averages hide the interaction; they
do not justify saying neutral IDs or numeric descriptions always help.
Correlated repetitions and mirrored geometry limit generalization, and this
small comparison does not identify a particular internal semantic mechanism.

## Gate and posthoc interpretation

All three candidates fail the frozen gate. The best overall condition, D, reaches
83.3%, below 90%; full accuracy is 81.3% and moderate 68.8%, below 85%; its
6.25-point gain over A is below ten points. B and C regress overall and also
fail the magnitude requirements. **No native-menu validation was triggered.**
No additional paid calls, live race or preset promotion followed this comparison.
Retain `damped` as the live baseline and keep the original application default.

Posthoc decoding of D−A finds seven gains: five full-left, one full-right and
one straight. Four losses are three moderate-right answers and one moderate-left.
Every moderate miss under D selects full steering with the correct sign. Chosen
full wheels increase from eight in A to eighteen in D: correct full-target
answers rise seven→thirteen, while incorrect full choices on moderate targets
rise one→five. The menu change shifts the selected magnitude distribution;
the resulting regressions prevent promotion on the overall gain alone.
Every nonzero selected angle in all four conditions follows raw target y's sign,
which does not establish correct magnitude arithmetic.

Across repetitions, physical-angle choices agree on 21/24 cases in A, 22/24
in B, 22/24 in C and 20/24 in D. Both repetitions are correct on 17/24, 17/24,
16/24 and 18/24 respectively. These repeats deliberately change option order
and sometimes opaque-ID mapping, so they measure stability under those declared
changes as well as response variation. Of D's four full-left fixtures, only one
is correct in both presentations; three change between correct and incorrect.
Different studies also use fresh geometry;
the control's higher score than an earlier study cannot be attributed to order
cycling or another isolated change.
On the four x=15-discriminating cases, scores are A 5/8, B 4/8, C 5/8 and
D 4/8. The combined menu's overall gain does not support improved actual-x
calculation on that small subset. Physical choices also never keep the same
submitted insertion position across the two presentations of a case, weakening
a universal fixed-submitted-position explanation; the provider's internal
presentation order remains unknown.

## Spending and evidence

This comparison charged **192 calls / $0.018151392 / 444,012 tokens**, with no
new uncertain requests. Ending shared ledger: **58,840/75,000 requests /
$7.278268036/$10 / 237,404,036/250,000,000 charged tokens**, 69 historical
uncertain requests and no pending reservations. Remaining guards allow 16,160
request slots, $2.721731964 and 12,595,964 charged-token slots, subject to the
conservative per-call reservation. All hard ceilings and prior spending persist.

The [results summary](0021-results-summary.json) preserves audited groups,
placement coverage, predefined paired contrasts, factorial effects, repeat
counts and the failed gate for every candidate. The
[prompt archive](0021-menu-prompts.json) preserves exact frozen source strings,
order, fixture and route hashes. The chart is generated from verified summaries
under `artifacts/jev-menu-v1/report/` as PNG, PDF and SVG.
