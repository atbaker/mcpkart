# Track telemetry iteration

October 18, 2026. Requested by the user after observing poor anticipation of curves. First telemetry iterations are complete; Jev remains short of the three-lap target.

Keep the existing track, handling, 15 direct controls, continuous 60 Hz clock, three-second rescue, provider routes, and racing instructions fixed. Change only the evidence presented to the model. Preserve earlier recordings under `artifacts/rescue-v1/`; use new output directories for this experiment.

## Motivation from the recordings

The first rescued driving screen did not complete three laps with any of the three routes. Jev and Clef reached only 12 of 120 required checkpoints, despite travelling around the circuit repeatedly. Luna stopped after consecutive provider refusals. Clef also exceeded the simulation's 100 ms maximum scheduling-lateness limit (115 ms), so its run is infrastructure-invalid. These are exploratory single runs, not ten-run model rankings.

An audit found no steering-sign or coordinate-transform bug. Jev selected acceleration for all 337 on-road decisions and never braked while on-road. It entered a roughly 20 m radius bend at 24 m/s. Luna sometimes turned away from the nearby road even when the heading and offset implied the opposite correction.

The original observation requires converting radians and curvature into intuitive bend shape while distinguishing kart-relative geometry from road-relative geometry. Its nine samples can also miss narrow curvature peaks: a 3.8 m radius right bend around road position 87.9 m can fall between preview samples. This motivates testing both clearer presentation and denser geometry summaries. It does not prove that formatting explains the driving failures.

## Candidate representations

| Profile | Evidence |
| --- | --- |
| `raw` | Existing world position/heading, signed offset and heading error in radians, nine ego-frame centreline points and curvature values, handling, checkpoint and rescue state. |
| `road` | Explicit left/right offset and edge clearances; road/kart alignment in degrees; ego-frame velocity; preview tangent change from the current road tangent; bend direction and radius; dense summaries of the next three bend regions. |
| `road_text` | The same road facts as `road`, expressed as a compact prose report inside structured state. |
| `road_physics` | `road` plus the lateral acceleration required at the current speed, its ratio to current surface grip, and the grip-limited minimum steady turn radius. |
| `kart_physics` | A later Jev-only candidate: `road_physics` plus explicit kart nose/velocity alignment relative to the current road and a factual steering curvature/radius table. |

All distances ahead mean arc length along the centreline from its nearest projection, not Euclidean distance forward from the kart. Dense summaries use at most 1 m spacing plus every published centreline vertex through a 60 m horizon. Regions with absolute curvature at most 0.004 radians/metre are grouped as straight. Summaries retain direction, start/end, total heading change, and minimum radius/location, and declare any truncation to three regions.

No candidate selects controls, supplies a recommended speed or braking point, or computes a racing line. Physics-derived telemetry is explicitly a richer observation than the raw version. It describes steady-state grip only; transient steering and yaw response still matter.

## Protocol

1. Build a fixed collection of reference-driver snapshots around approaching and alternating bends, plus saved model failure states. Use identical states across variants and routes. Keep reference actions outside the model's evidence.
2. Alternate variant/request ordering and retain exact inputs, selected controls, errors, response identities, payload sizes, latency, and cost. Static reference-action agreement and short held-action effects are diagnostics, not unique correct-answer labels or proof of closed-loop control.
3. Choose a common candidate for a separately labelled live screen through the existing MCP server. Measure ordered checkpoint progress, off-road time, rescues, completion, observation age at application, and simulation validity. Keep failures and original results.
4. A promising screen justifies further paired trials. One screen does not establish the approved eight-of-ten target or isolate representation effects from changing network latency and sampling variance.

Geometry tests cover coordinate rotation/translation, signs, dense curvature peaks, no input mutation, physical scaling, and JSON compatibility. The persistent $10 budget ledger applies across these iterations.

## Paired probe results

All 120 requests returned valid choices: ten fixed situations × four profiles × three routes. Exact redacted request/response bodies and the frozen manifest are in `artifacts/telemetry-probes-v1/`. This pilot cost $0.01125 in reported usage. Each cell below has ten observations, including a cold connection request; these medians do not characterize tail latency.

| Route | Raw median request | Road | Road text | Road physics |
| --- | ---: | ---: | ---: | ---: |
| Jev | 179 ms | 189 ms | 168 ms | 182 ms |
| Luna | 212 ms | 210 ms | 281 ms | 219 ms |
| Clef | 432 ms | 445 ms | 432 ms | 470 ms |

At the first fast bend approach, all three raw-profile choices accelerated. All three `road_physics` choices braked and turned left. The three physics choices left about 4.06–4.08 m minimum road margin in the fixed short rollout, compared with 3.61–3.91 m for raw choices. This is a useful braking signal, not evidence of sustained successful driving. The saved near-departure failure states still went off-road under every variant; the fixed 200 ms delay put them too close to departure for this diagnostic to establish recovery.

There is no unambiguous winning profile. Steering choices and reference-action agreement sometimes worsened, and richer geometry sometimes encouraged a premature turn. Median short-rollout road margins improved slightly with `road_physics` across all three routes. Select it as a common candidate for the next live screen because of that signal and the consistent early braking, rather than optimizing each model separately.

Across the thirty situation/route pairs, braking choices rose from 0 with raw evidence to 9 with road, 16 with road text, and 22 with road physics. However, each profile still produced six short-rollout departures and the same summed off-road time (1.65 s). Physics telemetry reduced projected forward progress by about 27%. Its increased road margin is therefore partly a consequence of slowing down. Luna also selected right steering with physics telemetry on both recorded left-bend departure states, a directional regression. Treat these as evidence that presentation changes behavior, not proof of better steering.

The exact request sizes remained below the existing 8,192-byte conservative input guard, including framing allowance. Geometry profiles also add dense summaries, so raw versus road is not a pure formatting comparison; `road` versus `road_text` is the closer structured-versus-prose comparison.

## Live screen

Recorded under `artifacts/telemetry-physics-v1/`, using the same saved routes as the raw screen. Jev ran first, then Luna. The user narrowed the initial PoC to Jev during Clef's run, so Clef was stopped and its partial recording preserved. It also exceeded the local timing limit and cannot count as valid realtime evidence. No further paid calls to Luna or Clef are planned for the initial PoC. This single-run screen tests a promising observation profile; it is not the approved ten-run qualification batch.

| Route/profile | Credited checkpoints / 120 | Completed laps | Elapsed | Off-road time | Rescues | Median action age | Realtime valid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Jev/raw | 12 | 0 | 170.1 s | 102.1 s | 31 | 199 ms | Yes |
| Jev/road physics | 108 | 2 | 170.1 s | 78.0 s | 26 | 184 ms | Yes |
| Luna/raw | 15 | 0 | 26.7 s | 12.9 s | 3 | 232 ms | Yes |
| Luna/road physics | 65 | 1 | 170.1 s | 69.2 s | 21 | 233 ms | Yes |

Both Jev screens reached the 170.1 s deadline. The enriched observation produced substantially more credited progress and less off-road time, but still failed to finish three laps. It completed laps in 60.7 s and 70.1 s, versus about 18.9 s per lap for the scripted reference. Frequent rescues remain necessary. Network latency also differed between runs; this single paired seed cannot assign the entire difference to telemetry.

Luna's raw screen terminated at 26.7 s after three consecutive provider refusals (13 refusals in 112 requests). The enriched screen ran to the 170.1 s deadline, with five refusals in 590 requests. Its larger progress total therefore does not constitute a like-duration comparison, and changed refusal behavior cannot be attributed to formatting from a single run.

## Jev steering coordination iteration

Jev's first on-road brake moved from never in the raw screen to 1.75 s into the enriched run (16.79 m/s, road position 13.21 m). On-road braking choices increased from 0/337 to 98/433. Its first departure changed from running wide through the right edge at high speed to oversteering through the left edge at lower speed. At 3.72 s it still chose left acceleration while 3.80 m left of centre and pointing 41.4° left of the road. Braking remained applied for 60.4 s in total, including 38.0 s below 1 m/s; repeated stopping and delayed release cost time.

The `kart_physics` candidate makes the kart's current pose relative to the road explicit, separate from upcoming bend direction, and exposes nominal steering curvature/radius as vehicle facts. The five steering settings map to wheel angles and bicycle-model curvature `tan(angle)/wheelbase`; actual motion remains constrained by grip and response delays. Current wheel, road, and body-yaw curvatures are labelled separately. It supplies no control recommendation.

The second static probe batch compares only Jev with `road_physics` and `kart_physics`. It reuses ten frozen states and adds left/right inside-oversteer cases at ticks 212 and 503, exactly reconstructed from the recorded commands and original rescue policy. Both reconstructed states match saved road telemetry and runtime pose/velocity samples with zero differences. Fixtures, provenance, and labels remain outside the model's evidence except for the actual factual observation. Record this batch under `artifacts/jev-steering-probes-v1/`.

Before further timed trials, replay decoding/encoding was moved outside active physics. Admission waits for any in-flight archive work, prepares sanitized replay bytes before starting the clock, and prevents new catalog parsing during the race. Cached saved replays remain playable. Current-trial downloads wait until the race ends. Concurrent admission and replay tests cover the boundary. Earlier timing-invalid evidence remains invalid; the limit is unchanged.

All 24 Jev-only probe requests succeeded, costing $0.00256. The additional kart-alignment profile did not fix the recorded left-oversteer correction: both profiles again selected left acceleration. Both selected left acceleration in the right-oversteer case, where that direction provides a correction. Median short-rollout road margins were identical (2.718 m); median requests were 194 ms with road physics and 217 ms with kart physics across twelve states each. The richer profile has no demonstrated advantage and is not promoted to the live candidate. Retain `road_physics` as the strongest observed Jev candidate, with all its failed completion and rescue results intact.

An identical Jev first-bend request selected hard-left braking in the first probe batch and left acceleration in the second. Single-call fixture results are not repeatability estimates; further profile selection should include repeated samples before drawing strong conclusions.

The first post-isolation scripted control check completed all three laps in 56.72 s without leaving the road or using rescue, while a cached Jev replay was opened and played. However, maximum physics lateness reached 153.77 ms at race time 47.28 s, exceeding the unchanged 100 ms limit. Preserve this infrastructure-invalid run at `artifacts/archive-isolation-reference/`. Removing replay JSON work does not establish that every scheduling pause has been resolved.

A free repeat completed three laps in 56.73 s with no off-road time or rescues. Maximum physics lateness was 50.93 ms, p95 1.11 ms, and world/wall drift 1.20 ms; it passed the unchanged realtime limits. Preserve it at `artifacts/archive-isolation-reference-repeat/`, alongside the failed first check. No further paid model calls followed the Jev-only static probes.

There are 112 passing tests and a clean Ruff check. The shared ledger charges $0.46576 against the $10 cap ($0.41674 provider-reported usage; the difference is conservative charging for uncertain requests), with no pending reservations. Benchmark/probe defaults now select Jev; paid driving defaults to `road_physics`. No candidate has demonstrated the required three-lap completion/pace or eight-of-ten pass. Further Jev work should address steering correction and braking release, with repeated fixture samples and independent timing validity checks before a larger batch.
