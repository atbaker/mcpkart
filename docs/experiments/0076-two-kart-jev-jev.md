# 0076: two Jev-controlled karts sharing a track

The first competitive prototype completed all four registered duels. All eight
kart attempts finished; seven were clean and one needed a rescue. Actual model
races included ten contact events and seven recorded lead changes. The closest
finish was 0.63 s. This establishes a working two-kart experience on the existing
stadium family, with independent model-selected controls and physical interaction.

| Start | Red finish | Blue finish | Rescues, red/blue | Contacts | Lead changes |
|---|---:|---:|---:|---:|---:|
| Standard, side by side | 87.92 s | 93.68 s | 0 / 1 | 0 | 1 |
| Clockwise, side by side | 85.97 s | 84.42 s | 0 / 0 | 7 | 2 |
| Standard, staggered | 84.42 s | 85.05 s | 0 / 0 | 3 | 4 |
| Clockwise, reversed stagger | 85.47 s | 79.33 s | 0 / 0 | 0 | 0 |

Each attempt crossed all 120 ordered gates. Clean means zero off-road time and
zero rescues. Finishes on the same physics tick tie; both karts may finish after
the winner crosses. Lead changes are the game's credited-progress metric and
do not, by themselves, establish intentional overtaking.

## What changed

One process-isolated Python clock now advances both karts at 60 Hz. Each driver
has its own capability, observation, command sequence and inference loop. One
POST per racer may be in flight, up to two globally, against one shared atomic
ledger. Inputs persist during inference. There is no common minimum response
delay, host steering, action filtering, fallback driver or response repair.

The 24 m stadium/mirror, 12 m/s speed ceiling, .12 rad wheel range, three laps
and fifteen physical native inputs remain. New radius-1 m circular bodies use
swept equal-mass contact with restitution .15. Contact resolves before finite
gates and rescue. The whole footprint determines road/gate clearance. Rescues
are phased for at least one second and until separated; finished karts stop
and become non-colliding. Separation correction awards no progress.

The goal-only questions state mechanics and the competitive objective. Both
receive factual opponent position/relative velocity, body clearances and race
progress. The complete physical wheel/pedal menus remain. No passing policy,
steering threshold, braking predicate or suggested action is supplied. See the
[driver guide](../two-kart-driver.md) and [prospective registration](0076-two-kart-jev-jev-registration.json).

## Verification and accounting

All 2,472 actual queries and 21,014 saved physics frames reconstructed exactly.
Root observed each actual process exit and fully audited its raw/native replies,
facts/questions, input applications, shared budget chain and timing before the
next admission. All four timing-valid; no endpoint error or new uncertainty.
The supplemental audit also verified exact raw response bytes, globally unique
IDs and reported usage within full reservations.

Before paid driving, 572 tests passed with three optional Rust skips; Ruff and
native/concurrency checks passed. The solo core refactor matched the original
simulation at 20,000 frames across eight seeds. Four complete free dual-driver
controls and the 170.1 s neutral clock passed after the documented
[GC qualification amendment](0076-two-kart-free-gc-amendment.md). Physics advanced
21 frames during a 350 ms HTTP-parent pause. The long run's maximum lateness
was 14.708 ms, p95 1.565 ms, drift 1.333 ms, with zero cyclic collections.
The original failed long run remains preserved; limits were not relaxed.

Added 2,472 requests and $0.266525784. Cumulative boundary: 82,106 requests,
288,768,441 charged tokens, $9.415764812003035, all 70 historical uncertainties
retained and no pending reservation. User authorization raised only the dollar
ceiling to $20; 100,000 requests and 500 million tokens remain the other caps.
[Authorization](0076-two-kart-session-authorization.json).

The registration, source bytes, full captures, recordings and root reviews are
under ignored `artifacts/two-kart-session-v1/`; versioned
[outcomes](0076-0077-two-kart-outcomes.json) cover this and the paired follow-up.
This four-entry study is closed: no retries, replacements or further paid calls
are authorized by its old window. Nominal shared-track driving is established;
robust recovery, intentional race strategy and larger fields remain unproven.
