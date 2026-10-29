# MCP Kart project plan

## Current state

The [0085 both-question timing study](experiments/0085-both-head-timing.md)
is closed: baseline recovered 4/8 delayed episodes versus 1/8 with timing facts
in both questions, and both passed 3/3 ordinary checks. The original state
scored 2/4 versus 0/4; blue 0/2 each, red 2/2 versus 1/2. Known timing facts
alone have not improved this selected recovery bank. Keep the new pedal-timing
flag off by default. Physics, rules and controls remained unchanged. Future
work should diagnose the control/observation bottleneck before stacking facts.
No further paid work is authorized by this closed comparison.

The [0084 motion-only validation](experiments/0084-motion-validation.md) is
closed: both profiles scored 1/4 on the original delayed state, 0/2 on the blue
holdout, 2/2 on the red holdout, and 3/3 ordinary-latency checks. The earlier
motion-only advantage did not repeat; no defaults were promoted or application
source changed. Both original successes began with brake and included contact,
despite identical pedal question text. Additional facts alone have not
demonstrated reliable delayed control.
Future work should separate stale-observation control from adding measurements.
All 22 entries are closed; this recommendation opens no paid window.

The [0083 factual observability study](experiments/0083-wheel-observability.md)
is closed: motion-only recovered delayed post-contact 2/2 vs baseline 0/2;
timing/both 1/2 each. All sixteen severe-drift attempts failed, and all four
normal checks passed. The four delayed successes involved contact and initial
native braking, despite identical pedal question text. Further paired motion-
only/baseline holdouts are needed before promotion; defaults remain unchanged.
The new optional wheel packets provide measured motion and known scheduled
wait, without action rules. All 18,543 prior questions remain byte-exact with
flags off; Python physics/runtime/UI source is unchanged.

The [0082 harder recovery study](experiments/0082-harder-recovery.md) is closed:
4/16 unassisted successes, all in normal-latency post-contact episodes. Both
profiles scored2/2 there and0/2 in severe drift or either +1 s condition. No
geometry success-rate advantage. A fast 209 ms maximum target API run still
failed drift; failures are not solely long-provider-stall events. The next
prompt hypothesis is separate factual own-motion/timing visibility ablations
for the wheel head, which currently lacks those own-motion fields. No action
rules, game changes or paid continuation are introduced by this recommendation.

The [0081 recovery benchmark](experiments/0081-recovery-benchmark.md) is closed:
12/12 bounded checkpoint episodes recovered without rescue on three selected,
free-qualified recorded states. Both fact profiles passed. Added 500 ms waiting
slowed misalignment baseline more in two repeats/cell, but no general prompt
advantage is established. Optional full-precision checkpoints, relative pacing,
episode endpoints and explicit added waits now support repeatable comparisons.
Next: a broader frozen feasible state bank and declared delay ladder; keep
geometry experimental and the baseline/default unchanged. No paid window is open.

The [0080 overload retry](experiments/0080-jev-overload-retry.md) completed
both baseline karts with 575 valid replies and no further HTTP 529. It used two/three
rescues, with materially slower API replies than the earlier geometry duel.
Provider recovery is observed for that run; gate-facts benefit remains unproven.
The original interrupted run is preserved and all paid windows remain closed.

The [0079 gate-facts pilot](experiments/0079-factual-next-gate-geometry.md)
added only measured next-gate coordinates/orientation to the wheel question.
Geometry finished four attempts cleanly, but only one matched pair completed;
the second baseline duel stopped on provider HTTP 529. First-gate performance was
nearly identical and no post-miss recovery episode occurred. Keep the default
unchanged. A focused next test needs an explicitly declared already-passed
gate start with free feasibility evidence, rather than relying on rare natural
misses. No new paid window is open.

The [two-kart checkpoint](experiments/2026-10-22-two-kart-checkpoint.md)
establishes a shared-track competitive Python prototype. Two independent
goal-only models use direct physical controls, collide and finish against one
60 Hz clock. The three frozen cohorts completed 48/48 kart attempts, 30 clean:
Jev 29/40 clean overall; OpenAI 1/8, with Jev winning all eight paired matches.
Nearby-grid validation shows recovery and missed-gate weaknesses. Deliberate
passing and robust racing strategy remain unproven. The
[driver guide](two-kart-driver.md) covers the reusable server, free practice,
one-match command, clock qualification and replay exports.

Earlier solo findings follow; the new contact footprint applies to the duel
mode and preserves the solo model's existing behavior.

The [0075 geometry comparison](experiments/0075-goal-only-wheel-road-geometry.md)
is closed: 0/2 geometry and 0/2 minimal races earned a gate before rescue.
All four eventually finished with assistance. Geometry did not demonstrate
better recovery. The new experimental flag adds factual road heading and
edge clearances only; defaults and Python physics remain unchanged.

The [0074 repeatability check](experiments/0074-goal-only-wheel-motion-repeats.md)
is closed: all eight races finished, all four clockwise runs clean, all four
recovery runs assisted once. Motion reduced no paired rescues and was slower
in all four pairs, so the pilot advantage did not reproduce. Minimal recovery
returned to forward preview before rescue but earned no gate before rescue.
The then-proposed geometry experiment was implemented and executed in 0075 above.

The [0072 challenge](experiments/0072-goal-only-challenge.md) finished two harder
starts with the frozen goal-only prompt, but both required rescue: two rescues
for the behind-preview recovery case and one for the larger initial error.
The ordinary holdout is unrun at the request admission floor. The extension
was exercised, but its initial recovery was assisted. Robustness remains a
limitation. The later request-ceiling increase did not reopen this study;
its ordinary holdout remains unrun. All current paid studies are closed.

The user prefers goals, mechanics and measurements without a supplied action
policy. The [0071 follow-up](experiments/0071-goal-only-recovery-domain.md)
finished four of four starts cleanly in 79.52–81.63 seconds. It relaxed the old
pose-domain stops without changing prompts, game or measurements. No actual
query entered that extended domain, so recovery remains untested. One reply
took 1.38 seconds; the earlier 2.197-second event's origin remains unknown.
The [0070 pilot](experiments/0070-question-local-policy-ablation.md) preserves
one clean goal-only finish, one inherited-domain stop and two clean policy
controls. Those studies are closed. Earlier counts below describe the supplied-
policy driver.


The solo proof of concept now has a working opt-in Python driver on the
24 m stadium and clockwise mirror. Jev completed 14/14 useful attempts,
13/14 clean, including 12 consecutive fresh clean starts. OpenAI GPT-6 Luna
Decisions transferred to the same setup with 2/2 clean finishes. This is
small-start-variation tracking on one course family, not traffic or general
recovery validation. See the [progress checkpoint](experiments/2026-10-21-progress-checkpoint.md),
[experiment index](experiments/README.md) and [driver guide](question-context-driver.md).

The user has set Clef aside. Its two 0068 attempts failed the driving domain;
the separate post-top-up 0069 attempt timed out on its third request, so its
second race remained unrun. Cache effects are unknown. Retain all outcomes.
All paid windows are closed; the fixed 0072 entries were retained without replacements.

Current shared budget: 98,715 requests, 331,956,791 charged tokens,
$11.443828922002771, 71 uncertainties and no pending reservations. Caps are
$20 / 110,000 requests / 500 million tokens. See the [snapshot](experiments/model-budget-snapshot.json)
and the [dollar-cap authorization](experiments/0076-two-kart-session-authorization.json).
The live ledger must be transferred between environments and never reset.

## What enabled the current driver

- A forgiving stadium: two 60 m straights, radius-30 m bends, 24 m full road
  width, 12 m/s speed ceiling and 0.12 rad wheel range. Moderate wheel has a
  nominal 30 m turning radius. Original application defaults are preserved.
- The historical driver supplied 15 m bearing-based steering and edge/motion
  pedal rules. The goal-only follow-up removes these rules while retaining
  the same measurements and component choices in one API request.
- Factual geometric bearing supplied directly, component-specific definitions,
  and current facts inside each question's structured instructions.
- Low observed latency and independent 60 Hz physics. The previous control
  stays applied during inference; no common minimum decision delay is imposed.
- Exact per-query prompt/native/physics/clock/accounting replay. Free host
  controllers establish feasibility separately and never count as model races.

The [findings checkpoint](experiments/2026-10-21-progress-checkpoint.md) separates
controlled representation results from whole-controller live comparisons.
The historical policy cohorts largely measure execution of an engineered
feedback policy. The goal-only results add evidence of model-selected driving
on this forgiving solo course; they do not establish general racing-line,
braking or recovery capability.

## Established scope and constraints

- Solo and two-kart three-lap racing through 40 ordered finite gates per lap. Freeze track,
  handling, controls, observations and prompts within each comparison.
- Keep process-isolated Python/FastMCP and asyncio pacing. Rust remains an
  optional historical experiment, not a dependency for the working driver.
- Models directly choose the original 15 steering/throttle/brake inputs.
  The factored interface asks for five wheel and three pedal choices in one
  POST and maps their pair to exactly one original action. No host steering,
  lane keeping, action filtering, smoothing, retry or provider fallback.
- Physics advances continuously while requests are in flight. Faster routes
  can act more often. Measure full observation age at application as well as
  API latency and simulation lateness.
- Three seconds continuously off-road triggers a recorded rescue to the
  departure area, stopped and aligned. Rescue gives no checkpoint credit and
  invalidates older replies. Clean finishes require zero rescue and zero grass.
- A useful finish takes at most twice its matched scripted reference. The
  original eight-of-ten milestone was broadened by rescue rules; always report
  assisted and clean outcomes separately. Current cohorts cover only one solo
  course family and small initial offsets/headings. The two-kart cohorts also
  include physical contact, close starts and finite circular footprints.
- Paid work requires a fresh finite authorization/protocol, complete current
  timing qualification, native/interface checks, exact free controls, shared
  budget guards and full audit between single-race launches. Preserve failures.

[The realtime timing ADR](adr/0001-racing-time-is-independent-of-model-responses.md)
and [original experiment](experiments/0001-realtime-driving.md) retain the
initial design. [Cloud development](cloud-development.md) covers operational
setup, credentials, timing gates and recovery.

## Open questions before the next study

These are possible next steps, not authorization to collect more paid data.

1. Test how much the final package depends on each scaffold using frozen
   ablations and matched fresh inputs. Jev's representation comparisons do
   not automatically establish the same causal effects for OpenAI.
2. Broaden physical robustness: larger initial errors, changed bends, sustained
   latency and eventual recovery. The 15 m guide fails free sustained-delay
   stress tests. The 22 m focused package passed static/free gates in 0063/0065;
   its actual 500 ms Jev driving study remains unrun after the 0066 reboot.
3. Keep goal-only as the baseline and test factual representation without
   adding action advice. Label any supplied-rule comparison explicitly.
4. Test factual next-gate geometry on predefined missed-gate recovery states,
   without prescribing actions. The duel mode now has radius-1 m bodies and
   full-footprint road/gate checks; the solo mode retains its point semantics.
5. Separate deliberate opponent-aware decisions from ordinary road following.
   Contacts and credited-progress lead changes establish interaction, not
   intention. Add tracks or larger fields only through new frozen studies.

## Decisions API and harness

OpenRouter's `POST /api/alpha/decisions` accepts structured state and named
questions. Preserve returned model/provider identity, actual native choices,
request bodies and certain usage accounting. Separate endpoint compatibility,
prescribed-command copying, policy agreement and actual racing outcomes.
None is a substitute for the others. The current experimental driver uses
empty shared state and immutable per-snapshot facts inside each question.
See [API research](research/decision-models.md) and [curated examples](experiments/current-driver-examples.json).

## Temporal and later product scope

Keep physics and inference independent of Temporal, then measure orchestration
overhead. A Race Workflow could own admission, start, cancellation, completion
and results while an independent runtime executes physics. A long-running
Activity and an external race service remain candidates; recovery semantics
need an explicit design. Temporal is not yet part of the measured driving loop.

Two-kart contact and spectators are implemented. Later scope includes several
racers, items, public
matchmaking and service bots. GitHub OAuth could identify racers; organization
teams and six versus eight racers remain open. Leaderboards should distinguish
racer identity, model/provider and agent client or harness, with controlled
comparison evidence separate from self-reported entries. GCP and Temporal
Serverless Workers remain intended deployment targets, not established capacity.
The previous application is preserved under [legacy](../legacy/README.md).
