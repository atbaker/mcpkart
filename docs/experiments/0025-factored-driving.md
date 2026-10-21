# Joint and factored decisions on the 24 m stadium

Status: completed with amended recording validation and the provenance
limitations below. Factored decisions improved seed 11 and worsened seed 12,
so the paired screen failed. No holdouts or preset promotion followed.
The current-source Python clock gate and exact 24 m seed-11 free control passed
before paid racing. The original prospective design is retained below.

The [command-semantics screen](0024-factored-commands.md) completed all 96 calls:
both layouts followed 48/48 prescribed commands, and the factored compatibility
gate passed. This establishes the entry requirement for this driving comparison;
it has not established a driving improvement.

## Fixed comparison

Retain the 24 m stadium, three laps through 120 ordered gates, 12 m/s ceiling,
0.12 rad maximum wheel angle, process-isolated Python with asyncio pacing,
`road_navigation` telemetry, geometry descriptions and the unchanged `damped`
guide. Both layouts offer the same fifteen direct native commands:

- Joint selects one complete wheel-and-pedal command in one question.
- Factored selects a wheel and pedal in two questions within one POST. Both
  valid components map atomically to the corresponding native command.

The interface package changes question structure, menu descriptions and
component-specific scopes together. It is not a test of factor count alone.
No prescribed command is supplied during a race. The model chooses every input;
the host provides no steering target, line follower or automatic control choice.
Physics continues while inference is pending and the previous input remains held.

Run four paid races in this fixed paired order:

| Starting pose | Order | Matched scripted reference |
|---|---|---:|
| Seed 11 | Joint, then factored | 77.2833 s |
| Seed 12 | Factored, then joint | 77.2167 s |

Use the same seed setup within each pair. Freeze the exact references, source
fingerprint, helper hashes, question text, handling, race deadlines and validation
limits before the first paid race. Independent review covers route
identity, provenance, exact replay and retention of error attempts.

## Entry, admission and verification

Before paid admission, require the completed command-semantics gate, a passing
full Python clock qualification on the current source, and a successful exact
24 m seed-11 free control. Preserve the shared **75,000-request / $10 /
250,000,000-token** limits and all historical charges. Before each race, require
at least **1,000 remaining request slots** and **5,000,000 remaining charged-token
slots**, as well as ordinary per-request budget admission and session time.
Insufficient headroom leaves a race unrun; it does not reset or raise a limit.

Pin the same Jev model/provider and retain one request in flight, zero client
retries and no provider fallback. Stop the comparison at the first endpoint or
identity failure, retain the affected attempt and charge, and leave subsequent
races unrun. Invalid factored components never become a partial native input.
Do not silently rerun or replace a failed paid attempt.

Save request/component responses, applied native commands, observations, timing,
rescues and ledger boundaries. Validate every race against the same timing
limits and exact command replay. Keep heavy analysis, installations, builds and
plots outside timed windows. Report finishes, race time, reference ratio,
rescues and grass time separately; a parked rescue-free attempt is not a finish.

## Screen decision and bounded continuation

Useful pace means a completed race within **twice its matched scripted reference**.
The candidate must finish both starts at useful pace, with no endpoint, timing
or replay impairment. Its rescue count must be no worse than joint on either
seed and strictly better on at least one. Two paired starts provide a screen,
not an estimate of reliable driving across tracks or racers. No preset promotion
is automatic.

Only if both candidate starts satisfy the frozen clean-finish rule and the paired
improvement criterion may two candidate holdouts, seeds 13 and 14, be considered.
A clean finish requires all 120 gates, zero rescues and zero grass time, useful
pace, valid timing and exact replay, with no endpoint or accounting impairment.
Report both rescue and grass measures, and freeze any holdout protocol separately
before collecting them.
The same budget headroom and session deadline must still permit admission.
Otherwise conclude this four-race screen without additional holdout calls.

The authorized session admission deadline remains **06:17:26 UTC**; do not start
a new race with fewer than fifteen minutes remaining. The completed results and frozen qualification/source evidence follow below.

## Verification correction before continuation

The first joint race finished all 120 gates in 102.2 seconds, with two rescues
and six seconds of grass. The phase then stopped because the new verifier's
reconstructed observation omitted the factual top-level `finished` field added
by `RaceRuntime.observe`. No later race started. Both newly added verifiers
shared this omission; their original failure reports remain preserved.

Two separate diagnostics reconstruct all 6,133 physics samples and 392 submitted
observations. Deriving `finished` from the replayed simulation makes every
observation exact, without ignoring any field. All 389 applied native commands,
timing, endpoint identity and accounting checks also pass. This is a validation
correction, with no change to source, physics, model questions or paid inputs.
The first race remains in the comparison. A separately frozen amendment must
certify that attempt before continuing only the three unrun entries; it must
preserve the original stop, verifier files, protocol and result metadata.

The [validation amendment](0025-validation-amendment.json) was frozen at
01:03:38 UTC. The separately retained wrapper preflight passed six negative
certificate cases without model calls or ledger changes. It permits only
indices 1–3 and binds admissions and results to the amendment. The correction
adapts the expected-observation formatter inside offline replay; production
telemetry and decision payloads retain their original functions and contents.
The original failed audit, stop and first result's `continue=false` remain
historical evidence; the amended audit explicitly certifies the known omission.

There is a material execution-provenance gap. An accidental `--preflight`
invocation after collection overwrote the retained independent amended-preflight
output. That output fails the temporal check, “Amended preflight did not precede
the three unrun paid entries.” It cannot establish a prospective independent
amended-preflight pass; the wrapper's six-case check is distinct evidence.
Available visible tool history also does not establish who executed the three
remaining races. The saved recovery-context diagnostic records both limitations.
The final amended audit verifies the actual frozen recordings, physics and
accounting; it does not recover that missing prospective execution provenance.

## Completed paired results

All four races finished the 120 ordered gates within twice the matched
reference, with valid timing, exact amended replay and zero endpoint errors.
All four retained attempts form one continuous audited ledger chain, with no
duplicate race attempts or newly uncertain charges.

| Seed | Layout | Time | Reference ratio | Rescues | Grass time | Requests |
|---|---|---:|---:|---:|---:|---:|
| 11 | Joint | 102.2000 s | 1.3224× | 2 | 6.0000 s | 392 |
| 11 | Factored | 87.5333 s | 1.1326× | 1 | 3.0000 s | 336 |
| 12 | Factored | 120.6167 s | 1.5621× | 2 | 6.5833 s | 460 |
| 12 | Joint | 81.6167 s | 1.0570× | 1 | 3.0000 s | 311 |

Factored was 14.6667 seconds faster with one fewer rescue on seed 11, but
39.0000 seconds slower with one more rescue on seed 12. It fails the frozen
requirement of no worse rescues on both seeds. Neither candidate attempt was
rescue-free or grass-free, so the clean-finish holdout gate also failed.
No seeds 13/14 were collected and no preset was promoted.

Median request latency was 232.73 ms for joint (703 calls) and 235.46 ms for
factored (796 calls). These response counts are not independent driving trials.
Two paired initial poses cannot establish reliable improvement across tracks,
starts or racers. The changed request structure and component-specific scopes
also prevent attributing an effect to factor count alone.

The final amended audit passed with no errors or warnings. It accounts for
**1,499 requests, $0.186641280 and 4,636,819 charged tokens**, with zero new
uncertain charges. The fixed end boundary is **60,723 requests,
$7.497665116 and 242,850,694 charged tokens**, with 69 historical uncertain
requests unchanged and no pending reservations. All existing caps were retained.

## Frozen evidence and reporting boundary

The [machine-readable results](0025-results-summary.json) preserve the completed
audit, per-race replay/timing details, frozen protocol and amendment, budget
boundaries, paired outcomes, and recovery-context qualification. The exact
[prompt archive](0025-factored-prompts.json) remains unchanged. This report uses
saved completed evidence only; it does not rerun audits or inspect an advanced
ledger.

| Artifact | SHA-256 |
|---|---|
| Original frozen protocol | `996c1741e841189d75cbb1f0a428354034865095f5b88529591f1843a9c12e91` |
| Frozen validation amendment | `ba50d1def0a4d577aadb4230b7178b619e33813ec578b6f30ef21c4965a2bebf` |
| Versioned prompt archive | `d052add990b45361ac6c4e21467b40fb7f81ab2f589a01226511aa14c61ba2c0` |
| Final amended recording audit | `a56259e060e423e21dddd01e6e88abb11cc737d05341277669eb4e0deb06d8de` |
| Recovery-context diagnostic | `3b76b3c22f4b6e629ba911544ed948b4e968ecfb478bda28eeb9d021afdf0fd5` |

The frozen production source fingerprint is
`1f2670f72c1c9c12ef77db117f55453f1b6067b8c8a7e94b197379c209f88feb`.
The protocol's prerequisite evidence and original helper hashes, plus the
amendment's correction-helper hashes, are retained verbatim in the results
summary. Final recording validity and incomplete prospective execution
provenance are reported separately.
