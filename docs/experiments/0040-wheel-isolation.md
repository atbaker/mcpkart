# Separating wheel-question and factual-context effects

Status: complete static diagnostic, October 20, 2026. Final audit and separate
collection-provenance verification passed. Wheel scores were 15/18 combined,
15/18 wheel-only/full facts and 18/18 wheel-only/reduced facts. All fifty-four
raw wheel responses were strictly valid; thirty-six original missing-pedal
native rejections remain preserved. There is no accuracy gate and no outcome
qualifies native controls or live use. The original registration follows, with
an immutable copy retained under `artifacts/jev-wheel-isolation-v1/prospective-design.md`.

The recent deadband, criterion-placement, literal-condition and plain-English
packages did not establish a qualified driver. This probe changes request
structure and available facts instead of adding another wording package. It
separates removing the pedal question from removing pedal-related factual state
while holding the requested wheel question fixed.

## Three arms and the exact common baseline

Return to the frozen **0034 `facts` wording and fixed bearing policy**, without
the failed 0036–0039 additions. Preserve the 0034 common definitions, physical
descriptions followed by criterion-local eligibility clauses, native wheel and
pedal IDs, component meanings and native inverse. No deadband-first addition,
physical-definition relocation, literalized criteria or English rewrite remains.
This rollback is common to all arms, not an experimental comparison with an
earlier historical result.

Symmetrically replace the existing `WHEEL_TASK` in **all three arms** with the
following exact string, including its leading newline:

```python
"\nWHEEL TASK: Select the single allowed absolute wheel ID whose supplied policy condition holds. Return only that wheel choice."
```

This removes the original promise that a pedal is selected separately in the
same request, which would be false in an isolated wheel request. Every other
instruction byte is unchanged. The combined arm retains its original pedal
question; its statement that the wheel is selected separately in that request
remains true. Do not correct or reword only an isolated arm.

Use these exact contexts:

| Context | Submitted questions | Submitted state |
| --- | --- | --- |
| `combined_full` | Original wheel and pedal heads, with the common neutral wheel task above | Complete 0034 `facts` projection |
| `wheel_full` | That identical wheel question only, under the original `wheel` key | Byte-identical complete 0034 `facts` projection |
| `wheel_facts` | The identical wheel-only question | Fixed wheel-relevant projection described below |

Here “full” means the complete **0034 facts projection**, containing both
components' policy facts. It does not mean dense original `road_navigation`
telemetry. The physical wheel criteria and their submitted order must be
identical within each three-arm case unit. The combined pedal menu follows
that unit's frozen normal/reversed menu assignment.

The unchanged bearing policy uses the canonical factual scalar
`round(degrees(atan2(y,x)),4)` from the same three-decimal 15 m preview x/y
coordinates, thresholds -22/-7/+7/+22 degrees and inward boundary ties.
Keep the original pedal guard and low-speed priority for combined-arm scoring.
Python physics, the 24 m stadium, 12 m/s ceiling, 0.12 rad wheel limit, three
laps and three-second rescue remain fixed. No simulation advances or native
control is applied during paid collection. Preserve application defaults and
the joint `damped` baseline.

## Exact wheel-only factual projection

Construct the complete 0034 facts state first, including the canonical bearing.
Both `combined_full` and `wheel_full` receive that same object representation.
For `wheel_facts`, retain only:

- The original complete top-level `units` string, unchanged.
- `road.preview_15m_bearing_deg`.
- `road.preview_columns`: the original three entries `ahead_m`, `ego_x_m`,
  `ego_y_m`, in the same order.
- `road.preview`: the sole original ahead-15 row and its three original cells.
- `next_gate.known` and `next_gate.signed_plane_m`.

Remove every other path, including kart speed, road status/offset/clearances
and the complete current-road-frame object. Do not rename, recalculate,
reformat or replace a retained scalar, unit string or table cell. Independently
verify exact source JSON representations and this complete whitelist. Add no
query-specific eligibility flag, host-evaluated guard, target wheel, selected
branch, expected answer or recommendation.

All wheel criteria use the retained bearing. The unchanged COMMON text still
defines pedal aliases `speed`, `L` and `B`; their referenced pedal facts are
absent in `wheel_facts` and cannot be evaluated there. Those definitions are
irrelevant to the requested wheel choice but may affect responses. Preserve
them as part of the selected factual-deletion treatment and register this
limitation; do not silently rewrite COMMON for the reduced arm.

Retained next-gate facts support the unchanged domain contract. Fresh states
must have finite forward 15 m coordinates, finite positive squared range and
no known positive uncredited next-gate plane. Keep full observation provenance
outside payloads so all policy labels and source facts remain independently
reconstructible. Wheel-only state cannot evaluate the pedal policy and is not
represented as a complete driving observation.

## Fresh cases and counterbalanced order

Generate eighteen fresh synthetic current states in nine reflected pairs,
using seed **2026102040**. Cross wheel magnitude with pedal class: six straight,
six moderate and six full wheel labels, with six source cases per pedal.
All fifteen native source targets occur, with each straight target twice and
each non-straight target once. Match held-native-input coverage and prohibit
complete held-input copies of their targets.

Keep the recent focused coverage: fresh signed small straight bearings within
0.05–1.5 degrees in absolute value, at least two degrees from other wheel
thresholds, broad track arcs and protected guard predicates. The acceleration
pairs cover stopped off-road, slow outward guard-true and fast near-edge inward
guard-false states. Include off-road inward coast as well as on-road outward
coast/brake cases. These pedal-related source facts supply varied context in
the two full-facts arms; they are intentionally absent from `wheel_facts`.

Require distinct rounded 15 m x/y pairs absent from earlier static banks and
demonstrations. Generate geometry from fixed constraints, never model answers.
Full current observations must reconstruct exactly through production renderers,
including stationary null velocity angles. Reflections and transient synthetic
states remain related constructed observations rather than independent races
or demonstrated physical recoveries.

Collect **54 calls**: eighteen cases x three contexts, one presentation each.
Shuffle with seed `2026102040` and use **all six context permutations three
times each**. Assign matched menu order within each case, with nine normal
and nine reversed units. Each context occupies each request position six times;
within every context/position cell, three presentations have each menu order.
Freeze and independently verify the exact assignments before collection.

## Original native rejection and separate diagnostic scoring

Preserve the inherited production `DecisionClient.decide`, transport,
reservation and accounting behavior. A property-only question adapter may
submit the exact combined question dictionary or its unchanged `wheel` member
alone. Do not rewrite response heads or aliases, fabricate a pedal, replace a
native choice or change the production decoder to make isolation look native.

The factored production decoder expects both heads and normally rejects a
single-head response for its missing pedal. **Preserve that original record
and rejection unchanged.** It is expected incompatibility with native decoding,
not by itself an endpoint failure of this dedicated probe. Determine requested
wheel diagnostic validity separately from the original typed raw response.
Require the original `wheel` head to be a non-refused typed choice with one
of the five unchanged wheel IDs. Require HTTP/API success, exact dated model
and TypeSafe provider, reported aggregate accounting and the exact single-POST
ledger transition. Unexpected requested-head, endpoint, identity or accounting
failures stop collection. Do not excuse them as a missing unrequested pedal.

Save complete credential-free payloads, original typed responses, unmodified
production records and separate diagnostic validity/score fields. **Any
unsolicited answer head is a technical stop**, even when the requested wheel
head is valid. Preserve and report its original response and production record;
never use an unrequested pedal to construct or qualify a native success. All
arms are static, and no returned action reaches
an actuation path. The combined arm's pedal/pair agreement may be reported as
ancillary evidence but cannot supply an accuracy gate or live admission.

There is **no accuracy gate, correctness stop or automatic qualifying
continuation under any outcome**. Retain every valid planned response regardless
of correctness. Technical, identity, uncertain-accounting, hard-budget and
deadline failures preserve every attempted and unrun entry; there are no
retries, replacements or provider fallback. Keep one paid writer and one
request in flight.

## Prespecified comparisons and interpretation

The primary paired wheel comparisons are:

- **`wheel_full` minus `combined_full`:** removing the other question while
  keeping the full facts state and requested wheel question fixed.
- **`wheel_facts` minus `wheel_full`:** deleting irrelevant factual state in
  an otherwise identical wheel-only request.

Report each context's requested-wheel validity, wheel accuracy, magnitude,
signed direction and small-straight sign; paired gains/losses; chosen-wheel
distributions; expected native-decoder rejections; unsolicited heads; and source
coverage. Report raw uncertainty descriptively without inventing a native joint
distribution, normalization or calibration.

This is not a full factorial: there is no combined-head/reduced-state arm, so
no interaction is identifiable. Head removal also changes the response contract
and possibly provider processing; factual deletion changes information and
length. Neither contrast establishes an internal attention mechanism. The
neutralized task and fresh bank also prevent treating historical scores as
concurrent comparison arms. Eighteen related cases and one presentation do
not establish repeatability or general driving competence.

A future isolated-component driver would need a separately designed native
interface and physical/timing validation. Two sequential component requests
could increase observation age; this diagnostic does not qualify such a loop.

## Resource and evidence boundary

The starting shared ledger is **61,567 requests, $7.586051301999877 and
245,014,989 charged tokens**, with 69 historical uncertain requests and no
pending reservations. **4,985,011 tokens remain**, already below the unchanged
five-million-token live race-admission floor. Live actuation therefore remains
held regardless of this diagnostic's accuracy. Do not relax that guard or
promise a live attempt.

Preserve all history and the shared **75,000 requests / $10 /
250-million-token** caps. Each POST retains the full conservative
**16,384-input + 235,929-output = 252,313-token** reservation, including isolated
requests; do not shrink advertised output or factored input reservation because
only one question is submitted. The authorized session admission deadline
remains **06:17:26 UTC**.

Before collection, freeze exact neutralized questions, arm-only head/state
differences, fresh bank, projection, expected decoding interpretation, route,
source, order and helper hashes. Require actual-wire mocks for all planned
payloads and requested-head failures, zero real model calls and unchanged shared
ledger, immutable passing independent preflight and timestamped root
authorization. Final independent audit follows writer termination and
reconciles every raw response, separate diagnostic score and ledger transition.
Keep raw evidence ignored; preserve exact versioned prompts and audited results.

## Completed head/context diagnostic

All **fifty-four planned calls** completed with **fifty-four strictly valid
requested raw-wheel responses**, zero diagnostic technical/accounting failures,
no unrun entries and no retries or replacements. Every planned response was
retained. The common 0034 wording rollback and neutralized wheel task were
fixed in all three contexts; they are not comparisons with historical scores.
No paid command was applied and no physics advanced.

| Measure | Combined/full | Wheel-only/full | Wheel-only/reduced |
|---|---:|---:|---:|
| Requested raw wheel valid | 18/18 | 18/18 | 18/18 |
| Wheel agreement | 15/18 | 15/18 | 18/18 |
| Straight wheel | 3/6 | 3/6 | 6/6 |
| Moderate wheel | 6/6 | 6/6 | 6/6 |
| Full wheel | 6/6 | 6/6 | 6/6 |
| Original native decode accepted | 18/18 | 0/18 | 0/18 |
| Expected missing-pedal native rejections | 0 | 18 | 18 |
| Pedal agreement, ancillary | 18/18 | Not requested | Not requested |

The **thirty-six original `invalid_action`/missing-pedal native verdicts remain
unchanged**, with no fabricated pedal or native action. They are expected
production decoding rejections, separate from requested-wheel validity and
endpoint/accounting failures. Both wheel-only contexts returned only `wheel`;
combined responses returned `wheel` and `pedal`. There were no unsolicited
heads. Missing pedal observations are not zero pedal accuracy, and a valid
wheel score does not turn these incomplete outputs into native commands.

Removing the pedal head with full facts produced **zero paired accuracy gains
and zero losses**. Both contexts missed the same three states, although one
wrong magnitude changed. Removing pedal-related factual state from an otherwise
identical wheel-only request produced **three gains and no losses**:

| Bearing | Expected | Combined/full | Wheel-only/full | Wheel-only/reduced |
|---|---|---|---|---|
| −1.3176° | `straight` | `hard_right` | `right` | `straight` |
| +1.2240° | `straight` | `left` | `left` | `straight` |
| +1.3176° | `straight` | `hard_left` | `hard_left` | `straight` |

Thus all gains on this bank were small-bearing straight cases: two positive
and one negative. Combined pedals were 18/18 correct, six in each class, as
ancillary observations. Wheel probabilities and confidence fields were present
in all fifty-four replies and remain descriptive; none was normalized or used
to invent a joint native distribution or calibration claim.

The reduced arm still retained unused pedal definitions in common instructions;
the measured package deletes factual inputs under those fixed instructions.
It is not a full factorial because combined-head/reduced-state was absent,
so no interaction is identified. Head removal changes the response contract
and potentially provider processing; factual deletion changes information and
length. Neither isolates an internal attention mechanism. Eighteen related
synthetic cases and one presentation per context do not establish repeatability
or general driver competence.

**There is no accuracy gate and no native/live qualification under any outcome.**
The perfect reduced-arm score remains a raw-wheel diagnostic result. It does
not validate a pedal policy, native action interface or closed-loop driver.
Retain joint `damped` and the original application default.

## Validation and retained free corrections

The final audit passed with **`complete=true` and no errors or warnings**.
It reconstructed the eighteen full states and wheel labels, verified exact
head/state masks and common wording, strict requested raw-head validation,
all thirty-six unmodified expected native rejections, combined outputs, order
and every complete ledger transition. Source inheritance and decoding review
passed before admission. The origin manifest checked thirty-nine evidence
files and an exact policy copy; no old frozen CLI ran against a later ledger.
Production source, physics and handling remained unchanged.

Before freezing, independent review required a full predicted post-request
ledger transition instead of adopting partially checked actual state. The
artifact runner and free checks were hardened, all **114 local mocks passed**,
and the earlier scripts/proofs were retained under
`artifacts/jev-wheel-isolation-v1/diagnostics/pre-full-ledger-guard/` with their
hash manifest and reason. Client, payload and question bytes did not change;
no model call or paid evidence was changed or rerun. This was a free admission
check correction, not a model observation.

Separate collection-provenance verification passed all **48 checks**, including
immutable preflight/authorization chronology, all fifty-four exact wire
payloads, requested heads/masks/questions, raw choices, native verdicts, saved
full-ledger validations, source identity, actual writer and complete ledger
chain. Its initial reader expected the obsolete report key `correct` instead
of `wheel_correct` and raised `KeyError` before writing an initial JSON result.
That exception metadata is retained in the final proof. Only the checker was
corrected; no frozen helper, paid record, source or ledger changed. Root tool
chunk/session identifiers were checked against preserved execution confirmation
rather than independently queried from tool infrastructure; actual writer and
ledger records were independently verified.

Current-boot runtime timing remains passed at **04:09:25 UTC**, bound to source
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`, boot
`f534ef07-e837-401d-bf64-a0fe7c51e3d3` and HTTP parent PID 1751/start ticks
85454. This is runtime evidence, not candidate qualification. Free host-policy
rollouts remain nominal tracking evidence, not Jev races or validated recovery.

Independent frozen preflight passed at 04:41:28 UTC. Root authorization
`b985046ea65242bf9494169154c284e4` at **04:41:50 UTC** preceded the sole writer's
**04:41:55.486747 UTC** start. Its session was
`4cc553359b9743eab9a9eee061273313`, PID 6573, with explicit collection enabled.
All fifty-four calls appear in the completion record and root confirmed exit
zero. No retry, fallback, cap or conservative reservation was relaxed.

The diagnostic used **fifty-four requests, $0.003147563999995384 and 78,623 charged tokens**.
Its saved audited end boundary is **61,621 requests, $7.589198865999872 and
245,093,612 charged tokens**, with 69 historical uncertain charges unchanged
and pending empty. Remaining **4,906,388 tokens** are below the unchanged
**5,000,000-token live-admission guard**. Live is resource-blocked independently
of diagnostic outcomes; authorized static research continues within shared
hard caps and the 06:17:26 UTC deadline.

This report uses saved evidence and does not rerun an audit against a later
ledger. The [machine-readable summary](0040-wheel-isolation-summary.json)
retains frozen and completed evidence; the exact
[prompt archive](0040-wheel-isolation-prompts.json) remains unchanged.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `3379845a94125eec380de731cd738cb6131f438aa45775ca90f21bc48ae1e441` |
| Exact prompt archive | `bbc9daab0e47b37bc5bf9880ce998c46293b7f9de5faf5fdbbc67036db576e09` |
| Final audit | `d797a8eaae0e10c138de78e51d754384318fe38389c7b9f36f25a7fdfa5cd9ac` |
| Audited report summary | `83d1ec0472df89113fe417f45769544069bbfe95d457885ca9baa670a50ec00b` |
| Frozen origin manifest | `16e16a8beb56fafafba3149cf708de812691bf38aa0dde8caa04a332e5435e9a` |
| Preserved ledger-guard correction reason | `b107d492d6d0c34ebe0e702684fa30fde58272d74ae7a99bd2efb85f232caa81` |
| Collection provenance | `6619b7e75d79fabb88cdd9b8295cd7e3a59ae4fa274a0c5e9cf226507bf12a07` |
