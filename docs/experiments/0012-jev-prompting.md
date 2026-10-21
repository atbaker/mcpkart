# Jev prompt comparisons on fixed courses

The `damped` question preset improved assisted driving on the fixed stadium.
In three paired starts, rescues were **3, 5, 3** versus **11, 24, 11**, with
3/3 finishes versus 2/3. An exploratory continuation with the unchanged preset
finished **10/10** candidate starts, median **110.63 s (1.43× reference)** and
**five rescues**. No candidate finished without rescue. All 12 original winding
pilots failed to finish, so the original clean-driving milestone remains open.

Status: model experiments complete October 19, 2026; promoted-source free clock validation passed. The user approved a **50,000-request** ceiling,
retaining the one shared **$10** cap, and prioritized improving the decision
model's prompting. Starting ledger: 24,933 requests, $2.499126424 charged,
117,233,513 charged tokens, 65 uncertain requests, no pending reservations.
The 250,000,000-token guard is unchanged. The locked administrative change is
recorded under `artifacts/jev-prompts-v2/request-limit-authorization.json`.

Reopening a ledger now preserves its saved request limit when no explicit limit
is passed. New ledgers still default to 25,000; explicit limits can only lower
an existing limit. The hard $10 constructor limit remains in force. No spending
history was reset or reclassified.

## Protocol

Use the process-isolated **Python** runtime with asyncio pacing and the existing
60 Hz simulation. Qualify the complete free timing gate on the current source
before paid driving. Keep one request in flight, native direct controls, no
retries or provider fallback, ordered finite gates, three laps, the existing
three-second rescue rule, and a deadline of three paired reference durations.
Keep every failed attempt. Stop a batch on endpoint or timing errors and
investigate before more paid trials. Successful responses must retain the
previously resolved Jev model and TypeSafe provider identity.

The first comparison changes only `numeric` versus `geometry` input descriptions,
with the original instructions and `road_navigation` telemetry, on:

- Original winding: 9 m road, 24 m/s speed ceiling, 0.32 rad wheel range.
- Stadium: 16 m road, 12 m/s speed ceiling, 0.12 rad wheel range.

Course and handling stay fixed within each comparison. Prior league results are
historical context, not newly paired replicas. Additional prompting will be
screened on fixed recorded states spanning both correction directions, then
validated through complete live attempts. Static choices alone do not establish
better driving. No course or handling changes are planned in this phase.

The predeclared prompt screen uses five versions of the same geometry menu:
original instructions; a concise present-alignment question; balanced left/right
examples plus that question; per-choice applicability rubrics; and an explicit
unwinding/response-lag reminder. The rubrics are exactly symmetric under
left/right reflection and retain all 15 native control IDs. The static screen
uses the previous eight development states plus their synthetic local reflections,
three repeats per version (240 calls), with rotated order. These states are not
untouched holdouts. Every candidate then gets a complete seed-zero live screen
on each of the two fixed setups; replicas are contingent on actual driving.

## Timing and initial baselines

Source `429ac85d294dec7c7dab10cffaa34e9cea4333c90fd49aff7781b80e59c0e95a`
passed the complete free gate: three winding races, including the HTTP-parent
pause, and a 170.1 s neutral-control check. Worst race lateness was 29.362684 ms;
the long check had 16.438621 ms maximum, 1.644882 ms p95 and 0.679035 ms drift.
The paired live stadium reference finished in 77.2833 s without rescue. Tests:
349 passed, three optional Rust skips; Ruff and diff whitespace checks passed.

All four initial paid attempts passed timing and independent exact replay, with
no endpoint errors. Each row is a single seed-zero screen, not qualification.
The model is not seeded; identical initial poses do not produce identical choices.

| Fixed setup | Choice descriptions | Gates | Finish time / deadline | Rescues |
| --- | --- | ---: | ---: | ---: |
| Winding original | Numeric | 16/120 | deadline 170.10 s | 24 |
| Winding original | Geometry | 90/120 | deadline 170.10 s | 27 |
| Stadium 12 m/s | Numeric | 120/120 | 116.65 s | 9 |
| Stadium 12 m/s | Geometry | 120/120 | 166.25 s | 16 |

Geometry is not a demonstrated general improvement. The winding numeric run
spent 75.05 s between gates 15 and 16, while the geometry stadium run spent
46.45 s between gates 108 and 109. Winding geometry still chose left inputs in
many outward-left drift states. Its 90 gates do not exceed the previous numeric
95-gate historical screen. Stadium geometry exceeds twice its 77.28 s reference.

The 240-call static screen cost $0.032060826 and completed without endpoint
errors. Examples changed the late original left-drift snapshot to right steering
in 3/3 repeats, but kept right steering on its reflected counterpart. Rubrics
corrected some oval left-drift snapshots while failing their reflections. The
unwinding reminder was also inconsistent. This repeats the earlier warning that
an isolated corrected choice is insufficient evidence for a better driver.

## Question salience and fixed demonstrations

The next frozen comparison keeps the entire `road_navigation` state and geometry
menu. It changes where factual measurements appear: an instruction prefix repeats
current road tangent versus nose, actual wheel angle, actual yaw, speed, offset,
edge clearances, the 3/6/10 m centreline positions and the still-required gate's
plane/bearing. This prefix describes measurements; it does not select or rank an
input. Each actual submitted question is saved in the request record.

A second factor supplies fixed state/control demonstrations. All eight earlier
minimal-probe fixtures are annotated once offline using the existing reference
policy, and paired with their local reflections (16 examples total). The live
prompt includes the eight matching the kart's wheel range. Their individual
handling/speed facts remain explicit. These labels are reference-policy choices,
not proof of uniquely correct actions. The teacher is never called during live
driving. The model continues to select one of the same 15 direct joint inputs.

The 16 new static development fixtures come from the fresh geometry baselines:
the first outward-left drift, outward-right drift, missed-gate and aligned state
on each setup, each paired with its local reflection. Selection preceded new
candidate answers. Three repeats of baseline, salience, demonstrations and their
combination produced 192 successful calls for $0.052036488. Combined salience and
demonstrations selected opposite steering on both the stadium outward-left state
and its reflection in all three repeats; their strengths still differed. Most
versions kept steering left on the winding outward-left state. Complete live
screens remain necessary. Raw protocols, helper hashes, exact examples, actual
wire bodies and native choices are preserved under `artifacts/jev-prompts-v2/`.

One request in the earlier worked-example winding screen timed out after
5.006974 s at observation tick 3430. Its full $0.001376256 reservation was charged;
377 successful replies followed in that same attempt. The batch stopped after
preserving the full recording. Exact replay passed, managed credential readiness
remained current/ready, and the new 192-call screen succeeded before remaining
live candidates resumed. The endpoint-impaired attempt is retained, not replaced
by a retry, and is distinguished from clean prompt comparisons.

## Complete first prompt screens

All eight predeclared screens are retained and timing-valid. These are single
seed-zero pilots; two contain one endpoint timeout each.

| Fixed setup | Prompt | Gates | Finish / deadline | Rescues | API errors |
| --- | --- | ---: | ---: | ---: | ---: |
| winding24 | concise | 47/120 | 170.10 s | 22 | 0 |
| winding24 | examples | 28/120 | 170.10 s | 25 | 1 |
| winding24 | rubrics | 46/120 | 170.10 s | 27 | 0 |
| winding24 | damped | 55/120 | 170.10 s | 21 | 0 |
| stadium12_gentle | concise | 120/120 | 132.47 s | 7 | 0 |
| stadium12_gentle | examples | 120/120 | 94.40 s | 4 | 0 |
| stadium12_gentle | rubrics | 120/120 | 141.78 s | 8 | 1 |
| stadium12_gentle | damped | 120/120 | 98.07 s | 2 | 0 |

No first-phase prompt completed winding. The stadium unwinding reminder (two
rescues) and balanced examples (four) are promising only as pilots. Any later
replication compares against the original instructions with the same geometry
menu to isolate the instruction factor.

The rubric stadium screen had a final-request timeout at tick 8412, charged its
full $0.001376256 reservation. The kart finished during the wait. Exact replay
passed; readiness stayed current/ready. Four fresh aligned-state endpoint checks
then succeeded for $0.000449316 before the final unrun candidate resumed. Both
error-affected attempts remain in the dataset.

## Choice naming and applicability: predeclared follow-up

A third prompt comparison is frozen before its answers. It crosses two factors:
canonical versus arbitrary choice IDs, and geometry-only versus positive
near-corridor applicability criteria. All four versions retain the original
instructions, full `road_navigation` state, the same 15 physical joint inputs,
and their original order. The applicability text is fixed for each input and
describes its use for a large/small heading correction; it does not inspect the
current state or calculate a recommended control.

The opaque IDs use a fixed, audited bijection. The native selected label and the
canonical physical input are both recorded. This is a label conversion only:
there is no ranking, smoothing, fallback, or control adjustment. Credential-free
mock checks must verify every alias before paid calls. The static development
screen uses all 16 new fixtures, three repeats of four versions (192 calls),
followed by six complete seed-zero live screens on the same two configurations.
Its protocol and mapping are under `artifacts/jev-prompts-v2/menu-protocol.json`.

## Held-out validation rule

Before any held-out answers, freeze the selection rule: require a completed,
timing-valid, exactly replayed experimental pilot with no endpoint errors.
Prefer a completed original winding candidate if one exists; otherwise use
stadium. Minimize rescues, then elapsed time. Compare the selected prompt with
the original instructions and geometry menu on seeds 1, 2 and 3, alternating
order (baseline/candidate, candidate/baseline, baseline/candidate). These starts
are held out from this phase's prompt selection, not claimed to be novel global
track designs. Preserve old references; create separate paired references and
run a free live seed-three control before paid validation.

If all three candidate runs finish within twice reference and at least two need
zero rescues, extend the candidate to seeds 4–10. Otherwise report the three-start
replication and leave the ten-start milestone unproven. Every attempted case is
retained; endpoint errors do not trigger replacement of a held-out case.

## Complete salience/demonstration screens

| Fixed setup | Prompt | Gates | Finish / deadline | Rescues | API errors |
| --- | --- | ---: | ---: | ---: | ---: |
| winding24 | salient | 8/120 | 170.10 s | 27 | 0 |
| winding24 | demos | 50/120 | 170.10 s | 29 | 0 |
| winding24 | salient_demos | 25/120 | 170.10 s | 32 | 0 |
| stadium12_gentle | salient | 120/120 | 108.05 s | 6 | 1 |
| stadium12_gentle | demos | 107/120 | 231.85 s | 26 | 0 |
| stadium12_gentle | salient_demos | 120/120 | 139.00 s | 8 | 0 |

All six attempts passed timing and exact replay. The larger demonstration bank
did not improve these live screens. Static improvements on the stadium drift
fixture and its reflection did not establish clean race performance. The
salience-only stadium attempt had a single 5.006835 s timeout at tick597, charged
its full $0.002752512 reservation, followed by 311 successful replies. After
replay and current/ready environment checks, all 192 menu-screen requests
succeeded before the final unrun context cases resumed. No failed attempt was
replaced.

## Paired held-out result

The frozen rule selected `damped` instructions with the geometry menu on stadium.
The new offline references contain seeds 0–10, all zero-rescue finishes. The live
free seed-three control finished in 77.2833 s with zero rescues and 21.964896 ms
maximum clock lateness before paid validation.

| Seed | Original time | Rescues | Gates | Damped time | Rescues | Gates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 122.12s | 11 | 120/120 | 91.22s | 3 | 120/120 |
| 2 | 231.55s (deadline) | 24 | 108/120 | 103.25s | 5 | 120/120 |
| 3 | 120.80s | 11 | 120/120 | 133.65s | 3 | 120/120 |

All six assigned attempts passed timing and exact replay with no API errors.
The candidate finished 3/3 versus 2/3, with median rescues **3 versus 11**. It
reduced rescues on all three paired starts. It was slower on seed three, so this
is not a uniform speed gain. That candidate's longest gate gap was only 5.85 s;
its median on-road speed at observation times was 7.889 m/s, illustrating the
trade-off between avoiding rescues and maintaining speed.

The candidate had **0/3 zero-rescue finishes**. The preregistered clean-driving
expansion rule failed and no clean-driving qualification is claimed. A separate
exploratory assisted-driving follow-up was then declared for seeds 4–10, with the
same frozen prompt, physics, references, limits and route. It will report all ten
candidate starts descriptively; only seeds 1–3 have paired baseline controls.
No prompt was retuned after these held-out answers. All failed and error-affected
attempts stay in the dataset.

## Complete choice-name/criteria screens

| Setup | Variant | Gates | Finish / deadline | Rescues |
| --- | --- | ---: | ---: | ---: |
| winding24 | opaque | 37/120 | 170.10s | 29 |
| winding24 | situational | 55/120 | 170.10s | 24 |
| winding24 | opaque_situational | 60/120 | 170.10s | 24 |
| stadium12_gentle | opaque | 120/120 | 136.48s | 14 |
| stadium12_gentle | situational | 120/120 | 106.70s | 7 |
| stadium12_gentle | opaque_situational | 120/120 | 179.22s | 11 |

All six passed timing and exact replay without endpoint errors. Neither renaming
the choices nor adding these applicability criteria established a useful gain
over the selected guide. The static screen also changed few decisions.

## Ten-start assisted follow-up

The seven additional starts were declared after the clean-driving gate failed;
this is an exploratory assisted follow-up, not a passed preregistered clean-driving
qualification. Only seeds 1–3 have matched baseline controls. The prompt was
never retuned during validation.

| Seed | Finish time | Rescues | API errors |
| --- | ---: | ---: | ---: |
| 1 | 91.22s | 3 | 0 |
| 2 | 103.25s | 5 | 0 |
| 3 | 133.65s | 3 | 0 |
| 4 | 110.13s | 4 | 0 |
| 5 | 122.28s | 5 | 0 |
| 6 | 111.13s | 5 | 0 |
| 7 | 124.13s | 7 | 1 |
| 8 | 99.72s | 5 | 0 |
| 9 | 147.10s | 7 | 0 |
| 10 | 97.60s | 4 | 0 |

All ten finished three laps, each within twice its seed's reference duration.
Median rescues were five, total 48; none was rescue-free. Seed seven contained
one 5.007455 s timeout, conservatively charged $0.001376256. Another 214 successful
responses followed in that attempt. Replay and current credential/network
readiness checks passed before only the unrun seeds resumed. The affected case
is included, with its seven rescues; it was not replaced.

These results support a limited assisted-driving improvement, not general
navigation or clean driving. The earlier constant-turn stadium controls also
completed with many rescues; completion alone is a weak test here. The guide
reduced rescues in the paired comparison but was slower on the third seed.
The comparison tests the whole preset and does not identify one sentence as the
cause. Original-course viability remains unmet.

## Reusable preset and exact text

`--instruction-style damped` exposes the exact tested question. Use it with
`--telemetry road_navigation --control-language geometry`. The guide describes
absolute wheel settings, asks for the gentlest adequate correction, and reminds
the model to unwind before yaw overshoots alignment. Its concise base also
prioritizes near-road alignment and explains the still-required gate. It chooses
no input in code. All 15 joint inputs remain available, and the model's native
choice is passed directly to MCP. The original instructions remain the default.

[Exact tested question text, menus and alias mapping](0012-prompt-texts.json)
are versioned without raw race recordings. Longer demonstration banks, literal
measurement salience and alternative labels are retained as experimental
results, not promoted defaults. The new preset's instructions, all 15 criteria,
and a complete native payload were verified byte-for-byte against the frozen
prototype, without making a model request.

For a qualified Python process server and the preserved shared ledger:

```sh
.venv/bin/python -m mcpkart.bench reference --seeds 11 --delays 0 \
  --course stadium --road-width 16 --max-speed 12 --max-steering-angle 0.12 \
  --output artifacts/damped-stadium-reference.json
.venv/bin/python -m mcpkart.bench screen --models typesafe/jev-1.14 \
  --course stadium --road-width 16 --max-speed 12 --max-steering-angle 0.12 \
  --telemetry road_navigation --control-language geometry --instruction-style damped \
  --reference artifacts/damped-stadium-reference.json --output artifacts/damped-stadium-screen
```

Fresh environments and changed sources need their complete free timing gate
before paid driving. These profile settings are an explicit novice game class;
they do not change or qualify the original winding default.

## Audit, cost and source verification

All **37 paid driving attempts** passed timing and independent exact replay,
with verified isolated Python workers. Every one of 17,335 applied commands
was attributed to its recorded native model choice (including the fixed alias
bijections). Worst paid-trial lateness was **42.071164 ms**.

The ledger reconciles **18,493 new calls**: 17,865 driving,
624 static and 4 fresh health checks. All 18,489 successful responses
identify `typesafe/jev-1.14-20261014` / `TypeSafe`; four requests timed out.
There were no client retries or provider fallbacks. New conservative charges
were **$2.941561350**, including all uncertain reservations.

The preserved shared ledger ends at **43,426 / 50,000 requests**,
**$5.440687774 / $10**, 191,294,133 / 250,000,000 charged tokens,
and no pending reservations. Its 69 lifetime uncertain requests include all
65 predating this continuation. `model-budget-snapshot.json` is an exact copy
of the latest ledger. No prior charge or counter was reset.

The paid study used source
`429ac85d294dec7c7dab10cffaa34e9cea4333c90fd49aff7781b80e59c0e95a`.
The promoted preset uses
`588958f4c0bd594064b55c24cc9b678a4a41448c7334592521bb91bfa2130e6c`.
Tests on the promoted source: **349 passed, three optional Rust skips**, Ruff
clean; CLI help lists `damped`. No Rust worker was used or built.

The promoted source passed its complete credential-free gate: all three
scripted races finished without rescue, including the HTTP-parent pause.
Worst race lateness was 9.996607 ms. The 170.1 s neutral check had
14.154443 ms maximum lateness, 1.639616 ms p95, and
1.179538 ms drift. Verification matched the promoted fingerprint and
confirmed zero model requests. The spending ledger stayed exactly unchanged.
The paid study remains attributed to its original frozen source; promotion
changed the optional question catalog, with native payload equivalence checked.

Ignored evidence under `artifacts/jev-prompts-v2/` contains all declared protocols,
request/answer records, failures, exact replay checks, paired references, budget
authorization, timeout reviews and payload-equivalence proof. `final-audit.json`
reconciles every request, cost, token and uncertainty increment. The report folder
contains all 37 driving rows as CSV/JSON, the three matched trajectory pairs,
and paired metric figures as PNG/PDF. No viewer or public tunnel was deployed.
