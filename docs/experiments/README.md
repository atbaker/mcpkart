# Experiment index

Start with the [current findings checkpoint](2026-10-21-progress-checkpoint.md)
and [portable prompt/response examples](current-driver-examples.json). For
running the working driver, use the [driver guide](../question-context-driver.md).

## Current evidence

| Result | Evidence |
| --- | --- |
| Jev current 15 m driver: 14/14 useful, 13/14 clean | 0052, 0053, 0054, 0068 |
| OpenAI: 2/2 clean starts with the unchanged Jev-developed setup | 0068 |
| Clef: two driving failures; post-top-up retry ended on request timeout | 0068, 0069 |
| 22 m package: free/static gates passed; actual 500 ms Jev driving unrun | 0063, 0065, 0066, 0067 |

Counts from different static banks are not a pooled learning curve. Read each
report's frozen design, failed gates and limitations. Free scripted controls
are feasibility evidence, not model performance. Live results cover the solo
stadium and mirror with small starting-pose variation, not arbitrary tracks.

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
