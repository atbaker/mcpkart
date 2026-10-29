# Experiment index

Start with the [two-kart checkpoint](2026-10-22-two-kart-checkpoint.md).
The [earlier findings checkpoint](2026-10-21-progress-checkpoint.md)
and [policy-driver prompt/response examples](current-driver-examples.json) cover through 0069. For
running the working drivers, use the [two-kart guide](../two-kart-driver.md)
or the [solo guide](../question-context-driver.md).

## Current evidence

Latest: [0085 timing in both questions](0085-both-head-timing.md) is closed
with all 22 actual episodes. Baseline/timing scored 2/4 versus 0/4 on the
original delayed state, 0/2 each on blue, 2/2 versus 1/2 on red, and 3/3 each
at ordinary latency. No improvement; keep defaults off. Motion/geometry stayed
off; no physics, rules, menus or UI changes. [Figure](figures/0085-both-head-timing-results.svg),
[results](0085-both-head-timing-results.json), [actual native examples](0085-both-head-timing-native-excerpts.json).
810 tests/3 optional Rust skips, Ruff, 19,422 prior questions exact; fresh complete
clock,12 free interfaces and all 7,198 frames/347 native replies/694 transitions
passed. Added $0.03861; ledger 99,403 requests/$11.520516764002778/333,848,829 tokens,
71 uncertainties retained, pending empty. Caps $20/110k/500m unchanged; all paid
windows closed. Both original baseline successes first braked and contacted;
all four timing attempts first accelerated. This is descriptive, not causal.

Earlier: [0084 motion-only validation](0084-motion-validation.md) is closed after
22 actual episodes. Baseline and motion tied: original delayed 1/4 each, blue
holdout 0/2 each, red holdout 2/2 each, normal 3/3 each. The earlier motion
advantage did not repeat; defaults stay off. Both original delayed successes
first braked and had contact; identical pedal questions still yielded different
answers. No application source changed.
[Figure](figures/0084-motion-validation-results.svg),
[all outcomes](0084-motion-validation-results.json),
[actual native examples](0084-motion-validation-native-excerpts.json).
341 valid replies / 7,351 frames / 682 budget transitions passed root audits;
added $0.03808. Ledger: 99,056 requests / $11.481907970002775 / 332,896,219 charged
tokens; caps $20 / 110k / 500m, 71 uncertainties retained, pending empty. All paid
windows are closed. The complete 0083 clock was revalidated and reused, not
rerun; twelve new free interfaces passed with no real calls.

Earlier: [0083 factual wheel motion/timing](0083-wheel-observability.md) is
closed after 28 actual episodes. Delayed post-contact: baseline 0/2, motion 2/2,
timing 1/2, both 1/2; severe drift 0/16, all four normal checks passed. All four
new delayed recoveries included contact and a first brake reply; joint-profile
performance does not isolate a steering mechanism. Defaults off; motion-only
needs matched holdouts. [Figure](figures/0083-wheel-observability-results.svg),
[outcomes](0083-wheel-observability-results.json), [native examples](0083-wheel-observability-native-excerpts.json).
740 tests / 3 optional Rust skips, 18,543 prior questions byte-exact, all native/physics/
clock/budget audits passed. 538 valid replies added $0.06123; current ledger 98,715 calls,
$11.443828922002771 / $20, 331,956,791 / 500m tokens, 71 uncertainties, pending empty;
request cap 110k unchanged. All paid windows closed.

Earlier: [0082 harder recovery and one-second delay](0082-harder-recovery.md)
is closed after all 16 actual episodes:4 unassisted successes / 12 target rescues.
Both profiles recovered the post-contact state 2/2 at normal latency, 0/2 with
an added second; severe drift 0/2 for both at either delay. Legal free 200/1200 ms
witnesses were replayed; no host policy entered the paid path. No geometry
success-rate advantage. [Figure](figures/0082-harder-recovery-results.svg),
[all outcomes](0082-harder-recovery-results.json), [actual native excerpts](0082-harder-recovery-native-excerpts.json).
321 valid native replies added $0.03580; ledger 98,177 requests / $11.382596324002778,
330,447,089 tokens, 71 uncertainties, pending empty. User explicitly raised request
ceiling 100k→110k; $20 / 500-million-token caps unchanged. All paid windows closed.

Earlier: [0081 repeatable recovery and added-delay benchmark](0081-recovery-benchmark.md)
completed 12/12 selected checkpoint episodes without rescue, with 503 valid
native replies. Both baseline and gate geometry passed. The two-repeats/cell
misalignment comparison showed a smaller delay penalty with geometry, but no
success-rate advantage; keep the default unchanged. The two missed-gate
recoveries drove a circuit in 29.02 / 28.25 s. [Visual results](figures/0081-recovery-results.svg),
[paths](figures/0081-missed-gate-paths.svg), [all outcomes](0081-recovery-benchmark-results.json)
and [actual native examples](0081-recovery-native-excerpts.json).
Added $0.05594; current ledger: 97,856 requests / $11.346796826002786,
329,563,859 charged tokens, 71 uncertainties, pending empty. All paid windows closed.

Earlier: [0080 fresh baseline after overload](0080-jev-overload-retry.md)
completed both karts with 575 valid HTTP 200 replies and no new uncertainty.
Finishes 97.47 / 110.25 s used two/three rescues. API p95 886 / 809 ms, max 3.72 s
was much slower than 0079 geometry, so prompt benefit remains unproven.
Added $0.06206; current ledger: 97,353 requests / $11.290856144002776,
328,183,549 charged tokens, 71 uncertainties, pending empty. All paid windows closed.

Earlier: [0079 factual next-gate geometry](0079-factual-next-gate-geometry.md)
is closed. Geometry finished 4/4 clean; the one complete baseline duel had
one clean/one rescued finish. The other baseline duel stopped on provider HTTP 529,
with both unfinished attempts infrastructure-censored and no replacement.
Sharp-start first gate 3.57 s baseline / 3.52 s geometry; no post-miss recovery
exposure. Benefit remains unproven; defaults unchanged. [Visual](figures/0079-gate-geometry-results.svg).
Added 2,180 requests / $0.24545. Current ledger: 96,778 requests /
$11.228800136002755, 326,650,735 charged tokens, 71 uncertainties, pending empty;
caps unchanged.

Earlier: [0078 nearby-grid Jev/Jev validation](0078-two-kart-nearby-grids.md)
finished 24/24 kart attempts, 15 clean, with 29 contacts and 17 lead changes.
Across all three two-kart cohorts, 48/48 finished and 30 were clean. The game,
goal-only prompt and controller stayed frozen throughout actual collection.
[0077](0077-two-kart-jev-openai.md) paired both model assignments on four grids:
Jev won 8/8 (7 clean), OpenAI 1/8 clean. [0076](0076-two-kart-jev-jev.md)
established the first four Jev/Jev duels (8 finishes, 7 clean).
[Outcomes](0076-0078-two-kart-outcomes.json) and
[actual native examples](0076-0078-two-kart-native-excerpts.json) retain successes
and failures. At the 0078 closure, cumulative caps were $20 / 100,000 requests /
500 million tokens; charged $10.983352472002839, 94,598 requests, 70 uncertainties.

Earlier: [0075 wheel-local road geometry](0075-goal-only-wheel-road-geometry.md)
finished all four recovery races with assistance. Neither arm earned a first
gate before rescue (0/2 each). Geometry needed two/one rescues versus minimal's
one/one. No demonstrated improvement; all audits passed and the study is closed.
The option adds factual heading/edges, no action rules. Caps remain unchanged.

Earlier: [0074 wheel-motion repeatability](0074-goal-only-wheel-motion-repeats.md)
finished all eight races: four clockwise clean, four recovery assisted once.
Motion reduced no paired rescues and was slower in all four pairs, so the
[0073 pilot](0073-goal-only-wheel-motion.md) advantage did not reproduce.
Minimal recovery regained forward preview before rescue but earned no gate.
All audits passed; closed. Caps remain $10/100,000 requests/500 million tokens.
The original [geometry design](0075-wheel-road-geometry-proposal.md) and its
constructed examples are preserved separately from the later 0075 results.

Earlier: [0072 goal-only challenges](0072-goal-only-challenge.md) finished both
admitted harder starts with rescue (two and one respectively), zero clean.
The recovery case made 29 extended-domain queries but first returned to the
forward-preview domain after rescue. The ordinary holdout remained unrun at
the budget floor. These results identify a robustness limit.

The preceding [0071 goal-only follow-up](0071-goal-only-recovery-domain.md) finished
4/4 starts cleanly in 79.52–81.63 seconds after relaxing inherited pose-domain
stops. No actual query entered the extended domain; recovery remains untested.
Median API reply was 226 ms; one took 1.38 seconds. The prior
[0070 pilot](0070-question-local-policy-ablation.md) retains goal-only 1/2 clean
and policy 2/2 clean, including the on-road domain stop after a 2.197-second
reply. These are separate small cohorts.


| Result | Evidence |
| --- | --- |
| Two-kart goal-only: Jev 40/40 finishes, 29 clean across declared grids/opponents | 0076–0078 |
| Paired two-kart comparison: Jev wins 8/8; OpenAI 8/8 finishes, 1 clean | 0077 |
| Jev goal-only: 4/4 clean nominal follow-up; no extended-domain queries | 0071 |
| Jev goal-only challenge: 2/2 assisted finishes, 0 clean; ordinary holdout unrun | 0072 |
| Jev 15 m policy driver before0070: 14/14 useful, 13/14 clean | 0052, 0053, 0054, 0068 |
| OpenAI: 2/2 clean starts with the unchanged Jev-developed setup | 0068 |
| Clef: two driving failures; post-top-up retry ended on request timeout | 0068, 0069 |
| 22 m package: free/static gates passed; actual 500 ms Jev driving unrun | 0063, 0065, 0066, 0067 |

Counts from different static banks are not a pooled learning curve. Read each
report's frozen design, failed gates and limitations. Free scripted controls
are feasibility evidence, not model performance. Live results cover the solo
stadium and mirror; 0072 adds two larger pose challenges. Arbitrary tracks remain untested.

The latest [budget snapshot](model-budget-snapshot.json) preserves all charges,
including the 0069 uncertainty. Raw recordings and complete execution evidence
remain in ignored `artifacts/`; prompt archives and summaries are versioned.

## Session reviews

- [Eight-hour review and pause](2026-10-19-eight-hour-review.md)
- [Six-hour continuation log](2026-10-19-six-hour-continuation.md)
- [Renewed six-hour review](2026-10-20-renewed-six-hour-review.md)

## Individual studies

### Runtime and initial driving

| Study | Report |
| --- | --- |
| 0001 | [First experiment: realtime driving through MCP](0001-realtime-driving.md) |
| 0002 | [Track telemetry iteration](0002-track-telemetry.md) |
| 0003 | [Jev navigation: compact observations and control language](0003-jev-navigation.md) |
| 0004 | [Jev: gate geometry and short observation history](0004-gates-and-observation-history.md) |
| 0005 | [Isolate the physics clock, then repeat Jev](0005-isolated-physics-clock.md) |
| 0006 | [Linux Docker timing controls](0006-linux-docker-clock.md) |
| 0007 | [Rust race-engine experiment](0007-rust-race-engine.md) |
| 0008 | [Remote Linux timing comparison](0008-remote-linux-clock.md) |
| 0009 | [Python race engine on GCP](0009-python-on-gcp.md) |

### Cloud setup, track design and broad prompt trials

| Study | Report |
| --- | --- |
| 0010 | [Jev navigation in rebuilt Codex Cloud](0010-jev-on-codex-cloud.md) |
| 0011 | [Jev speed classes, simpler courses and visual observations](0011-jev-speed-classes.md) |
| 0012 | [Jev prompt comparisons on fixed courses](0012-jev-prompting.md) |
| 0013 | [Stadium width comparison](0013-stadium-width.md) |
| 0014 | [Prompt experiments on the approved 24 m stadium](0014-stadium-prompts.md) |
| 0015 | [Further prompt iterations on the 24 m stadium](0015-prompt-iterations.md) |

### Control semantics, arithmetic and forecasting diagnostics

| Study | Report |
| --- | --- |
| 0016 | [Jev factual skills and supplied-policy execution](0016-jev-factual-skills.md) |
| 0017 | [Current wheels versus the calculated target](0017-held-wheel-target.md) |
| 0018 | [Reading preview coordinates and executing the calculation](0018-coordinate-calculation.md) |
| 0019 | [Literal numbers and explicit products](0019-literal-expressions.md) |
| 0020 | [Six worked examples for the steering calculation](0020-worked-examples.md) |
| 0021 | [Answer IDs and descriptions](0021-answer-menu.md) |
| 0022 | [Observation context and answer menu](0022-observation-context.md) |
| 0023 | [A division-free equivalent steering rule](0023-division-free-rule.md) |
| 0024 | [Factored wheel and pedal commands](0024-factored-commands.md) |
| 0025 | [Joint and factored decisions on the 24 m stadium](0025-factored-driving.md) |
| 0026 | [Predicting the consequence of a held input](0026-motion-forecast.md) |
| 0027 | [Forecast context and binary answer labels](0027-risk-context.md) |
| 0028 | [Current road-frame motion and present surface labels](0028-road-motion.md) |
| 0029 | [A physics scaffold on naturally reached states](0029-natural-forecast.md) |
| 0030 | [Forecasting under a different API question name](0030-question-key.md) |

### Explicit policies and factual representation

| Study | Report |
| --- | --- |
| 0031 | [Placing fixed-policy clauses beside their criteria](0031-criterion-policy.md) |
| 0032 | [A fixed bearing policy with factual angle telemetry](0032-bearing-policy.md) |
| 0033 | [Transferring the bearing policy to a driving question](0033-native-policy-bridge.md) |
| 0034 | [Applying the bearing policy from a smaller factual state](0034-policy-facts.md) |
| 0035 | [Broader native validation of the factual bearing policy](0035-broader-native-validation.md) |
| 0036 | [Checking the straight-wheel deadband first](0036-deadband-first.md) |
| 0037 | [Placing only eligibility conditions in the criteria](0037-condition-only.md) |
| 0038 | [Expanding criterion aliases into literal factual references](0038-literal-conditions.md) |
| 0039 | [Expressing fixed eligibility in plain language](0039-plain-conditions.md) |
| 0040 | [Separating wheel-question and factual-context effects](0040-wheel-isolation.md) |
| 0041 | [Replicating the wheel factual-mask diagnostic on broader states](0041-wheel-mask-replication.md) |
| 0042 | [Repeated small-bearing wheel choices under two factual views](0042-small-bearing-repeat.md) |
| 0043 | [Complete wheel/pedal decisions with component-specific definitions](0043-component-definitions.md) |
| 0044 | [Complete native choices with named wheel and pedal fact groups](0044-component-fact-groups.md) |
| 0045 | [Fixed worked examples for complete grouped native decisions](0045-component-worked-examples.md) |
| 0046 | [Absolute bearing facts and magnitude-first wheel conditions](0046-absolute-bearing.md) |
| 0047 | [Wheel control descriptions and the meaning of straight](0047-wheel-command-semantics.md) |
| 0048 | [Exploratory driving with grouped dynamics and advisory rules](0048-advisory-driving.md) |
| 0049 | [Current facts inside each question](0049-question-local-facts.md) |
| 0050 | [Fresh replication of factual relocation](0050-factual-relocation-replication.md) |

### Question-local driving and fresh-start validation

| Study | Report |
| --- | --- |
| 0051 | [Driving pilot with facts inside each question](0051-question-context-driving.md) |
| 0052 | [Driving pilot with a separate native compatibility check](0052-native-compatibility-driving.md) |
| 0053 | [Eight fresh starts with the unchanged question-local driver](0053-fresh-start-validation.md) |
| 0054 | [Versioned question-context driver: two-start integration smoke](0054-versioned-driver-smoke.md) |

### Delay robustness and experimental alternatives

| Study | Report |
| --- | --- |
| 0055 | [Free feasibility screen: prompt-only cruise speed under longer delays](0055-latency-governor-feasibility.md) |
| 0056 | [Moving current facts into the held-motion forecast question](0056-forecast-relocation.md) |
| 0057 | [A focused forecast question with question-local current facts](0057-forecast-focus.md) |
| 0058 | [Free feasibility: damping the supplied bearing rule with current yaw](0058-yaw-damping-feasibility.md) |
| 0059 | [Native validation of the yaw-damped bearing rule](0059-yaw-native-rule.md) |
| 0060 | [Free feasibility of rounded current angles for yaw damping](0060-quantized-yaw-feasibility.md) |
| 0061 | [Native execution with rounded current angles and equivalent formulas](0061-quantized-native-rule.md) |
| 0062 | [Free scalar-bearing policy search with separate physical holdouts](0062-scalar-policy-search.md) |
| 0063 | [Free farther-preview feasibility after the failed scalar-policy holdout](0063-long-preview-feasibility.md) |
| 0064 | [Native check of the selected farther-preview scalar rule](0064-long-preview-native.md) |
| 0065 | [Focus the pedal question while freezing the qualified scalar wheel question](0065-pedal-focus.md) |
| 0066 | [Actual Jev driving with a minimum 500 ms decision interval](0066-delay-driving.md) |
| 0067 | [Free timed controls after the interrupted latency pilot](0067-recovery-free-controls.md) |

### Same-setup model comparison and Clef rerun

| Study | Report |
| --- | --- |
| 0068 | [Same-driver comparison: Jev, OpenAI Decisions and Cloudflare Clef](0068-fixed-model-comparison.md) |
| 0069 | [Clef after an OpenRouter account top-up](0069-clef-topup-rerun.md) |

### Policy-free driving

| Study | Report |
| --- | --- |
| 0070 | [Removing the supplied policy while retaining question-local facts](0070-question-local-policy-ablation.md) |
| 0071 | [Goal-only driving beyond the former policy domain](0071-goal-only-recovery-domain.md) |
| 0072 | [Frozen goal-only challenge starts](0072-goal-only-challenge.md) |
| 0073 | [Matched wheel-motion facts: 4 finishes, 1 clean; recovery still assisted](0073-goal-only-wheel-motion.md) |
| 0074 | [Eight motion repeats: no rescue advantage, slower in all four pairs](0074-goal-only-wheel-motion-repeats.md) |
| 0075 | [Road geometry facts: 0/4 first gates before rescue; no demonstrated benefit](0075-goal-only-wheel-road-geometry.md) |

### Two-kart competition with goal-only drivers

| Study | Report |
| --- | --- |
| 0076 | [Four Jev/Jev duels: 8 finishes, 7 clean](0076-two-kart-jev-jev.md) |
| 0077 | [Eight paired Jev/OpenAI duels: all finish, Jev wins 8/8](0077-two-kart-jev-openai.md) |
| 0078 | [Twelve nearby-grid Jev/Jev duels: 24 finishes, 15 clean](0078-two-kart-nearby-grids.md) |
