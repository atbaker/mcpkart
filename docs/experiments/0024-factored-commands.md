# Factored wheel and pedal commands

Status: complete and independently audited. This is a command-semantics and provider
compatibility screen in the authorized six-hour session. It follows the
[division-free comparison](0023-division-free-rule.md) as a distinct decision
interface hypothesis. It does not measure driving performance or formula execution.

## Frozen comparison

Compare the same fifteen direct native inputs in two request layouts:

- **Joint:** one question chooses a complete wheel-and-pedal combination from
  fifteen geometry descriptions.
- **Factored:** one request contains a five-choice wheel question and a
  three-choice pedal question. Both valid answers decode bijectively to one
  existing native input. Missing or invalid components reject the whole input.

Each layout uses one POST and one budget reservation. Splitting the questions
adds component-specific instructions and repeats the guide across questions;
this package does not isolate menu size from instruction or context effects.
The host only maps the selected components to the existing native command.
It does not choose steering, pedals or a target trajectory.

Every question quotes the unchanged `damped` guide and supplies the same full
observation, then explicitly requires an absolute wheel angle and pedal that
override driving advice and state. Success means following that prescribed
command. During this screen no command is applied and no physics advances.
The retained fixture formula fields are unused; scoring uses `command_spec`,
physical quantities and the native command mapping.

Use 24 fresh synthetic snapshots in twelve mirrored pairs, twelve on straights
and twelve on curves. Python, the 24 m stadium, 12 m/s ceiling, 0.12 rad wheel
limit and 8 m/s fixture speed remain fixed. Prescribed commands are assigned
independently of the fixture formula: eight cases per wheel magnitude and eight
per pedal. All fifteen native combinations occur, with unequal counts. Mirror
pairs reverse the prescribed nonzero wheel and retain the pedal.

Twenty-four cases × two layouts × two repetitions produce **96 planned calls**,
48 per layout. Shuffle with seed 2026102024, alternate the first layout, then
reverse cases and swap layout order for repetition two. The first logged request
is factored and serves as the provider compatibility check within the planned
batch. No separate paid probe is omitted from accounting. Stop on the first
endpoint/identity failure or uncertain accounting, retaining the attempted
request and all unrun entries. Responses, repeated cases and mirrored fixtures
are correlated; the two components within a request are also not independent.

## Qualification and verification

The factored layout must satisfy all of these frozen conditions:

- Wheel correct on at least **46/48** responses.
- Pedal correct on at least **46/48** responses.
- Every one of the **15 native combinations** returned wholly correctly at least once.
- Complete collection, **zero endpoint errors**, and a passing independent audit.

Report wheel, pedal and whole-command agreement separately, paired layout
changes, per-command coverage, presentation stability, latency and aggregate
usage. Passing only qualifies the next checks: a fresh full Python clock gate,
a free 24 m control and a separately frozen paired joint/factored driving screen.
No pursuit-math gate or automatic live promotion applies.

The new collection source fingerprint is
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
The protocol and ten helper hashes are frozen. The local mock passed 96 planned
wire bodies plus one deliberate error, using zero model calls and leaving the
shared ledger unchanged. It checks atomic component decoding and one request/
commit per decision. Independent preflight passed all 24 command labels and
reconstructed observations, mirror checks and all 96 exact payloads. The mock
does not establish live provider support; the first logged factored response
will test that support.

Pin `typesafe/jev-1.14`, resolved to `typesafe/jev-1.14-20261014` at `TypeSafe`,
with freshly checked unchanged prices, one request in flight, no client retries
and no provider fallback. Preserve the shared **75,000 requests / $10 /
250,000,000 tokens** limits. Starting ledger: **59,128 requests / $7.298194180 /
237,895,863 charged tokens**, 69 historical uncertain requests and no pending
reservations. Each request conservatively reserves 16,384 input tokens plus the
advertised output ceiling. The session admission deadline remains **06:17:26 UTC**.

Exact prompt source, guide, component suffixes, menus, native mapping, fixture
metadata and freeze manifest are in the
[prompt archive](0024-factored-prompts.json). Ignored recordings will remain under
`artifacts/jev-factored-commands-v1/`.

## Results and qualification

All **96 planned requests** completed with the pinned dated Jev model and
TypeSafe provider, no endpoint errors, no retries or replacements, no unrun
entries and no new uncertain charges. The first logged factored request
succeeded, and all 48 factored responses supplied valid wheel and pedal answers
in one response. The provider supports this two-question request form in the
observed setup.

| Layout | Wheel correct | Pedal correct | Whole command correct |
|---|---:|---:|---:|
| Joint | 48/48 | 48/48 | 48/48 |
| Factored | 48/48 | 48/48 | 48/48 |

All fifteen native combinations were returned wholly correctly in the factored
layout, satisfying the frozen coverage requirement. The two layouts return the
same correct native command in all 48 matched pairs. Both repetitions are
correct and choose the same native command on all 24 cases in each layout.
The independent final audit passes, and **the command-semantics gate passes**.

These results qualify the fresh Python clock gate, free 24 m control and a
separately frozen joint/factored race comparison. They measure following an
explicit command and accepting the response format; neither layout has
demonstrated a driving improvement in this screen. The host did not apply any
control, advance physics or supply an optimal driving action. No live preset
is promoted by these results.

## Observed latency and usage

| Layout | Median request latency | Tokens projected for 400 static requests | Cost projected for 400 static requests |
|---|---:|---:|---:|
| Joint | 236.54 ms | 1.289 million | $0.05134 |
| Factored | 241.30 ms | 1.361 million | $0.05557 |

Each request has reported aggregate usage. These projections multiply the
observed static request sizes and charges; they do not predict race decision
counts, changing live telemetry sizes, latency tails or driving capability.
The factored layout still uses one POST and one budget reservation per decision.
No component marginal probabilities are multiplied into a joint confidence.

## Completed audit and spending boundary

The final audit verified 24 independent command labels and reconstructed
observations, all 96 exact request bodies, layout question and menu contracts,
atomic component mapping, model identity and every ledger transition. The
[results summary](0024-results-summary.json) preserves the completed audit,
frozen protocol/helper hashes, groups, coverage decision, paired results and
usage projections. Its collection source fingerprint is
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.

The screen used **96 calls / $0.012829656 / 318,012 charged tokens**. Its ending
shared ledger was **59,224/75,000 requests**, **$7.311023836/$10**, and
**238,213,875/250,000,000 charged tokens**, with 69 historical uncertain requests
and no pending reservations. These are the saved completed boundaries; later
work may advance the [current shared snapshot](model-budget-snapshot.json).
The results were finalized from saved evidence without rerunning an audit or
substituting a later source or ledger state.
