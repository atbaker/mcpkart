# Observation context and answer menu

Status: complete and independently audited, October 20, 2026. First comparison in the user-authorized
[six-hour session](2026-10-20-six-hour-session.md). Prior menu changes improved
full targets while worsening moderate targets. Test whether unrelated telemetry
affects the same calculation and whether that depends on menu presentation.

## Frozen design

Twenty-four fresh synthetic snapshots, twelve reflected pairs, balance eight
straight, eight moderate and eight full targets. Twelve snapshots are on straight
regions and twelve on curves; held-wheel and yaw transients remain balanced.
All rounded 15 m x/y pairs and requested road positions are absent from studies
0016–0021 and the six demonstration coordinate pairs. The deterministic generator
reads geometry fields only, never model responses. Minimum quantization margin
is 0.006068 rad. Six cases distinguish actual x from x=15, fourteen oppose the
current heading-sign cue; coarse labels do not identify exact atan execution.

Cross two state presentations with two menus, for 192 calls (24 × 4 × 2 repeats):

| Context | State | Menu |
|---|---|---|
| A `full_physical` | Full telemetry plus named raw 15 m coordinates | Existing semantic IDs and physical descriptions |
| B `raw_physical` | Only raw `{x,y}` | Same physical menu |
| C `full_numeric` | Same full telemetry | Rotating opaque IDs and signed-radian descriptions |
| D `raw_numeric` | Only raw `{x,y}` | Same numeric menu |

All four receive the **identical factual wrapper and literal atan question**
containing the raw coordinate numbers. Remove the target-locator paragraph in
every condition so the raw-only condition receives no reference to an absent
table. No current-query numerator, denominator, ratio, angle or answer is
computed by the host. Full-state named coordinates are exact copies. There
are no worked examples or control applications.

Use the same five absolute angles in all menus. Match physical insertion order
within each case/repetition and match opaque mappings across C and D. Shuffle
cases with seed 2026102022; cycle angle order and opaque assignments independently
as in 0021. Every angle occupies each submitted position and opaque ID nine or
ten times across 48 units; each condition occupies each request position twelve
times. Reverse case and condition order for repetition two. Compare answers
and repeat stability as physical angles rather than raw IDs. Provider-internal
option order is unknown; cyclic presentation changes are part of these repeats.

Prespecify state contrasts B−A and D−C; menu contrasts C−A and D−B; and combined
D−A. State main effect averages B−A and D−C; menu main effect averages C−A and
D−B. Report interaction, each magnitude, direction, region, heading mismatch,
paired changes and changed-presentation stability. Repetitions and reflected
fixtures are correlated. Removing telemetry changes both information load and
driving context; an effect cannot isolate an internal attention mechanism.

## Qualification and limits

Require 90% overall, 85% in each magnitude, a ten-point gain over A, zero endpoint
errors and passing independent audit. **Only C retains full driving facts and
is eligible for a native-menu continuation.** B and D are diagnostic: their raw
state omits speed, progress, recovery and motion information. A raw-state gain
must transfer to a separately tested representation retaining all driving facts
before considering live use. A qualifying full-state candidate needs separately
frozen fresh native-menu validation (at most192 calls); no race or promotion
is automatic. Supplied-policy accuracy does not establish optimal steering.

Pin freshly discovered `typesafe/jev-1.14`, resolving to
`typesafe/jev-1.14-20261014` at `TypeSafe`, at unchanged prices. One request
in flight, no retries or provider fallback; stop at the first endpoint/identity
error and preserve failures/unrun entries. Save exact credential-free payloads,
responses and all ledger boundaries. Starting ledger: **58,840 requests /
$7.278268036 / 237,404,036 charged tokens**, 69 historical uncertain requests,
no pending reservations. Preserve **75,000 requests / $10 / 250 million tokens**
and the conservative16,384-input plus advertised-output reservation.

The mock captures192 actual wire bodies plus a deliberate503 without model
calls or ledger changes. Independent review reconstructs geometry/atan2 labels,
freshness, locator-free questions, full/raw inputs, physical menu equivalence,
opaque mappings and ordered wire serialization. Freeze every helper and fixture
hash before paid collection; final audit follows runner exit, completion marker,
all saved records and empty pending reservations. The runner checks the session
deadline **06:17:26 UTC** before each request and records an admission stop
without starting another call if time expires. Production source/handling remain
unchanged; this is a static test, not a timed race.

Evidence: ignored `artifacts/jev-context-v1/`, plus versioned exact prompt archive
and audited summary. Every later round must preserve the shared ledger.

## Results

All **192 requests** completed with the frozen dated Jev model and TypeSafe
provider, zero endpoint errors and no new uncertain charges. No request was
retried, replaced or omitted. The final audit passed after runner exit, all
saved records and the completion marker were present, and pending reservations
were empty.

| Required target | A Full / physical | B Raw / physical | C Full / numeric | D Raw / numeric |
|---|---:|---:|---:|---:|
| Straight | 14/16 | 5/16 | 11/16 | 4/16 |
| Moderate | 16/16 | 14/16 | 15/16 | 12/16 |
| Full | 3/16 | 13/16 | 10/16 | 16/16 |
| Overall | 33/48 (68.8%) | 32/48 (66.7%) | 36/48 (75.0%) | 32/48 (66.7%) |

Removing telemetry improves full-target answers but loses many straight-target
answers. Under the physical menu, full accuracy rises from 3/16 to 13/16 while
straight accuracy falls from 14/16 to 5/16. Under the numeric menu, the respective
changes are 10/16 to 16/16 and 11/16 to 4/16. Overall accuracy falls with raw
state in both menus. This does not support removing the full driving facts as
a general calculation improvement.

The full-state numeric menu gains three net correct answers over A, but its
full-left accuracy is 2/8 versus 8/8 for full-right. The raw numeric condition
answers both full directions 8/8, while answering only 4/16 straight targets.
These shifts concern the magnitude of a supplied mathematical target; they do
not establish better driving or an internal attention mechanism.

## Matched contrasts and presentation changes

| Prespecified contrast | Wrong to correct | Correct to wrong | Net correct gain |
|---|---:|---:|---:|
| B−A: raw state, physical menu | 11 | 12 | −1/48 |
| D−C: raw state, numeric menu | 7 | 11 | −4/48 |
| C−A: numeric menu, full state | 9 | 6 | +3/48 |
| D−B: numeric menu, raw state | 3 | 3 | 0/48 |
| D−A: both changes | 14 | 15 | −1/48 |

The matched state main effect is **−5.21 percentage points**, averaging the
two raw-minus-full contrasts. The menu main effect is **+3.13 points** and the
interaction is **−6.25 points**. These are descriptive matched differences,
not independent-sample significance tests. The state contrast changes telemetry
content and length together; the menu contrast changes both IDs and descriptions.
Neither identifies a particular internal reasoning mechanism.

Across the two presentations of each case, the selected physical angle matches
on 21/24 A cases, 19/24 B, 18/24 C and 22/24 D. Both answers are correct on
15/24, 14/24, 15/24 and 15/24 cases respectively. Submitted angle order changes
between presentations, and numeric menus also change their ID assignments.
These are presentation comparisons rather than identical-request repeatability
tests. Provider-internal option order remains unknown, and mirrored cases and
repeated responses remain correlated.

## Qualification decision

**C is the only eligible full-state candidate and fails the frozen gate.** Its
75.0% overall accuracy is below 90%; full accuracy of 10/16 and straight accuracy
of 11/16 are below 85%; its gain over A is 6.25 points, below ten points. The
passing audit and zero endpoint errors do not overcome these quality failures.
No native-menu continuation, live race or preset promotion was triggered.

B and D are diagnostic only. They omit speed, progress, recovery and motion
facts, so even a strong raw-state result would need to transfer to a separately
tested representation preserving those facts before live qualification. Their
overall and subgroup scores also fail the numerical gate here.

Retain `damped` as the live baseline, with Python and the 24 m stadium. The next
separately frozen static hypothesis changes the algebraic presentation of the
same rule to avoid division and atan, while retaining full state. It is a new
question comparison under the ongoing session, not qualification earned by
this failed gate. No current-query products, ratios, angles or recommendations
are supplied by the host.

## Final audit and spending boundary

The final audit independently reconstructed all 24 observations and mathematical
labels, verified mirror and freshness contracts, all 192 ordered payloads,
matched raw inputs and physical choices, opaque mappings, request order, model
identity and every saved ledger transition. Frozen helper hashes and production
source fingerprint remain recorded in the
[audited summary](0022-results-summary.json). The source fingerprint is
`588958f4c0bd594064b55c24cc9b678a4a41448c7334592521bb91bfa2130e6c`.
No simulation step or control application was part of this static comparison.

This comparison used **192 calls / $0.011092704 / 275,939 charged tokens**, with
no new uncertain charges. Its ending shared ledger was **59,032/75,000 requests**,
**$7.289360740/$10**, and **237,679,975/250,000,000 charged tokens**; 69 historical
uncertain requests and no pending reservations. These are this comparison's
completed boundaries. Later rounds may advance the
[current shared snapshot](model-budget-snapshot.json); no historical charge or
limit is reset.
