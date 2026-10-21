# Moving current facts into the held-motion forecast question

Prospective design, October 20, 2026. The question-local representation greatly
improved fixed-rule driving, but useful anticipation remains unproven. Earlier
held-input forecasts in 0026–0029 often always selected the currently safe
outcome. This new static comparison asks whether relocating the same current
facts into the question improves half-second road-departure predictions.
It does not resume or reclassify any failed older forecast study.

Build 48 fresh synthetic current poses, in 24 reflected pairs, balanced across
safe/hazard and current straight/curve region. Use two deterministic jittered
variants of each of 0026's twelve physical construction templates. Keep the
held-input distribution matched across the two risk classes, all five wheels
and all three pedals represented. Perturb position, current heading, motion,
speed, yaw and actual wheel within bounded ranges, and accept only states
with at least 0.5 m initial clearance and at least 0.5 m future margin for
their class. Private exact thirty-step physics labels whether the kart centre
is strictly outside the road at any future frame. Exclude 15 m coordinate pairs and requested road positions in all prior
fixture banks that expose those facts; retain the complete exclusion-source
manifest. These are new parameter tuples
from related templates, not naturally reached states or independent tracks.
Record all template, jitter, exclusion and forecast reconstruction evidence.

Both arms receive the same complete current road-navigation state, explicit
current road-frame angles/velocity, original units, current surface/on-road
facts, handling, held input, progress and rescue fields. Use exactly 0028's
quoted damped guide and required binary forecast task, with both semantic
criteria. Prepend the same factual-location clarification to both arms:
"CURRENT FACTS LOCATOR: In the following task, state means the complete factual
object supplied in request state or in this question's current_facts field.
Read that current object; it contains no future forecast." No future states, forecast margins, labels, evaluated risk predicates
or recommended controls may enter the submitted facts or rules.

The shared arm uses instructions={rules:fixed_text} and the factual state in
`state`. The local arm uses the same structured rules plus the complete facts
in instructions.current_facts, with state={}. No other wording, fact, menu or
question changes. One joint binary question, one POST. This is a prediction
experiment; no native kart action is selected or applied.

One response per arm per case gives 96 fixed calls. Within each of the four
risk × region strata, balance all four first-arm × first-criterion combinations
three times. Shuffle fixed case units with seed 2026102056; retain paired arm
adjacency and identical criterion order within each pair. Freeze all cases,
questions, exact order, route, source/helper hashes and ledger before any paid
request. Root runs one bounded static batch with one request in flight, no
retries/fallbacks/replacements. Stop at the first API/identity/accounting error
and preserve the failed charge and unrun suffix.

The primary relocation gate requires local accuracy at least 40/48, at least
20/24 in each risk and region class, at least eight paired net gains over shared,
and no more than four paired losses, with all technical audits valid. Report
both arms, confusion counts, paired changes and mirror agreement. These are
static capability and relocation criteria, not proof of optimal action choice
or actual driving improvement. Any subsequent native/driving work requires
its own prospective protocol; none is admitted here.

Keep Python, 24 m, 12 m/s, 0.12 rad, three laps and three-second rescue. Shared
caps stay $10 / 75,000 requests / 500 million cumulative tokens; preserve all
prior charges, full per-POST reservation and deadline 11:38:01 UTC. Root alone
reviews/collects. No application default, baseline or existing driver changes.

## Results

All 96 calls completed and the full raw-wire/private-label/identity/accounting
and provenance audit passed. There were no retries, replacements, endpoint
errors or new uncertain charges, and no controls were applied.

| Arm | Correct | Safe | Hazard | Straight | Curve |
|---|---:|---:|---:|---:|---:|
| Shared factual state | 24/48 | 24/24 | 0/24 | 12/24 | 12/24 |
| Facts inside question | 31/48 | 18/24 | 13/24 | 14/24 | 17/24 |

The shared arm predicted `stays_on_road` on all 48 cases. The local arm made
19 hazard predictions and 29 safe predictions, yielding 13 paired gains and
six losses (net seven). It produced eleven false-safe and six false-hazard
forecasts. Mirror-pair answer agreement was 24/24 shared and 15/24 local;
constant safe answers explain the shared arm's high agreement.

The primary gate failed: local overall, risk/region subgroup, net-gain and
loss thresholds were not met. The relocation gain does not establish robust
prediction or qualify a driving addition. It does break the constant-safe
pattern on this bank and motivates a separately registered diagnostic, without
reinterpreting this failure. The bank consists of correlated synthetic template
variants and reflections, not 48 independent real driving situations.

Delta: 96 requests / 278,001 charged tokens / $0.011507496, with zero new
uncertainty. Full evidence, including root tool execution confirmation, all
307 prospective checks and the unchanged 1,440-step private forecast audit,
is under `artifacts/jev-forecast-relocation-v1`. The [versioned summary](0056-forecast-relocation-summary.json)
retains all case outcomes. Protocol SHA256:
`6ce3e9989f05a028f6ce492590fbc6cf416cd969a1207c8879368d3d36c97b51`.
