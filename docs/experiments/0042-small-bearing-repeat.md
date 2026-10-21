# Repeated small-bearing wheel choices under two factual views

Status: complete, October 20, 2026. All **96 preregistered calls** completed:
full facts **16/48**, reduced facts **43/48**, with **30 paired gains and
three losses**. Five reduced-view wheel errors remain. The final technical
audit, additive reporting supplement and all **71 separate provenance checks**
passed. All 96 original missing-pedal native rejections remain intact.
There is **no accuracy, native or live qualification gate** under any outcome.
The user paused further work at **05:15:14 UTC**; no new experiment is admitted.

Namespace: artifacts/jev-small-bearing-repeat-v1; base seed **2026102042**.
The original prospective registration below is preserved. Its immutable
prospective-design.md retains the precollection text, including the former
06:17:26 UTC deadline, which the user pause supersedes.

The [0040 diagnostic](0040-wheel-isolation.md) found small-bearing straight
wheel errors with full facts and a 15/18 to 18/18 gain after factual deletion.
The fresh broader [0041 replication](0041-wheel-mask-replication.md) scored
**60/60 in both views**, including 30/30 natural and 30/30 synthetic cases
per view. Its final technical audit passed with no errors. The earlier
accuracy advantage therefore did **not replicate**; no differential benefit
or equivalence is established by that ceiling result.

This probe deliberately revisits fresh near-zero bearings with repeated
presentations. It measures observed choice stability and paired factual-view
differences on that focused bank. It does not retry, replace or relabel an
earlier error, change a failed qualification, or select a new driver package.

## Exact inherited wheel question and factual projections

Use the exact 0040 wheel-only question and contexts **`wheel_full`** and
**`wheel_facts`**. Preserve all instruction bytes, physical descriptions,
criterion-local eligibility clauses, component IDs and native meanings,
including the already-neutralized wheel task:

```python
"\nWHEEL TASK: Select the single allowed absolute wheel ID whose supplied policy condition holds. Return only that wheel choice."
```

Do not add deadband-first text, relocate physical definitions, literalize or
rewrite criteria, split COMMON, introduce a namespace, add examples or change
the fixed bearing policy. The wheel question is identical across views when
menu order is matched. Submit only the original `wheel` head.

Construct the complete observation and canonical bearing using the existing
production renderers and pure factual builders. Bearing remains
`round(degrees(atan2(y,x)),4)` from the same three-decimal 15 m preview x/y.
No current-query target, guard result, selected branch, recommendation or
host control enters a model payload.

- `wheel_full` receives the complete unchanged 0034 `facts` projection:
  original units; kart speed; road status, signed offset, both clearances and
  bearing; original three preview columns and sole 15 m row; road-left
  velocity and original frame units; next-gate known status and signed plane.
- `wheel_facts` is the exact 0040 deletion mask: original top-level units;
  road bearing, original preview columns `ahead_m`, `ego_x_m`, `ego_y_m` and
  sole 15 m row's three cells; next-gate known status and signed plane.

All retained scalars, unit strings, table cells and JSON representations must
match their common source exactly. The original unused pedal definitions
remain in COMMON for both views, including in the reduced view where their
facts are absent. This limitation remains part of the unchanged treatment.
The reduced observation is not a complete driving state.

## Twelve fresh small-bearing poses

Generate **six fresh reflected pairs**, twelve synthetic current poses total,
with fixed seed `2026102042`. Every target wheel is **STRAIGHT**, with
absolute canonical bearing **0.05–1.5 degrees** and equal positive/negative
coverage through reflection. Preserve the current supported-domain,
stationary-null rendering and protected guard predicates. In particular,
require finite forward 15 m coordinates, positive finite squared range and
no known positive uncredited next-gate plane.

Freeze these six pair types before any answer:

| Pair | Factual source condition | Source pedal label |
| --- | --- | --- |
| 1 | Stationary, off-road | ACCELERATE: low-speed priority applies even though the guard is true |
| 2 | Fast, near-edge, on-road and moving inward; guard false | ACCELERATE |
| 3 | On-road and moving outward, guard true; speed 2.6–5.4 m/s | COAST |
| 4 | Off-road and moving inward; speed 2.6–5.4 m/s | COAST |
| 5 | On-road and moving outward, guard true; speed 7–11.5 m/s | BRAKE |
| 6 | Off-road and moving inward; speed 7–11.5 m/s | BRAKE |

Thus each source pedal label has **four poses**. Pedal labels and guard
evaluations are audit evidence only: no pedal is requested, scored as a model
choice, or fabricated. Synthetic source guard cases do not establish successful
physical recovery.

The twelve held native inputs are the **twelve non-straight native IDs, once
each**: six base left/hard-left inputs across the three pedals and their
right/hard-right reflections. Freeze the exact assignment. Every held wheel
differs from the straight target, so there is no complete held-input copy of
the target. Held-input coverage remains provenance even where the factual
projection omits that input.

Require distinct rounded 15 m x/y pairs absent from the **25 listed
materialized prior banks, including 0041, and documented demonstrations**.
Freeze the exact exclusion manifest, source reconstruction, proposal ranges,
accepted geometries, canonical pose indices and reflections before paid
collection. Use geometry and labels only, never earlier model answers to
tune this new bank. Freshness is scoped to those materialized banks and demos;
no exhaustive historical-query freshness is claimed.

## Four presentation blocks and exact counterbalancing

For canonical pose index **`i=0..11`** and repetition **`r=0..3`**, assign:

```python
cell = (i + r) % 4
first_context = cell % 2       # 0: wheel_full; 1: wheel_facts
reverse_menu = (cell // 2) % 2
```

Each pose crosses all four first-context/menu cells exactly once. Each view
receives four presentations of that pose, with each menu order twice. Match
the menu between both contexts in each pose/repetition unit. Preserve original
IDs and physical meanings when reversing order; do not remap choices.

Collect repetition blocks **1 through 4** in order. Within block `r+1`,
independently shuffle the twelve pose units using seed **base + 100 + r**:
`2026102142`, `2026102143`, `2026102144`, `2026102145`. Expand each unit into
its first context followed by the other context, two requests per unit.
Each block has six units per first context and six per menu order. Freeze
the complete 96-entry request order before any answer.

There are **48 planned responses per context**, not 48 fresh poses. Repetition
is prospectively registered collection, not a retry after an incorrect answer.
Retain every valid planned response regardless of correctness. No accuracy
stop, format prerequisite, adaptive prompt, provider fallback, replacement or
extra presentation is permitted. Technical, identity, accounting, hard-budget
or deadline failures preserve all attempted and unrun entries and stop further
admission. Use one paid writer and one request in flight.

## Unchanged native rejection and strict raw-wheel validity

Preserve original production `DecisionClient.decide`, transport, `Budget`,
reservation and factored decoder behavior. Every valid planned wheel-only
request must retain the original **missing-pedal native rejection**, with no
action and no native success. Preserve all original typed responses and
production records unchanged, including any technical failure. No returned
value reaches an actuation path; no race advances.

Score the requested original raw wheel head separately. Require a non-refused
typed allowed wheel ID, HTTP/API success, exact dated Jev model and TypeSafe
provider, valid nonempty response ID, reported usage/cost and the exact complete
single-POST ledger transition. Identity and accounting validation must remain
independent of the core decoder, which rejects the missing pedal before some
ordinary native checks. Any unsolicited answer head is a technical stop,
even if its requested wheel is valid; retain the original response and record.

Do not reinterpret an endpoint, requested-head, identity, accounting or
unexpected native-core failure as an expected missing pedal. Never synthesize
a pedal, native action, joint uncertainty or successful native verdict.

## Prespecified reporting and limits

Report:

- Correct wheel choices **0–4 per pose and context**, plus totals out of
  **48 per context**, preserving technical failures and unrun denominators.
- Paired view gains/losses on the **48 pose-by-repetition units**, including
  both-correct and both-incorrect counts. Separate stable errors from changes
  across presentations.
- **Identical-payload literal-choice agreement**. Within each pose/context,
  each menu order occurs twice: compare those two byte-identical saved
  payloads, rather than calling all four menu-varied presentations identical.
  Verify payload equality by saved hashes and report actual pair coverage.
- Menu order, bearing sign and each of the six factual guard/source-pedal
  pair types; chosen-wheel distributions; expected missing-pedal core
  rejections; unsolicited heads and all technical failures.
- Latency, tokens and cost by context and repetition block. Raw probabilities
  and confidence are descriptive, without normalization or calibration claims.

There is no accuracy or differential-effect threshold that admits a driver,
another validation, native controls or live racing. A constant wrong choice
can have perfect repeat agreement; agreement is not correctness. Four
presentations per view on twelve related synthetic poses do not establish
reliability, independence, pedal competence, optimal control or general racing
ability. Provider state and request order may influence replies despite
registered counterbalancing. Mirrors and repeats are not 96 independent
states. Do not pool this focused bank with the distinct 0040/0041 banks as a
single treatment-effect estimate.

## Evidence and resource boundary

The completed 0041 saved boundary is **61,741 requests, $7.595243421999866 and
245,244,034 charged tokens**, with 69 historical uncertain charges and no
pending reservations. **4,755,966 tokens remain**, below the unchanged
five-million-token live admission floor. This diagnostic cannot remove that
resource block or qualify native/live use under any score.

Preserve Python, 24 m track width, stadium handling and actual reflected
geometry, 12 m/s ceiling, 0.12 rad wheel limit, three laps, three-second
rescue, joint `damped` baseline and original application defaults. Production
source remains
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
The current-boot clock qualification is separate runtime evidence, not a model
or native qualification.

Keep the shared **75,000-request / $10 / 250-million-token** hard caps and
the complete **16,384-input + 235,929-output = 252,313-token** reservation
on every wheel-only POST. The admission deadline remains **06:17:26 UTC**.
The 96-call plan does not override actual per-call budget or time admission.

Before collection freeze exact inherited questions, masks, route and source;
case-generation and exclusion manifests; canonical pose/repetition labels;
complete order, menus and repeated-payload hashes; helper and evidence hashes.
Require actual-wire free mocks, strict raw/native-core checks, full-ledger
mutation guards, immutable passing independent preflight and timestamped root
authorization. Free checks make no model calls and leave the real ledger
unchanged. Do not rerun old frozen CLIs against the advanced ledger.

Final independent audit follows root confirmation of writer termination and
reconciles every payload, original native rejection, raw diagnostic score,
repeat comparison and complete ledger transition. Preserve credential-free
raw evidence under ignored artifacts and version exact prompts and audited
summaries. Preserve every previous failed gate and the zero observed 0041
accuracy difference; no follow-up package or paid continuation is selected
automatically.

## Collected results

These are **twelve related synthetic poses**, four presentations per view,
not 96 independent states. Every target wheel was straight. All 96 responses
were strict raw-wheel diagnostic-valid, with zero technical/accounting failures,
unsolicited heads or unrun entries. None produced a complete native action;
all original missing-pedal decoder rejections are preserved.

| Measure | Full facts | Reduced facts |
| --- | ---: | ---: |
| Correct wheels | 16/48 (33.3%) | 43/48 (89.6%) |
| Repetition 1 | 5/12 | 12/12 |
| Repetition 2 | 4/12 | 10/12 |
| Repetition 3 | 3/12 | 10/12 |
| Repetition 4 | 4/12 | 11/12 |
| Normal menu | 7/24 | 21/24 |
| Reversed menu | 9/24 | 22/24 |
| Identical-payload literal agreements | 19/24 | 21/24 |
| Identical pairs with both answers correct | 6/24 | 20/24 |
| Identical pairs agreeing on the same wrong answer | 13/24 | 1/24 |

On the 48 matched pose-by-presentation units, reduced facts gained 30 correct
answers and lost three: net +27, with 13 both correct and two both incorrect.
Each identical-payload comparison uses the two responses with the same pose,
context and menu, verified by saved wire hashes: 24 pairs per view, 48 total.
Full facts had 14 both-incorrect identical-payload pairs, of which 13 repeated
the same wrong choice and one gave different wrong choices. Reduced facts had
one both-incorrect pair. Literal agreement therefore does not imply correctness.

| Pose suffix | Bearing degrees | Full correct /4 | Reduced correct /4 |
| --- | ---: | ---: | ---: |
| 00-a | +0.9405 | 4 | 2 |
| 00-b | −0.9405 | 4 | 4 |
| 01-a | +0.3186 | 2 | 1 |
| 01-b | −0.3186 | 3 | 4 |
| 02-a | +0.6395 | 0 | 4 |
| 02-b | −0.6395 | 1 | 4 |
| 03-a | +1.4002 | 0 | 4 |
| 03-b | −1.4002 | 1 | 4 |
| 04-a | +1.2260 | 0 | 4 |
| 04-b | −1.2260 | 0 | 4 |
| 05-a | +1.3939 | 1 | 4 |
| 05-b | −1.3939 | 0 | 4 |

Reduced-view errors were two hard-left choices on 00-a and three left choices
on 01-a. Full-view choices were straight 16, hard-left 12, hard-right 7, right 8
and left 5; reduced choices were straight 43, left 3 and hard-left 2.
The versioned [summary](0042-small-bearing-repeat-summary.json) retains all
per-pose choices, bearing-sign, menu and repetition breakdowns, uncertainty
fields and original saved-report details. Probabilities and confidence are
descriptive, without calibration or normalization claims.

### Source guard and pedal strata

These are wheel scores grouped by factual source conditions. Pedal labels
are audit metadata, with no requested or observed pedal choices. The reduced
view omits those facts; this grouping does not identify internal causality.

| Source pair | Full correct /8 | Reduced correct /8 |
| --- | ---: | ---: |
| Stationary off-road | 8 | 6 |
| Fast near-edge inward, guard false | 5 | 5 |
| On-road outward, coast | 1 | 8 |
| Off-road inward, coast | 1 | 8 |
| On-road outward, brake | 0 | 8 |
| Off-road inward, brake | 1 | 8 |

Grouped by source pedal, wheel correctness was accelerate **13/16 vs 11/16**,
coast **2/16 vs 16/16**, and brake **1/16 vs 16/16**. Reduced facts helped
most in the coast/brake source strata and worsened the stationary off-road
stratum. The broader 0041 bank's **60/60 in both views** and zero differential
remain unchanged; do not pool the two banks into one treatment-effect estimate.

## Reporting omission, additive correction and provenance

The frozen base audit passed technical integrity and accounting, but its
report omitted two prespecified outputs: identical-payload literal-choice
agreement and explicit guard/source-pedal strata. The original frozen audit,
base report, raw replies, protocol and ledger remain unchanged. A separate
repeat-analysis-supplement.py computed the missing metrics from saved wire
payloads and raw answers; its JSON passed with no errors. No API call or paid
rerun was made. The supplement completes the omitted reporting and preserves
the original omission.

Separate provenance passed **71 checks with errors empty**, independently
matching all 96 wire replies, native rejections, labels, order, complete ledger
transitions, writer/authorization chain, all 48 identical-payload groups and
the additive strata. Root execution IDs bind the saved root confirmation,
rather than an independently queried infrastructure service.

Independent prospective preflight passed at **05:07:59 UTC**. Root authorized
collection at **05:08:10 UTC**, authorization ef154017ad8f46e7a28beeabb0eff2ed.
The writer session was 38768598b6fa49f99d0bbfef7c74cd97, PID 9513/start 547492,
on boot f534ef07-e837-401d-bf64-a0fe7c51e3d3. Root confirmed writer
6f361d/session 26773 exited zero; final audit 41a54f exited zero,
passed:true, complete:true, errors:[]. Collection completed at 05:08:40 UTC;
the base audit passed at 05:08:50 UTC.

| Saved artifact | SHA-256 |
| --- | --- |
| protocol.json | afa3bb05e170bb672550e660eca72b65ce4cebf126e2b362cd5ecf81fa341352 |
| prospective-design.md | d20ee0c8ed3ed564e7ef3bcbc09864fb490a37ec5a2a3ec2dc36d5aaa0a9b05b |
| audit.py | 28c0592b9cb443073af6a89ec02532d66298efd40fdcf043c699818aca6e00cc |
| final-audit.json | 19303ef02454ec9cc683cfdcc3c5f6c52fbc0dccadac8b791602090c0edf38a4 |
| report/summary.json | b86813086bd53cb498574feb81f359bbc40cbf08c48c5a5570057733b701ae87 |
| repeat-analysis-supplement.py | becdc1467948c014573b904c358516337b6a42784899430967f2ccc426df2b34 |
| repeat-analysis-supplement.json | f891612a4473406b50b66d452761d0ce0f67b2db9e016edfb014029ff73d348c |
| collection_provenance.py | 9226d0fb31d3647b23a3b273e0dc86ecbf228665153882ae584f205bfbb80b15 |
| collection-provenance-verification.json | 3d8f4ae644ef284c0f294991b860cac8152c603a63cd8c2991b294072f4639be |

## Cost, limits and user pause

The delta was **96 requests, $0.004836216000004612 and 120,353 charged tokens**,
with no new uncertain charges. Full facts used 63,871 tokens/$0.002572920;
reduced facts used 56,482/$0.002263296. Median latencies were
**233.3653695 ms full / 236.2880295 ms reduced**; means were
260.6245428/280.9989505 ms. This sample shows no latency gain from deletion.
Per-block latency, cost and tokens remain in the saved summary.

The final shared ledger is **61,837 requests, $7.600079637999871 and
245,364,387 charged tokens**, pending empty and the same 69 historical uncertain
charges. **4,635,613 tokens remain**, below the unchanged five-million-token
live guard. Python, physical handling, production source, joint damped baseline
and original application defaults are unchanged.

This focused result identifies a substantial context difference on these
poses, with five reduced-view errors still present. It establishes neither
reliable native control nor playability. Current-boot clock qualification
remains separate runtime evidence. No further validation, native/live race or
promotion is admitted by this diagnostic. The user paused all new work at
**05:15:14 UTC**; the former deadline is superseded, and **0043 has no files or
calls**. See the [eight-hour review](2026-10-19-eight-hour-review.md).
