# Isolate the physics clock, then repeat Jev

October 18, 2026. The user requested a separate physics clock, free scripted controls, and a return to Jev only after timing is reliable. The preceding [timing investigation](0004-gates-and-observation-history.md) reproduced maximum-lateness violations without a model and did not identify one HTTP-loop hotspot.

## Implementation and invariants

Each race gets a fresh Python worker process with a minimal `mcpkart.physics_worker` entrypoint. The HTTP/MCP process handles transport and spectator requests. The child owns the existing 60 Hz simulation loop, control queue, observation capture, command application, rescue rules and recording. It does not import FastMCP, Starlette or Uvicorn. Worker initialization precedes the race epoch.

Private IPC carries reliable command replies and coalesced spectator snapshots. Dedicated readers and writers keep pipe backpressure outside the physics event loop. Active messages are bounded; the full recording transfers only after physics stops. The web process reports the age of cached spectator state, while MCP observations come directly from the child. Capture, queue and application timestamps remain the child's actual monotonic timestamps. A delayed parent does not advance, reset or restamp them.

The process backend is the server default. `--clock-backend event_loop` retains the original backend for explicit diagnostics. Runtime identity and process provenance are saved with trials; resuming an older or differently configured comparison is refused. Worker failure ends the attempt and preserves available request evidence as an incomplete recording. It does not restart the kart or silently continue a paid comparison.

Track, handling, 15 controls, three laps, rescue behavior, reference and timing limits are unchanged. Validity still requires maximum lateness at most 100 ms, p95 lateness at most 25 ms, and absolute final world/wall drift at most 100 ms. Catching up after a delay does not erase a violation.

## Declared validation protocol

Freeze implementation source before live trials. Run `scripts/validate_clock.py` against the process backend with the paired `artifacts/rescue-reference.json`. It runs three consecutive free scripted three-lap races through the real HTTP MCP endpoint, with an additional spectator polling state about 20 times per second. Preserve every attempt and stop at the first failed control. Each must finish all 120 ordered gates and satisfy the existing timing limits under the same source fingerprint.

During control two, at approximately 20 race seconds, the harness sends SIGSTOP to the verified local HTTP parent PID for 350 ms, then always sends SIGCONT. It never signals the physics child or process group. This pauses the entire parent, including IPC readers, rather than only one coroutine. Require at least twelve child samples whose actual capture timestamps fall inside that interval, distinguishing continuing simulation from later catch-up. Preserve any effect of delayed controls on driving; no compensating steering, braking or clock adjustment is added.

Record race duration, off-road time, rescues, lateness distribution, drift, observation age at application, worker provenance and the fault interval. Save an aggregate validation report and the exact harness hash. Unit/integration checks also cover timestamp ordering and replay, blocked parent loop and reader, worker death, stale race commands, rescue guards, admission/cleanup races and MCP transport.

Only after all three controls pass, run a fresh seed-zero Jev screen with the prior valid candidate: `road_physics`, original instructions, numeric control descriptions and the pinned TypeSafe route. Keep the 170.1 s deadline (three times the 56.7 s offline reference). This is one exploratory screen under the new runtime, not an eight-of-ten qualification or a clean latency comparison with the old process architecture.

Starting persistent model budget: **$0.714740002 of $10**, with no pending reservations. Scripted controls make no model requests.

## Results

### Free controls

All three consecutive controls passed under one source fingerprint. Each completed 120 gates and three laps, with zero off-road time and zero rescues. Saved evidence is in `artifacts/process-clock-validation-v1/`: `validation.json`, each full MCP trial, logs, and `replay-analysis.json`.

| Metric | Control 1 | Control 2, parent paused | Control 3 |
| --- | ---: | ---: | ---: |
| Race duration | 56.683 s | 56.833 s | 56.700 s |
| Maximum physics lateness | 9.96 ms | 7.06 ms | 3.24 ms |
| p95 physics lateness | 2.09 ms | 2.09 ms | 2.09 ms |
| Final world/wall drift | 2.24 ms | 2.20 ms | 2.27 ms |
| Median observation age at application | 16.61 ms | 16.62 ms | 16.61 ms |
| Maximum observation age at application | 50.56 ms | 383.66 ms | 50.08 ms |
| Median queue-to-application delay | 11.00 ms | 11.06 ms | 11.02 ms |
| Realtime-valid | yes | yes | yes |

The declared 350 ms pause lasted 360.12 ms at approximately 20.05 race seconds. The child recorded **22 actual physics samples inside that interval**, with maximum lateness 3.40 ms during the pause. The large observation-age maximum in that control preserves the transport interruption; the kart continued holding its last input. This separates clock continuity from control freshness. No missed ticks, epoch adjustment or compensating action was used.

The extra spectator made 3,026 successful polls with no errors. Its longest round trip was 316.68 ms during the injected interruption. Each race used a different child PID, initialized before its clock epoch, and reported no loaded HTTP/MCP framework modules. After the clocks stopped, all **10,216 recorded poses** replayed exactly from the actual applied-tick controls and unchanged simulation. This validates these local controls; it does not establish production capacity or eliminate all possible host scheduling delays.

Validation before the controls: **254 passing tests**, clean Ruff check of `src`, `tests` and `scripts`, and independent review of worker lifecycle and IPC. No model spending occurred in this stage.

### Jev screen

After the reliability gate passed, the fresh seed-zero screen at `artifacts/jev-process-clock-v1/` used the existing TypeSafe route, road-physics telemetry, original instructions and numeric controls. No source changes or CPU-heavy analysis ran alongside its clock.

| Metric | Jev, process backend |
| --- | ---: |
| Ordered checkpoints | 63/120 |
| Completed laps | 1 |
| First lap | 119.717 s |
| Trial duration / deadline | 170.100 s |
| Off-road time | 71.383 s |
| Rescues | 23 |
| Requests / API errors | 749 / 0 |
| Commands discarded after rescue | 20 |
| Median / p95 API latency | 179.96 / 270.59 ms |
| Maximum API latency | 4,491.83 ms |
| Median / p95 observation age at application | 200.40 / 287.53 ms |
| Maximum observation age at application | 4,517.77 ms |
| Median / p95 MCP control round trip | 17.67 / 27.67 ms |
| Maximum physics lateness | 22.88 ms |
| p95 physics lateness | 2.40 ms |
| Final world/wall drift | 2.37 ms |
| Realtime-valid | yes |
| Three-lap completion | no |
| Model cost | $0.072393930 |

The physics clock remained valid throughout the longer model trial as well as the controls. Jev still failed to finish. This screen provides usable evidence of driving and end-to-end decision delays, without the previous clock-invalidity confound. It does not establish why this trajectory differs from the earlier 108-checkpoint road-physics screen: request timing, latency tails and the transport architecture differ, and these are individual trajectories rather than a repeated comparison. No observation profile or model is promoted from this result.

Independent replay verified all 10,207 model-run samples, including exact kart/progress/rescue/control state and final summary. All 729 accepted commands match their recorded application step and timestamp; all 20 rejected commands were based on observations preceding a rescue and were excluded from physics. All 23 reset events match replay. The model trial and all three controls share the current source fingerprint and identical track/configuration.

After this screen the persistent ledger conservatively charges **$0.787133932 of $10**, with no pending reservations ($0.738113004 provider-reported). The free controls used no model requests.

### Controlled gate-telemetry follow-up

The road-physics trajectory stalled at required gate 16 from 23.250 to 89.667 s: **66.417 s**, 323 decisions and nine rescues without a credited gate. None of the API calls in that interval exceeded one second. Reconstructing its forward crossing at 23.6399 s gives lateral position +5.0235 m, outside the gate's ±4.5 m span, so withholding credit was correct. By 25.6 s the required gate was 13.801 m behind the kart's nose. Credit finally arrived at the valid forward crossing at 89.6664 s, lateral +3.0916 m.

This is evidence of a missed-gate recovery problem independently of the long API latency tail elsewhere. It does not prove that additional telemetry will fix it. Declare one further exploratory screen using the existing `road_navigation` profile, which explicitly describes required-gate bearing, plane, span and forward crossing rules. Keep original instructions, numeric controls, seed zero, the same pinned route, reference, deadline, rescue settings and frozen implementation. Save separately at `artifacts/jev-process-navigation-v1/`. The earlier navigation screens had invalid clocks, so they do not settle this comparison. Do not promote a profile from a single trajectory or extend the batch by searching for a favorable run.

The follow-up was **timing-invalid** and stopped through MCP at 87.000 s with reason `timing_invalid`, preserving the full recording and all 382 requests. Maximum lateness was 163.74 ms, p95 1.14 ms, and final drift 7.50 ms. It had zero API errors and cost $0.038824254. Its partial trajectory reached 49/120 gates, one lap and twelve rescues; the shortened, invalid run does not establish a comparison or a gate-telemetry improvement.

There were six retained late-wake bursts, four exceeding 100 ms. The first violation was already at tick 26, about 0.544 s wall time. The worst burst covered 245.50 ms wall time but only 6.05 ms child CPU. Delays also occurred while the clock was catching up via `asyncio.sleep(0)`, so positive timer oversleep alone does not explain them. GC max was 2.57 ms, physics-step max 2.72 ms and state work max 5.06 ms. This establishes that HTTP isolation alone has not removed the intermittent timing failure. It does not uniquely identify OS scheduling, native blocking or GIL behavior.

Further paid calls are held. Declare one free 120 s stationary-kart clock diagnostic with the process backend and existing watchdog enabled. Poll fresh observations through MCP at approximately 5 Hz and record a separate 60 Hz client-process heartbeat using absolute monotonic timestamps. Keep all physics/timing rules unchanged; this tests scheduling, not driving. Buffer evidence and write it only after the child clock stops. Compare watchdog and client heartbeat timestamps with any physics gaps. Enabling the watchdog is a distinct recorded runtime configuration; its result cannot silently replace the original controls.

Apple documents [App Nap timer/priority throttling](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/AppNap.html) and [process activity assertions](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/PrioritizeWorkAtTheAppLevel.html). These make host policy a possible investigation path, not a diagnosed cause. No global power settings, priority boosts, activity assertions or timing-limit changes have been applied.

### Free child-watchdog diagnostic

The declared stationary diagnostic also reproduced a failure without inference: 120.017 s simulation time, maximum lateness **122.79 ms**, p95 1.15 ms and final drift 0.39 ms. Its full result, aligned client heartbeat and exact driver source are preserved at `artifacts/process-watchdog-clock-v1/`. GC max was 2.36 ms. The watchdog recorded 6,403 samples, retained ten stalled-physics stack samples and itself had a 116.33 ms gap with only 0.69 ms child process CPU. The separate client process had a maximum heartbeat lateness of 135.94 ms; align timestamps before inferring a shared host pause from these unrelated maxima.

Alignment shows that the child and client worst wakes ended only **0.256 ms apart**, about 4.373 s into the race. All twelve retained child inter-wake gaps of at least 40 ms overlapped a client heartbeat gap of at least 40 ms. Eight of ten retained watchdog stacks showed the main thread in `selectors.select`; the remaining two showed timing-diagnostic work. This supports a disturbance shared across independent event loops. It does not establish one continuous whole-host freeze or uniquely identify the selector, OS policy or a native wait. Watchdog timestamps precede its CPU-clock query and stack capture, so those stack locations are not exact timestamped execution traces. Exclude the client's later 119 ms gap after the child ended, when full result collection can block the client loop.

A small standalone launch probe found requested child QoS `USER_INTERACTIVE` and nice zero for both main-thread and executor-thread subprocess launches in two repetitions. That does not support a requested-QoS difference caused by launching from `asyncio.to_thread`; effective overrides and the actual long-running server's policy remain unmeasured.

Before any production scheduling change, declare one artifact-only, free 120 s A/B timer diagnostic. Both fresh Python workers load the same Foundation framework, use a shared future monotonic epoch and run identical 60 Hz asyncio heartbeats. Only one brackets measurement with Apple's scoped `NSActivityUserInitiatedAllowingIdleSystemSleep` activity. End the activity on exit. Neither arm changes priority, uses `NSActivityLatencyCritical`, or changes global power settings. Preserve both arms and require the control to reproduce a timing violation before inferring any benefit. This tests one power-management hypothesis; it does not validate the kart or establish causality from a clean pair.

The A/B pair is saved at `artifacts/mac-clock-activity-v1/run-01/`, with the exact helper and a prior 0.1 s binding smoke check preserved beside it. Both workers initialized before the common epoch, recorded 7,200 steps and exited cleanly. Both reported requested QoS `USER_INTERACTIVE`, relative priority zero and nice zero. The treatment's activity ended after measurement.

| Minimal-clock metric | Framework-loaded control | Scoped activity |
| --- | ---: | ---: |
| Maximum lateness | 122.41 ms | 105.82 ms |
| p95 lateness | 1.27 ms | 1.27 ms |
| Steps over 100 ms | 4 | 2 |
| Maximum wake gap | 138.00 ms | 122.16 ms |
| Maximum CPU-clock query duration | 0.76 ms | 2.35 ms |

Both worst wakes occurred at tick 1,969. The scoped activity did not keep timing within the existing limit. A single pair does not establish a general effect size or diagnose App Nap; no production activity hint is added. No CPU-clock query exceeded 5 ms in either minimal worker, so the observed minimal-clock violations do not require a long CPU-clock query. The local AC-power configuration also reports low-power mode disabled; this does not rule out other scheduling policies.

Declare one final free 120 s minimal-clock comparison, preserving the previous helper and evidence. Two new workers load identical framework paths, create no activity assertions and share an epoch. Compare the asyncio timer with plain `time.sleep` in its own dedicated process. Keep the fixed 60 Hz targets, all samples, requested-policy measurements and post-stop recording. Save at `artifacts/mac-clock-sleeper-v1/`. This tests whether the delays require the asyncio/selector path; neither arm runs the game, MCP or a model.

Both minimal workers completed 7,200 steps. The asyncio arm reached **149.73 ms** maximum lateness, with four steps exceeding 100 ms; plain sleep reached **67.56 ms**, with none exceeding 100 ms. p95 lateness was 1.26 ms and 3.96 ms respectively. Their maximum CPU-clock query durations were 0.49 ms and 2.22 ms. Both reported the same requested QoS and nice values. This pair supports investigating the pacing mechanism but is not a repeated comparison or a guarantee that a threaded clock will fix the game.

### Native sleeper pacing

Implement a dedicated native sleeper thread in the physics child, keeping simulation and input application on the child's event loop. The thread receives one absolute tick deadline, sleeps without busy-waiting, then wakes the event loop through its thread-safe callback mechanism. Warm the thread before the race epoch, retain every fixed step and catch up against the original epoch, and stop/join it on terminal and cancellation paths. Preserve actual observation/application timestamps and reject stale callbacks. No steering logic, track, physics rule, rescue behavior or timing limit changes.

Use a distinct recorded `clock_mode`, `fixed_step_native_sleeper`, for the process backend; the inline diagnostic backend retains its original asyncio timer. The stable runtime identity already guards clock mode and prevents mixing or resuming results across this change. Repeat the same declared three consecutive free controls, including the HTTP-parent pause, under a new source fingerprint and fresh output directory. Only resume Jev if all three pass. Do not treat the earlier successful controls as validation of this new pacing implementation.

The current validation harness explicitly requires the expected clock mode before starting a race; its original version is preserved with the first controls. Save new controls at `artifacts/native-clock-validation-v1/`. If they pass, make one fresh `road_navigation` Jev screen at `artifacts/jev-native-navigation-v1/` to resume the interrupted gate-telemetry hypothesis. Keep the same original instructions, numeric controls, seed, pinned route, reference and deadline. This changes pacing from the earlier recordings, so progress differences cannot be attributed solely to telemetry. Preserve failures and do not extend the declared screen by searching for favorable trajectories.

The first native-paced control finished all 120 gates in 56.683 s with zero off-road time or rescues, but **failed timing**: maximum lateness 130.74 ms, p95 3.84 ms and final drift 3.70 ms. The harness stopped the batch immediately. The planned parent pause and remaining two controls therefore did not run, and **no native-paced Jev screen ran**. The prepared route-only directory is not a trial result.

Independent replay verified all 3,402 samples and 3,374 applied controls, including exact progress, control state, elapsed time and final summary. The sleeper initialized before the epoch and had exited by final collection. Two late-wake bursts remain: ticks 88–96 peaked at 130.74 ms, and ticks 2,972–2,979 peaked at 120.27 ms. The latter included a 134.80 ms wall gap with 1.45 ms child CPU; GC max was 2.31 ms. Thus the minimal sleeper comparison did not establish full-runtime reliability and does not justify promoting this pacing mode.

Retain native pacing as an explicit **diagnostic option**, `--clock-pacing native`, with distinct saved identity. Restore process-isolated asyncio pacing as the default; `--clock-backend event_loop` still explicitly selects the earlier combined runtime. Both pacing paths have exhibited timing violations. The implementation and tests preserve the native experiment without claiming it fixes local scheduling. Future harness runs must explicitly name `--clock-mode fixed_step_wall_clock` or `--clock-mode fixed_step_native_sleeper`; preserved harness copies and hashes identify the historical controls.

HTTP isolation is complete and verified, but a consistently reliable clock on this local host is **not established**. The experiment's reliability gate holds further paid trials. The useful driving result remains the valid 63/120-gate screen and its independently identified missed-gate stall; the navigation hypothesis remains unsettled. A repeat on a separate host/OS is a stronger next discriminator than further observation/prompt changes mixed with invalid clocks. No remote deployment or host configuration change was performed.

Process isolation is implemented and its independence from the HTTP parent is verified, but **local timing is not yet consistently reliable**. Preserve the three successful controls, the valid Jev screen and both new invalid diagnostics. Further paid testing remains held; no timing rule, GC policy or process priority was changed to produce a pass.

The persistent ledger after the two screens conservatively charges **$0.825958186 of $10**, with no pending reservations ($0.776937258 provider-reported). All later clock diagnostics made no model requests. The local server is left on the default process-isolated asyncio mode, with watchdog disabled; race workers and diagnostic clients have finished.

Final implementation validation: **270 passing tests**, clean Ruff check of `src`, `tests` and `scripts`, and a clean whitespace diff check. Independent review passed the final 48 runtime/process/web checks, including both pacing modes, actual-timestamp failure detection, mode-admission mismatch cleanup and worker lifecycle races. The default server configuration was verified after restart without starting another race.

Follow-up: [the Linux Docker experiment](0006-linux-docker-clock.md) reproduces a
timing violation in its first scripted control, with a materially different
CPU-accounted state-publication span. It preserves the failure separately and
does not resume Jev.
