# Jev navigation in rebuilt Codex Cloud

October 18, 2026 (Pacific). The replacement runtime passed the full free timing
gate and one timing-valid Jev screen. Jev reached **68/120 gates**, with one
completed lap and 22 rescues. Three-lap driving remains unproven. A focused
48-call coaching comparison gave mixed results and was not promoted.

## Transport and experiment contract

The Decisions client previously supplied an explicit HTTPX transport, which
disables HTTPX's environment-proxy discovery. It now uses the default transport,
preserving zero connection retries and disabled redirects while allowing the
managed Cloud proxy to inject the OpenRouter Network secret. A real loopback
proxy regression test checks successful and HTTP 503 responses, each with exactly
one request. Before clocks started, **291 tests passed**, three optional Rust
tests skipped, and Ruff passed.

An authenticated, model-free OpenRouter key lookup returned HTTP 200. The public
catalog still resolved `typesafe/jev-1.14` to
`typesafe/jev-1.14-20261014`, provider `typesafe` / TypeSafe, at $0.000000042 per
input token. The driver retained that route with provider fallback disabled.
The key was provided by the managed environment; it was never written to the
repository or supplied to the web server or its physics workers.

The declared screen used `road_navigation`, original instructions, numeric
controls, seed zero, three laps, the frozen **56.7 s** reference, **170.1 s**
deadline, and three-second stopped rescue. Track, handling, finite ordered-gate
rules, fifteen direct controls and 60 Hz physics stayed fixed. The model selected
every control; no steering policy was added to the driver.

Source commit before the transport change:
`6367454c44d267081db19976a4faae3dedde5e55`. Application fingerprint used by the
free gate, live screen and static probes:
`c3502155e8fbdadbe3c7ec5cac24809daba04a616c0175f3f46fea34e710ffef`.
The environment used Linux 6.18.55 x86-64, Python 3.14.8, five visible logical
CPUs, a four-core cgroup quota and 16 GiB memory limit. Server and clients ran on
the same host, using the Python process backend and asyncio pacing, watchdog off.

## Free timing qualification

Fresh attempt: `artifacts/cloud-clock-rebuilt-v1/`. Prepared the frozen helpers
with `scripts/package_remote_clock.py --engine python --prepare-directory`.
Ran three real-MCP races with internal spectator polling, the deliberate HTTP
parent pause in race two, then the 170.1 s neutral clock check. An external 5 Hz
spectator poller covered the batch. No builds, tests or heavy analysis ran during
timed trials. Stop-on-first-failure and the **100/25/100 ms** maximum/p95/drift
limits were retained.

| Measurement | Race 1 | Race 2, parent paused | Race 3 | Neutral clock |
| --- | ---: | ---: | ---: | ---: |
| Simulation duration | 56.683 s | 56.650 s | 56.717 s | 170.100 s |
| Maximum physics lateness | 5.491 ms | 4.736 ms | 4.652 ms | 8.078 ms |
| Exact final p95 lateness | 1.795 ms | 1.524 ms | 1.487 ms | 1.460 ms |
| Final world/wall drift | 2.056 ms | 1.233 ms | 1.017 ms | 2.591 ms |
| Timing valid | yes | yes | yes | yes |

Every scripted race completed 120 gates with zero off-road time and rescues.
During the 350.187 ms HTTP-parent pause, the physics child recorded 21 actual
samples, with maximum lateness 1.918 ms. External spectator polling completed
1,802 requests with no errors. The final verifier checked all four recordings,
helper/source identity, child entrypoint and distinct process provenance. This
qualifies this runtime for the frozen solo workload, rather than every future
Cloud instance. The setup smoke retained by the rebuilt image remains separate;
it was not overwritten or counted as this declared gate.

## Live navigation baseline

Recording: `artifacts/jev-cloud-navigation-v1/typesafe--jev-1.14--seed-0.json`.

| Measurement | Result |
| --- | ---: |
| Ordered gates / completed laps | **68/120 / 1** |
| First lap | 120.133 s |
| Off-road time / rescues | 67.800 s / 22 |
| Requests / API errors | 705 / 0 |
| Applied controls | 684 |
| Replies rejected after rescue / after race end | 20 / 1 |
| Median / p95 API latency | 211.16 / 272.08 ms |
| Maximum API latency | 1,169.03 ms |
| Median / p95 observation age at application | 233.20 / 299.68 ms |
| Maximum physics lateness | 30.415 ms |
| Exact final p95 physics lateness | 1.524 ms |
| Final world/wall drift | 1.251 ms |
| Timing valid / three-lap completion | yes / no |
| Model cost | $0.071693664 |

The clock passed while Jev drove. Compared with the previous GCP/Rust navigation
screen (50 gates, 156 ms median API latency), this screen made more progress but
had slower API responses. A single trajectory on another host/engine cannot
isolate either factor or establish an improvement in model competence.

## Replay and failure diagnosis

Independent deterministic replay reproduced every saved kart pose, progress,
control, rescue, tick and exact elapsed time in all five recordings: **30,620
samples and 11,679 applied commands**. Commands were checked for increasing
application ticks, frozen simulation configuration and complete consumption.
Maximum/p95 physics lateness and final drift were recomputed from saved samples
and monotonic timestamps and matched the reports. Live worker identity and all
705 returned model/provider identities also passed. Evidence and replay code:
`artifacts/jev-cloud-navigation-v1/{analyze.py,verification.json}`.

The dominant gate interval was **63.533 s**, from credited gate 15 at 21.667 s
to gate 16 at 85.200 s. At its first forward crossing, tick 1449 / 24.150 s,
the kart was approximately **4.5423 m** from gate centre laterally, outside the
4.5 m half-width by 4.2 cm. This interpolation uses rounded saved x/y; its
rounding uncertainty is much smaller than the miss. The gate correctly remained
required while the kart travelled around the circuit. Twenty on-road requests
were already beyond the required plane. Existing navigation facts did not
prevent this stall. The next-largest credited-gate interval was 5.650 s.

Steering errors also persisted. Of on-road requests at 2–20 m/s with offset
over 1 m and nose over 15 degrees toward the same side, 59 were left-drift
cases; 52 selected left steering again. The 13 right-drift cases selected
left braking seven times, straight acceleration twice, hard-right braking
three times and hard-left acceleration once. These geometric counts describe
behavior; curved-road situations do not have one uniquely correct action.

Before the first departure at 5.200 s, Jev repeatedly held hard-left acceleration
as the nose angle relative to the road grew through 19.5, 30.1, 45.1 and 56.4
degrees. The earliest same-side offset/heading selector fired too late: at tick
301, and even twelve ticks earlier, every available input left the road in a
fixed 233 ms delay plus 400 ms open-loop diagnostic. This motivates examining
earlier centre-crossing behavior, rather than treating impossible late recovery
as the only correction test. These offline alternatives were never sent to the
live driver as recommendations.

## Focused coaching comparison

Declared `artifacts/jev-cloud-coaching-v1/protocol.json` before 48 calls:
original versus `anticipate_alignment_v1`, eight fixed situations, three
interleaved repeats each. Selected the first departure on each physical side
and exactly 48/24 ticks before it, rest, the first actual observation after gate
credit, the first on-road observation beyond the required gate, and scripted
reference tick 114. Recorded-state fixtures were replayed and validated against
runtime samples. Selection did not use candidate actions or their outcomes.

Only instructions changed. The coaching text explains both mirror cases of
heading toward the centre from the opposite side, unwinding before overshoot,
distinguishing nearby alignment from a distant bend, and releasing braking.
Telemetry and physical controls stayed the same. Exact instructions, criteria
provenance, fixture states, chosen controls, probability/confidence diagnostics,
latencies, identities and costs are retained under the probe directory.

| Situation | Original, three repeats | Coaching, three repeats |
| --- | --- | --- |
| First left departure, 0.8 s earlier | Hard-left accelerate ×3 | Right brake ×2, right coast ×1 |
| First left departure, 0.4 s earlier | Hard-left accelerate ×3 | Hard-left accelerate ×2, right brake ×1 |
| First right departure, 0.8 s earlier | Left accelerate ×2, straight accelerate ×1 | Straight accelerate ×3 |
| First right departure, 0.4 s earlier | Straight accelerate ×3 | Straight accelerate ×3 |
| Rest / first observation after gate credit | Straight accelerate ×3 each | Straight accelerate ×3 each |
| Beyond required gate | Hard-left accelerate ×3 | Hard-left accelerate ×3 |
| First bend | Hard-left brake ×2, left brake ×1 | Straight coast ×3 |

All 48 calls succeeded and cost **$0.005077044**. Fixed-delay short rollouts
showed improved early-left road margin, but reduced early-right margin and no
late-right recovery. Later-left choices were inconsistent. First-bend behavior
also changed. This is mixed evidence, so the coaching prompt remains an artifact
candidate and no second paid live run was made. Three repeated choices and short
rollouts do not establish general driving reliability. The benchmark default
remains `road_physics` with original instructions.

## Budget, handoff and next work

Started from the existing shared ledger at **$0.914245672**. This work added
753 requests and **$0.076770708**. The ledger and versioned spending snapshot
now charge **$0.991016380 of $10**, with $0.941995452 provider-reported total,
61 previously uncertain requests and no pending reservations. The full current
ledger was preserved; the rebuild did not create a new allowance.

Keep raw recordings and diagnostics under ignored `artifacts/`. Owned server
and polling processes were stopped after collection. The snapshot supports a
future rebuild; after any additional paid work, migrate the actual latest ledger
before using another host and avoid concurrent paid ledger copies.

The next focused investigation should test earlier wheel unwinding on both
physical sides and retain the finite-gate miss as a separate recovery fixture.
Another broad prompt sweep or ten-run qualification is not justified by this
candidate. Completion, eight-of-ten reliability, useful race pace, multiplayer
and Temporal integration remain unestablished.
