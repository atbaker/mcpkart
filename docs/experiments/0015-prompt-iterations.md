# Further prompt iterations on the 24 m stadium

Status: complete, October 19, 2026. The user authorized a higher request
ceiling and a few more prompt iterations. The shared ceiling is now **75,000
requests**, with the **$10** cap and **250-million-token** guard unchanged.
The locked atomic administrative change preserves all prior spending, tokens,
uncertain requests and pending state. Starting ledger: 49,762 requests,
$6.221778952 charged, 210,940,833 charged tokens, 69 uncertain requests and no
pending reservations. `request-limit-authorization.json` preserves before/after
states under `artifacts/jev-prompts-v4/`.

Keep the user-selected 24 m stadium, Python process runtime and asyncio pacing.
The [previous iteration](0014-stadium-prompts.md) showed that a directional veto
worsened both starts, while an early-braking paragraph could leave a kart
stationary on-road for 209 seconds. The existing `damped` preset remains the
control; no previous failed attempt is retried or replaced.

## Frozen physical and comparison rules

The stadium retains two 60 m straights, radius-30 m semicircles, 24 m full road
and gate width, 12 m/s speed ceiling and 0.12 rad maximum wheel angle. Keep
`road_navigation` observations, all 15 native geometry-menu choices, continuous
60 Hz physics, three laps, 40 ordered finite gates per lap, three-second rescue,
stale reply rejection and the three-times-reference deadline. No steering
controller, computed control recommendation or racing line enters the state.

The source fingerprint remains
`588958f4c0bd594064b55c24cc9b678a4a41448c7334592521bb91bfa2130e6c`.
The existing complete clock gate and 349-test source validation apply on this
same machine boot. New zero-delay references cover starts 0–18, and a free live
control checks start 5. Local mock preflights verify actual payloads: only
instructions change, while state, route pinning and all native criteria remain
identical. No real model calls are made by those preflights.

The request alias is `typesafe/jev-1.14`, freshly resolved to
`typesafe/jev-1.14-20261014` at provider `TypeSafe`, with the previous prices.
Every successful reply must match that model/provider. Keep one request in
flight, no automatic retry or provider fallback. Retain every failed race;
stop a batch on endpoint or timing errors and inspect before continuing unrun
cases. Different instruction lengths can affect payload size and inference
latency; results compare complete prompt profiles rather than isolated clauses.

Admit another race only with at least 1,000 global request slots and five million
charged-token slots available. The per-request shared dollar/request/token hard
caps remain enforced throughout each race. Do not raise another limit or reset
spending if a guard is reached.

## Iteration plan

Freeze each round's exact texts, order, reference, route, source and helper hashes
before its first model call. Adapt only between complete rounds. Up to three
screens compare `damped` and two candidates over two fresh starting poses each,
with reversed order on the second pose. These are paired initial conditions;
Jev responses are not seeded.

Require both completed useful-pace races and no endpoint/timing impairment
before ranking a candidate by rescue-free finishes, paired rescue totals and
pace. Prefer no worsening on either pose and a strict improvement on at least
one. Static choices or a single clean race cannot establish improved driving.

If a frozen candidate achieves two clean useful-pace finishes and improves on
its controls, replace remaining screens with ten fresh qualification starts
plus three new baseline controls. The screening starts do not count toward
those ten. Stop qualification if three non-clean/non-finished attempts make
eight clean completions out of ten impossible. This branch allows at most
25 paid attempts overall; three ordinary screens use 18. All branches remain
subject to the shared budget guards. Do not promote a preset from two pilots.

## Round 1

The [exact round-one texts](0015-prompt-texts-r1.json) freeze these contrasts:

- `pedal_release` replaces the failed early-braking prefix with a general rule
  about releasing the brake and using forward motion to turn, on either road
  or grass. It retains the exact `damped` base. This targets both permanent
  braking at rest and unnecessary low-speed driving.
- `motion_balance` replaces the long guide with a compact physical explanation:
  heading, velocity, wheel angle and yaw must be considered together; following
  a bend still requires turning; braking is temporary and a stopped kart needs
  motion to change its heading. This tests the whole shorter question.

Declared order:

1. Start 5: `damped`, `pedal_release`, `motion_balance`.
2. Start 6: `motion_balance`, `pedal_release`, `damped`.

Round-one results:

| Instructions | Start 5 time / rescues | Start 6 time / rescues |
| --- | ---: | ---: |
| `damped` | 89.05 s / 2 | 116.58 s / 4 |
| `pedal_release` | 102.05 s / 6 | 76.98 s / 1 |
| `motion_balance` | 112.32 s / 9 | 117.32 s / 10 |

All six finished within twice reference, passed timing and exact replay, and had
no endpoint errors. None was rescue-free. Brake release improved one start and
worsened the other; the shorter guide worsened both. Retain `damped` for the
next screen. The round used 2,266 calls, $0.271523028 and 6,840,881 charged tokens,
with no new uncertain requests. Its audit reconciles the 75,000-request ledger
and attributes every accepted command to a native model reply.

## Offline geometric-policy diagnostic

Before a formula-guided question is tested, check that the supplied static
policy itself can drive the fixed physics. The offline pure-pursuit diagnostic
uses the existing 10 m ego preview point and the nominal bicycle formula
`atan(2 * 1.8 * ego_y / (ego_x² + ego_y²))`, quantized to the five physical wheel
angles, with acceleration and held inputs during an injected response delay.
It makes no network/model calls and never runs in the paid driver. Any paid
formula variant supplies only fixed equation text: Jev must perform the
calculation and select its native input. This tests executing a supplied policy,
not discovering that policy.

Both starts 7 and 8 finished with zero grass/rescues at delays zero and 0.25 s.
At 0.5 s, both stopped as unsupported when the selected target lay behind the
kart, at 8.27 and 9.30 s. Those are retained failures, not clean completions.
The diagnostic does not supply an invented behind-target recovery controller.
Actual network latency tails can exceed these delays.

This justifies one new offline calibration variant using the existing 15 m row,
with the same six start/delay cases. Preserve the original script and all six
10 m results; declare the 15 m variant before running it, with no further
distance search in this iteration. No track or handling parameter changes.

The 15 m diagnostic also finished both starts without grass/rescues at zero
and 0.25 s delay. Times were 76.23/78.88 s for start 7 and 76.52/78.72 s for
start 8. At 0.5 s, both again stopped unsupported because the target moved
behind the kart, at 20.15/21.18 s. This improves the tested quarter-second
oracle pace but does not establish half-second robustness. All twelve offline
outcomes remain saved, including the four unsupported cases; there was no
further distance tuning. Behind-target stops limit the tested policy domain,
not a proof about every possible recovery behaviour.

## Round 2

No round-one candidate met the consistent paired improvement rule. The
[exact second-round texts](0015-prompt-texts-r2.json) keep `damped` as control
and add two distinct quantitative prefixes to its unchanged base:

- `pursuit_formula`: while on-road with a forward 15 m preview target and no
  missed-gate recovery, the model is asked to calculate the nominal wheel angle
  using the static equation above and choose the nearest physical angle.
  Pedals and unsupported/off-road/gate-recovery states use the ordinary guide.
  The host never evaluates the equation in a paid request. This is a test of
  supplied geometric-policy execution under actual response times, with the
  known offline delay/support limitations explicitly retained.
- `straight_release`: near a straight, an explicit heading/yaw condition asks
  the model to release steering before existing rotation crosses alignment.
  With `H=road.road_vs_kart_deg`, `Y=kart.yaw_deg_s` and `T` the 10 m preview's
  `road_turn_deg`, the condition is `abs(T)<=3` and either `abs(H)<=3` or
  (`H*Y>0` and `abs(H)<=0.30*abs(Y)+3`). It applies only on-road while
  approaching the still-required gate plane; otherwise use the ordinary guide.
  These are frozen engineering thresholds, not validated optimal controls.

Declared order:

1. Start 7: `damped`, `pursuit_formula`, `straight_release`.
2. Start 8: `straight_release`, `pursuit_formula`, `damped`.

The full factual state and all native choice descriptions remain unchanged;
only the fixed question text changes. Local mock verification again passes.
The existing live scripted control remains applicable to the unchanged source,
machine and physical setup.

Round-two results:

| Instructions | Start 7 time / rescues | Start 8 time / rescues |
| --- | ---: | ---: |
| `damped` | 98.43 s / 1 | 131.28 s / 3 |
| `pursuit_formula` | 91.55 s / 5 | 99.93 s / 6 |
| `straight_release` | 108.42 s / 6 | 101.52 s / 5 |

All six finished within twice reference, with valid timing, exact replay and no
endpoint errors. Both additions worsened rescue counts on both starting poses.
Round two used 2,135 calls, $0.270431574 and 6,792,846 charged tokens, with no
new uncertain requests. The cumulative twelve-race audit passes and reconciles
the full shared ledger.

A posthoc diagnostic compares saved native choices with each supplied rule;
it runs only after racing stops and never feeds a calculated recommendation to
the paid driver. The formula matched on 149/486 eligible decisions (30.7%;
149/485 actually applied decisions). The straight-release rule matched on all
81/81 occasions when its stated condition applied. Agreement is not optimality
and does not prove why a departure occurred. These results distinguish a
poorly executed supplied formula from a followed rule that did not improve the
paired rescue outcomes. Keep `damped` as control.

## Round 3

The [exact third-round bank and renderer source](0015-prompt-texts-r3.json)
freeze two related question-context changes, with the exact production `damped`
base in all three conditions:

- `inverse_frame` explicitly restates current nose heading relative to the road:
  `nose_vs_current_road_deg = -road.road_vs_kart_deg`, including a LEFT/RIGHT
  description. It supplies no desired heading, target control or action score.
  Earlier salience work already added direction words; this narrower contrast
  tests the inverse orientation relation, not categorical words for the first time.
- `inverse_history` uses that same frame and additionally shows one previous
  observed snapshot: time, lateral offset, road/nose angle, actual wheel, yaw,
  speed, gates and rescue count. Suppress history on the first observation,
  across rescues and when either available clock is nonmonotonic. This adds
  factual history to the question; it is not a pure wording-only comparison.

Declared order: start 9 uses `damped`, `inverse_frame`, `inverse_history`; start
10 reverses that order. All state fields and all fifteen native criteria remain
identical. The driver saves the exact submitted question for every reply, and
the audit reconstructs every question from the saved observation sequence.
The same admission and hard spending guards apply. There are at most seven
additional paid attempts available after this screen under the overall 25-race
plan; a strong late candidate would receive limited fresh-start follow-up,
not a claimed ten-start qualification.

Round-three results:

| Instructions | Start 9 time / rescues | Start 10 time / rescues |
| --- | ---: | ---: |
| `damped` | 73.85 s / 0 | 106.90 s / 4 |
| `inverse_frame` | 139.53 s / 3 | 149.80 s / 2 |
| `inverse_history` | 153.07 s / 0 | 135.58 s / 3 |

All six finished within twice reference, with valid timing, exact replay and no
endpoint errors. The two zero-rescue races also had zero grass time. Inverse
orientation framing worsened start 9 and improved start 10's rescue count,
while slowing both. History tied the baseline's clean first start and reduced
start 10 from four rescues to three, but took 79.22 and 28.68 seconds longer.
Its first finish was only narrowly within the useful-pace limit (1.9802×
reference). That is a weak rescue-count hint with a substantial pace cost,
not evidence of reliable clean driving. Median endpoint latency stayed similar
between baseline and history (about 231–249 ms across these individual runs),
so added inference latency alone does not explain the large race-time gap.

Round three used 2,757 calls, $0.349015758 and 8,766,047 charged tokens. The audit
reconstructed every one of its 2,757 submitted questions exactly; 1,028 included
a guarded previous observation. No candidate in any round achieved two clean,
useful-pace starts, so no larger qualification branch was triggered.

A launch error before the first round-three race is retained separately under
`r3/launch-failures/credential-env-removed/`. The root command incorrectly removed
the configured API-key environment variable; client construction failed before
`run_trial`. No race or model request started and the ledger exactly matched the
round's starting ledger. Original logs and protocol were preserved before
launching the still-unattempted case with the configured credential. No paid
race was retried or replaced.

Ignored raw evidence and independently frozen round folders live under
`artifacts/jev-prompts-v4/`. Versioned summaries and the latest budget snapshot
preserve the outcome without publishing raw recordings.

## Outcome and next research direction

Retain the existing optional `damped` preset with `road_navigation` and the
geometry menu on the fixed 24 m stadium. Do not promote any of these six new
variants or claim that the clean-driving target has been met. The six fresh
baseline races produced one clean finish; the twelve candidate races also
produced one. Starting poses differ across rounds, so compare each candidate
with its own matched controls rather than pooling candidates as one treatment.
These are two-start screens with stochastic model responses, not a reliable
effect estimate. Source physics, handling, runtime and the application default
instruction style were not changed during this phase.

The strongest new diagnostic is the compliance split: the formula prompt did
not reliably induce its specified rule, whereas the steering-release condition
was followed without improving rescue outcomes. The former does not isolate
arithmetic inability: parsing, units, instruction priority or the longer base
guide could also matter. The latter does not prove why individual departures
occurred. More emphatic wording alone has little support from these screens.

The next useful prompt experiment is a small, frozen factual-skill diagnostic:
mirrored cases separating road-versus-nose orientation, wheel versus yaw,
units, nearest native angle and formula execution. Compare minimal and full
question contexts before another live prompt sweep. Static correctness would
still need fresh closed-loop validation. A later single-request split between
wheel and pedal questions could test whether the joint menu obscures those
judgments; that would be an interface experiment requiring separate verification,
not an established improvement. These follow-ups were not run in this phase.

## Final verification and spending

The complete audit passes for all 18 races: 120 ordered gates each, useful pace,
valid Python process clocks and exact deterministic replay. It attributes all
7,074 accepted commands to native model replies, checks every request's route
and all fifteen unchanged physical control descriptions, verifies frozen helper
and prompt hashes, and reconciles every budget checkpoint. There were 7,158
real model calls, no endpoint errors and no new uncertain requests. Worst paid
clock lateness was 44.361 ms, within the frozen validity limits. The full free
clock gate and 349 passing source tests remain applicable to the unchanged
source; per-round local HTTP mocks and per-race timing/replay supplied the new
verification. The owned server was stopped and port 8765 closed afterward.

This phase charged **$0.890970360** and **22,399,774 tokens**. Final shared ledger:
**56,920 / 75,000 requests**, **$7.112749312 / $10**, **233,340,607 / 250,000,000
charged tokens**, 69 historical uncertain requests and no pending reservations.
Only the authorized request ceiling increased; no spending history was reset
and no other cap changed. The [latest budget snapshot](model-budget-snapshot.json)
contains the exact ledger. [Machine-readable results](0015-results-summary.json)
preserve the race metrics, audit counts and posthoc rule agreement without raw
observations. The local paired-result figure is
`artifacts/jev-prompts-v4/report/prompt-iterations.png` (also PDF).
