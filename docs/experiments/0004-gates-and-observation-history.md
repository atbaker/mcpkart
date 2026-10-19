# Jev: gate geometry and short observation history

October 18, 2026. Follow-up to the [compact telemetry experiment](0003-jev-navigation.md), requested by the user. This experiment is exploratory; no configuration has passed the three-lap completion/pace criterion.

## Questions

1. Does explicit required-gate geometry and a factual explanation of gate credit prevent circulating past a missed checkpoint?
2. Does a short history of observations help Jev correct growing heading and lateral-motion errors before leaving the track?

The previous compact run's first lap took 54.42 s, faster than road physics at 60.70 s. Its overall progress was worse because it stalled at two required gates. A gate centre behind the kart's nose is not sufficient evidence of a missed gate: at 66.0833 s the centre was behind the nose, but the kart was still on the approach side of its crossing plane and earned credit at 66.1333 s. At 68.15 s it was beyond a different required gate's plane without earning credit.

## Fixed controls and game rules

Keep the same track, handling, fifteen direct controls, 60 Hz real-time clock, three-second rescue to rest, original racing instructions, numeric control descriptions and pinned Jev/TypeSafe route. The paired reference remains 56.7 s for seed zero; the deadline remains 170.1 s. The existing $10 budget ledger is shared and never reset.

The simulator only credits the next required gate when motion crosses its plane from signed distance <=0 to >0, within the finite lateral gate span. Reverse crossings, other gates and rescue teleports do not grant credit. Missing a gate does not change which gate is required. The new observations explain these existing rules without selecting a control or changing the rules.

## Profiles and memory

| Profile | Difference |
| --- | --- |
| `road_physics` | Existing strongest observed configuration; control. |
| `road_navigation` | Road physics plus explicit required-gate range, bearing, gate orientation, signed position relative to its plane and lateral span, and crossing rules. |
| `road_history` | Road navigation plus at most three prior driver observations from the preceding second, and an observed checkpoint-progress clock. |
| `compact` | Prior compact profile; separate control for its gate-information ablation. |
| `compact_navigation` | Compact plus the same explicit gate facts; clarify magnitude-plus-side fields versus signed numeric fields. |

Recent history contains past observed pose, speed, lateral velocity, wheel/yaw state, held input and credited progress. It contains no predicted outcome, racing line, recommended action, target speed or target steering. Samples retain their actual observation times and never include future state. No continuous sample stream is supplied that the live driver could not observe.

Rescue clears recent motion history. The checkpoint-progress clock continues through rescue because neither race time nor checkpoint credit resets. Credit timestamps are labelled as when the driver observed an increased count, not the exact crossing time. Starting memory in the middle of a recording does not invent earlier credit timestamps. New race identities or rewound state clear tracking.

## Protocol

Compare the five profiles with three interleaved repetitions over eight fixed situations: first bend, early recorded left/right correction, a left-to-right transition, a valid gate approach whose centre lies behind the nose, the following gate-credit observation, and early/later observations of a missed gate. Include source hashes, exact replay validation and history provenance. Gate cases are selected using crossing geometry, not a controller's preferred action. Do not expose fixture names, reference controls or diagnostic labels to the model.

This plans 120 static calls. Historical contexts use actual preceding driver request observations reconstructed from original applied commands and validated against runtime samples. Scripted contexts use an explicitly recorded twelve-tick observation cadence; independent fixture targets do not become invented prior driver observations. Synthetic situations have no invented past. Retain all responses, errors, exact payloads, action distributions, costs and latency.

Check that gate information does not provoke a turn-back response in the valid off-axis approach. Check both left and right drift to catch one-sided regressions. Fixed-delay short rollouts remain diagnostics; they cannot establish full missed-gate recovery or closed-loop viability.

Then run at most two separately recorded exploratory live screens at seed zero if the static results and remaining budget support them. Prefer a candidate that improves correction without worsening the opposite direction or confusing valid gate approaches. If static effects are inconclusive, `road_navigation` is the simpler direct test of the gate-information hypothesis. Record completion, ordered checkpoints, lap times, gate stalls, off-road time, rescues, observation age, model latency and independent clock validity. Do not change source during a live screen, run CPU-heavy analysis alongside it, or promote a profile merely for a faster first lap.

## Results

Starting persistent budget charge: $0.532133326 of $10, with no reservations pending.

### Static probes

All 120 calls returned admissible choices, with no request errors. Each profile has 24 calls: eight situations repeated three times in interleaved order. Saved at `artifacts/jev-gates-history-probes-v1/`, including exact payloads and responses.

The navigation-record selectors chose the first valid behind-nose approach at tick 223 (3.7167 s), and the first actual driver observation after its credit at tick 237 (3.95 s). The missed-gate targets are ticks 4089 (68.15 s) and 4211 (70.1833 s), 2.0333 s apart with the same required gate. These were selected by fixed geometric rules, not by action quality. All target and preceding history states were replayed and validated against original runtime samples. The earlier 66.0833 s example explains the distinction but is not hand-picked as the paid fixture.

| Situation | Road physics | Road navigation | Road history |
| --- | --- | --- | --- |
| First bend | Left accelerate 3/3 | Hard-left brake 2/3, left brake 1/3 | Left coast 3/3 |
| Early left drift | Left accelerate 3/3 | Left accelerate 3/3 | Left accelerate 3/3 |
| Early right drift | Left accelerate 3/3 | Left accelerate 3/3 | Left accelerate 3/3 |
| Left-to-right transition | Hard-right brake 2/3, straight accelerate 1/3 | Hard-right brake 3/3 | Straight accelerate 3/3 |
| Valid behind-nose approach | Left accelerate 3/3 | Straight accelerate 3/3 | Straight accelerate 3/3 |
| After gate credit | Left accelerate 3/3 | Left accelerate 3/3 | Left accelerate 3/3 |
| Early missed gate | Hard-right brake 3/3 | Hard-right brake 3/3 | Hard-right brake 3/3 |
| Later missed gate | Hard-left brake 3/3 | Hard-left brake 2/3, hard-right brake 1/3 | Hard-right brake 3/3 |

Compact and compact-navigation both retained hard-left braking at the first bend, failed early left correction, and selected left acceleration after gate credit. Navigation changed the valid approach from left acceleration to straight acceleration in all repeats. At the transition it changed compact's hard-right brake 3/3 to hard-right brake once and straight acceleration twice. All profiles braked at the early missed gate, and the compact profiles had the same mixed later-gate brake choices (hard-right twice, hard-left once).

The added facts change behavior but do not solve the left-drift failure. History provides no general advantage in these snapshots. Gate cases have no unique correct action; a selected brake or steering direction alone cannot prove recovery. All three navigation variants selected straight acceleration in all three valid behind-nose approach repetitions. Median API latency ranged from 179 to 187 ms across profiles; short samples and network variation do not establish a model-compute difference.

The static batch cost $0.012116412. Before live screening, the shared ledger charged $0.544249738, with no pending reservations.

### Live screen

Choose `road_navigation` with original instructions and numeric controls first. Its repeated early braking and preserved right-drift correction make it a simpler live candidate than history, which changed the transition to acceleration. Early left correction is explicitly still unresolved.

The first seed-zero screen, `artifacts/jev-road-navigation-live-v1/`, reached 98/120 checkpoints and two laps (64.48 s and 67.42 s), with 25 rescues and 75.00 s off-road before the 170.1 s deadline. It made 901 requests with zero request errors. Median API latency was 164.58 ms and median observation-to-application age 183.13 ms. Its longest interval between credited gates was 6.83 s; no on-road request had the kart beyond the next required gate plane (0/505). This screen did not exhibit the compact profile's long gate stalls. The earlier road-physics run also avoided those stalls, so this is not proof that the new gate facts caused an improvement.

**The first screen is timing-invalid.** Maximum physics lateness reached 163.00 ms at race time 57.03 s, above the unchanged 100 ms limit, with another burst reaching 121.59 ms at 156.43 s. p95 lateness was 1.30 ms and final drift 1.36 ms. These measurements identify scheduling delays without establishing their cause. Keep the full run as diagnostic evidence; do not count it as a valid realtime success or a clean comparison with the earlier valid 108-checkpoint road-physics result.

The second planned live slot repeats the same profile, instructions, numeric controls, pinned route, seed, physics and reference in `artifacts/jev-road-navigation-live-repeat-v1/`. It is a timing repeat, not a switch to history. Both recordings remain preserved.

| Metric | First screen | Exact-configuration repeat |
| --- | ---: | ---: |
| Ordered checkpoints | 98/120 | 99/120 |
| Completed laps | 2 | 2 |
| Lap times | 64.48 / 67.42 s | 68.45 / 68.12 s |
| Off-road time | 75.00 s | 72.32 s |
| Rescues | 25 | 24 |
| Requests / API errors | 901 / 0 | 780 / 0 |
| Median API latency | 164.58 ms | 176.93 ms |
| Median observation age at application | 183.13 ms | 199.23 ms |
| Longest credited-gate interval | 6.83 s | 6.22 s |
| On-road observations beyond required gate plane | 0/505 | 0/447 |
| Maximum physics lateness | 163.00 ms | 221.36 ms |
| p95 physics lateness | 1.30 ms | 1.50 ms |
| Realtime-valid | no | no |
| Model cost | $0.091170366 | $0.079319898 |

The repeat also missed the deadline and failed clock validity. Its longest scheduling burst affected ticks 1015–1029 (race time 16.9167–17.15 s), peaking at tick 1021. Twenty-six physics steps exceeded 100 ms across five bursts. Final world/wall drift remained 1.24 ms; catching up later does not remove a timing violation. Neither screen counts as valid realtime evidence or establishes a performance ranking. The prior valid road-physics result remains the default candidate; no new profile is promoted.

Both diagnostic trajectories avoid the compact run's prolonged gate stalls. Steering correction remains unresolved in the repeated frozen cases and frequent rescues persist in the live trajectories. In the repeat, 59/82 on-road observations with offset >1 m and nose >15 degrees toward the same side (speed >2 m/s) selected steering toward that side again. This describes coordination behavior, not a unique correct-action label for curved roads.

The 120 static calls and two model screens cost $0.182606676. The persistent budget now conservatively charges **$0.714740002 of $10**, with no pending reservations ($0.665719074 provider-reported total).

### Timing investigation

Further paid screens are held while collecting local timing evidence. The active-race replay guard already prevents archive scans and parsing, and the live state payload is bounded. Remaining source candidates include allocation/garbage-collection pauses and state timing-statistic work; neither is established as the cause by the existing recordings. Add bounded in-memory GC/slow-span/late-wake CPU diagnostics, then run a free scripted reference. Do not change physics, GC policy, checkpoint behavior, or timing limits simply to turn invalid recordings into passes.

Timing diagnostics now record GC generation/duration, slow physics/sample/state/JSON spans, and CPU time between late wakes. Each event list is bounded to 64 entries, with lifetime counters/maxima retained. The live viewer receives aggregate summaries; full bounded events are saved in trial results. Hooks are removed at every termination path, including cancellation before the task begins. GC policy is unchanged.

After restarting the instrumented server, the free control at `artifacts/timing-diagnostics-reference-v1/scripted-live.json` completed all 120 gates in 57.00 s with no off-road time or rescue, but was also **timing-invalid**: max lateness 111.51 ms, p95 1.24 ms, drift 1.21 ms. No model requests were made. The worst delayed wake followed a 125.82 ms wall gap with only 0.57 ms of server-process CPU time. A separate generation-two GC event used 39.62 ms CPU / 40.27 ms wall time. Thus GC can cause smaller delays, but busy server computation is not supported as the cause of that worst gap. Descheduling, timer behavior or unmeasured blocking remain possible; this does not identify a host-level cause yet.

The next free scripted control ran with an independent low-CPU 60 Hz heartbeat process. Its absolute monotonic timestamps can be compared with the server's late-wake gaps. The heartbeat buffers observations in memory and writes its ignored artifact after the race. Both controls use the same instrumented source and unchanged clock limits. This is an extension of local timing diagnosis, not another paid model screen or a change to the driving comparison.

That control (`artifacts/timing-diagnostics-reference-heartbeat-v1/scripted-live.json`) completed all gates in 56.67 s with no off-road time/rescue, but was also invalid: 219.35 ms maximum lateness, 1.16 ms p95, 1.23 ms drift. GC never exceeded 1.69 ms. The server's worst wake followed a 232.75 ms wall gap with 6.56 ms process CPU. During that same interval the independent heartbeat continued waking; its largest gap was 44.39 ms and its maximum lateness during the race was 40.85 ms. Thus the evidence does not support a uniform whole-host freeze or heavy server GC as the explanation for this incident. Process/thread-specific scheduling, timer behavior or blocking remain possible. Full aligned samples and the derived comparison are preserved in `artifacts/timing-host-heartbeat-v1.json` and `artifacts/timing-heartbeat-comparison-v1.json`.

An opt-in in-server watchdog now samples the event-loop thread's stack during a long wake gap, without capturing locals. It buffers bounded records and changes no timing/GC/physics policy. Enable it with `mcpkart-web --watchdog`; it is off by default. These timing controls do not add model spending.

The watchdog control at `artifacts/timing-watchdog-reference-v1/scripted-live.json` completed all gates in 56.63 s, with no off-road time/rescue, but again failed timing: max lateness 209.91 ms, p95 1.53 ms, final drift 1.22 ms. The watchdog took 3,077 samples and retained eight stalled-physics stack samples. Its own longest sampling gap was 140.48 ms with only 9.89 ms process CPU. Captured stacks vary across a GC callback, selector waits, timer processing and small HTTP callbacks. They do not establish one consistently blocking CPU hotspot. The watchdog also needs the GIL, so gaps can reflect process/thread scheduling or native GIL blockage; this evidence does not uniquely identify the underlying cause.

All three scripted controls complete the course without rescue while violating the unchanged maximum-lateness rule. None is promoted as valid realtime evidence. Keep all failed controls and model screens. Frozen-state Jev correction failures and model-free clock failures are independently observable; more model spending would currently mix these problems. No physics rewrite or GC-policy change is justified by the captured worst-gap evidence alone. A future focused infrastructure experiment should isolate the physics clock from the HTTP event loop and compare free controls before resuming paid driving. That isolation is proposed, not implemented or validated here.

Validation: 220 passing tests and a clean Ruff check, covering observation history, gate geometry, replay provenance, bounded diagnostics, watchdog stack capture and hook/thread cleanup. Final shared model budget remains $0.714740002, with no pending reservations. The local development server is left running with the opt-in watchdog enabled for inspection; all races and diagnostic helpers have finished.
