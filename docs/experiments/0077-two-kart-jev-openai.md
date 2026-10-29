# 0077: Jev versus OpenAI on the same two-kart setup

Both models finished all eight paired races. Jev won all eight and finished
cleanly in seven; OpenAI finished cleanly in one and used seventeen rescues
overall. This favors Jev for this particular frozen setup. It is not a general
model ranking: the representation was developed around Jev, response latency
differed, and the cohort is small and limited to one track family.

| Grid | Jev assignment | Jev finish | OpenAI finish | Rescues, Jev/OpenAI |
|---|---|---:|---:|---:|
| Standard, side by side | Red | 83.78 s | 92.78 s | 0 / 1 |
| Same grid, assignments swapped | Blue | 90.00 s | 102.58 s | 0 / 3 |
| Clockwise, side by side | Red | 81.68 s | 89.90 s | 0 / 1 |
| Same grid, assignments swapped | Blue | 82.22 s | 101.58 s | 0 / 3 |
| Standard, staggered | Red | 91.17 s | 128.38 s | 1 / 2 |
| Same grid, assignments swapped | Blue | 85.27 s | 100.83 s | 0 / 3 |
| Clockwise, reversed stagger | Red | 80.18 s | 90.00 s | 0 / 0 |
| Same grid, assignments swapped | Blue | 89.75 s | 112.08 s | 0 / 4 |

All sixteen attempts crossed all 120 ordered gates. Clean means zero grass
time and zero rescues. The paired assignment swaps balance each model across
the declared positions. Red/blue identity remains tied to its grid position,
so these data do not separately identify a color/identity effect.

## Conditions held fixed

The [prospective registration](0077-two-kart-jev-openai-registration.json)
admitted exactly eight duels, with no retries or replacements. The game,
Python shared clock, collision/body mechanics, handling, road, rescue, goal-only
questions, factual packet, native menus and controller were unchanged from
[0076](0076-two-kart-jev-jev.md). Both drivers were independent, with the last
native input held during inference. Response frequencies were not equalized;
latency is part of these race conditions.

Jev used `typesafe/jev-1.14`, resolved to `typesafe/jev-1.14-20261014` through
TypeSafe. OpenAI used `openai/gpt-6-luna-decisions`, resolved to
`openai/gpt-6-luna-decisions-20261006` through OpenAI. Both were called through
OpenRouter's native Decisions endpoint, with pinned providers, no fallbacks
and no retries. Current route identities, limits and prices were rechecked.
All fifteen physical wheel/pedal combinations passed mocked checks for both
routes concurrently before admission.

## What the traces show and do not show

Actual contact occurred in seven of eight races: thirteen onset events and
twelve recorded lead changes overall. These events demonstrate shared physical
interaction; they do not establish intentional blocking, passing or planning.
Jev's one assisted run and OpenAI's seven assisted runs remain failures of the
clean-finish endpoint despite eventual completion.

In the first staggered race, OpenAI's gap between gates 45 and 46 was 36.63 s
(34.55 to 71.18 s), and it traveled 1,372.50 m before finishing. Ordinary three
laps are about 925 m. Thus a completed credited race can include substantial
extra travel after missed progress. The stored trace permits diagnosis; no
prompt or game fix was introduced during this comparison. Gate recovery and
opponent-aware strategy remain separate questions from finishing eventually.

The current wheel packet supplies a 15 m road preview and the next gate's
known/signed-plane facts. It does not supply full ego-frame gate geometry.
A future factual-geometry experiment could test this limitation without adding
a supplied recovery action rule. That is a recommendation, not an experiment
performed here. API latency and driving errors were not causally separated.

## Evidence and accounting

All 4,957 actual queries and 49,097 saved physics frames reconstructed exactly.
Root observed every process exit and completed the raw/native, factual/question,
application, physics, timing and shared-ledger audits before the next admission.
The additional body audit verified exact request/response bytes and hashes,
globally unique IDs and usage/cost within full reservations across all 7,429
calls from 0076–0077. No endpoint error, new uncertainty or pending reservation.
The complete current 0076 clock gate was reused on unchanged source/boot/server;
it was not rerun or silently assumed valid on a new engine.

Added 4,957 requests and $0.754692696. At closure the cumulative ledger was
87,063 requests / 300,283,312 charged tokens / $10.170457508002935, with all
70 historical uncertainties retained. Caps remain $20 / 100,000 requests /
500 million tokens. Combined 0076–0077 session cost was $1.021218480.
[Outcomes](0076-0077-two-kart-outcomes.json) retain every attempt, and complete
captures/reviews are under ignored `artifacts/two-kart-session-v1/`.

This eight-entry study is closed. No later tuning, race or retry is authorized
by its old window. The next registered work is separate nearby-grid validation
of Jev, with the game and prompt still fixed.
