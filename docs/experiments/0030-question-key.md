# Forecasting under a different API question name

Status: closed at the registered format gate, October 20, 2026. All eight
prescribed-format calls returned valid answers, but only seven were correct.
The required 8/8 gate failed, so all 32 physical forecasts remain unrun.
Final audit and corrected separate provenance verification passed; the audit
retains `complete=false` because the planned forecast phase was not collected.
No forecast comparison, qualification or live-use inference follows.
The original prospective registration is retained below.

In 0029, the unchanged forecast question and a fixed physics scaffold both
scored 8/16 on naturally reached current states by always selecting the physical
`stays_on_road` outcome. Earlier tests of quoted-guide presence, answer IDs,
current road-frame facts and explicit current-surface labels did not repair
that pattern. Prescribed response mapping and current-motion reading have
worked, which is distinct from forecasting future motion.

The API question has so far been named `control`, although it asks for a
forecast rather than a driving input. This small comparison changes only that
question name and its corresponding response lookup. It tests sensitivity to
an untested framing variable, not the internal cause of earlier failures.

## Deliberately reused states and fixed forecast task

Reuse the exact frozen 0029 bank of sixteen naturally reached current states.
These are intentionally repeated diagnostic fixtures, not fresh validation.
Keep their reconstruction and thirty-frame held-input labels unchanged. A
naturally reached current state is followed by a hypothetical continuation
holding its current native input fixed; the recorded racer may have issued
different later commands. The bank has eight safe and eight hazardous states,
eight on current straights and eight on current curves.

Both forecast arms receive the identical complete 0029 baseline state: existing
`road_navigation` plus the four factual current road-frame quantities and unit
text from 0028 B, retaining both current-surface labels and all body-frame,
handling, progress, rescue and runtime `finished` fields. Keep Python, the
24 m stadium, 12 m/s speed ceiling, 0.12 rad wheel limit, three laps and
three-second rescue unchanged. No physics scaffold, worked example, alternative
guide, future risk value or control recommendation is added.

The exact quoted `damped` guide, required half-second forecast question and
semantic criteria are the unchanged 0029 BASELINE. The physical answer IDs are
`leaves_road` and `stays_on_road`. Predict whether the centre is strictly outside
the road at any of the next thirty exact 60 Hz frames when the current native
input stays held. Touching an edge remains on-road. Expected answers, future
traces and reconstruction proofs remain outside forecast payloads.

| Arm | Submitted question property | Expected raw answer property |
|---|---|---|
| Control | `questions.control` | `answers.control` |
| Forecast name | `questions.future_departure` | `answers.future_departure` |

All question content and state are identical within a matched forecast pair.
The wire property name and corresponding parser lookup are the sole intended
changes. Their spelling and length change together; an effect would concern
this API-name contrast, not an isolated semantic mechanism.

## Prescribed-format gate and ordered forecasts

First collect **eight prescribed-format controls**: two question names × two
required physical categories × two criterion orders. Use the same fixed full
state representation in both arms. Assign current-state cases independently
of the prescribed outcome. These instructions explicitly supply a category and
ask for its matching criterion; they do not ask for a physical forecast or a
recommended control. Providing a required category is confined to this separate
format stage and is not an oracle leak into the forecast stage.

Collect all eight structurally valid controls, then require **8/8 correct**
before any forecast request. A valid but wrong category does not stop the
remaining format controls; after the eighth it leaves all 32 forecasts
conditionally unrun. Endpoint, identity, malformed-response and uncertain-charge
failures stop immediately at either stage. A missing arbitrary-key answer is
a technical parsing failure, not evidence of poor physical forecasting.

If the format gate passes, collect **32 forecasts**: sixteen states × two
question names, one presentation each. Shuffle states with seed `2026102030`.
At shuffled state index `j`, alternate the first question name using `j % 2`
and the first physical criterion using `j // 2 % 2`. Match criterion order
within each state. Each arm occupies each request position eight times and
has each physical criterion first eight times. Submitted option order does
not establish provider-internal ordering.

The maximum is **40 paid calls**. The new control arm is collected alongside
the forecast-name arm; historical 0029 responses are not substituted for it.
There are no hidden health probes, replacement attempts or additional repeats.
After the format gate, collect all structurally valid planned forecasts without
quality stopping or adaptation. No controls are applied and no race starts.

## Narrow artifact adapter and prospective verification

The `control` arm uses the original production `DecisionClient`. The
`future_departure` arm uses an ignored artifact subclass. Its copied `decide`
method changes only the raw answer lookup to the selected question ID, and
its question property supplies that ID on the wire. Do not rewrite responses,
fabricate answer aliases or transform one returned property into another.
Preserve the original budget reservations and commits, typed validation,
error handling, identity checks, default proxy-aware transport and no-retry
behavior. Each call still has one question, one POST and one budget reservation.

Before buying any response, freeze a source-normalization proof against the
original production method, original/helper identities and adapter bytes.
Normalization may reverse only the explicitly registered lookup change;
every other method statement must match. Verify that referenced helpers resolve
to the original implementations, and separately check the question-property
override. Reject any other unregistered code change.

Local wire/parser mocks must cover both genuine raw answer properties,
unchanged control payloads, missing or wrong properties, invalid choices,
identity mismatches, endpoint failures and one-reservation/one-commit accounting.
They must preserve raw response evidence and make no real model calls or
ledger changes. Freeze an immutable passing independent preflight and root
authorization before the actual writer starts. No production source or physics
changes are authorized by this diagnostic, so it requires no new live clock
gate. A local mock does not establish live arbitrary-key provider support;
the paid format controls test that support within the declared accounting.

## Analysis and strict interpretation limits

Report prescribed-format compliance separately from forecasting. For each
forecast name, report overall accuracy, safe/hazard and straight/curve confusion
counts, chosen physical outcomes, paired gains/losses and identical choices.
Preserve raw probabilities where returned, but describe them without treating
them as calibrated physical risks or evidence of an internal mechanism.

A switch from always-safe to always-hazard would show question-name sensitivity
while remaining 8/16 overall; it would not establish useful forecasting.
A null result limits this particular API-name hypothesis on these reused states,
not every possible question name or the model's general capacity. Comparing
new and historical identical control requests can describe stability but
does not create additional independent states.

There is **no qualification threshold under any outcome**. Even perfect
forecast accuracy here would concern a deliberately reused bank and could only
motivate separately frozen fresh validation. No result automatically triggers
native-command validation, a live race, qualification or promotion. One
presentation per arm/state gives no within-arm repeatability estimate. Keep
related same-course cases and paired arms distinct from independent driving
trials. Retain the joint `damped` baseline and application defaults.

## Admission and evidence contract

The completed 0029 boundary is **61,091 requests, $7.537810101999889 and
243,821,197 charged tokens**, with 69 historical uncertain requests and no
pending reservations. Preserve all historical charges and the shared
**75,000-request / $10 / 250-million-token** limits. Every call retains the
existing reservation of **16,384 input tokens plus 235,929 advertised output
tokens**. The [authorized session](2026-10-20-six-hour-session.md) admission
deadline remains **06:17:26 UTC**. No cap or reservation is relaxed to finish.

Use the pinned dated Jev model and TypeSafe provider, one paid writer and one
request in flight, zero retries and no fallback. The production source
fingerprint remains
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
Freeze the reused bank identity, actual question bodies, order, route, adapter,
normalization proof, helper hashes and current source before collection.
Record the actual writer identity and protocol hash in every call and completion
record, with exact credential-free bodies and raw response evidence.

Hard-budget and deadline stops admit no additional request. Preserve every
attempt, technical failure, charge and conditionally or technically unrun
entry. Final audit follows writer termination and verifies the reused fixture
identity and labels, exact question-name-only payload contrast, genuine raw
answer lookups, format-gate ordering, independent source-normalization proof,
route identity, writer attribution and every ledger transition. Do not rerun
older audits against a later ledger. Keep raw evidence under ignored
`artifacts/jev-question-key-v1/`. The unchanged
[exact prompt archive](0030-question-key-prompts.json) preserves the frozen
protocol and adapter evidence; the [results summary](0030-results-summary.json)
preserves actual format results, conditional unrun entries, audit, corrected
provenance and exact budget boundaries.


## Observed format results and registered stop

| Requested question key | Prescribed categories correct | Valid responses |
|---|---:|---:|
| `control` | 3/4 | 4/4 |
| `future_departure` | 4/4 | 4/4 |
| Total | **7/8** | **8/8** |

The first `control` format call was explicitly prescribed `leaves_road` but
selected `stays_on_road`. That sole wrong answer was valid typed data, not an
endpoint, identity or parser failure. The remaining valid format controls were
collected as registered. After the eighth call, the runner stopped before index
8; `format-stop.json` records `format_gate_failed` and all **32 conditionally
unrun forecasts**. No call was retried or replaced and the gate was not relaxed.

The genuine requested response head was available in every observed format
call, including all four `answers.future_departure` responses. The adapter kept
ordinary budget and identity validation without response-key aliases or fallback
rewriting. This establishes the declared adapter path for these eight calls;
it does not establish general arbitrary-key support or forecasting ability.

**No physical forecast was collected.** There is no forecast accuracy, confusion
comparison, gain, historical-control stability result or question-key forecast
effect. Unrun entries are not incorrect answers: zero observed forecast counters
are not a 0% score or a null-effect result. The 4/4 versus 3/4 format counts are
tiny prescribed-mapping observations, not an established key improvement, and
cannot explain the previous constant-safe forecasts.

The bank was intentionally reused from 0029 and could not qualify a prompt under
any outcome. The failed format prerequisite closed this round. No replication,
native validation, live race or promotion followed. Retain joint `damped` and
unchanged application defaults.

## Audit, adapter proof and corrected provenance

The final audit **passed with no errors or warnings**, correctly retaining
**`complete=false`, `format_gate_passed=false`, eight format responses and zero
forecast responses**. It verified the registered stop, all 32 unrun entries,
requested-key wire/response attribution, route, frozen helpers and sequential
accounting. Its offline checks of sixteen reused fixture labels and 480 future
steps validate prepared ground truth; they are not model forecast observations.

Before paid admission, source-normalization proof and independent review passed.
Reversing only the registered answer lookup recovered the exact production method
source and AST, with referenced helpers resolving to original objects. The free
preflight passed **67 local wire mocks**: forty planned payloads and twenty-seven
adapter compatibility/error cases, without real model calls or ledger changes.
Production source and physics remained unchanged.

Separate collection-provenance verification passed all **43 checks**, including
immutable preflight/authorization chronology, source identity, all eight actual
writer/requested-head/wire identities, the exact budget chain and the registered
format stop. The writer execution session was
`09c38c73915b4c6da67d6f1673f9f1a1`, with explicit collection enabled.

The initial provenance checker falsely failed two checks: its pair grouping
omitted physical option order, and it compared raw method-source hashes with a
manifest using dedented source. Correct grouping gives four exact question-key
pairs; canonical hashes match the frozen normalization manifest. The initial
JSON is preserved byte for byte and both results are retained in the summary.
Only the independent checker was corrected; no production source, paid record,
frozen helper, protocol or ledger changed. No paid discrepancy was established.

There were zero endpoint errors, technical failures or newly uncertain charges.
The phase used **eight requests, $0.0008887199999989548 and 21,505 charged tokens**.
Its saved audited end boundary is **61,099 requests, $7.538698821999888 and
243,842,702 charged tokens**, with 69 historical uncertain requests unchanged
and pending empty. Shared caps and conservative reservations remain unchanged.
This report uses saved evidence only; it does not rerun audits or inspect a
later ledger.

| Frozen or completed evidence | SHA-256 |
|---|---|
| Protocol | `dc32e7ee5072aed333ac97b48790473968897d24085d44001857ee3f43fc4ef4` |
| Exact prompt archive | `7a4db6689247126e2a4eb14abc2b92d12001f51cbe0e56080826de502cf9f8d9` |
| Final audit | `e78ad90a53b3310626716740aabaefa34423385701484ceaeabb304bafc6726c` |
| Audited report summary | `59aed4e6aeaaef82a430aee147d2f78bbdce05089a9c5890bcd70efa0574edbf` |
| Source-normalization proof | `ffd788653b8078c0a61f29075a07262b9fe1be47c34ddc85720fb4b782c983ab` |
| Corrected collection provenance | `ade8f45c545d88ff1aa48b0b42c7b7c02853352a07f9ae63e610cc2649b215ee` |
| Preserved initial provenance diagnostic | `7ada13029c34de99608cf501be426a6eafc376ac0fa239acf47ef327004f0d15` |

Source remains `1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
