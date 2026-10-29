# Repeatability of goal-only wheel-motion facts

The eight-race study is **closed**. All eight runs finished all 120 gates and
passed full audits. All four clockwise repeats were clean; all four recovery
repeats needed one rescue. Motion facts reduced no paired rescue counts and
were slower in all four pairs. The earlier large clockwise advantage did not
reproduce, so these data do not support adopting the motion bundle.

## New cohort results

| Entry | Block | Start | Facts | Time | Rescues | Grass | Replies ≥1 s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | recovery | wheel_motion | 95.12 s | 1 | 3.00 s | 2 |
| 1 | 1 | recovery | minimal | 89.23 s | 1 | 3.00 s | 0 |
| 2 | 1 | larger_errors | minimal | 79.75 s | 0 | 0.00 s | 0 |
| 3 | 1 | larger_errors | wheel_motion | 81.40 s | 0 | 0.00 s | 0 |
| 4 | 2 | recovery | minimal | 88.92 s | 1 | 3.00 s | 0 |
| 5 | 2 | recovery | wheel_motion | 92.65 s | 1 | 3.00 s | 0 |
| 6 | 2 | larger_errors | wheel_motion | 80.92 s | 0 | 0.00 s | 0 |
| 7 | 2 | larger_errors | minimal | 78.93 s | 0 | 0.00 s | 0 |

Motion minus minimal elapsed time: recovery +5.88 s and +3.73 s; clockwise
+1.65 s and +1.98 s. All runs were useful (within twice their frozen reference).
This is a small comparison of two repeated poses, not a broad reliability
trial or proof that motion facts are harmful. Choices and latency both vary.

## Initial recovery and latency

Neither arm credited a gate before rescue in either block. Minimal returned
to a forward-preview query at 0.97/0.98 s, before rescues at 6.55/6.68 s;
first gate credits came at 7.82/7.93 s. This demonstrates partial reorientation,
not successful unassisted recovery. Motion first obtained a forward query
after rescues at 8.32/7.25 s; first gate credits were at 13.42/11.22 s.

Only two of 2,684 replies were at least one second, both in the first motion
recovery run. The other three recovery failures had every reply below one
second (maxima 725, 959 and 633 ms). Long replies are therefore not necessary
for this failure. Median latency was 221 ms, p95 302 ms, p99 439 ms and max
1,250 ms. HTTP round trips do not distinguish network, queue and inference.

| Entry | Replies >500 ms | Total time beyond 500 ms |
| --- | --- | --- |
| 0 | 6 | 1.873 s |
| 1 | 2 | 0.390 s |
| 2 | 0 | 0.000 s |
| 3 | 2 | 0.121 s |
| 4 | 1 | 0.459 s |
| 5 | 3 | 0.218 s |
| 6 | 0 | 0.000 s |
| 7 | 3 | 0.358 s |

Exposure is the sum of max(round-trip − 500 ms, 0) over all replies; this
is a descriptive diagnostic, not a correction to finish times. No race was
excluded, retimed, replaced or rerun based on its outcome or latency.

## Combined context with 0073

The new cohort above stands on its own. Combining it descriptively with the
four pilot races yields three races per start/fact cell:

| Start | Facts | Clean | Median time | Total rescues |
| --- | --- | --- | --- | --- |
| recovery | minimal | 0/3 | 89.23 s | 3 |
| recovery | wheel_motion | 0/3 | 95.12 s | 3 |
| larger_errors | minimal | 2/3 | 79.75 s | 3 |
| larger_errors | wheel_motion | 3/3 | 81.40 s | 0 |

All 12 finished; five were clean. All six recovery races required one rescue.
The pilot clockwise minimal run was the sole assisted clockwise outcome and
also had 12 replies ≥1 s. That association does not establish latency causality.
The motion profile still cannot be credited with a repeatable advantage.

## Validation and spending

Production/controller/prompt/physics source remained unchanged throughout.
All 5,553 prior question sets reconstructed before collection. The unchanged
509-passed/three-optional-Rust-skip software checks, 34 native mocks and four
exact-interface free controls from 0073 were reused after hash verification.
The complete 0072 engine timing gate was reused and reverified on the same
core, boot and server; no new free timing run is claimed. Route identity,
prices and full reservation limits were freshly checked; replay catalog was
prewarmed while idle. See the [prospective registration](0074-goal-only-wheel-motion-repeats-registration.json).

Root launched one actual paid race per explicit process, observed exit zero,
confirmed it and fully audited before admitting the next. All 2,684 native
queries and 41,223 saved physics frames reconstructed exactly, including raw
facts, exact questions, response identities, controls, runtime/timing and
accounting. No request errors, invalid domain stops or new uncertainty.

Added **2,684 requests, 4,635,487 charged tokens and $0.183844542**. The final
ledger is **78,209 requests, 279,731,476 tokens and $9.051934310003073**,
pending empty and all 70 uncertainties retained. Caps remain **$10 / 100,000
requests / 500 million tokens**. The study closed early after its fixed eight
entries; no paid window or additional repeat is active.

## Artifacts and next proposed comparison

- [Actual race summary](0074-goal-only-wheel-motion-repeats-summary.json)
- [Repeat cohort and separate combined comparison](0074-goal-only-wheel-motion-repeats-comparison.json)
- [Recovery timelines](0074-goal-only-wheel-motion-repeats-analysis.json)
- [Actual requests and native responses](0074-goal-only-wheel-motion-repeats-responses.json)
- [Road-geometry proposal and constructed examples](0075-wheel-road-geometry-proposal.md)

The geometry proposal isolates heading relative to the road and left/right
edge clearances inside the wheel question, with motion disabled in both arms.
It contains a finite four-race design and three constructed requests, without
changing production code or claiming new model results. Future implementation
and free qualification must precede any paid use. The key endpoint is a first
gate before rescue; a forward preview alone does not count.

Raw evidence, frozen helpers, execution confirmations, audits and plot provenance
remain under ignored `artifacts/jev-goal-wheel-motion-repeats-v1/`. The visual
comparison is `wheel-motion-repeat-results.png`/`.svg`; its manifest binds all
12 source trials and outputs by hash.

## Original prospective design

The following design was fixed before the eight new outcomes. Its exact
original bytes are preserved as `prospective-design.md` in the artifact folder.

Prospectively registered after the user's “Do it” instruction, before any new
paid outcome. Eight new races repeat the exact two starts and two factual
profiles of 0073 twice. No production source, prompt, game or control change.

Fixed order: block 1 motion/recovery, minimal/recovery, minimal/clockwise,
motion/clockwise; block 2 minimal/recovery, motion/recovery, motion/clockwise,
minimal/clockwise. Seeds and poses are exactly 201 (−10 m/+124°) and clockwise
202 (+6 m/+35°). References 107.9833333333 s and 78.6500 s. Each arm has two
new races per start, yielding three per cell when combined descriptively with
0073. Analyze this repeat cohort separately before showing the combined counts.

Primary outcomes are paired rescue counts, clean finishes, first gate and first
forward-preview query before rescue. Also retain useful finishes, elapsed time,
grass, gate counts, all steering/pedal choices, input tokens and cost. Quantify
latency exposure with p50/p95/max, counts >=1 s and total time beyond 500 ms;
report whether off-road entry precedes or follows long replies. No exclusion,
retiming, latency correction or causal attribution from this small cohort.

Both arms retain goal-only rules, same pedal question, physical menus, native
inverse, empty shared state, original geometry and optional wheel motion group.
Python process/asyncio 60 Hz engine, 24 m stadium/mirror, max speed 12 m/s,
max wheel .12 rad, 3 laps/120 ordered finite gates, 3 s off-road rescue remain.
Pinned Jev version/TypeSafe route, one POST in flight, 5 s timeout, full
reservations, max 800 decisions and deadline 3x reference per race. No retries,
replacements, extra seeds/models, host driving, fallback or progress repair.

The $10/100,000-request/500-million-token cumulative caps and all 70 existing
uncertainties remain. No ledger mutation at registration. Retain admission
floors of 1,000 requests/5 million tokens/15 minutes. Paid window 90 minutes
from protocol freeze; technical/API/source/timing/accounting failure stops
later admission. Root launches one actual paid race per process, observes exit,
fully audits, then admits the next. Quality failures retain remaining entries.

The unchanged production controller reuses its 509-passed/3 optional Rust-skip
software checks, 34 native mocks, four exact-start timed free interface controls
and complete engine gate from 0073/0072. Reverify all frozen hashes, runtime,
boot and PID/start ticks and reconstruct all 5,553 prior saved question sets.
These are reused qualified controls, not fresh free runs or model evidence.
Recheck public route identity/prices/reserves and prewarm the idle replay catalog.
Freeze all current helpers and evidence references before paid collection.

Close after exactly these eight entries. A subsequent road-geometry comparison
must be separately registered, implemented and free-qualified after this study,
without retroactively changing these races or their controller source.
