# 0078: Jev versus Jev on nearby starting grids

All 24 kart attempts in twelve duels finished their three credited laps. Fifteen
were clean; eight needed rescue and one spent time off-road without rescue.
The initial shared-track result transfers to nearby grids, but clean driving is
less dependable than the first four duels suggested. This is a playable
prototype with a recovery limit, rather than a reliable competitive driver.

[Visual comparison of all 24 duels](figures/0076-0078-two-kart-results.svg)
and [actual missed-gate detail](figures/0076-0078-missed-gate-detail.svg).

| Run | Grid | Red finish | Blue finish | Rescues, red/blue | Contacts | Lead changes |
|---|---|---:|---:|---:|---:|---:|
| 0 | Close side | 90.77 s | 83.42 s | 1 / 0 | 2 | 2 |
| 1 | Close side, clockwise | 85.15 s | 82.05 s | 0 / 0 | 3 | 0 |
| 2 | Near tandem | 83.12 s | 82.55 s | 0 / 0 | 2 | 3 |
| 3 | Near tandem, clockwise | 96.45 s | 106.13 s | 1 / 2 | 1 | 3 |
| 4 | Wide diagonal | 88.82 s | 86.90 s | 0 / 0 | 3 | 1 |
| 5 | Wide diagonal, clockwise | 81.72 s | 84.72 s | 0 / 0 | 8 | 5 |
| 6 | Wide diagonal, clockwise, repeat | 136.10 s* | 87.18 s | 0 / 0 | 4 | 0 |
| 7 | Wide diagonal, repeat | 88.77 s | 97.28 s | 1 / 2 | 0 | 0 |
| 8 | Near tandem, clockwise, repeat | 93.02 s | 83.83 s | 1 / 0 | 0 | 0 |
| 9 | Near tandem, repeat | 84.28 s | 90.33 s | 0 / 1 | 2 | 2 |
| 10 | Close side, clockwise, repeat | 93.93 s | 81.92 s | 2 / 0 | 2 | 1 |
| 11 | Close side, repeat | 82.67 s | 88.60 s | 0 / 0 | 2 | 0 |

\* Run 6 red was **not clean**: 2.22 s off-road, despite zero rescues. It traveled
1,301.24 m and took 44.30 s between gates 111 and 112. A credited three-lap
finish can include extra travel after a missed gate. Clean requires both zero
off-road time and zero rescues. All attempts crossed all 120 ordered gates.

## Frozen comparison

The [prospective registration](0078-two-kart-nearby-grids-registration.json)
declared six nearby grids and two repeats each, with the second block in reverse
order. Starts vary lateral/longitudinal separation and small initial headings;
they retain the 24 m stadium or clockwise mirror. The exact positions are in
the registration. Each grid first passed a complete, audited free control.

Game physics, contact, handling, goal-only questions, native controls and model
controller stayed byte-for-byte fixed from 0076–0077 throughout collection.
Both drivers used the same pinned Jev route. No supplied action rules, host
steering, fallback, retry, replacement race or performance-driven adjustment
was introduced. Each actual process exited and passed the complete root audit
before the next was admitted.

There were 29 contact onsets and 17 credited-progress lead changes. These show
physical interaction; they do not identify intentional passing or blocking.
The two repeats of a grid are too few to estimate its failure probability.
The repeat block also occurs later in time, so repeat differences are not a
controlled latency or model-randomness intervention.

## Failure evidence and latency

Eight attempts used eleven rescues altogether. In run 7 both karts needed
rescue even though the race recorded no contact. Thus contact alone cannot
explain all failures. Run 6 additionally exposes missed-gate recovery: red
eventually finished without rescue but with a long detour. This is distinct
from continuous clean progress.

The current wheel question contains a 15 m road preview and next-gate
known/signed-plane facts, without complete gate geometry in the kart's frame.
A future factual-geometry ablation could test whether this contributes to
recovery failures without supplying an action policy. No such treatment was
implemented or tested in this session.

The 7,535 API replies had median 226.1 ms, p95 393.2 ms, p99 706.5 ms and maximum
3.215 s. Fifty-five took at least one second, seven at least two, and two at
least three. The final race was clean for both karts despite maxima of 3.002 s
and 3.215 s. Long replies and errors therefore need event-level analysis; these
observations do not establish their causal effect or whether network/provider
inference caused them. There was no endpoint error or new uncertain request.

## Verification and accounting

All 7,535 actual query bodies/native replies, 68,290 saved physics frames and
15,070 budget transitions reconstructed exactly. Timing passed the original
100 ms maximum lateness, 25 ms p95 and 100 ms drift limits; the largest saved
sample lateness in this cohort was 32.996 ms. The complete qualified clock was
reused only while source, boot and server identity remained unchanged.

After collection, all 14,964 requests across 0076–0078 were rebuilt using the
unchanged prompt builder and verified against their exact raw bytes and hashes.
All response IDs were unique and reported usage/cost fit full reservations.
All 138,401 physics frames had already passed each race's full audit. Original
source is archived under `artifacts/two-kart-session-v1/collected-source/`.

Added 7,535 requests, 20,078,308 charged tokens and $0.812894964. Final cumulative
ledger: 94,598 requests / 320,361,620 charged tokens / $10.983352472002839, with
all 70 historical uncertainties and no pending reservation. Caps remain
$20 / 100,000 requests / 500 million tokens. The whole two-kart goal added
14,964 requests, 38,176,468 tokens and $1.834113444.

[All outcomes](0076-0078-two-kart-outcomes.json),
[summary and latency](0076-0078-two-kart-summary.json), and
[six actual native examples](0076-0078-two-kart-native-excerpts.json) are versioned.
Full recordings, raw captures, root reviews and visuals remain under ignored
`artifacts/two-kart-session-v1/`. All paid windows are closed; no further calls
are admitted by this study or by its old helper.
