# MCP Kart project plan

## Current state

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
All prior paid windows are closed; this cleanup introduces no new model calls.

Current shared budget: 71,160 requests, 267,423,949 charged tokens,
$8.563495772000609, 70 uncertainties and no pending reservations. Caps remain
$10 / 75,000 requests / 500 million tokens. See the [snapshot](experiments/model-budget-snapshot.json).
The live ledger must be transferred between environments and never reset.

## What enabled the current driver

- A forgiving stadium: two 60 m straights, radius-30 m bends, 24 m full road
  width, 12 m/s speed ceiling and 0.12 rad wheel range. Moderate wheel has a
  nominal 30 m turning radius. Original application defaults are preserved.
- Explicit 15 m bearing-based steering and edge/motion-based pedal rules in
  the prompt. The model chooses both native components in one API request.
- Factual geometric bearing supplied directly, component-specific definitions,
  and current facts inside each question's structured instructions.
- Low observed latency and independent 60 Hz physics. The previous control
  stays applied during inference; no common minimum decision delay is imposed.
- Exact per-query prompt/native/physics/clock/accounting replay. Free host
  controllers establish feasibility separately and never count as model races.

The [findings checkpoint](experiments/2026-10-21-progress-checkpoint.md) separates
controlled representation results from whole-controller live comparisons.
The current task is largely execution of an engineered feedback policy;
success does not establish independent racing-line or braking strategy.

## Established scope and constraints

- Solo three-lap racing through 40 ordered finite gates per lap. Freeze track,
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
  course family and small initial offsets/headings.
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
3. Decide how much policy the game should expose and what capability we want
   to measure: supplied-rule execution, model-selected strategy, or both.
4. Define a kart collision footprint before adding opponents. Current road
   boundary checks use the kart position as a point; visual width does not
   establish multiplayer clearance.

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

Later scope includes several racers, collisions, items, spectators, public
matchmaking and service bots. GitHub OAuth could identify racers; organization
teams and six versus eight racers remain open. Leaderboards should distinguish
racer identity, model/provider and agent client or harness, with controlled
comparison evidence separate from self-reported entries. GCP and Temporal
Serverless Workers remain intended deployment targets, not established capacity.
The previous application is preserved under [legacy](../legacy/README.md).
