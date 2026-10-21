# Predicting the consequence of a held input

Status: complete and independently audited, October 20, 2026. All 96 requests
completed, but the forecast-capability gate failed. Both guides always chose
`stays_on_road`: 24/48 correct overall and 0/24 correct on hazardous cases.
The original prospective design is retained below.

The previous factored-interface screen gave mixed paired driving results. This
comparison tests a different prerequisite: can Jev predict near-term road
departure from the supplied motion, and does an explicit consequence-comparison
prefix preserve that ability?

Keep the Python physics, 24 m stadium, 12 m/s ceiling, 0.12 rad wheel limit,
three laps and three-second rescue unchanged. Twenty-four fresh synthetic
snapshots form twelve reflected pairs, balanced between straight/curve regions
and safe/hazard outcomes. These are constructed transients, not recorded racing
trajectories. Every snapshot starts on-road with at least 0.75 m centre clearance.
All five held wheel settings and all three pedals occur in each risk class;
the complete held-command distribution is identical across classes.

The factual task holds the current native input for exactly thirty 60 Hz steps
(half a second), with normal steering/yaw lag and grip. Predict whether the kart
centre is ever strictly outside the road during those future frames. An edge
touch counts as on-road. Exact offline simulation supplies labels before model
collection; safe fixtures retain at least 0.843 m clearance and hazard fixtures
reach at least 0.797 m beyond an edge. Future states, clearance values, labels
and reconstruction proofs remain outside every submitted payload.

Compare the exact `damped` guide with a fixed consequence-comparison prefix
followed by that unchanged guide. Both are quoted as reference material. The
identical required forecast task overrides driving advice: answer only the
binary prediction, without changing or recommending a control. Both receive
the same complete current `road_navigation` state, factual runtime `finished`
field and fixed physical definitions of every native input. The host computes
no current-query recommendation and applies no controls.

Twenty-four cases × two guides × two repetitions yield 96 planned calls.
Shuffle cases with seed 2026102026, alternate first guide, and independently
balance binary criterion order. Each repetition has six case units in each
first-guide/first-criterion combination. Reverse cases, guide order and criterion
order for repetition two. Submitted option order is not a claim about provider
internal ordering. Reflections and repeated cases remain correlated.

Freeze the exact fixture bank, question strings, order, route, source fingerprint,
helper hashes and starting ledger before collection. Use the same dated Jev
model and TypeSafe provider, one paid writer/request in flight, no retries or
fallbacks. Stop on the first endpoint, identity or uncertain-accounting failure;
preserve the charge and explicit unrun cases. Record actual writer identity,
ordered bodies, typed responses and every ledger transition. All shared caps
remain **75,000 requests / $10 / 250 million charged tokens**, with the existing
conservative reservation and **06:17:26 UTC** session deadline.

The consequence candidate must achieve at least **44/48 overall**, **21/24 in
each risk class** and **21/24 in each track-region class**, with no lower total
than the control, no endpoint/accounting failures and a complete independent
audit. This is a prediction-capability gate, not a claim of static improvement
or optimal driving. Report confusion errors, subgroup results, paired changes
and repeat stability. Correctly predicting a held input does not show that the
model can select a better alternative.

A passing candidate can motivate separately frozen fresh native-command
validation, then a budget-permitted single fresh paired start (seed 13) as an
exploratory driving comparison. Neither step is automatic; preserve the existing
per-race admission guards. A single pair cannot establish consistent improvement
or qualify a preset. The joint `damped` baseline and application default remain.

Evidence is retained under ignored `artifacts/jev-motion-risk-v1/`. The exact
[prompt archive](0026-motion-prompts.json) and [results summary](0026-results-summary.json)
preserve the frozen protocol and completed audit alongside this note. Starting audited boundary: 60,723 requests, $7.497665116 charged and
242,850,694 charged tokens; 69 historical uncertain requests, pending empty.


## Results and decision

All 96 calls completed with the frozen dated Jev/TypeSafe route, zero endpoint
errors, no retries or replacements, and no new uncertain charges. The final
audit passed with no errors or warnings. It independently checked all 24 labels
and 720 future simulation steps, the full factual payloads and option order,
frozen helper hashes, writer attribution and continuous budget accounting.
No controls were applied.

| Guide | Overall | Safe | Hazard | Straight region | Curve region |
|---|---:|---:|---:|---:|---:|
| Quoted `damped` | 24/48 | 24/24 | 0/24 | 12/24 | 12/24 |
| Consequence prefix + quoted `damped` | 24/48 | 24/24 | 0/24 | 12/24 | 12/24 |

Every response selected `stays_on_road`. Across both guides this produced
**48 false-safe forecasts and zero false-hazard forecasts**. All 48 matched
guide pairs chose identically, giving zero gains and zero losses. All 48 repeat
pairs and 48 mirror pairs also chose identically. That stability follows from
the constant answer; it does not establish useful sensitivity to motion.
Within each guide, the same twelve safe fixtures were always correct and the
twelve hazard fixtures always wrong. Repeated calls and mirrors are related
observations, not 96 independent driving situations.

The candidate met the safe-class threshold and matched the control total, but
failed **44/48 overall**, **21/24 hazards** and **21/24 in each track region**.
The capability gate therefore failed despite clean technical execution.
No native-command validation or live followup was triggered, and neither the
joint `damped` baseline nor the application default changed.

This result concerns forecasting one fixed held input for half a second from
constructed transients. It does not identify an optimal action, measure live
control quality or prove general model incapacity. Both conditions retain a
quoted driving guide and semantic binary labels; this comparison does not
identify why all choices were safe. At this report's handoff, 0027 is preparing
a separate diagnosis of quoted-guide context and answer-label framing, with
prescribed binary-format positive controls; no paid 0027 calls have started.

## Collection provenance and budget boundary

The separate collection-provenance verification passed all checks: the immutable
independent preflight and authorization preceded the writer start, their hashes
and protocol/source/budget identities matched, and all 96 records carried the
same actual writer identity. The writer execution session was
`38d6c85eb6464584843ce2913ecd64e4`; no foreign writer or accounting stop occurred.
These checks and timestamps are retained verbatim in the results summary.

The phase used **96 requests, $0.010904880 and 263,672 charged tokens**.
Its fixed audited end boundary is **60,819 requests, $7.508569996 and
243,114,366 charged tokens**, with 69 historical uncertain requests unchanged
and no pending reservations. All **75,000-request / $10 / 250-million-token**
caps remain unchanged. This report copies saved completed boundaries; it does
not rerun an audit or inspect a later ledger.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `48d01cd9826df36ded25397d7a10379c4a9c9c4109415b2049cb6721f34f318f` |
| Exact prompt archive | `d6e4e9a8a7cdee49edeb4728d3313883f6ba60f769ccf9d745e274cf748f724a` |
| Final audit | `2911c4797dd5ee707fbe81ea8afe756cc04bfe23498383d217686370c5fa1c46` |
| Audited report summary | `ef642a57cf8631530f16ff3e1dbcd23edd68e925a49e04a67ee2b2e867ab941b` |
| Collection provenance verification | `28e907e181e8fb4fa2b5b39b6310083003024ab590d4b706b8da16fc760efe54` |

Source fingerprint remains
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
The versioned results preserve every subgroup, confusion count, paired/repeat
comparison, gate check, frozen helper hash and exact budget boundary.
