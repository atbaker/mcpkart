# Six worked examples for the steering calculation

Status: completed and independently audited, October 19, 2026 (client date). The user approved testing six
fixed worked examples after the [literal-expression study](0019-literal-expressions.md).
That revision improved overall formula accuracy but selected moderate wheels for
all sixteen full targets. This comparison tests whether demonstrations improve
the complete calculation and quantized choice on fresh inputs.

## Prospective design

Compare the exact previous literal-expression prompt against the same prompt
with six fixed worked examples inserted before the current question. Each example
shows numerator, denominator, ratio, atan in radians, nearest wheel and answer ID.
Two examples require each magnitude, with positive and negative y represented.
The fixed order interleaves magnitudes and directions:

| Order | x | y | Approximate delta, rad | Absolute wheel target, rad |
|---|---:|---:|---:|---:|
| 1 | 15 | +4 | +0.05968008 | +0.06 |
| 2 | 10 | -5 | -0.14301687 | -0.12 |
| 3 | 15 | +1 | +0.01592786 | 0 |
| 4 | 15 | -4 | -0.05968008 | -0.06 |
| 5 | 10 | +5 | +0.14301687 | +0.12 |
| 6 | 15 | -1 | -0.01592786 | 0 |

These demonstration inputs and worked answers are fixed before test responses.
They are separate mathematical questions; their coordinates do not overlap the
test bank. The current question is identical between conditions, including its
literal expression containing raw test x/y values. The host supplies no calculated
intermediate, angle or recommendation for the current query. Both conditions
retain the identical full observation, exact named raw-coordinate copy and same
five physical wheel criteria. Only the demonstration text and its wrapper change.
This tests the complete example package, including added length and wording;
it cannot attribute gains to one clause or establish internal calculation steps.
Only one fixed demonstration order is tested.

Use 24 fresh synthetic snapshots: twelve mirrored pairs, twelve straight-region
and twelve curve, with eight targets per magnitude. Rounded 15 m coordinate pairs
and requested road positions are absent from studies 0016–0019; demonstration
coordinates are also excluded. Deterministic geometry selection reads only prior
fixture geometry fields, never prior model responses. The minimum quantization
margin is 0.005034 rad. Four cases distinguish actual x from x=15; fourteen
oppose the current heading-sign cue. Coarse labels still cannot identify exact
atan execution. The fixed Python simulation uses the 24 m stadium, 12 m/s
ceiling and 0.12 rad wheel limit; fixture speed is 8 m/s, with balanced held
wheels and yaw transients. No simulation is advanced or control applied.

Two prompts and two repetitions yield **96 planned requests**. Shuffle cases
with seed 2026101920; balance which prompt comes first, then reverse case order
and swap pair order for repetition two. Responses are not seeded. Repetitions
and mirrored cases are correlated; 96 answers are not 96 independent geometries.
Report accuracy by magnitude and direction, region and heading-sign mismatch,
paired changes and repetition stability. Full-target accuracy is a key result;
a gain confined to straight targets cannot qualify the candidate.

## Verification, spending and continuation

Pin freshly discovered `typesafe/jev-1.14`, resolving to
`typesafe/jev-1.14-20261014` at `TypeSafe`, with unchanged prices. Keep one
request in flight, zero client retries, no provider fallback. Save every exact
credential-free payload, response and ledger boundary; stop on the first endpoint
or identity error. Retain failed attempts and unrun entries without replacements.

Starting ledger: **58,552 requests / $7.249370356 / 236,697,894 charged tokens**,
69 historical uncertain requests, no pending reservations. Preserve the shared
**75,000-request / $10 / 250,000,000-token** guards. The existing Budget reserves
16,384 input tokens plus the advertised output ceiling for each request. Hard
guards may stop collection without increasing any limit or resetting history.

The local mock captures all 96 planned actual wire bodies and a deliberate503,
without real model calls or ledger mutation. An independent audit reconstructs
the snapshots and labels, verifies the six worked calculations and exact text,
checks demo/test exclusions and unchanged current questions, and reconciles all
request/accounting records. Freeze all helpers, examples, fixtures, route and
order before paid collection. Run final audit only after the runner exits and
the completion marker, all records and empty pending reservations are verified.

Require **90% overall**, **85% within each magnitude**, **ten percentage points
over the fresh literal baseline**, a passing audit and zero endpoint errors.
Only a passing gate can trigger separately frozen fresh native-menu static
validation, bounded to 192 additional calls. Otherwise finish this comparison
without further paid calls. No live race or preset promotion is automatic;
static formula accuracy does not establish optimal controls or driving skill.

Ignored evidence lives under `artifacts/jev-examples-v1/`. The versioned prompt
archive preserves exact examples, generator, payload builder, preparation source
and hashes without publishing raw request logs.

## Results and gate decision

All 96 requests completed with the pinned dated model and provider, zero endpoint
errors and no new uncertain charges. The independent final audit passed after
runner exit, the completion marker, all records and an empty pending ledger
were verified. It checked all six demonstration calculations and exact text,
24 reconstructed snapshots and labels, 96 exact payloads, frozen helpers and
every request/accounting boundary. Runtime source and dependencies were unchanged.
Targeted Ruff checks passed for the payload, preparation, preflight, audit and
plot helpers. A broader artifact-only check reports four style findings in the
frozen generator and copied runner (redundant integer cast, implicit string
concatenation and import order). Their audited bytes are retained for provenance;
these findings do not change the recorded payloads or results.

| Required formula target | Literal control | With six examples |
|---|---:|---:|
| Straight | 13/16 (81.3%) | 13/16 (81.3%) |
| Moderate | 16/16 (100%) | 16/16 (100%) |
| Full | 2/16 (12.5%) | 5/16 (31.3%) |
| Overall | 31/48 (64.6%) | 34/48 (70.8%) |

The examples add three net correct answers, **6.25 percentage points**. Paired
responses change from wrong to correct five times and from correct to wrong
twice. These are forty-eight paired responses over the same 24 snapshots,
including repetitions and mirrors, rather than independent trials. The two
repetitions choose the same answer on 23/24 control cases and 22/24 example
cases; both repetitions are correct on 15/24 and 16/24 respectively.

The candidate fails all three performance requirements: 70.8% is below 90%
overall; straight accuracy 81.3% and full accuracy 31.3% are below 85%; the
6.25-point gain is below ten points. The independent audit and zero-error checks
pass. **Native-menu validation was not triggered.** No additional paid calls,
live race or preset promotion followed this comparison. Keep `damped` as the
live baseline and retain the original application default.

## Interpretation

The modest gain is confined to full-right targets in net counts. Full-right
accuracy rises 2/8→5/8; full-left stays 0/8. Moderate-left and moderate-right are
both 8/8 under each prompt. All selected full wheels are right turns. Overall
left-direction accuracy stays 8/16, right rises 10/16→13/16, and straight stays
13/16. This asymmetry limits the value of the gain for a driver needing both
turn directions.

Posthoc paired decoding finds three full-right gains and two straight gains;
both regressions are repetitions of one straight case. Thus the unchanged
straight total hides different correct and incorrect fixtures. On the four
x=15-discriminating cases, both prompts score 4/8 responses: both full-target
mirrors incorrectly receive moderate steering, while both moderate-target
mirrors are correct. The examples do not improve that small diagnostic subset.
Every nonzero selected wheel follows the raw target y sign under both prompts,
which does not establish that the numerical magnitude was calculated correctly.

These results concern one fixed demonstration package and order. They do not
separate demonstration content, formatting, answer IDs, repeated rule text or
additional length. A correct coarse wheel label also does not prove exact
arithmetic or atan execution. Different studies use fresh geometry, so compare
each candidate with its own paired control; the increase from a previous study's
score is not an independently measured improvement. Mathematical compliance
with this supplied rule is separate from the rule's quality as a driving policy.

## Spending and artifacts

This comparison used **96 calls / $0.010746288 / 262,130 charged tokens**, with
zero new uncertain requests. Ending shared ledger: **58,648/75,000 requests /
$7.260116644/$10 / 236,960,024/250,000,000 charged tokens**, 69 historical
uncertain requests, no pending reservations. All prior charges and hard limits
were preserved. Remaining guards allow 16,352 request slots, $2.739883356 and
13,039,976 charged-token slots, subject to the conservative per-call reservation.

The [results summary](0020-results-summary.json) preserves audited groups,
paired and repeat counts, the exact failed gate and the experiment's budget
boundary. The [prompt archive](0020-example-prompts.json) preserves the six
worked examples and all frozen source strings and hashes. A chart is generated
from these verified summaries under `artifacts/jev-examples-v1/report/`.
