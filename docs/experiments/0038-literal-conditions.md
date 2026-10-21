# Expanding criterion aliases into literal factual references

Status: complete, October 20, 2026. Final audit and separate collection-provenance
verification passed. Baseline scored 16/18 exact
pairs and literal criteria 15/18, with no paired gains and one loss. The
perfect pair/wheel gate failed; no broader validation or live race is admitted
and no preset is promoted. The original registration follows, with an immutable
copy retained under `artifacts/jev-literal-conditions-v1/prospective-design.md`.

The completed [0037 condition-only pilot](0037-condition-only.md) scored 16/18
exact native pairs in each arm. Its condition-only candidate selected 17/18
wheels and 17/18 pedals, failing the perfect pilot gate. A +1.1383-degree
straight-coast state still elicited full left; a fast near-edge inward-motion
state elicited braking although its policy guard was false and required
acceleration. Those outcomes do not identify their internal cause. This pilot
tests whether literal references in each eligibility criterion improve execution
of the same supplied rule.

## One mechanical text change

Preserve the byte-exact 0032 bearing `policy.py`, the exact 0034 factual state
projection, Python physics, 24 m stadium, 12 m/s speed ceiling, 0.12 rad wheel,
three laps and three-second rescue. Preserve joint `damped` and application
defaults. Labels measure agreement with the supplied engineering policy, not
optimal controls or live driving capability.

The baseline questions are byte-identical to the frozen 0037 condition-only
candidate. Each criterion contains its original eligibility clause alone.
Physical control descriptions remain in the component instructions under their
unchanged IDs and in matching submitted menu order. Both questions keep their
driving prefix, complete common definitions, component tasks and physical
definition lists. The wheel keeps the unchanged deadband-first instruction.

The candidate changes **only criterion values**, using a single whole-word
substitution pass:

```python
ALIAS_PATTERN = re.compile(r"\b(theta|speed|B)\b")
ALIAS_SUBSTITUTIONS = {
    "theta": "road.preview_15m_bearing_deg",
    "speed": "kart.speed_m_s",
    "B": B_EXPRESSION,
}
```

`B_EXPRESSION` is exactly this parenthesized fixed text:

```text
(road.on_road is false OR (road.offset_m>0 AND road.left_edge_clearance_m<=3 AND current_road_frame.velocity_left_m_s>=0.5) OR (road.offset_m<0 AND road.right_edge_clearance_m<=3 AND current_road_frame.velocity_left_m_s<=-0.5))
```

This guard uses the full road-left-velocity field path directly; the common
definition's `L` alias does not appear in it. The regular expression expands
only `theta`, `speed` and `B`, using a replacement callback once. All other
criterion bytes remain unchanged, including comparisons, parentheses, spacing,
`is true` and `is false`. For example, replacing `B` in `B is false` leaves
the complete parenthesized guard followed by `is false`; it does not evaluate
the guard or change it to a host-supplied Boolean.

The entire instructions string for each component must remain byte-identical
between arms. So must all physical meanings, menus, IDs, order, atomic native
Cartesian inverse and factual state. Both arms receive the same existing
factual bearing and current speed, surface, signed offset, clearances and
road-left motion. No evaluated condition, guard flag, branch, target, example,
recommendation or host-selected control enters a payload. No command is applied
and no physics advances during this static collection.

The comparison changes reference locality, text length and criterion syntax
together. A difference cannot establish an internal alias-resolution mechanism.
The added guard is a fixed definition, not a calculation on the current query.

## Fresh coverage pilot

Use fixed seed **2026102038** for eighteen fresh synthetic states in nine
reflected pairs. Include one pair per wheel-magnitude × pedal combination:
six straight, six moderate and six full labels; six cases for each pedal.
All fifteen native targets occur, with each straight target twice and each
signed non-straight target once. Match this coverage for held inputs with no
complete held-input copy of a target.

All six straight bearings must satisfy **0.05 ≤ abs(theta) ≤ 1.5 degrees**,
with both signs and each pedal represented. Other labels remain at least two
degrees from every wheel threshold. Keep 0037's branch assignments: stopped
off-road straight acceleration; slow outward moderate acceleration with the
speed-below-2 priority; fast near-edge inward full acceleration with a false
guard; one off-road inward coast pair; and the remaining coast/brake pairs
under on-road outward guards. Maintain protected predicate margins.

Require finite forward 15 m targets, positive finite squared range and no
known positive uncredited next-gate plane. Reconstruct full current states
through production renderers before the unchanged factual projection, including
null velocity angles at rest. Synthetic off-road states have zero rescue
elapsed time and no previous rescues. These fixtures do not validate physical
recovery or braking effectiveness.

All eighteen rounded 15 m x/y pairs must be unique and absent from materialized
0016–0037 static banks, including 0035's natural bank, and documented examples.
This is the declared freshness scope; it does not claim exhaustive comparison
against every historical model query. Geometry and fixed coverage constraints,
not paid responses, determine generation. Reflections and paired arms remain
related observations; one presentation per arm does not estimate repeatability.

## Collection and perfect gate

Collect **36 calls maximum**, eighteen cases × baseline/candidate. Shuffle
case units with seed `2026102038`; at index j alternate first arm by `j % 2`
and reverse both component menus by `j // 2 % 2`. Match each pair's state and
menu order. Each arm occupies each request position nine times. First-arm ×
menu-order cells contain five, five, four and four units; normal/reversed menus
cover ten/eight case units.

There is no correctness stop or format gate. Retain every structurally valid
planned response. Technical, identity, uncertain-accounting, hard-budget or
deadline failure stops admission and preserves every attempt and unrun entry.
Use the pinned dated Jev model at TypeSafe, one paid writer, one request in
flight, zero automatic retries and no fallback.

The candidate must satisfy every requirement:

- **18/18 exact native pairs, 18/18 wheels and 18/18 pedals** correct.
- **Zero BRAKE selections below 2 m/s**.
- Complete collection, strictly typed atomic components, exact native inverse,
  zero endpoint/accounting errors and passing independent audit.

Report paired gains/losses descriptively, component and subgroup scores,
guard-branch coverage, chosen-input distributions and each preserved error.
Comparative gain is not a separate admission requirement. A perfect score
without gains establishes no comparative improvement.

Passing can motivate only a **new fresh sixty-case broader native validation
under unchanged 0035 thresholds**. It does not admit direct live use or promote
a preset. An eventual race separately requires the current-boot clock gate,
exact serving identity, applicable exact free control, all native gates and
actual resource/time admission. Another failed pilot retains its gate failure.

## Resources and evidence

The saved completed 0037 boundary is **61,495 requests, $7.579654281999889 and
244,855,779 charged tokens**, leaving **5,144,221 tokens**, with 69 historical
uncertain charges and no pending reservations. Preserve all history and the
shared **75,000-request / $10 / 250-million-token** caps. Every call retains
the conservative **16,384 input + 235,929 output = 252,313 token** reservation.
The authorized admission deadline remains **06:17:26 UTC**.

The five-million-token race-admission guard remains unchanged. Read the actual
ledger after each phase: a pilot and broader validation may leave insufficient
headroom for live racing even if their score gates pass. No live outcome or
token availability is promised.

Production source remains
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
The complete current-boot Python clock gate passed at 04:09:25 UTC; this
qualifies timing only and does not waive native or paid admission conditions.

Before collection, freeze exact aliases/guard/expanded clauses, questions,
policy, factual projection, bank, origin references, route, order and helper
hashes. Require actual-wire mocks with zero model calls and unchanged ledger,
unchanged inherited production decoding/accounting, exact factual/label proofs,
immutable passing independent preflight and timestamped root authorization.
After writer termination, independently reconcile every raw typed response,
native mapping, payload and ledger transition. Preserve failures and unrun
entries. Never rerun earlier audit CLIs against an advanced ledger.

## Completed literal-conditions pilot

All **thirty-six planned calls** completed with no endpoint/accounting errors,
unrun entries, retries or replacement trials. Every valid planned reply was
retained. Baseline questions were exact 0037 candidate. The only registered
change was the criterion-value package: literal factual field references and
expanded Boolean eligibility conditions. All component instructions, physical
definition lists, factual inputs, policy, native IDs and inverse mapping stayed
unchanged. No evaluated guard, target or branch was added to state, no paid
command was applied and no physics advanced.

| Measure | Baseline aliases | Literal criteria |
|---|---:|---:|
| Exact native pair | 16/18 | 15/18 |
| Wheel component | 16/18 | 15/18 |
| Straight wheel | 4/6 | 3/6 |
| Moderate wheel | 6/6 | 6/6 |
| Full wheel | 6/6 | 6/6 |
| ACCELERATE pedal | 6/6 | 6/6 |
| COAST pedal | 6/6 | 6/6 |
| BRAKE pedal | 6/6 | 6/6 |
| All pedals | 18/18 | 18/18 |
| BRAKE chosen below 2 m/s | 0/4 slow cases | 0/4 slow cases |

Literal criteria had **no paired gains and one loss**. Fifteen states were
correct in both arms and two were wrong in both. Every pedal and every
non-straight wheel was correct in each arm. The remaining errors were:

| Bearing | Expected | Baseline | Literal criteria |
|---|---|---|---|
| −1.3417° | `straight_accelerate` | `hard_right_accelerate` | `hard_right_accelerate` |
| +0.8387° | `straight_coast` | `hard_left_coast` | `hard_left_coast` |
| +1.4776° | `straight_brake` | Correct | `hard_left_brake` |

All three literal-arm errors were straight targets well inside the straight
interval. The new loss was the positive small-bearing brake state. No response
was rerun or replaced and no threshold was relaxed. The candidate failed
**18/18 exact pairs and 18/18 wheels**; perfect pedals, low-speed-brake and
technical requirements passed. Comparative gain was descriptive, not an
additional gate requirement. No broader validation, live race or promotion
is admitted. Retain joint `damped` and unchanged application defaults.

This package did not improve supplied-policy compliance on this bank. Literal
paths and Boolean expansion were changed together, so the result does not
isolate an internal mechanism or establish a general directional bias.
Eighteen synthetic states in nine reflected pairs and one presentation per
case limit generalization and leave within-arm repeatability unmeasured.
These are rule-compliance labels, not optimal controls or race outcomes.

## Validation, runtime and accounting

The final audit passed with **`complete=true` and no errors or warnings**.
It checked all eighteen factual states and labels, exact alias/guard expansion,
unchanged instructions and physical definition lists, identical paired states,
matching menu order, raw typed components and native inverse, fixed request
order and every sequential budget transition. Source inheritance and local
wire/error mocks passed before admission. The origin manifest checked
seventy-five evidence files and an exact policy copy; no old frozen CLI ran
against a later ledger. Production source, handling and physics were unchanged.
Inherited free host-policy evidence establishes nominal tracking only: no
complete source rollout triggered the guard or established physical recovery.
Separate collection-provenance verification passed all **47 checks**, including
immutable preflight/authorization chronology, all thirty-six exact wire payloads
and raw typed pairs, fixed order, source, writer and the entire ledger chain.
It confirmed identical states, instructions and physical definitions, with
only the registered whole-word alias expansion in criteria. Baseline questions
matched the frozen 0037 candidate origin exactly. Root tool chunk/session
identifiers were checked against preserved execution confirmation rather than
independently queried from tool infrastructure; actual writer and ledger records
were independently verified.

The current-boot runtime timing gate passed at **04:09:25 UTC**, bound to source
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`, boot
`f534ef07-e837-401d-bf64-a0fe7c51e3d3` and HTTP parent PID 1751/start ticks
85454. Timing qualification does not waive candidate control, native gates or
actual resource/time admission. Separately recorded free-policy seeds 21/22
are possible future validation evidence, with no model qualification granted.

Independent prospective preflight passed at 04:17:54 UTC. Root authorization
`b7498bb9cd194f0398b1c31c5511f57b` at **04:18:22 UTC** preceded the sole writer's
**04:18:27.941159 UTC** start. Its session was
`a164a03a01d44802bbef238acd25e52f`, PID 3859, with explicit collection enabled.
All thirty-six calls are in the completion record and root confirmed exit zero.
Existing identity checks, caps, conservative reservations and no-retry/no-fallback
policies were retained.

The pilot used **thirty-six requests, $0.0030219839999938714 and 75,401 charged tokens**.
Its saved audited end boundary is **61,531 requests, $7.582676265999883 and
244,931,180 charged tokens**, with 69 historical uncertain charges unchanged
and pending empty. This report uses saved evidence and does not rerun an audit
against a later ledger.

The [machine-readable summary](0038-literal-conditions-summary.json) retains
frozen and completed evidence. The exact [prompt archive](0038-literal-conditions-prompts.json)
remains unchanged. A passing pilot would still require fresh broader validation
under unchanged 0035 thresholds; this pilot did not pass.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `c93bd299d83d5e3b0ca8e76dcf9c4a590c3dc7583a7741edf3c25fba6d10e0c2` |
| Exact prompt archive | `1aebde4dcae22c905dc9eb188e5623871915b8df769c30e6e533752a106a1483` |
| Final audit | `bdf30c04bb20432f8e78f9863da2cd469b220c11d4c5a70ed4c50fbe9275ab54` |
| Audited report summary | `78f561597a333a089c59bdbdb06e527f5b13c41b063478e4d8ab1ed8aa746c7b` |
| Source-inheritance proof | `ba91bbaea3b4fadba5f68f444ed35cadaaef68c14dc03ba4353c8856f3e8c270` |
| Frozen origin manifest | `17ca7f86a5a4cb6a9fa61ac1d7ba4f67a36661550489b93326fd2809d83eb74d` |
| Collection provenance | `cfc5cfc449c6267bdec6ac079b3960ee1169d8211fe9732b59681d68f2cebbed` |

Source remains `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
