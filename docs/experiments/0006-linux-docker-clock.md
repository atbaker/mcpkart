# Linux Docker timing controls

October 18, 2026. The user requested Linux Docker controls to investigate whether the intermittent stalls are specific to the native macOS runtime, then a return to Jev if timing is reliable.

## Declared protocol

Run the server, process-isolated physics worker, MCP driver and validation harness inside one ARM64 Linux container. Docker Desktop uses a Linux VM on this same Mac, so this is a practical environment comparison, not proof that an OS kernel alone causes a difference. Record the resolved image, Python version, dependency versions, selector, clock implementations, source fingerprint and VM/cgroup resources. Match the macOS Python 3.14.8 interpreter and locked dependencies. Keep physics, track, controls, rescue, reference and timing limits unchanged.

Use the default process backend, asyncio pacing (`fixed_step_wall_clock`) and watchdog disabled. Start with `--init`, so the HTTP parent has a container PID greater than one. Derive its PID from container-side state and run the harness in that same namespace. Publish only host localhost port 8766 for spectators; the macOS server on port 8765 is separate. All compared monotonic timestamps come from Linux. Keep the Mac virtual environment and `.env` out of the image. Bind the existing `artifacts/` directory for results and the shared budget ledger.

Freeze application/image source before timed trials. First run the suite inside Linux and check that the existing paired reference matches its simulation configuration. If platform floating-point differences prevent exact reference matching, preserve the macOS reference and generate a separately labelled Linux reference using identical physics; document any difference before live controls.

1. Run one batch of three consecutive scripted three-lap races through real MCP, using `scripts/validate_clock.py`. Each must finish all 120 ordered gates and meet the unchanged limits: maximum lateness ≤100 ms, p95 ≤25 ms and absolute final drift ≤100 ms. Control two pauses only the verified HTTP parent for approximately 350 ms; require at least twelve actual child samples inside that Linux monotonic interval. Retain in-container spectator polling, plus about 5 Hz host-side polling through the published port. Stop at the first failed control, preserving it rather than retrying until a pass.
2. If all three pass, run a free neutral-control clock check for three times the paired reference duration (170.1 s with the existing 56.7 s reference). Send `straight_coast` through MCP about 5 Hz, recording acknowledgements and an independent Linux client heartbeat. This intentionally stationary check is scored on timing and duration, not lap completion. Use the same backend, mode, watchdog, source and host spectator polling. Buffer data until the clock stops.
3. Verify common source/configuration/runtime identity and replay recorded physics after clocks stop. Only if all free gates pass, run one fresh Jev `road_navigation` screen with original instructions, numeric controls, seed zero, the pinned TypeSafe route and the same reference/deadline. This resumes the missed-gate telemetry hypothesis; the earlier navigation screens had invalid timing. It is one exploratory trajectory, not an eight-of-ten qualification or a causal comparison with differently configured past runs.

Use fresh directories under `artifacts/linux-docker-clock-v1/` and `artifacts/jev-linux-navigation-v1/`. Preserve logs, failed attempts and source hashes. No code edits or CPU-heavy analysis run alongside a live clock. Bound command duration and ensure a paused HTTP parent receives SIGCONT during cleanup.

Free controls require no API access. After the gate passes, `docker exec --env-file .env` supplies credentials only to the paid driver. Do not bake credentials into an image or write them into environment manifests. Keep the existing shared `artifacts/budget.json` and $10 total cap. Starting charge: **$0.825958186**, no pending reservations.

## Results

### Environment and preflight

The image built successfully and the Linux suite passed **270 tests**, with a clean Ruff check. Python is exactly 3.14.8, with locked dependencies, `EpollSelector`, and the default process/asyncio clock. All thirty saved reference configurations match exactly; the unchanged seed-zero reference remains 56.7 s. No Linux recalibration was necessary.

The VM reports Linux ARM64, kernel `7.0.14-linuxkit`, four CPUs and 8,320,299,008 bytes of memory. The image is `sha256:e7d17410126521b7484df67fbeaa5d6ef44beed3af80c05f28688aa53c386843`; source fingerprint `2dec4a203d6f8fdfea3cde0dafae5225832132ba87fb427c753d8ddbdb132c23` matches the host checkout. The HTTP parent is container PID 7. Selected image/container/host provenance, installed packages, clock implementations and resource counters are saved under `artifacts/linux-docker-clock-v1/`. The free container has no API key or `.env` mount.

### First scripted control

The first control completed all three laps and 120 ordered gates in **56.683 s**, with zero off-road time or rescues, but **failed timing**:

| Metric | Linux Docker control 1 |
| --- | ---: |
| Maximum physics lateness | 104.26 ms |
| p95 physics lateness | 3.89 ms |
| Final world/wall drift | 0.62 ms |
| Maximum recorded GC duration | 3.39 ms |
| Realtime-valid | no |

The unchanged maximum is 100 ms; catching up later does not remove that violation. The declared harness stopped after this first failure. **Controls two and three, the parent pause, the longer free check, and Jev did not run.** There was no retry-until-pass or limit change.

The largest delayed wake, tick 1,287, followed a 117.72 ms wall gap containing **102.22 ms of recorded child process CPU**. A `runtime_state` span ran for 102.02 ms wall / 101.72 ms process CPU and ended about 53 microseconds before that late wake. This is different evidence from the earlier low-CPU macOS gaps. It implicates work concurrent with state publication, but process CPU covers every child thread and this is a VM: the responsible function, thread and underlying cause are not established by the span alone. No GC overlapped it. Maximum measured physics-step duration was 0.81 ms.

Container cgroup counters recorded no CPU throttling or memory/OOM events; the container has no additional CPU quota within the VM's four CPUs. This does not measure every host/VM scheduling effect. The Linux interpreter reports experimental JIT unavailable and disabled, so JIT compilation does not account for the burst.

Independent replay inside Linux passed **30,536 checks**: all 3,402 samples, 3,379 applied inputs, final progress and summary match exactly. Exported track and physics match the earlier macOS model run. Source, runtime identity, actual child mode and provenance agree; no native sleeper or web framework is loaded in the physics child.

In-container polling made 1,115 requests without errors (maximum round trip 117.46 ms). The Mac-side spectator made 434 requests through published port 8766 without errors (maximum 123.44 ms); those totals include setup/collection time. Absolute Mac and Linux timestamps were not compared. Host polling has stopped; its full report and the bounded supervisor/control sources are preserved with the failed trial.

### Outcome

The Linux VM also reproduces a violation, so reliable timing is **not established there**. This does not prove that the same mechanism causes the Mac and Linux failures or rule out the shared Mac host. The CPU-accounted state-publication span is a concrete target for staged/thread-specific profiling before another qualification batch. Preserve this first failed batch as its own environment result.

No paid calls were made. The shared ledger is unchanged at **$0.825958186 of $10**, with no pending reservations. The credential-free Linux server remains available on [localhost:8766](http://127.0.0.1:8766/); the macOS server remains separate on port 8765. Rebuild after source changes, use fresh per-environment output directories, and repeat the declared gate before returning to Jev. [The container guide](../linux-container.md) documents the reproducible setup and cleanup.
