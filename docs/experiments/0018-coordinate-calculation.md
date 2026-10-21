# Reading preview coordinates and executing the calculation

Status: complete, October 19, 2026 (client date). The user asked to keep
iterating after the [held-wheel comparison](0017-held-wheel-target.md). That
comparison weakened universal current-input copying as an explanation, but its
question revision still produced only 51.4% static accuracy and almost never
selected required full steering. Separate reading the target coordinates from
executing a composite rule before another live change.

## Prospective design

Use 24 fresh synthetic snapshots, twelve mirrored pairs, generated from the
unchanged Python simulation. Twelve are on initial straights and twelve on
curves. The nominal targets balance eight straight, eight moderate and eight
full cases. Current wheels span all five native angles and yaw spans -12/0/+12
deg/s, with one declared transient per geometry rather than another factorial.
Speed is 8 m/s. Reflected fixtures use the clockwise stadium; the live setup
remains the user-selected 24 m stadium, 12 m/s ceiling and 0.12 rad wheel limit.
No physics is advanced and no control is applied.

Geometry is selected by a declared local numerical grid before model responses.
All targets are forward and at least 0.003 rad from a quantizer boundary;
actual minimum margin is 0.007117 rad. Eight geometries distinguish actual x
from replacing it with 15. Twelve break the previous correlation between road
heading-error sign and nominal formula sign (including six nonstraight targets).
Coarse labels still do not identify precise atan execution.

Freeze four kinds of question:

- **Coordinate readback:** choose the actual ordered x/y pair at ahead_m=15
  from four distinct options: the actual pair, the 10 m pair, swapped x/y or
  the 15 m pair with y's sign flipped. Opaque answer IDs rotate evenly.
- **Formula:** choose one of the same five absolute wheel angles using the
  nominal atan equation, or an equivalent signed-ratio range table. Both use
  the same target and expected answer; the finite-precision table is equivalent
  on this bank's margin-separated cases, not exactly at every mathematical tie.
- **Numerator:** from isolated raw x/y values, select 3.6*y rounded to three
  decimal places. No kart state or calculated intermediate is supplied.
- **Denominator:** from the same isolated values, select x*x+y*y rounded to
  three decimals. Numeric answer IDs rotate evenly and all options are distinct.

For readback and formula, compare the existing table with a named representation.
The named condition adds only `preview_target_15m={ahead_m:15,ego_x_m:x,ego_y_m:y}`,
an exact copy of the raw values already present in the unique 15 m row. Retain
the full table and every other observation field. A shared target-location
instruction explains both representations. No numerator, denominator, ratio,
delta, target class or recommended control is added to state. Thus named/table
pairs change factual duplication and salience, not the underlying available
geometry. The isolated arithmetic tasks are separate component tests; they
also remove unrelated state, so their scores are not a pure representation
contrast with full-state formula questions.

Two repetitions produce **384 planned calls**: 96 readback, 192 formula, 48
numerator and 48 denominator. Shuffle case/task units with seed 2026101918,
pair table/named requests where applicable, reverse units and swap pair order
on repetition two. Responses are not seeded. Twenty-four geometries and their
repetitions do not constitute 384 independent examples. Separately correct
readback does not prove that the same internal extraction happened during a
formula request, nor do these mathematical labels establish optimal steering.

## Verification and spending contract

Retain freshly checked `typesafe/jev-1.14`, resolved to
`typesafe/jev-1.14-20261014` at `TypeSafe`, with unchanged prices. One request
in flight, zero client retries, no provider fallback. Save every exact payload,
response and before/after ledger without authentication headers. Stop on the
first endpoint/identity error, preserve attempted cases and leave unrun entries
explicit. Never replace a paid attempt.

Starting ledger: **57,976 requests**, **$7.209357208**, **235,712,034 charged
tokens**, 69 historical uncertain requests and no pending reservations. Preserve
the **75,000-request / $10 / 250-million-token** guards and all prior spending.
Reserve 16,384 input tokens plus the advertised output ceiling through the
existing shared Budget. Hard guards may stop collection without another cap
increase.

The local HTTP mock captured all 384 planned wire bodies and one deliberate
mock failure with zero real calls and an unchanged ledger. It verified exact
state/question contrasts, five unchanged wheel choices and exclusion of oracle
metadata. Freeze fixture, generator, route, order, payload, runner and audit
hashes before the first paid request. Independent review reconstructs snapshots
and computes readback, formula and component answers from the actual supplied
facts without trusting expected IDs.

A strong formula profile must reach at least 90% overall, at least 85% on each
target magnitude, and at least ten percentage points over the fresh table/atan
reference, with a passing audit and zero endpoint errors. Only then may a
separately frozen native-menu check use up to 192 further static calls on fresh
states. No race or preset promotion is automatic. Otherwise finish this
comparison before choosing a further experiment.

Ignored raw evidence is under `artifacts/jev-coordinate-v1/`. The versioned
[exact prompt/generator archive](0018-coordinate-prompts.json) and
[results summary](0018-results-summary.json) preserve the handoff without
publishing raw request logs.


## Results

All **384 planned calls** completed with the frozen dated Jev model and TypeSafe
provider, zero endpoint errors and no new uncertain charges. Table and named
readback were both **48/48**, and isolated numerator calculation was **48/48**.
Isolated denominator calculation was **24/48**. Formula accuracy remained weak:

| Formula question | Straight targets | Moderate targets | Full targets | Overall |
| --- | ---: | ---: | ---: | ---: |
| Table / atan | 0/16 | 16/16 | 4/16 | 20/48 (41.7%) |
| Named / atan | 2/16 | 16/16 | 6/16 | 24/48 (50.0%) |
| Table / ratio bins | 11/16 | 9/16 | 3/16 | 23/48 (47.9%) |
| Named / ratio bins | 12/16 | 14/16 | 0/16 | 26/48 (54.2%) |

Named coordinates add four net correct atan answers: five table-wrong/named-right
pairs and one table-right/named-wrong pair. For ratio bins, the corresponding
counts are ten gains and seven losses, adding three net correct answers. Changing
atan to ratio bins adds three net correct answers in table state (13 gains,
10 losses) and two in named state (10 gains, eight losses). Each contrast has
48 paired responses; the same cases and repetitions recur across contrasts.

The **strong-gain gate fails for every formula profile**. The best overall
profile, named/ratio bins, gains 12.5 percentage points over table/atan, but its
54.2% overall accuracy is below 90% and its full-target accuracy is 0/16, below
85%. The other profiles also miss overall and per-magnitude thresholds. No
optional native-menu validation was triggered, no live race followed this
screen and no driving preset was promoted. Retain `damped`.

Repeated choices were identical on 24/24 table/atan pairs, 22/24 named/atan,
21/24 table/ratio-bin and 24/24 named/ratio-bin pairs. Both readback conditions
and numerator were identical and correct on all 24 repeat pairs. Denominator
choices matched on 19/24 repeat pairs, with 11 pairs correct twice. Stable
responses can be stably wrong; repeat agreement does not establish execution
of the equation.

## Component interpretation and limits

The perfect **separate readback** answers show that Jev can locate and select
the displayed 15 m pair in this factual task. They do not establish that the
same extraction happened inside a separately asked formula question. Adding
the named copy produces only a modest gain here, while the preference for
moderate wheels persists: 44/48 table/atan and 40/48 named/atan answers were
moderate, despite only 16 moderate targets per profile.

A separate, explicitly posthoc inspection found that every wrong denominator
answer matched one of two offered alternatives: **15 matched x*x+y** and
**nine matched 225+y*y**. None selected x+y or a fallback option. The minimum
absolute error was 0.163548 square metres, more than 300 times the 0.0005
rounding half-unit, so these are substantive expression alternatives rather
than three-decimal rounding disagreements. A selected distractor identifies
the selected number, not the model's internal computation.

These component errors do not explain the full-rule errors causally. The
denominator was correct on **0/16 moderate-target component calls**, while
both atan profiles answered the corresponding formula targets **16/16**.
Conversely, denominator accuracy was **13/16 on full-target components**, while
full-target formula accuracy was only 4/16 for table/atan and 6/16 for named/atan.
Using the correct numerator and each selected wrong denominator in an offline
hypothetical calculation changes the coarse wheel label in only eight of the
24 wrong component answers; sixteen preserve it. This calculation neither
supplies a model control nor reveals how separate formula answers were obtained.

Nonzero formula answers usually followed the raw y sign: 44/48 table/atan
choices and all 46 named/atan, 30 table/bin and 36 named/bin choices did so.
The four table/atan exceptions were mirrored straight-target cases that followed
the current road-heading sign instead. This weakens a universal heading-sign
shortcut, without demonstrating arithmetic execution. All six **nonstraight**
heading-sign-mismatch geometries have moderate targets, so heading mismatch
and target magnitude are confounded; their high atan accuracy cannot identify
an independent benefit from resolving sign conflicts. Exact trigonometry also
remains unidentified because omitting atan changes none of these coarse labels.

The separately frozen [literal-expression follow-up](0019-literal-expressions.md)
subsequently completed **192 calls** on fresh numeric geometry, retaining
denominator and full-rule tasks separately while substituting actual coordinate
literals into the written expressions. It improved overall static scores but
regressed full-angle answers and failed its validation gate. That combined
wording change did not qualify a live driver.

## Final verification and spending

The final audit passed all 24 reconstructed observations and labels, 48
arithmetic labels, mirror and coverage checks, frozen helper hashes, all 384
exact request bodies, route identities, unique request/reservation identifiers
and every ledger transition. No entries were omitted, retried or replaced.
The posthoc inspection made zero model calls and left the ledger and frozen
helpers unchanged. No simulation steps or controls were applied in this static
screen. Runtime source fingerprint remains
`588958f4c0bd594064b55c24cc9b678a4a41448c7334592521bb91bfa2130e6c`;
production source and dependencies were unchanged.

This screen used **384 calls**, **$0.028945476** and **711,290 charged tokens**.
Its ending shared ledger was **58,360 / 75,000 requests**, **$7.238302684 / $10**,
**236,423,324 / 250,000,000 charged tokens**, 69 historical uncertain requests
and no pending reservations. These are this screen's ending boundaries; later
experiments may advance the [current shared snapshot](model-budget-snapshot.json).
All existing limits and prior spending were preserved.
