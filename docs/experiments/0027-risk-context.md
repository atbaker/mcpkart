# Forecast context and binary answer labels

Status: complete, with passing final audit and corrected collection-provenance
verification, October 20, 2026. All sixteen prescribed-format controls passed;
all four forecast profiles scored 16/32 by always predicting `stays_on_road`.
No forecast benchmark was met. The original prospective design is retained below.

In [0026](0026-motion-forecast.md), both quoted guides always selected
`stays_on_road`: 24/48 correct overall and 0/24 hazardous cases. Test whether
the model can follow this binary format when the physical answer is prescribed,
then compare quoted-guide presence and answer-ID wording on fresh forecasts.
Effects will not identify an internal reasoning mechanism.

## Fixed physical task and fresh cases

Keep Python physics, the 24 m stadium, 12 m/s ceiling, 0.12 rad wheel limit,
three laps and three-second rescue unchanged. Thirty exact 60 Hz frames hold
the factual current native input unchanged for 0.5 seconds. Predict whether the
kart centre is ever strictly outside the road during those future frames;
touching an edge remains on-road. This is a forecast, not a control selection.

The fresh bank contains **32 synthetic current states in sixteen reflected
pairs**, balanced between safe/hazard outcomes and straight/curve current
regions: sixteen per class and eight per region × risk cell. Every current
centre is on-road, with no active rescue or previous rescues. The achieved
minimum initial clearance is 0.75 m; safe future clearance is at least 0.843 m
and hazards extend at least 0.799 m beyond an edge. These are constructed
transients, not recorded race trajectories. Current region need not describe
every future frame.

Each risk class has the same complete held-command distribution, covering all
five wheels and all three pedals. Fourteen distinct native commands occur in
each class; straight braking is absent from both. All 32 rounded 15 m coordinate
pairs are distinct and disjoint from the earlier banks and demonstrations
checked by the generator. The generator reads prior geometry, not model answers.

Every condition receives the same complete factual `road_navigation` state,
including runtime `finished`. Exact offline physics supplies labels, while
future traces, risk labels, clearance proofs, expected answers and reconstructed
internal state remain outside forecast payloads. The host supplies no evaluated
forecast, alternative input or driving recommendation and applies no controls.

## Context × answer-ID comparison

| Condition | Context name | Quoted reference guide | Answer IDs |
|---|---|---|---|
| A | `guide_semantic` | Unchanged `damped` | `leaves_road` / `stays_on_road` |
| B | `empty_semantic` | Empty | Same semantic IDs |
| C | `guide_opaque` | Unchanged `damped` | Rotating `option_a` / `option_b` |
| D | `empty_opaque` | Empty | Same counterbalanced opaque mapping |

The forecast question and physical criterion descriptions are identical in all
four conditions. Its final sentence is **“Answer YES or NO using the criteria.”**
This prospective change from 0026 makes the instruction compatible with opaque
IDs; the contrast with 0026 is therefore not a pure guide-presence replication.
The quoted reference is either the complete unchanged `damped` text or empty.
Both descriptions retain their physical meanings when IDs or insertion order
change. Submitted order is not evidence of provider-internal option ordering.

Before any forecast calls, collect **16 prescribed-format controls**:
four contexts × two prescribed physical outcomes × two criterion orders. The
current-state case cycles independently of the prescribed outcome. These calls
test response-format and physical-label mapping compliance; they are explicitly
not scored as physics forecasts and do not apply driving controls.

Collect all sixteen structurally valid controls, then require **16/16 correct**
before admitting a forecast request. A wrong prescribed choice stops the round
after these sixteen calls, leaving all 128 forecasts unrun. An endpoint,
identity, malformed-response or uncertain-accounting failure stops immediately
at either stage, retaining its record and charge. No retries or replacement
calls repair a failure.

Only after that format gate passes, collect **128 forecasts**: 32 states × four
contexts × one presentation. The maximum round is therefore **144 calls**.
Shuffle states with seed `2026102027`; rotate context order by `j % 4`, criterion
order by `j // 4 % 2`, and opaque mapping by `j // 8 % 2`. This gives two state
units in each of sixteen presentation cells; each context occupies each request
position eight times. Match criterion order and opaque mappings within a state.
There is no second repetition. Shared cases and reflected pairs remain
correlated rather than independent samples.

## Prespecified analysis and limits

Report format compliance separately from forecast accuracy. For forecasts,
report confusion counts, safe/hazard and straight/curve results, selected
physical outcomes, paired gains/losses and mirror agreement. Compare guide
removal B−A and D−C, opaque IDs C−A and D−B, and combined D−A; report the guide
and ID main effects plus their interaction. Interpret these as effects of
presentation on this bank, without inferring internal arithmetic, attention or
causes of the previous constant safe answer.

Use **29/32 overall and 14/16 within each risk and region class** as descriptive
per-condition capability benchmarks. They do not qualify a driving prompt.
This round is diagnostic only: regardless of scores, it triggers no automatic
native validation, live race, qualification or preset promotion. Accurate
forecasting of a held input would not show that the model chooses a better
input; poor results would not establish general model incapacity. Retain the
joint `damped` baseline and unchanged application defaults.

## Registered admission and provenance

Pin the same dated Jev model and TypeSafe provider, source fingerprint
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`,
one paid writer and one request in flight. Preserve zero retries/fallbacks,
strict endpoint/accounting stops, conservative token reservations and the
**75,000-request / $10 / 250-million-token** shared caps. The
[authorized session](2026-10-20-six-hour-session.md) admission deadline remains
**06:17:26 UTC**.

The starting audited boundary after 0026 is **60,819 requests, $7.508569996 and
243,114,366 charged tokens**, with 69 historical uncertain requests and no
pending reservations. Preserve the actual ignored ledger and every subsequent
transition; no limit or historical charge resets between stages or hosts.

Before paid admission, freeze fixtures, ordered requests, exact questions,
menus, route and helper hashes. Retain an immutable passing independent
preflight, a timestamped root authorization preceding collection, and the actual
writer's process/session identity. Match that identity and protocol across every
call and completion record. Final audit follows collection termination and must
reconstruct physical labels, exact observations, format-control prescriptions,
ordered wire bodies, mapping/order balance, coverage and the entire budget
chain. Keep failures and both conditionally and technically unrun entries
explicit. No older audit is rerun against a later ledger.

Fixture and collection evidence is under ignored `artifacts/jev-risk-context-v1/`.
The [exact prompt archive](0027-risk-prompts.json) preserves the frozen protocol;
the [results summary](0027-results-summary.json) preserves completed records,
format controls, subgroups, contrasts, helper hashes and exact budget boundaries.

## Completed results

The prescribed-format controls were **16/16 correct**: 4/4 per context, 8/8 for
each required physical category and 8/8 for either criterion order. Literal
prescribed mapping worked with both guides and both ID styles, including
selecting the hazardous outcome when explicitly required. These are instructed
category selections, not physics forecasts. The format gate passed before all
128 forecast requests were admitted.

| Forecast profile | Overall | Safe | Hazard | Straight region | Curve region |
|---|---:|---:|---:|---:|---:|
| A: `guide_semantic` | 16/32 | 16/16 | 0/16 | 8/16 | 8/16 |
| B: `empty_semantic` | 16/32 | 16/16 | 0/16 | 8/16 | 8/16 |
| C: `guide_opaque` | 16/32 | 16/16 | 0/16 | 8/16 | 8/16 |
| D: `empty_opaque` | 16/32 | 16/16 | 0/16 | 8/16 | 8/16 |

All **128 forecasts** mapped to the physical `stays_on_road` category, producing
64 false-safe forecasts and zero false-hazard forecasts. All five matched simple
contrasts and the interaction had zero difference in correct counts and
accuracy. Each simple contrast had zero gains, zero losses and 32/32 identical
physical choices. Guide and ID main effects were zero. All 64 mirror comparisons
agreed, as expected from a constant answer. There is one forecast per
context/state, so there is no within-context repeat-stability estimate.

Every profile met the safe-class count but failed **29/32 overall** and
**14/16 hazardous, straight-region and curve-region** benchmarks. These were
descriptive benchmarks, not an automatic driving-qualification gate. No native
validation, live comparison or promotion followed. The joint `damped` baseline
and application defaults remain unchanged.

Removing the quoted guide and rotating opaque IDs did not resolve the constant
safe forecasts on this bank. Prescribed mapping success does not establish
physical interpretation of the transients; the internal cause remains unknown.
The labels describe one input held for half a second, not optimal actions or
general model capacity. The common YES/NO ending differs prospectively from
0026, and the fixture banks differ, so cross-study comparisons do not isolate
a wording effect. Shared contexts and mirrored fixtures are related observations.

## Completed audit and separate provenance qualification

All **144 requests** completed with zero endpoint errors and no new uncertain
charges; no attempted or planned entries are missing. The saved final audit
passed with no errors or warnings. It checked 32 forecasts and 960 exact
simulation steps, format prescriptions, factual payloads, ordered mappings,
frozen helpers, writer attribution and budget accounting. The recorded writer
execution session was `80975aaadb6e4139939f1718bf928bcb`, with explicit collection
enabled.

The separate collection-provenance verification passed all **32 checks**.
The immutable independent preflight and root authorization preceded collection;
all 144 call records match the actual writer, frozen protocol and exact budget
chain. The recorded writer start was 01:43:35.650770 UTC, after authorization
at 01:43:34.993007 UTC. No foreign writer or accounting stop occurred.

Its initial source-identity check falsely failed because the checker used the
narrower `mcpkart.probe.source_fingerprint` algorithm instead of this experiment's
`mcpkart.bench.fingerprint` algorithm. The initial failed JSON is preserved
byte for byte. Correcting only that checker algorithm independently reproduced
the full Python-plus-Rust fingerprint, which matched the actual bench function
and frozen `1f2670…` source. Original evidence hashes and all 144 identities,
budget transitions and wire hashes were rechecked unchanged. No source change
was established; no unresolved source-timing limitation remains. The results
summary retains both the initial failure and corrected verification.

The format stage used $0.001480038 and 35,843 charged tokens; the forecast stage
used $0.013128528 and 317,448 tokens. Total use was **144 requests,
$0.014608566000001488 and 353,291 charged tokens**. The saved final audit's exact
end boundary is **60,963 requests, $7.523178561999893 and 243,467,657 charged
tokens**, with 69 historical uncertain requests unchanged and pending empty.
All shared caps remain unchanged. This report uses saved completed evidence;
it does not rerun audits or inspect a later ledger.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `73242a3f8ef29b57be1bf3fba0c202487b432931f4d7cdb5cce8e91d392c3ce5` |
| Exact prompt archive | `ed3be3c97bcfa7db8276d310e21d65327d7bfad56817f52c524b6faa92b782bf` |
| Saved final audit | `d42fec9fce148c6636bea66fbcabe5f75cb8a2f519b5718f57fdf24e5d75fa3a` |
| Audited report summary | `71956019995c4a9d17d27eebe0b01cc40c3958c4a3b48b7535e645748d553f91` |
| Corrected collection provenance | `2b1b8a363af49e53744612cb01ebc43ce72b888f783f132d70028efb5a68af13` |
| Preserved initial checker result | `9bcf23dcd06d448901228c98ddc14b696098c6b289ad905c6c1a6cb15b4f2211` |

The separate provenance verification's hash and complete checks are recorded in
the results summary alongside the frozen collection-source fingerprint.
