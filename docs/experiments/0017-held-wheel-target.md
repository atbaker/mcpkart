# Current wheels versus the calculated target

Status: complete, October 19, 2026. The user approved the targeted follow-up
to the [factual diagnostic](0016-jev-factual-skills.md). That diagnostic selected
moderate wheels on 90/96 formula-related responses, but every formula snapshot
also held moderate wheels. It could not distinguish copying that input from a
moderate-steering preference or another shortcut. Keep the previous evidence
frozen and use fresh geometry to test that confound.

## Frozen comparison

Twelve new geometric snapshots (six mirrored pairs) are crossed with all five
physical held-wheel angles, -0.12/-0.06/0/+0.06/+0.12 rad, and yaw rates
-12/0/+12 deg/s. This produces 180 cases. All geometry and the nominal formula
target stay fixed within each fifteen-case motion group. Current wheel, its
held coast-control representation and yaw are internally consistent rendered
facts; their combinations are declared transient snapshots, not steady-state
or recorded trajectories. Speed remains 8 m/s. No simulation steps are taken.

A deterministic local numerical grid selects geometry before any model answer:
six initial-straight positions, six desired formula values, fixed heading/offset
grids, and at least 0.003 rad from quantization boundaries. Reflected snapshots
use the clockwise stadium. Targets balance sixty straight, sixty moderate and
sixty full cases, with both directions represented. The actual minimum margin
is 0.005745 rad. One mirrored pair distinguishes the correct actual-x calculation
from incorrectly replacing x with 15, with margins on both answers. Broad
quantization still does not distinguish omitting atan on these cases; do not
infer precise trigonometric execution from correct labels.

The underlying Python source, 24 m road width, 12 m/s ceiling, 1.8 m wheelbase
and 0.12 rad maximum wheel angle remain fixed. The live track and driving
preset are unchanged. These static mathematical labels are not optimal controls.

Compare two question versions, with identical full observations and the same
five wheel-answer criteria:

- `baseline` is the exact prior minimal factual wrapper and pursuit-formula
  question, using the actual x/y values from the 15 m preview row.
- `explicit_target` adds a fixed prefix separating the currently held wheel/yaw
  from the new mathematical target. It also states the equivalent magnitude
  branches: abs(delta)<=0.03 gives straight; (0.03,0.09] gives moderate;
  abs(delta)>0.09 gives full, with the sign determining direction. This is a
  combined question change; any gain cannot be attributed to one clause alone.

The host does not calculate or recommend a wheel in a submitted request.
Expected labels, case IDs, proof and group metadata stay outside the payload.
Only the model performs the supplied calculation and selects an answer.

Two repetitions of each case/context produce **720 calls maximum**. Shuffle
cases with order seed 2026101917, pair the two contexts, then reverse case order
and swap context order for repetition two. Responses are not seeded. There are
twelve distinct geometries, not 720 independent driving situations. Report
accuracy by target magnitude, held wheel and yaw, plus paired prompt changes,
repeat stability and sensitivity to irrelevant current-input facts. Invariance
alone is not correctness: a constant wrong answer can also be invariant.

## Verification, spending and continuation rule

Use freshly checked `typesafe/jev-1.14`, resolved to
`typesafe/jev-1.14-20261014` at `TypeSafe` with unchanged prices. Retain one
request in flight, zero client retries and no provider fallback. Save every
exact credential-free payload, response and before/after ledger. Stop on the
first endpoint/identity error and retain every attempted case. Global hard
caps can stop collection; never turn an unrun case into an observed answer.

Starting ledger: **57,256 requests**, **$7.145243368**, **234,138,647 charged
tokens**, 69 historical uncertain requests, no pending reservations. Preserve
**75,000 requests / $10 / 250 million tokens**. Each request reserves the
conservative 16,384 input ceiling and advertised output ceiling through the
existing shared Budget. No limit or historical charge is reset.

The local HTTP mock captured all 720 planned wire bodies plus one deliberate
mock error, using zero real model calls and leaving the ledger unchanged. It
verified the exact question contrast, unchanged five choices and exclusion of
oracle metadata. Freeze helper, fixture, order, route and proof hashes before
paid collection. Independent review checks the formula labels and factorial,
mirror and geometry-invariance contracts. No server or race is started and no
control is applied.

A strong gain requires the revised question to reach at least 90% overall
accuracy, at least 85% for each target magnitude and each held-wheel subgroup,
and a gain of at least ten percentage points over baseline, with a passing
audit and zero endpoint errors. Only then may a separately frozen static
native-menu validation use up to 240 further calls on fresh states. No race or
preset promotion happens automatically. Otherwise finish this comparison and
record its limitations before another prompt iteration.

Ignored evidence lives under `artifacts/jev-wheel-target-v1/`. The
[exact prompt and generator archive](0017-wheel-target-prompts.json) and
[results summary](0017-results-summary.json) preserve the handoff without
publishing raw request logs.

## Results

All 720 planned requests completed with the expected dated Jev model and
TypeSafe provider, no endpoint errors and no new uncertain charges. Each prompt
has 360 responses over the same twelve geometries, crossed motion states and
two repetitions; these are correlated conditions, not 360 independent examples.

| Required formula target | Baseline | Explicit target wording |
| --- | ---: | ---: |
| Straight | 3/120 (2.5%) | 64/120 (53.3%) |
| Moderate | 120/120 (100%) | 120/120 (100%) |
| Full | 14/120 (11.7%) | 1/120 (0.8%) |
| Overall | 137/360 (38.1%) | 185/360 (51.4%) |

The revised question adds 48 net correct answers (+13.3 percentage points).
Paired responses changed from wrong to correct 62 times and from correct to
wrong 14 times. The gain largely comes from straight targets, while full-angle
answers regress. Even the straight gain is asymmetric: the revised question
was correct on 56/60 positive-delta straight-target responses but only 8/60
negative-delta mirrors. A general improvement in magnitude reasoning is not
established. Both prompts still favor moderate wheels: 343/360 baseline and
295/360 revised choices were moderate.

The prospectively declared strong-gain gate **fails**. The gain exceeds ten
points, but 51.4% overall is below 90%, full-target accuracy is below 85%, and
held-wheel subgroup accuracies range from 47.2% to 54.2%, below 85%. The optional
native-menu validation was not triggered. No more paid calls, live races or
preset promotion followed this screen. Retain the current live `damped` preset.

## Held-input and yaw effects

The simple universal-copying explanation is inconsistent with this bank.
Chosen wheels matched held wheels on only 72/360 baseline and 75/360 revised
responses (20.0% and 20.8%) when all five held settings were balanced. In 61/72
baseline and 64/72 revised geometry/yaw/repetition groups, the answer stayed
identical across all five held wheels. A fixed answer within such a group
naturally matches one of the five held values; matching alone is not evidence
of copying. This does not exclude smaller held-input influences, and differences
in remaining groups can also reflect stochastic responses.

Similarly, answers stayed the same across all three yaw values in 107/120
baseline and 109/120 revised groups. Exact repeated answers matched on 165/180
baseline and 173/180 revised case pairs. Stable wrong answers remain wrong:
only 24/72 baseline and 34/72 revised five-wheel groups were entirely correct.

Every nonzero selected wheel followed the nominal formula's sign, but road
heading sign is correlated with that sign throughout these snapshots. This
cannot identify which sign cue the model used. The remaining failures are
predominantly magnitude selection on this declared mathematical task, not an
established causal explanation for earlier off-road departures.

On the one mirrored geometry pair where substituting x=15 changes the expected
angle, baseline was correct 0/60 times and revised wording 1/60. The incorrect
x=15 shortcut's answer matched 60/60 and 59/60 responses respectively. A general
moderate-wheel preference predicts the same answers there, so these counts do
not diagnose x substitution. Omitting atan remains indistinguishable under all
current coarse labels. Precise trigonometry is not identified.

## Recommendation and final verification

Retain the Python runtime, fixed 24 m setup and existing live baseline. The
question change has a partial static gain with a severe full-angle weakness;
it has not earned a driving trial under this protocol. The next useful
representation test should separate reading the actual 15 m x/y pair from
executing the arithmetic, for example with named coordinates and an independent
factual readback. Keep expected targets and steering recommendations outside
model state. That would test a specific representation hypothesis without
treating the current static gain as reliable driving. This follow-up was not
run here.

The final independent audit passes all 180 reconstructed observations and labels,
180 mirror relations, the 12×5×3 factorial, frozen helper hashes, all 720 exact
request bodies, route identity, unique request/reservation identifiers and every
ledger transition. The paired-result heatmap uses the same 0–100% scale, reports
cell denominators and is saved as PNG/PDF under
`artifacts/jev-wheel-target-v1/report/wheel-target-accuracy.*`.

An earlier audit was mistakenly launched while the last requests were still
running. It correctly refused because a reservation was pending, wrote no
spending ledger or snapshot, and made no model calls. Its rejection is retained
as `audit-before-collection-complete.json`. After collection exited, the full
audit was rerun and passed with no pending reservations. No paid request was
retried, omitted or replaced.

Runtime source fingerprint remains
`588958f4c0bd594064b55c24cc9b678a4a41448c7334592521bb91bfa2130e6c`.
Production source/dependencies were unchanged; the existing source tests remain
applicable. New verification comprised 721 mock POSTs, independent static
reconstruction/preflight and the complete paid-request audit. No server was
started and no controls were applied.

This screen used **720 calls**, **$0.064113840** and **1,573,387 charged tokens**.
Final shared ledger: **57,976 / 75,000 requests**, **$7.209357208 / $10**,
**235,712,034 / 250,000,000 charged tokens**, 69 historical uncertain requests
and no pending reservations. All existing limits and historical spending were
preserved. The [latest budget snapshot](model-budget-snapshot.json) contains the
exact ledger.
