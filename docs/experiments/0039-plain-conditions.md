# Expressing fixed eligibility in plain language

Status: complete, October 20, 2026. Final audit and separate collection-provenance
verification passed. Both arms scored 14/18 exact native pairs, with one gain
and one loss. The perfect pair/wheel gate failed; no broader validation or
live race is admitted and no preset is promoted. Remaining tokens are also
below the unchanged five-million-token live-admission guard. The original
registration follows, with an immutable copy retained under
`artifacts/jev-plain-conditions-v1/prospective-design.md`.

The completed [0038 literal-conditions pilot](0038-literal-conditions.md)
scored 16/18 baseline versus 15/18 literal-criterion native pairs, with no paired
gains and one loss. All pedals and non-straight wheels were correct; the
candidate's three errors were small-bearing straight targets. Its perfect
pair/wheel gate failed. This pilot tests English eligibility wording under the
same policy, rather than changing the rule or attributing an internal cause.

## Exact scope and unchanged contract

Keep Python physics, the 24 m stadium, 12 m/s ceiling, 0.12 rad wheel limit,
three laps and three-second rescue unchanged. Retain joint `damped` and the
original application default. Copy the 0032 bearing `policy.py` byte-for-byte;
these engineering thresholds are not pursuit-equivalent or optimal-action labels.

Both arms receive the exact selected 0034 `facts` projection, with its original
unit strings, canonical four-decimal 15 m point bearing and copied current
values. Support status and exact labels must match the reconstructed full state.
No evaluated guard, eligibility flag, target, expected answer, example or
recommendation enters model state. The model selects every paid native pair;
no command is applied and no physics advances during this static pilot.

Baseline questions are **byte-identical to the frozen 0038 candidate**. The
candidate changes **only criterion values**, replacing each with the root-selected
English string in `artifacts/jev-plain-conditions-v1/plain_clauses.py`.
All existing instructions remain byte-identical, including the common aliases,
driving prefix, component tasks, wheel deadband-first suffix and physical
definition lists. Preserve physical meanings, IDs, menu contents/order, factual
state and the atomic native Cartesian inverse. Do not remove now-redundant
common definitions or add an example. The exact immutable source text is quoted
below as runtime strings; JSON quoting does not alter the submitted values.

```json
{
  "wheel": {
    "hard_right": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when road.preview_15m_bearing_deg points RIGHT by more than 22 degrees.",
    "right": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when road.preview_15m_bearing_deg points RIGHT by more than 7 degrees and at most 22 degrees.",
    "straight": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when road.preview_15m_bearing_deg is within 7 degrees of straight ahead in either direction, including exactly minus 7 or plus 7 degrees.",
    "left": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when road.preview_15m_bearing_deg points LEFT by more than 7 degrees and at most 22 degrees.",
    "hard_left": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when road.preview_15m_bearing_deg points LEFT by more than 22 degrees."
  },
  "pedal": {
    "accelerate": "FIXED POLICY ELIGIBILITY: choose ACCELERATE exactly when kart.speed_m_s is below 2 metres per second, regardless of any edge condition. Otherwise, choose it exactly when none of these three conditions holds: (1) road.on_road is false; (2) road.offset_m is positive, road.left_edge_clearance_m is at most 3 metres, and current_road_frame.velocity_left_m_s is at least positive 0.5 metres per second, with all three parts required together; (3) road.offset_m is negative, road.right_edge_clearance_m is at most 3 metres, and current_road_frame.velocity_left_m_s is at most negative 0.5 metres per second, with all three parts required together.",
    "coast": "FIXED POLICY ELIGIBILITY: choose COAST exactly when kart.speed_m_s is at least 2 and at most 6 metres per second, and at least one of these three conditions holds: (1) road.on_road is false; (2) road.offset_m is positive, road.left_edge_clearance_m is at most 3 metres, and current_road_frame.velocity_left_m_s is at least positive 0.5 metres per second, with all three parts required together; (3) road.offset_m is negative, road.right_edge_clearance_m is at most 3 metres, and current_road_frame.velocity_left_m_s is at most negative 0.5 metres per second, with all three parts required together.",
    "brake": "FIXED POLICY ELIGIBILITY: choose BRAKE exactly when kart.speed_m_s is more than 6 metres per second, and at least one of these three conditions holds: (1) road.on_road is false; (2) road.offset_m is positive, road.left_edge_clearance_m is at most 3 metres, and current_road_frame.velocity_left_m_s is at least positive 0.5 metres per second, with all three parts required together; (3) road.offset_m is negative, road.right_edge_clearance_m is at most 3 metres, and current_road_frame.velocity_left_m_s is at most negative 0.5 metres per second, with all three parts required together."
  }
}
```

The root-selected text file SHA-256 is `01f78a1e01752b71d37722ccddbd23945a0aec9c4ba38e14a629e196418bc853`.
The quoted strings must match the final prompt archive and actual wire payloads.
No helper may rewrite or evaluate them against the current observation.

## Policy equivalence and boundaries

The signed bearing convention is unchanged: positive means LEFT of the kart
nose and negative means RIGHT. Directional magnitude in words preserves the
same five disjoint wheel regions. Exactly −22 degrees selects moderate right;
exactly −7 and +7 select straight; exactly +22 selects moderate left. Full
wheel requires a magnitude strictly greater than 22 degrees, and moderate
wheel requires greater than 7 and at most 22. The canonical bearing remains
`round(degrees(atan2(y,x)),4)` from the same rounded 15 m x/y facts.

Each pedal string lists the same **three alternative edge conditions**. The
off-road condition stands alone; within each directional flank, offset sign,
clearance and outward road-left velocity must all hold together. At least one
whole condition makes the guard true. Positive road-left velocity means left;
negative means right. Zero offset satisfies neither flank condition. A negative
clearance is already outside, but the unchanged off-road condition handles it.

Speed below 2 m/s always selects ACCELERATE, even off-road. At exactly 2 or
6 m/s, a true guard selects COAST. Above 6 with a true guard selects BRAKE.
When speed is at least 2 and none of the three conditions holds, ACCELERATE
remains eligible. These are semantic restatements of the existing policy,
including ties and low-speed priority, not new thresholds or guard values.
Independent verification must check the exact strings, grouped conditions,
boundaries, label equivalence and absence of query-specific evaluated flags.

The initial independent semantic review passed fifteen wheel-boundary fixtures
and 3,402 pedal truth fixtures against the unchanged source policy. Its saved
proof is `artifacts/jev-plain-conditions-v1/plain-english-semantic-review.json`;
the root-selected text was unchanged. This free semantic check does not replace
full prospective preflight or model collection/audit.

The wording package changes syntax and text length together. Outcomes cannot
identify an internal Boolean-parsing, attention or reasoning mechanism.

## Fresh bank and balanced collection

Use fixed seed **2026102039** for eighteen fresh synthetic states in nine
reflected pairs. Retain one pair per wheel-magnitude × pedal combination:
six straight, six moderate and six full labels, with six cases per pedal.
All fifteen native targets occur; each straight target occurs twice and each
signed non-straight target once. Match held-input coverage without a complete
held-input copy of its target.

Keep all six straight bearings between 0.05 and 1.5 degrees in absolute value,
with both signs and each pedal represented; other wheel labels remain at least
two degrees from every threshold. Preserve stopped off-road straight
acceleration, slow outward moderate acceleration with low-speed priority,
fast near-edge inward full acceleration with a false guard, off-road inward
coasting and the remaining on-road outward coast/brake groups. Maintain the
existing protected predicate margins. The group assignments are geometry and
coverage constraints, not a selection based on model responses.

Reconstruct full factual states through production renderers before projection,
including null velocity angle at rest and zero rescue elapsed/prior rescues in
synthetic off-road cases. Require finite forward 15 m coordinates, finite
positive squared range and no known positive uncredited next-gate plane.
Reject unsupported states rather than inventing recovery answers. Static
fixtures do not validate physical braking or recovery.

All eighteen rounded 15 m x/y pairs must be unique and excluded from the
listed materialized prior static banks through 0038, including 0035 natural
states, and documented demonstrations. This is a bounded freshness claim,
not exhaustive comparison against every historical sent query. Reflections,
paired arms and components are related observations; one presentation per
state/context provides no within-arm repeatability estimate.

Collect **36 calls maximum**, eighteen cases × baseline/candidate. Shuffle case
units with seed `2026102039`; at shuffled index j alternate first arm using
`j % 2` and reverse both component menus using `j // 2 % 2`. Match paired
state and menu order, including the unchanged instruction-list order. Each
arm occupies each request position nine times. The four first-arm/order cells
contain five, five, four and four units, with ten/eight normal/reversed units.

Retain every structurally valid planned answer regardless of correctness;
there is no correctness stop or format gate. Technical, identity, uncertain-
accounting, hard-budget or deadline failure stops admission while preserving
all attempts and unrun entries. Use the pinned dated Jev model at TypeSafe,
one paid writer and request in flight, zero retries and no provider fallback.

## Perfect gate and separate broader validation

The English candidate must satisfy every requirement:

- **18/18 exact native pairs, 18/18 wheels and 18/18 pedals** correct.
- **Zero BRAKE selections below 2 m/s**.
- Complete collection, strictly typed atomic components, exact native inverse,
  zero endpoint/accounting errors and a passing independent audit.

Report paired gains/losses descriptively, wheel/pedal/magnitude/direction and
guard-subtype scores, chosen-input distributions and every preserved error.
Comparative gain is not a separate admission condition; perfect capability
without gains does not establish improvement.

A perfect pilot can motivate only **new fresh sixty-case broader native
validation under unchanged 0035 thresholds**. It neither replaces prior
failures nor admits direct live use or promotes a preset. The unchanged
broader gate requires at least 29/30 natural and 27/30 synthetic pairs;
synthetic wheels 6/6 straight and at least 11/12 each moderate/full; at least
9/10 in each synthetic pedal class; no low-speed BRAKE in either family;
complete collection, zero endpoint/accounting errors and independent audit.
Broad validation, exact candidate control and actual resource/time admission
remain separate.

## Resources and evidence

The completed 0038 boundary is **61,531 requests, $7.582676265999883 and
244,931,180 charged tokens**, leaving **5,068,820 tokens**, with 69 historical
uncertain charges and pending empty. Preserve all history and the shared
**75,000 requests / $10 / 250-million-token** caps. Every request retains the
full **16,384-input + 235,929-output = 252,313-token** conservative reservation.
The authorized session admission deadline remains **06:17:26 UTC**.

The **five-million-token live-admission guard remains unchanged**. Read the
actual ledger after each phase; no pilot or validation result promises enough
headroom for a race. Do not weaken reservations or a gate to extend this work.

Current-boot runtime timing passed at 04:09:25 UTC, bound to unchanged source
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`, boot
`f534ef07-e837-401d-bf64-a0fe7c51e3d3` and HTTP parent PID 1751/start ticks
85454. That qualifies timing only. Separately recorded seeds 21/22 passed
independent free replay, but remain nominal host-policy tracking evidence,
not Jev qualification or validated edge recovery.

Before paid admission, freeze these exact English clauses, baseline/expanded
origin references, questions, bank/generator, factual projection, policy,
physical lists, route, order, source and helper hashes. Require actual-wire
mocks with zero real calls and unchanged ledger, strict inherited production
decoding/accounting, independent factual/label/boundary proofs, immutable
passing independent preflight and timestamped root authorization. After writer
termination, audit all raw typed responses, payloads, native mappings and
sequential ledger changes. Preserve failures and unrun entries; do not rerun
old frozen audit CLIs against a later ledger.

## Completed English-criteria pilot

All **thirty-six planned calls** completed with zero endpoint/accounting errors,
no unrun entries, retries or replacements. Every valid planned answer was
retained. The exact quoted root-selected English strings were used unchanged.
Only criterion values differed from the exact 0038 candidate baseline;
component instructions, symbolic common definitions, factual inputs, physical
definition lists, IDs, native meanings and atomic inverse remained identical.
The engineering policy and its boundary/priority rules did not change. No
query-specific guard, target or branch was supplied. No paid command was
applied and no physics advanced.

| Measure | Baseline literal criteria | English criteria |
|---|---:|---:|
| Exact native pair | 14/18 | 14/18 |
| Wheel component | 14/18 | 14/18 |
| Straight wheel | 2/6 | 3/6 |
| Moderate wheel | 6/6 | 6/6 |
| Full wheel | 6/6 | 5/6 |
| ACCELERATE pedal | 6/6 | 6/6 |
| COAST pedal | 6/6 | 6/6 |
| BRAKE pedal | 6/6 | 6/6 |
| All pedals | 18/18 | 18/18 |
| BRAKE chosen below 2 m/s | 0/4 slow cases | 0/4 slow cases |

English criteria produced **one paired gain and one loss**, with thirteen
states correct in both arms and three wrong in both. The net pair gain was
zero. The preserved errors and changes were:

| Bearing | Expected | Baseline | English |
|---|---|---|---|
| +0.7681° | `straight_accelerate` | `hard_left_accelerate` | `hard_left_accelerate` |
| +0.9640° | `straight_coast` | `hard_left_coast` | `hard_left_coast` |
| +0.4776° | `straight_brake` | `hard_left_brake` | `hard_left_brake` |
| −0.9640° | `straight_coast` | `hard_right_coast` | Correct |
| −26.7125° | `hard_right_brake` | Correct | `hard_left_brake` |

The negative small-bearing coast gain was offset by an opposite-direction
full-wheel loss. Three positive small-bearing straight errors remained in
both arms. Thus the candidate errors are not all small-bearing or all positive.
All pedals were correct. The candidate failed **18/18 exact pairs and 18/18
wheels**; perfect pedals, low-speed and technical requirements passed. Paired
gain was descriptive, not a separate admission threshold. The failed gate was
not relaxed, and no state was rerun or replaced.

This fixed English-criterion package did not improve exact-pair agreement on
this bank. Equal totals conceal different responses and do not establish
internal equivalence or identify a language/logic mechanism. Only criterion
values became English; symbolic common definitions remained in the unchanged
instructions. Eighteen synthetic states in nine reflected pairs and one
presentation per case limit generalization and do not estimate repeatability.
Scores measure supplied-rule compliance, not optimal actions or race success.
Retain joint `damped` and the original application default.

## Audit, timing and resource boundary

The final audit passed with **`complete=true` and no errors or warnings**.
It verified all eighteen states and policy labels, the exact root English
strings and semantic/boundary proof, identical paired instructions/facts/native
meanings, baseline origin, raw typed components and native inverse, balanced
order and every ledger transition. Source inheritance and prospective wire/error
mocks passed before admission. The origin manifest checked eighty-six evidence
files and an exact policy copy; no old frozen CLI ran against a later ledger.
Production source, handling and physics remained unchanged.

Separate collection-provenance verification passed all **49 checks**, including
immutable preflight/authorization chronology, all thirty-six exact wire payloads
and raw typed pairs, source identity, actual writer and full ledger chain.
It bound the root English source and semantic-proof hashes, exact 0038 candidate
baseline, and unchanged state/instructions/physical definitions. Root tool
chunk/session identifiers were checked against preserved execution confirmation
rather than independently queried from tool infrastructure; actual writer and
ledger records were independently verified.

Current-boot runtime timing passed at **04:09:25 UTC**, bound to source
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`, boot
`f534ef07-e837-401d-bf64-a0fe7c51e3d3` and HTTP parent PID 1751/start ticks
85454. That is runtime timing qualification, not native/live admission.
Independently replayed free seeds 21/22 remain nominal host-policy tracking;
no model qualification or physical edge-recovery effectiveness follows.

Independent prospective preflight passed at 04:25:33 UTC. Root authorization
`d37c73e928b34ecd9f9cf6c9e1eccf84` at **04:25:51 UTC** preceded the sole writer's
**04:25:56.493346 UTC** start. Its session was
`a888619c25ec4e1baac1655a240f958f`, PID 4810, with explicit collection enabled.
All thirty-six calls are in the completion record and root confirmed exit zero.
Caps, conservative reservations, identity checks and no-retry/no-fallback
policies were retained.

The pilot used **thirty-six requests, $0.0033750359999942248 and 83,809 charged tokens**.
Its saved audited end boundary is **61,567 requests, $7.586051301999877 and
245,014,989 charged tokens**, with 69 historical uncertain charges unchanged
and pending empty. The remaining **4,985,011 tokens** are below the unchanged
**5,000,000-token live-admission guard**. Live racing is resource-blocked
independently of the failed pilot gate. This is not exhaustion of the shared
hard caps: authorized static work may continue within those caps and the
06:17:26 UTC deadline. No guard or reservation is weakened.

No broader validation, native/live qualification or promotion is admitted.
This report uses saved evidence and does not rerun an audit against a later
ledger. The [machine-readable summary](0039-plain-conditions-summary.json)
retains frozen and completed evidence; the exact
[prompt archive](0039-plain-conditions-prompts.json) remains unchanged.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `233f7d4f81a7436623dc4903fb435f37394a372eaf771e09a7f8db7bb22be3f8` |
| Exact prompt archive | `9deb15fafa32f03cb25830abc124dc8b8c88295d61a2970e41cd101d4576e0e0` |
| Final audit | `c668bb57c59f29d422aa5a6ea20b0911a97929bf748da698dd11a5d380e89421` |
| Audited report summary | `772c3bc84b8e51553748b615d03b13015af788893cbc8df8b5b33691ed66697c` |
| Root English source | `01f78a1e01752b71d37722ccddbd23945a0aec9c4ba38e14a629e196418bc853` |
| English semantic proof | `9ed8d97fba55eade375f0ab46c5fc01b4dafe66b30f35b570a2e84e62616ed25` |
| Frozen origin manifest | `001730cb9bc900863ce7e71911888cd3ddfb3ca7708785f02c85982a049f004f` |
| Collection provenance | `261960aac20a21dd13578b23f5a8704e4f59376bc92a264f0d632a575f1ec611` |
