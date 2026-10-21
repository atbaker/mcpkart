# Eight-hour Jev progress review

User-requested pause, October 19, 2026, approximately 2:15–10:15 p.m. Pacific
(October 19 21:15–October 20 05:15 UTC). New paid experiments are paused.
Study 0043 is uncollected and has no results. The earlier width and prompt
studies 0012–0015 finished before this window and are not counted below.

## Practical assessment

Jev can finish the 24 m stadium with automatic rescue assistance. We have
not demonstrated a more reliable autonomous driver during this window.
All four live races finished, but each required one or two rescues. The
factored interface improved one starting pose and worsened the other.
No replacement for the joint `damped` baseline was promoted.

The useful progress is a clearer account of decision failures. Supplying a
factual bearing and reducing observation complexity improved execution of
explicit rules on static cases. Those gains have not yet become validated
driving improvements. Small-bearing steering errors, response variability
and poor hazard forecasting remain. Rule-compliance labels are not labels
of optimal driving actions.

The process-isolated Python runtime remains in use. Its current-boot timing
qualification passed, and the rebuilt environment passed 445 tests with
three optional Rust skips. The available runtime evidence is stronger than
the evidence for consistent decision correctness.

## Actual races within the window

Study 0025 used two paired starts, three laps, the fixed 24 m stadium,
12 m/s speed ceiling, 0.12 rad wheel limit and three-second rescue.

| Start | Decision layout | Time | Automatic rescues | Off-road time |
| --- | --- | ---: | ---: | ---: |
| Seed 11 | Joint baseline | 102.20 s | 2 | 6.00 s |
| Seed 11 | Factored wheel/pedal | 87.53 s | 1 | 3.00 s |
| Seed 12 | Joint baseline | 81.62 s | 1 | 3.00 s |
| Seed 12 | Factored wheel/pedal | 120.62 s | 2 | 6.58 s |

Four finishes, zero rescue-free or grass-free runs. Both layouts needed
three rescues across their two races. All had useful pace, valid recorded
timing and zero endpoint errors. These are four races from two initial
poses, not a reliability estimate over many independent starts.

The [0025 report](0025-factored-driving.md) retains its validation and
execution-provenance limitations. Replay validation was amended to include
the runtime `finished` field in the expected observation. The available
history does not establish prospective independent amended-preflight success
or execution ownership of the remaining three races. Original failed
evidence remains preserved; the results are exploratory.

## Complete paid-study inventory

Scores below compare treatments only within their own study. Banks, tasks
and denominators differ; they are not a pooled learning curve. Completion
times are rounded UTC evidence/report times, not necessarily writer exit.

| Study | Calls | Trial and result | Outcome |
| --- | ---: | --- | --- |
| 0016 | 336 | Factual skills: strong simple reading; prescribed pedals 48/48; composed formula/native decisions weak. | Diagnostic, no driver qualification. |
| 0017 | 720 | Explicit wheel-target wording: formula 137/360 → 185/360; candidate full-wheel targets only 1/120. | Failed. |
| 0018 | 384 | Coordinate readback 96/96; numerator 48/48; denominator 24/48; best formula variant 26/48. | Failed. |
| 0019 | 192 | Literal arithmetic: denominator 23→35/48 and formula 22→29/48; full targets 0/16. | Failed. |
| 0020 | 96 | Six worked examples: formula 31→34/48. | Failed. |
| 0021 | 192 | Answer-menu factorial: baseline 37/48; best combined menu 40/48, with magnitude tradeoffs. | Failed. |
| 0022 | 192 | Observation context: full physical 33/48, full numeric 36/48, both raw variants 32/48. | Failed. |
| 0023 | 96 | Atan formula 36/48 versus division-free inequalities 31/48. | Failed. |
| 0024 | 96 | Joint and factored interfaces each followed 48/48 prescribed commands. | Compatibility passed; no driving claim. |
| 0025 | 1,499 | Four live races: four finishes, zero clean runs; split decisions helped one start and hurt the other. | Paired driving screen failed. |
| 0026 | 96 | Motion forecasts: both guides 24/48; all answers safe, all hazards missed. | Failed. |
| 0027 | 144 | Format controls 16/16; four forecasting contexts each 16/32, all answers safe. | Forecast benchmarks unmet. |
| 0028 | 96 | Road-frame facts improved current-motion readback 14→16/16; four forecast variants each 8/16. | No forecasting gain. |
| 0029 | 32 | Actual-state forecasting: baseline and physics scaffold each 8/16, all answers safe. | No improvement. |
| 0030 | 8 | Question-key format prerequisite 7/8. All 32 planned forecasts remained unrun. | Stopped at registered gate; forecast accuracy undefined. |
| 0031 | 60 | Supplied-policy placement: shared 15/30 versus local 12/30 native pairs; pedals both 30/30. | Failed. |
| 0032 | 60 | Supply factual bearing: raw XY 10/30 → bearing 28/30 native pairs; 18 gains, zero losses. | Static screen passed. |
| 0033 | 60 | Static versus driving framing: both 26/30 native pairs. | Native bridge failed. |
| 0034 | 60 | Fixed factual projection: full state 25/30 → selected facts 30/30; five gains, zero losses. | Static screen passed. |
| 0035 | 60 | Fresh broader validation: actual rollout poses 28/30, synthetic 29/30; pedals 60/60. | Natural overall and synthetic straight-wheel requirements failed. |
| 0036 | 60 | Deadband-first wording: 27→28/30; candidate straight 5/6 and pedals 29/30. | Failed. |
| 0037 | 36 | Conditions-only criteria: 16→16/18 pairs; one wheel gain offset by a pedal loss. | Failed. |
| 0038 | 36 | Literal field paths: 16→15/18 pairs; pedals perfect. | Failed. |
| 0039 | 36 | Plain English conditions: 14→14/18 pairs; one gain and one loss. | Failed. |
| 0040 | 54 | Combined/full 15/18; wheel-only/full 15/18; wheel-only/reduced facts 18/18. | Diagnostic; no native/live gate. |
| 0041 | 120 | Fresh broader replication: both wheel views 60/60, each natural and synthetic subset 30/30. | Earlier differential gain did not replicate here. |
| 0042 | 96 | Twelve fresh nearly straight poses, four presentations per view: full 16/48 versus reduced 43/48; 30 paired gains and three losses. | Focused diagnostic gain, five reduced-view errors; no native/live gate. |

The forecast tests establish failure on their specified tasks and supplied
information, not general impossibility of forecasting. The bearing policy
introduced in 0032 is a new engineering policy, not an equivalent rewrite
of the older pursuit formula.

## Latest repeatability result

Study 0042 has twelve poses in six reflected pairs, not 96 independent
states. Each pose appears four times per view, with two presentations per
menu order. Ten poses had four correct reduced-view answers; two positive
bearing poses accounted for the five reduced-view errors.

Across pairs of byte-identical requests, literal choices agreed in 19/24
full-view pairs and 21/24 reduced-view pairs. Agreement can be consistently
wrong. All 96 raw wheel replies were technically valid, while all 96 original
native missing-pedal rejections remain intact. Wheel-only replies were never
turned into native controls. The same distinction applies to 0040 and 0041.

The base 0042 report omitted its prespecified explicit repeat-agreement and
guard-stratum summaries. An additive saved-response supplement supplies them;
the frozen audit, original records and failed choices were not rewritten or
rerun. The [0042 report](0042-small-bearing-repeat.md) records final independent
verification status and the reporting correction. Separate provenance
verification passed all 71 checks, including independent reconstruction of
the supplement, with no errors.

The representation benefit is specific to these comparisons. It does not
identify an internal attention mechanism, establish equivalence at the
0041 ceiling, or prove reliable racing.

## Accounting and paused next step

All 27 saved before/after ledger boundaries from 0016 through 0042 reconcile
consecutively. There are no intervening unlisted charged calls:

- 4,917 model requests: 1,499 during four races and 3,418 static calls.
- 12,023,780 charged tokens and approximately $0.487330326 additional charges.
- Zero new uncertain charges; no pending reservations at pause.
- Actual shared total: 61,837 requests, $7.600079637999871 and 245,364,387 tokens.

The remaining 4,635,613 tokens are below the unchanged five-million-token
live admission floor. No new live race is currently admissible under that
guard. Shared hard caps remain $10, 75,000 requests and 250 million tokens.

The selected but uncollected 0043 idea would retain the full factual state
and one request containing both original decision heads, while giving each
question only its relevant original rule definitions. It is paused and has
no results. A practical next milestone would be a frozen complete prompt that
passes fresh native-pair tests, followed by repeated unseen live starts with
low rescue use. No further work or paid continuation is scheduled by this review.
