# Literal numbers and explicit products

Status: completed and independently audited, October 19, 2026 (client date). The completed
[coordinate/calculation comparison](0018-coordinate-calculation.md) found perfect
separate readback, but partial formula execution and 24/48 correct isolated
denominators. Its wrong denominator choices matched leaving y unsquared or
substituting 15 for x. Those separate questions do not establish the cause of
formula failures. Test a concrete question revision on fresh numbers.

## Prospective design

Generate 24 fresh synthetic snapshots, twelve reflected pairs, with the same
Python stadium, 24 m width, 12 m/s ceiling, 0.12 rad wheel limit and 8 m/s
fixture speed. Twelve snapshots are on straights and twelve on curves; eight
targets require each magnitude. All actual rounded 15 m x/y pairs and all road
positions differ from studies 0016–0018. Deterministic geometry selection uses
no model responses. The minimum quantization margin is 0.008996 rad. Four cases
distinguish actual x from x=15; fourteen oppose the current heading-sign cue,
including eight nonstraight targets. These are snapshots, not trajectories.

Compare two prompts in two blocks, twice per case: **192 planned requests**.

- Denominator: the previous isolated x*x+y*y question versus a literal
  `(x)*(x) + (y)*(y)` expression containing the raw numbers and an instruction
  to multiply each number by itself before adding. Both use identical isolated
  `{x,y}` state and the same four rotated numeric choices.
- Formula: the previous nominal atan question versus its expression with raw
  numbers substituted and both denominator products written explicitly. Both
  retain the full observation, the same exact named copy of the 15 m coordinates
  and the same five absolute wheel choices.

The host only copies raw coordinates and substitutes their strings. It supplies
no calculated products, sum, ratio, angle or recommendation. Literal substitution
and the explicit multiplication wording change together; the contrast cannot
separate their effects. Every choice remains Jev's answer to a mathematical
quiz, not a claim about optimal steering. Coarse labels cannot identify atan
execution. Multiple-choice arithmetic also does not test unrestricted numeric
generation. Responses are not seeded; repetitions and reflected cases are not
independent samples.

Shuffle case/block units with seed 2026101919; balance which prompt comes first,
then reverse units and swap prompt order for repetition two. Save every exact
payload, response and ledger boundary. Pin `typesafe/jev-1.14`, resolved to
`typesafe/jev-1.14-20261014` at `TypeSafe`, at freshly checked unchanged prices.
Use one request in flight, no client retries, no provider fallback, and stop on
the first endpoint/identity failure. Preserve failures and unrun entries.

## Verification and spending contract

The local mock checks all 192 actual request bodies and one deliberate 503,
with zero model calls and no shared ledger change. Independently reconstruct
all poses, rounded-coordinate math, criteria and literal question text, verify
fresh numeric inputs, then freeze all helper and fixture hashes before collection.
Audit only after the runner exits and the collection marker confirms completion.

Starting ledger: **58,360 requests / $7.238302684 / 236,423,324 charged tokens**,
69 historical uncertain requests and no pending reservations. Preserve the
**75,000-request / $10 / 250,000,000-token** caps. The existing Budget reserves
16,384 input tokens plus the advertised output ceiling for each call. No live
race, source change, handling change or control application is part of this test.

A strong literal formula gain must reach 90% overall, 85% on each magnitude
and ten percentage points over this bank's fresh named baseline, with no endpoint
errors and a passing audit. Only that result can trigger a separately frozen
fresh native-menu static validation of up to 192 calls. Otherwise finish this
iteration; no race or preset promotion follows automatically.

Ignored evidence: `artifacts/jev-literal-v1/`. The versioned prompt archive
preserves exact generator and question-builder source without raw request logs.

## Results

All 192 requests completed, with no endpoint failures, retries, replacements or
unrun entries. The final audit passed fixture reconstruction, independent
formula/Decimal labels, literal question reconstruction, exact captured payloads,
frozen hashes and every saved ledger boundary. It ran after the runner exited
and all 192 records and the completion marker were present.

| Task | Previous question | Literal expression |
|---|---:|---:|
| Isolated denominator | 23/48 (47.9%) | 35/48 (72.9%) |
| Full named-state formula | 22/48 (45.8%) | 29/48 (60.4%) |

Denominator pairs changed from wrong to correct thirteen times and from correct
to wrong once. Formula pairs improved twelve times and regressed five times.
All twelve formula improvements were straight targets and all five regressions
were full targets. The literal prompt selected 35 moderate wheels and thirteen
straight wheels, never full steering; every required full target received a
moderate wheel. Baseline choices were 42 moderate, five full and one straight.
Each pair is the same case and repetition; these counts are descriptive rather
than 48 independent trials. Across repetitions, denominator choices matched on
21/24 baseline and 23/24 literal cases; formula choices matched on 22/24 and
21/24 respectively.

The formula gain concentrates on straight targets, with a full-angle regression:

| Required magnitude | Previous question | Literal expression |
|---|---:|---:|
| Straight | 1/16 | 13/16 |
| Moderate | 16/16 | 16/16 |
| Full | 5/16 | 0/16 |

The literal formula gains 14.6 percentage points overall, exceeding the ten-point
gain requirement, but 60.4% fails the 90% threshold. Straight accuracy is 81.3%
and full accuracy is 0%, both below the 85% per-magnitude requirement. The
conditional native-menu validation was therefore **not triggered**. No further
paid calls, live race, preset promotion or source change followed this comparison.

Literal numbers and explicit products helped these static tasks, but the combined
revision has not produced a reliable calculation prompt. The component task and
full-state formula also differ in context and complexity, so their scores cannot
establish which arithmetic Jev performed while answering the formula question.
Perfect moderate-target performance together with failure at full targets limits
any claim that improved overall accuracy reflects faithful formula execution.
Posthoc decoding found 21 baseline and eight literal denominator errors matched
`x*x+y`; four baseline and five literal errors matched `225+y*y`. Under an
offline hypothetical with the correct numerator, every one of these 38 selected
wrong denominators still gives the prescribed coarse wheel label on this bank.
Those separate denominator mistakes alone therefore cannot reproduce the
observed formula-label failures. This checks the consequences of chosen scalar
answers; it does not reveal Jev's internal denominator during a formula request.
Retain `damped` as the live baseline and keep the original application default.
An explicit magnitude comparison is a possible next static hypothesis; this
iteration does not justify promoting the literal prompt on its overall score.

This follow-up charged **$0.011067672** and **274,570 tokens** for 192 requests,
with no new uncertain charges. The two studies 0018–0019 together added **576
requests / $0.040013148 / 985,860 tokens**. Current shared ledger: **58,552/75,000
requests / $7.249370356/$10 / 236,697,894/250,000,000 charged tokens**; 69 historical
uncertain requests, no pending reservations. The remaining guards allow 16,448
request slots, $2.750629644 and 13,302,106 charged-token slots; per-call admission
still reserves the advertised output ceiling.

The [results summary](0019-results-summary.json) preserves audited groups, paired
counts, the exact gate decision and the experiment's ledger boundary. The
[prompt archive](0019-literal-prompts.json) preserves the frozen generator,
payload builder, preparation source and hashes.
