# Transferring the bearing policy to a driving question

Status: complete, October 20, 2026. Final audit and separate collection-provenance
verification passed. Static and driving framings both
scored 26/30 exact native pairs. The driving gate failed its overall, straight
and moderate-wheel requirements; the conditional exploratory race is withheld.
No preset is promoted. The original prospective registration follows, with its
immutable copy retained under `artifacts/jev-native-policy-bridge-v1/prospective-design.md`.

The completed
[0032 comparison](0032-bearing-policy.md) passed its gate: the factual-bearing
arm selected 28/30 exact native pairs versus 10/30 for raw x/y, with eighteen
paired gains and no losses. Both arms selected every pedal correctly. The
bearing arm achieved 6/6 straight, 11/12 moderate and 11/12 full wheels.
That establishes supplied-policy execution on those cases, not race competence.

The next question is whether that capability transfers from an explicitly
static compliance question to the exact question framing proposed for driving.
The geometry is fresh, but this is not an independent replication of the
bearing-versus-x/y effect: both arms now receive the factual bearing. No native
control is applied and no physics advances during this bridge.

## Fixed policy, physical choices and the single contrast

Keep Python physics, the 24 m stadium, 12 m/s speed ceiling, 0.12 rad wheel
limit, three laps and three-second rescue unchanged. Preserve the joint
`damped` baseline and application defaults. Neither arm adds that guide.

Copy 0032's `policy.py` byte-for-byte. Its canonical point bearing is
`round(degrees(atan2(y,x)),4)`, computed from the same three-decimal 15 m
preview x/y facts. Thresholds -22, -7, +7 and +22 degrees select full right,
moderate right, straight, moderate left and full left, with exact boundary
ties directed toward the smaller absolute wheel angle. Keep the complete
pedal guard, low-speed acceleration priority and unsupported-domain handling
unchanged. This remains a supplied engineering policy, not an equivalent
pursuit formula or an optimal-control label.

Both arms receive identical full factual `road_navigation` observations,
current road-frame motion and `road.preview_15m_bearing_deg`. No evaluated
guard, chosen branch, eligibility flag, target wheel or recommended native
input enters model state. Only offline proof contains labels. The host adds
the same factual angle in both arms; Jev chooses every returned component.

Use the same two-question factored interface, production physical component
descriptions, native IDs and exact Cartesian inverse. Common definitions,
wheel/pedal tasks and criterion-local eligibility clauses are byte-identical
between arms. Change only each component's task prefix:

- `static`: the exact 0032 bearing-arm questions, including its original
  `STATIC POLICY-COMPLIANCE CHECK` prefix.
- `driving`: replace that prefix with the following exact string, including
  the trailing space inside the quotes:
  `"DRIVING POLICY. Choose the next native input by executing the supplied policy exactly. "`

The complete remaining instructions and all criteria are unchanged. Local
wire proofs must establish that this prefix replacement is the sole question
difference and that both arms submit identical current facts. No response-key
rewriting, aliases, host action selection or new production decoder is allowed.

This bridge checks fresh physical-choice compliance and framing transfer using
the native interface intended for the exploratory race. It does not re-prove
that interface from scratch: 0024 already tested prescribed native semantics,
and 0032 exercised this factored inverse. Extra prescribed-format controls are
therefore omitted.

## Fresh bank and inherited free evidence

Generate thirty fresh synthetic states in fifteen reflected pairs. All
fifteen prescribed wheel/pedal native targets occur exactly twice, and every
native held input also occurs twice. No complete held input equals its target.
Maintain six straight-wheel, twelve moderate-wheel and twelve full-wheel
labels, with ten for each pedal. Every canonical bearing is at least two
degrees from all wheel thresholds.

Retain 0032's pedal/rest coverage and predicate margins: two stationary
near-off-road acceleration cases, four slow outward acceleration cases and
four fast acceleration cases without the guard; ten guarded coast cases
and ten guarded brake cases. Vary actual wheels, yaw and motion consistently.
Stationary velocity angles are null. All 15 m targets are forward and finite,
and no known next gate has a positive uncredited signed plane. Exclude
unsupported cases without inventing a recovery label.

Require distinct rounded 15 m x/y pairs absent from the earlier static banks
and worked examples. Generate cases using declared geometry and coverage,
never paid responses. Reflections and transient synthetic poses remain related
constructed observations, not natural recovery episodes or independent races.

The fixed policy already passed 0032's four free nominal tracking runs, on
seeds 15 and 16 at zero and 250 ms delay with 250 ms request cadence. No policy
or physical parameter changes here, so no new free policy search or tuning is
needed. Freeze an origin manifest binding the unchanged policy and inherited
free scripts, reports and trajectories. Verify referenced file hashes and
saved independent evidence without altering those files or rerunning an old
audit CLI against the now-advanced ledger. Preserve the original limitations:
free nominal tracking does not validate unexercised pedal or recovery branches.

## Ordered collection and prospective gate

Collect **60 calls maximum**: thirty cases x static/driving framing, one
presentation each. Shuffle case units with seed `2026102033`. At shuffled
index j, alternate the first context using j%2 and reverse both wheel and
pedal menus using j//2%2. Match both menu orders within each case. Each
context occupies each request position fifteen times; the four first-context
and menu-order cells contain seven or eight units.

There is no format gate, correctness stop, retry or replacement trial. Retain
every valid planned response regardless of correctness. Technical, identity,
uncertain-accounting, hard-budget and deadline failures stop admission while
preserving every attempt and unrun entry. Use one paid writer, one request in
flight, no provider fallback and the pinned dated Jev model at TypeSafe.

The driving arm must meet every descriptive requirement:

- At least 27/30 exact native pairs correct.
- Wheel agreement 6/6 straight, at least 11/12 moderate and 11/12 full.
- At least 9/10 correct in each pedal class.
- Zero BRAKE selections when speed is below 2 m/s.
- Driving exact-pair accuracy no more than one net correct pair below the
  concurrent fresh static arm: driving_correct - static_correct >= -1.
- Complete collection, strictly typed atomic component answers, exact native
  inverse mapping, zero endpoint/accounting errors and a passing independent
  audit.

Report wheel, pedal and exact-pair agreement by class and signed direction;
paired gains and losses; chosen-input distributions; source-case coverage;
and raw response evidence. The net-score requirement does not prohibit more
than one individual paired loss if gains offset losses. One presentation
provides no within-arm repeatability estimate. Fresh cases do not establish
general driving competence, and passing this bridge does not promote a preset.

## Resource boundary and conditional exploratory race

The completed 0032 boundary is **61,219 requests, $7.554155703999885 and
244,222,231 charged tokens**, with 69 historical uncertain requests and no
pending reservations. Preserve all history and the shared **75,000 requests /
$10 / 250-million-token** caps. Retain the conservative **16,384-input plus
235,929-output = 252,313-token** reservation for each call. The authorized
session admission deadline remains **06:17:26 UTC**.

Before paid bridge admission, freeze the bank, exact questions and arm contrast,
origin manifest, menus, order, route, source and helper hashes. Require local
actual-wire mocks, unchanged inherited production decoding/accounting, passing
independent preflight and timestamped root authorization bound to the protocol,
preflight and shared ledger. The final audit follows writer termination and
reconciles every response and ledger transition.

Only a passing bridge can motivate a **separately frozen single exploratory
three-lap Jev race on seed 17**, using the exact driving questions and factual
bearing representation. Admit that race only if the existing guard still has
at least five million tokens available before it starts, with all other caps,
deadline and current source/environment timing qualification satisfied. Any
runtime/source change requires its applicable fresh clock qualification.
Unsupported policy-domain states must stop the exploratory attempt rather
than trigger invented recovery controls.

One exploratory race can demonstrate feasibility or expose closed-loop failures.
Report finish/progress, grass, rescues, timing, latency and supplied-policy
agreement. It cannot establish paired improvement over `damped`, qualify the
candidate or promote a preset. No second race is implied; preserve the live
admission guard and continue authorized static work within the remaining caps
and session deadline.

## Completed bridge observations

All **sixty planned calls** completed, with zero endpoint/accounting errors,
no unrun entries and no retries or replacement trials. Every valid answer was
retained. The fixed bearing policy, full factual state, two component IDs,
physical menus and their atomic Cartesian inverse remained unchanged; only the
registered task prefix differed. No paid control was applied and no physics
advanced.

| Measure | Static framing | Driving framing |
|---|---:|---:|
| Exact native pair | 26/30 | 26/30 |
| Wheel component | 26/30 | 26/30 |
| Straight wheel | 5/6 | 5/6 |
| Moderate wheel | 10/12 | 9/12 |
| Full wheel | 11/12 | 12/12 |
| ACCELERATE pedal | 10/10 | 10/10 |
| COAST pedal | 10/10 | 10/10 |
| BRAKE pedal | 10/10 | 10/10 |
| BRAKE chosen below 2 m/s | 0 | 0 |

Driving framing produced **one paired gain and one loss**, with twenty-five
states correct in both arms and three wrong in both. Its net exact-pair
accuracy difference was zero. Every pedal was correct in both arms, so all
pair errors were wheel errors. Equal overall scores do not mean identical
decisions, nor do they establish equivalent internal processing.

The driving arm passed full-wheel, pedal, low-speed-brake and relative-score
requirements, but failed **27/30 exact pairs, 6/6 straight and 11/12 moderate**.
The frozen bridge gate therefore failed. The conditional seed-17 exploratory
race is **not admitted**, with no retry, gate relaxation or preset promotion.
Retain the joint `damped` baseline and unchanged application defaults.

This bridge tests framing transfer on fresh synthetic states with bearing
available in both arms. It is **not a replication of the bearing-versus-x/y
contrast** from 0032, and the different bank prevents attributing its fresh
static score of 26/30 versus the earlier 28/30 to drift or framing. The current
comparison shows only the observed paired framing outcomes. Labels measure
execution of the supplied policy, not optimal actions or live competence.
Reflections, components and paired arms are related observations; one
presentation supplies no within-arm repeatability estimate.

## Validation and accounting

The final audit passed with **`complete=true` and no errors or warnings**.
It reconstructed all thirty policy labels and factual states, checked the exact
prefix-only question contrast, unchanged component menus and native inverse,
raw typed wheel/pedal answers, balanced order and all sequential budget changes.
The source-inheritance proof and local wire/error mocks passed before admission.
Production source, handling and physics remained unchanged.

The frozen origin manifest binds the unchanged bearing policy and twenty
origin evidence files. Its independent review and exact policy-copy check
passed; the audit did not execute an old frozen CLI against a later ledger.
Inherited free evidence supports nominal tracking only: no complete free run
triggered the guard, so braking, coasting and recovery remain physically
unvalidated. Those free host-policy races are not Jev race attempts.
Separate collection-provenance verification passed all **46 checks**, including
the immutable preflight/authorization chronology, sixty actual wire payloads,
raw typed pairs, source identity, writer and full ledger chain. Matched states
were byte-identical, and questions differed only by the initial registered
prefix. Static questions matched the frozen 0032 bearing origin exactly.
Root tool chunk/session identifiers were checked against preserved execution
confirmation rather than independently queried from tool infrastructure; actual
writer and ledger records were independently verified.

Root authorization at **03:24:37.566824 UTC** preceded the sole writer's
**03:24:44.051156 UTC** start. Its session was
`0a715fdc7d6e4bc5946f6a164ad0d880`, PID 38945, with explicit collection enabled.
The completion record contains all sixty calls; root confirmed process exit
zero. Existing identity checks, conservative reservations and caps were retained.

The bridge used **sixty requests, $0.007655171999997101 and 188,015 charged tokens**.
Its saved audited end boundary is **61,279 requests, $7.561810875999882 and
244,410,246 charged tokens**, with 69 historical uncertain charges unchanged
and pending empty. This report uses saved evidence and does not rerun an
audit against a later ledger.

The [machine-readable summary](0033-results-summary.json) retains frozen and
completed evidence. The exact [prompt archive](0033-native-policy-bridge-prompts.json)
remains unchanged.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `e5c8e82359218f6289840f18d5dbe3dc4609668019c17d1734e3773b05dd058b` |
| Exact prompt archive | `946a4e737af4818b1a8131f062d8514ac57607780927d29c03fb0c525f6ba005` |
| Final audit | `6c7c83640d2f22945f9721b9c0293a6f415cf5be0b7e17bd0d1362c89249ab85` |
| Audited report summary | `f1db5e25c7a400c1c2d4cfe4826df59867bd87080f080fdd5675e6d9f5965ec2` |
| Source-inheritance proof | `eb714b6022a7169f1fd90781a644871ed7b5c8a9d12e35adb418314cbbaa6637` |
| Frozen origin manifest | `3d06c7c8e72c3b9867bab4703f96ca4a1f8b33cd4e8f1ad266be53b7fe385bb7` |
| Collection provenance | `308e09fa25e0752fec4bc34c4378d1a98cb77c35c7b16cca07377515f2726cd9` |

Source remains `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
