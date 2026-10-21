# Stadium width comparison

The wider stadium reduced rescues in this three-start comparison. At 24 m,
Jev needed **2, 1 and 0 rescues**, versus **3, 4 and 7** at 16 m. The zero-rescue
attempt also spent no time on grass. At 32 m, rescues were **2, 1 and 1**, with
the fastest median time. All nine attempts finished within twice their paired
references. Use **24 m provisionally for the next prompt comparison**: it offers
more tolerance and produced a clean attempt, while retaining narrower bend
limits than 32 m. Three starts do not establish reliable clean driving.

Status: complete, October 19, 2026. The user accepts a stadium as the initial
driving target and requested more room for steering errors and future racers.
This comparison changes full road width while holding the kart, handling,
observation format and question preset fixed.

Earlier oval pilots widened the road from 9 to 16 m at the same 8 m/s speed and
0.32 rad wheel range: 32 versus 29 rescues, in 223.60 versus 211.43 s. This is
weak single-start evidence; the narrow attempt had an endpoint timeout. All
previous stadium attempts used 16 m. See the [league results](0011-jev-speed-classes.md)
and [prompt comparison](0012-jev-prompting.md).

## Results

Every row uses the same Python runtime, kart, 12 m/s speed ceiling, 0.12 rad
wheel range, `road_navigation` observations, geometry menu and `damped` preset.
All three-lap finishes passed timing and independent exact replay, with no
endpoint errors. Model decisions are not deterministically seeded.

| Full width | Finishes | Rescue-free finishes | Rescues by start 0/1/2 | Total rescues | Median time | Median reference ratio |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| 16 m | 3/3 | 0/3 | 3 / 4 / 7 | 14 | 109.98 s | 1.42× |
| 24 m | 3/3 | 1/3 | 2 / 1 / 0 | 3 | 102.48 s | 1.33× |
| 32 m | 3/3 | 0/3 | 2 / 1 / 1 | 4 | 92.92 s | 1.20× |

Median rescues were four, one and one. Median grass time was 12, 3 and 3 seconds.
Both wider settings used fewer rescues than 16 m in every paired initial pose.
Speed did not improve uniformly: at start zero, 24 m was slower than 16 m;
at start two, 32 m was slightly slower. There is no established monotonic benefit
from increasing width further. The 24 m recommendation follows these observed
results and is a development choice, not a preregistered qualification winner.

| Full width | Start | Three-lap time | Rescues | Grass time |
| --- | ---: | ---: | ---: | ---: |
| 16 m | 0 | 118.00 s | 3 | 9 s |
| 16 m | 1 | 109.98 s | 4 | 12 s |
| 16 m | 2 | 108.72 s | 7 | 21 s |
| 24 m | 0 | 125.80 s | 2 | 6 s |
| 24 m | 1 | 78.95 s | 1 | 3 s |
| 24 m | 2 | 102.48 s | 0 | 0 s |
| 32 m | 0 | 86.72 s | 2 | 6 s |
| 32 m | 1 | 92.92 s | 1 | 3 s |
| 32 m | 2 | 109.20 s | 1 | 3 s |

The longest gap between checkpoints was 6.37 s; no previous-style prolonged
missed-gate stall appeared. Every grass excursion in these attempts lasted until
rescue: total grass time is exactly three seconds per rescue, within floating
point rounding. Added room prevents some departures; reliable recovery and
clean navigation remain open. These starts all use the same counterclockwise
stadium; clockwise generalization and traffic are untested.

The paid phase used **3,325 calls**, all returned as
`typesafe/jev-1.14-20261014` / `TypeSafe`. All **3,298 accepted commands** were
attributed to their native direct-control replies. The remaining replies did
not become accepted commands, for example after rescue or race completion.
Worst paid clock lateness was 61.495879 ms, within the fixed timing limits.
The audit confirms the only physical configuration change was road width.

New charges: **$0.406448826**, 10,228,188 charged tokens and no new uncertain
requests. Final shared ledger: **46,751/50,000 requests**,
**$5.847136600/$10**, 201,522,321/250,000,000 charged tokens, 69 historical
uncertain requests and no pending reservations. Its limits and prior charges
are unchanged; the versioned budget snapshot matches the live ledger.

The nine offline references finished without grass or rescues. For every width,
reference times for starts 0/1/2 were 77.2833 / 77.2667 / 77.1833 s. All three
free live controls finished start zero in 77.2833 s without grass or rescues;
worst free live lateness was 35.669976 ms. The existing complete clock gate and
349-test source validation remain applicable: this phase changes configuration
and evidence files, with no runtime source changes. No Rust was used.

Evidence includes `final-audit.json`, `report/driving-results.csv` and `.json`,
and `report/width-trajectories.png` / `.pdf` under `artifacts/jev-widths-v1/`.
The figure uses the same world scale in all three panels, shows every attempt,
and breaks trajectory lines at rescues. The owned server and all trials are
stopped after collection.

## Frozen comparison

- Stadium centreline: two 60 m straights joined by radius-30 m semicircles.
- Full road widths: 16, 24 and 32 m. Kart and centreline dimensions stay fixed.
- Python process runtime, asyncio pacing, continuous 60 Hz physics.
- Speed ceiling 12 m/s; maximum absolute wheel angle 0.12 rad.
- `road_navigation` observations, `geometry` controls, `damped` instructions;
  the model still chooses among all 15 direct steering/pedal inputs.
- Three laps, 40 ordered gates per lap, existing three-second off-road rescue,
  stale reply rejection and a deadline of three paired reference durations.
- Starting poses 0, 1 and 2 at each width, ordered 16/24/32, 24/32/16 and
  32/16/24 respectively. No prompt or handling changes between attempts.
- Retain failures. Investigate any endpoint or timing error before continuing.
  Jev is not seeded; these are three paired initial poses, not deterministic
  paired model responses or ten-start qualification.

The shared ledger starts at 43,426/50,000 requests, $5.440687774/$10 and
191,294,133/250,000,000 charged tokens, with 69 uncertain requests and no pending
reservations. No limit is raised. Do not start another race with fewer than
1,000 request slots or 18 million charged-token slots remaining.

Source fingerprint is
`588958f4c0bd594064b55c24cc9b678a4a41448c7334592521bb91bfa2130e6c`.
The complete free clock gate already passed on this unchanged source and the
same running environment. Its verification predates this phase and follows
the current machine boot. Each new width also gets a zero-delay offline
reference for every tested starting pose and a free live scripted control.
The freshly discovered route retains `typesafe/jev-1.14-20261014`, provider
`TypeSafe`, and the previous prices. The requested public alias remains
`typesafe/jev-1.14`; actual responses must match the recorded model/provider.

Raw evidence and frozen helpers: `artifacts/jev-widths-v1/`. The protocol stores
helper hashes, setup declarations, route, clock-gate reference and starting
budget. All calls use the same shared `artifacts/budget.json`.

## What width changes

Width controls the grass/rescue boundary, finite checkpoint span and reported
edge clearances together. This is a comparison of complete wider-road rules,
not an isolated change to tyre dynamics. Inner bend radii are 22, 18 and 14 m;
the widest setup also permits tighter inside lines. Compare finishes,
checkpoint stalls, off-road time and rescues together.

Boundary checks currently use the kart's position as a point. The handling has
a 1.8 m wheelbase but no physical body width or kart collisions. The spectator
artwork is approximately 3.6 m across its wheels; that is a visual scale rather
than a collision clearance. Future passing tests need a defined kart footprint
and traffic/collision rules before a road width can be validated for multiplayer.
