# Goal-only challenge starts

The user authorized a frozen goal-only challenge after 0071. This protocol is
recorded before any new model outcomes. The shared request ceiling is unchanged:
the initial ledger is 73,554 requests, 271,730,425 charged tokens and
$8.734703564001506, with 70 uncertainties and no pending reservations.

## Fixed entries and free feasibility

The finite paid order, subject to qualification and budget admission, is:

| Entry | Group | Seed / course | Stationary start |
| --- | --- | --- | --- |
| 0 | Recovery | 201 / stadium | 10 m right of centre, nose 124 degrees left of road |
| 1 | Larger errors | 202 / clockwise | 6 m left of centre, nose 35 degrees left of road |
| 2 | Ordinary holdout | 205 / stadium | Original small seeded offset and heading |

Initial progress is zero and the first required gate remains gate 1. No gate
credit, velocity, steering, yaw or rescue state is injected. The recovery
preview is just behind the nose (negative ego x), so it exercises the formerly
rejected domain from the first model observation. Its first-gate challenge
may require additional travel; 120 ordered gates still define three credited laps.

Before paid registration, a free engineering screen tested a recovery start
at -4 m / +110 degrees. All three guides used a rescue, so that candidate is
preserved and excluded. A recorded amendment screened -10 m / +124 degrees
and -11 m / +127 degrees with a fixed guide order: original bearing/edge guide,
bearing-only with accelerate, then existing scripted reference, all at 200 ms.
The first no-rescue finisher was -10 m / +124 degrees with bearing-only:
107.98 s, 2.93 s grass, zero rescues. The other candidate also passed that
guide (107.68 s, 2.52 s grass). All failed and successful free rows are retained.
The larger-error and ordinary starts finished cleanly with the first guide
in 78.65 s and 78.13 s respectively. These free guides are never sent to Jev.

Run one new exact-start real-MCP free interface control per selected entry.
Recovery must finish without rescue and within twice its frozen static
reference time; grass is permitted and reported. Other entries must finish
cleanly within twice their reference. A technically valid but physically
unqualified free entry remains unrun, without a replacement. A technical,
clock or accounting failure halts collection.

## Frozen treatment and qualification

Use the unchanged 0071 goal-only prompt and question-local factual packet,
empty shared state, 15 native inputs, Jev version/provider, 5 s timeout,
one POST in flight, actual inference delays, no retries and no host driving.
Do not add action rules, recovery advice, examples, observations, smoothing
or control substitution. The public CLI and application defaults stay intact.

Python process/asyncio physics remains 60 Hz with the 24 m stadium/mirror,
12 m/s ceiling, 0.12 rad maximum wheel, 3 s off-road rescue and 40 finite gates
per lap. Only an optional explicit stationary starting pose is added to the
engine configuration. Default starts must remain exact; declared starts must
roundtrip through worker initialization and full factual/physics replay.
The prompt contains no new start-condition fields or driving instructions.

Because initialization source changes, run a COMPLETE fresh engine timing
gate on the restarted server: three controls, a parent-pause independence
check, 170.1 s neutral clock, HTTP spectator and exact replay. Bind new core,
controller and helper hashes, boot, server PID/start ticks and route metadata.
Recheck all 3,582 saved prior questions, including 0071. Run free native mocks
for all original controls and the previously stopped/passed-gate snapshots.
Reuse certainly-accounted Jev native API evidence; no paid native probes.
Software checks before timed collection: 496 tests passed, three optional
Rust skips, Ruff passed. Freeze all helpers and qualification evidence before
the exact-interface controls and paid outcomes.

## Outcomes and admission

Measure completion, 120-gate progress, useful finish (at most twice each
frozen free reference), clean finish (zero grass/rescues), elapsed time,
rescues, grass, actual queries outside each old guard, native/API errors,
latency, observation age, requests, tokens and cost. Distinguish a recovery
finish with grass from a clean one and from one helped by rescue. Record
whether the kart returned to the forward-preview domain and earned gates
after an initial extended-domain query; retain all failures.

Reference/race limits are 107.98/323.95 s, 78.65/235.95 s and 78.13/234.40 s,
respectively. The existing 800-decision quality cutoff remains. No artificial
delay is injected: a controlled-delay study is separate and unrun.

Root launches one actual paid race per explicit process, observes its exit,
and fully audits raw/native/identity/facts/questions/physics/clock/accounting
before another admission. No subagents, automatic paid loop or replacements.
Any API, native, source, timing or accounting failure halts later admission;
driving quality failures retain only the remaining fixed entries.

The window closes at 2026-10-21 17:10 UTC. Shared caps remain $10 / 75,000
requests / 500 million tokens. Retain 1,000-request / 5-million-token /
15-minute admission floors and full route reservations. Only 1,446 request
slots remain initially; later entries may therefore remain unrun. Do not
raise caps or shrink reservations. Preserve all 70 uncertain charges and
record every unrun entry with its reason and zero model requests.


## Results

Both admitted challenge races finished all 120 gates within their declared
useful-finish limits, but both needed rescue. Neither was clean. The ordinary
holdout remained unrun because only 779 requests remained, below the unchanged
1,000-request live-admission floor. No cap was raised and no entry was replaced.

| Group | Time | Gates | Rescues | Grass | Queries beyond old guards |
| --- | --- | --- | --- | --- | --- |
| Recovery: -10 m / +124 degrees | 93.40 s | 120/120 | 2 | 6.00 s | 29 |
| Larger errors: +6 m / +35 degrees | 85.58 s | 120/120 | 1 | 3.00 s | 0 |
| Ordinary holdout | Unrun: budget floor | — | — | — | — |

The earlier 0071 cohort remains four clean nominal starts. This challenge adds
**two assisted finishes and zero clean finishes**; do not pool them into a
claim of clean reliability. The recovery free controller itself used grass,
so its relevant feasibility standard was recovery without rescue. Jev did
not meet that standard. The larger-error free controller finished cleanly.

## What happened

The recovery attempt genuinely exercised the extension: 27 queries had a
nonforward preview, and two had a positive uncredited gate plane. At the
initial -90.3115-degree bearing Jev selected `hard_left_accelerate`, then
switched to `hard_right_accelerate` on the next query. It first left the road
at 4.02 s and was rescued at 7.02 s. Its first positive-x preview query was
7.08 s, after rescue; its first gate credit was 8.60 s. Thus this run provides
no evidence of unassisted recovery from the initial pose.

The same attempt later had a 1,792 ms reply at the 20.72 s snapshot while
`right_accelerate` was held. The next snapshot, at 22.53 s, showed a large
bearing change and lateral excursion. The second off-road spell led to a
rescue at 26.28 s. This sequence is consistent with stale controls contributing,
but it is not a controlled causal test of latency or an identification of
network versus inference/queue time.

The larger-error attempt crossed its first gate at 1.50 s without rescue and
stayed on-road until 10.67 s. It therefore made progress from the initial
error, then failed later. Rescue occurred at 13.67 s. Its 1,119 ms reply began
at 12.48 s, when already off-road, so that reply does not explain the initial
departure. A later 1,448 ms reply at 42.82 s was followed by continued driving
without another rescue. Latency alone is not an established explanation.

Across 667 replies, API p50 was 223.96 ms, p95 305.30 ms, maximum 1,792.41 ms;
three replies took at least one second. There were zero native/API errors.
The model selected some brake and coast inputs in these challenges, but the
outcomes do not establish successful braking or recovery strategy.

## What this establishes

The fairer goal-only setup remains playable in the game with its rescue rule.
This challenge has not strengthened the case for robust driving without rescue.
It has identified a useful boundary beyond the four earlier clean nominal
starts. A clean free-controller result establishes physical feasibility,
not a prediction of Jev's success.

The comparison does not isolate the causal effect of removing supplied rules:
there is no new matched supplied-policy arm, and the starts and stochastic
latency trajectories differ from the earlier nominal cohort. Keep the goal-only
baseline and preserve these failures.

One concrete next question is whether the model lacks useful physical state.
The frozen wheel question contains preview geometry and the next gate's signed
plane, but no current speed, actual steering angle, yaw rate or held control.
The pedal question has speed, clearances and lateral velocity, but no preview
geometry. An authorized future ablation could add those factual measurements
locally, without steering thresholds, suggested actions or recovery advice.
No prompt was edited and no follow-up model experiment was launched here.

## Validation and accounting

All raw/native/route/factual/question/physics/timing/accounting audits passed,
after the root observed each actual process exit and before another admission.
All 3,582 prior question sets remained exact, including 1,753 goal queries
with the extension enabled. Seventeen mocked native calls passed. The code
passed 496 tests, with three optional Rust skips, and Ruff.

A complete fresh engine clock gate passed on the new initialization source
and restarted server, including three controls, 21 physics samples during a
parent pause, the 170.1 s neutral run, HTTP spectator and 20,419 exact replayed
frames. Its source fingerprint is
`793bf26aa6b9257d0eab60f726c2578cbd74a5276aef70e8a2addfa233029253`.
The server binding is PID 10684 / start ticks 10192901 on boot
`4b247f0d-313e-4038-ac10-acff9274db8e`.

All three selected real-MCP free interface runs qualified: recovery 108.12 s,
2.93 s grass, zero rescues; larger errors 78.73 s clean; ordinary 78.35 s clean.
These are free-controller outcomes, not model races. Failed engineering
candidates and every free result remain preserved. The selected references
were frozen before model outcomes. The rescue-assisted recovery time being
shorter than its free reference does not establish better unassisted driving.

Added 667 requests, 1,113,244 charged tokens and $0.044061654. No new uncertainty;
all 70 prior uncertain charges remain, pending empty. The shared ledger is
74,221 requests / 272,843,669 charged tokens / $8.778765218001775. Caps stay
$10 / 75,000 requests / 500 million tokens. This finite study is closed.
New paid admission cannot meet the retained 1,000-request floor under that cap.

## Saved evidence

- [Portable summary](0072-goal-only-challenge-summary.json)
- [Thirteen exact prompt/response excerpts](0072-goal-only-challenge-prompts.json)
- [Trajectory and latency visual](../../artifacts/jev-goal-challenge-v1/challenge-results.png)
- [Vector visual](../../artifacts/jev-goal-challenge-v1/challenge-results.svg)

The visual uses recorded positions and API round trips. Rescue teleport
segments are omitted and their endpoints are marked. No new simulation or
model call was used to render it. Complete trials, free engineering failures,
raw wire bodies, clock evidence, ledger chains and diagnosis remain under
ignored `artifacts/jev-goal-challenge-v1/`. Reports and curated excerpts are
versioned. The original prospective design is preserved there with its hash.
