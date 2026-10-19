# MCP Kart

A Python experiment in autonomous kart racing: can low-latency decision models drive a kart in real time through MCP?

Python physics runs continuously at 60 Hz in a separate worker process, independent of the HTTP/MCP event loop. Models select one of 15 steering/throttle/brake combinations through OpenRouter's Decisions API, and a driver submits those controls to a real MCP server. A browser spectator shows the live race and saved replays. After three continuous seconds off-road, a rescue returns the kart near its departure point, stopped and facing along the road. Rescues are counted; the race clock keeps running.

## Run locally

Install [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync --locked --dev
.venv/bin/mcpkart-web
```

Open [the spectator](http://127.0.0.1:8765/). The MCP endpoint is `http://127.0.0.1:8765/mcp`. Put your own `OPENROUTER_API_KEY` in the ignored `.env` file when running paid model experiments; see `.env.example`. The server and scripted reference do not require an API key.

In a second terminal, establish the offline reference and drive it through MCP:

```sh
uv run mcpkart-bench reference
uv run mcpkart-bench live-reference --output artifacts/live-reference
```

The viewer's archive selector and replay controls can play saved trials without changing a live race. Replay recordings, request evidence, routes, and the budget ledger live under the ignored `artifacts/` directory.

## Codex Cloud

Use `bash scripts/setup_cloud.sh` as the environment's install/setup command.
It installs pinned Python tooling and locked dependencies, carries forward the
dated budget snapshot only when no ledger exists, and starts no model calls.
The [Cloud development guide](docs/cloud-development.md) covers setup, port
forwarding, secrets, the free timing gate, and transferring the latest budget.
Raw recordings and the local `.env` are not included in Git.

## Model experiments

```sh
uv run mcpkart-bench latency --samples 20 --output artifacts/latency
uv run mcpkart-bench screen --output artifacts/comparison
uv run mcpkart-bench compare --trials 10 --output artifacts/comparison
uv run python -m mcpkart.probe --output artifacts/telemetry-probes
uv run mcpkart-bench screen --telemetry road_physics --output artifacts/road-physics-screen
```

The initial PoC now focuses on **TypeSafe Jev 1.14**, and benchmark/probe commands default to Jev. Paid driving commands default to the `road_physics` observation profile; the scripted reference uses raw telemetry. Earlier OpenAI GPT-6 Luna Decisions and Cloudflare Clef recordings are preserved; those routes can be selected explicitly later with `--models`. A Jev pass will not count as validation of other models. Provider routes are saved before trials; automatic retries and fallbacks are disabled. Requests include coordinate conventions, handling limits, the selected kart/track telemetry, rescue state, and the next required checkpoint's geometry. No recommended controls or computed racing line are sent to a model.

`--telemetry` selects an observation profile. Original road/physics profiles and the newer compact and road-compass variants remain available; see `mcpkart-bench screen --help`. Physics profiles report cornering grip demand; compact profiles separate current pose from future bends. The [telemetry experiment](docs/experiments/0002-track-telemetry.md) and [Jev navigation iteration](docs/experiments/0003-jev-navigation.md) record comparisons and limits. Saved trial labels identify the profile; older recordings show that it was not recorded.

Probes accept `--repeats` and `--fixtures` for repeated focused comparisons. `--control-language explicit` names the same physical wheel/pedal inputs in words. `--instruction-style` can test a next-input question or general driving guide separately; the default preserves the original instructions. These options affect model evidence and instructions, without adding a steering controller.

The [gate and history experiment](docs/experiments/0004-gates-and-observation-history.md) adds opt-in `road_navigation`, `compact_navigation` and `road_history` profiles. Navigation profiles distinguish the bearing toward a gate from its crossing-plane orientation and explain finite forward gate credit. History uses at most three actual preceding driver observations within one second, clearing motion samples after rescue while retaining the observed checkpoint-progress clock. Use `--navigation-record` with the probe command to reconstruct valid off-axis and missed-gate cases from a saved trial.

Use `--reset-after-seconds X` on reference and model commands to change the rescue timeout; `0` disables it. Keep the same setting for paired references and model runs, and use a new output directory when changing experiment configuration. Commands based on observations captured before a rescue are discarded, then the driver gets a fresh observation.

The persistent `artifacts/budget.json` ledger enforces a $10 total cap and conservative reservations across reruns. Keep the ledger: deleting it would discard the spending history. A saved comparison refuses to resume if the implementation, simulation/rescue settings, paired baseline, pinned route or prompt configuration changes. Live reports retain the exact instructions and control descriptions. A comparison also verifies that the reference uses the same track and handling.

When switching environments, transfer the latest ledger before paid work. The Cloud setup seeds a missing ledger from the dated spending snapshot, but it cannot synchronize balances across hosts. Run only one paid experiment at a time.

The current assisted experiment targets at least eight of ten three-lap runs, with median completed-run duration within twice the paired scripted reference. Reports distinguish total completions, completions without rescue, and rescue counts. Assisted completion does not establish the original unassisted-driving goal. Incomplete batches never count as passes. This experiment compares complete model/provider routes and driver observations; it does not isolate model compute latency or establish general model rankings.

Saved replay bodies are prepared before the race clock starts and remain playable during a live trial. Newly saved recordings appear between races. Downloading the current trial is available after it ends, keeping large JSON work outside the physics clock.

Trial timing includes bounded GC, slow-span and late-wake CPU diagnostics. `uv run mcpkart-web --watchdog` additionally enables a small diagnostic thread in the physics worker that records source-only event-loop stacks during long physics gaps; locals are never captured. Full bounded evidence is saved in recordings, while the live viewer receives summaries. Instrumentation does not change physics, timing limits or GC policy. The [gate/history experiment](docs/experiments/0004-gates-and-observation-history.md) records earlier timing failures. All three initial controls in the [process isolation experiment](docs/experiments/0005-isolated-physics-clock.md) passed, including an HTTP-parent pause. A Jev screen also had valid timing but reached only 63/120 gates. Later model-free diagnostics and a native sleeper control reproduced intermittent failures, so local paid testing is held again. Process-isolated asyncio pacing remains the default; `--clock-pacing native` retains the unqualified native sleeper experiment, and `--clock-backend event_loop` selects the earlier combined runtime. Reports retain runtime identity and worker provenance; interrupted collection preserves request evidence as an incomplete trial.

## Development

For Linux, the [Docker/container guide](docs/linux-container.md) builds the same
locked Python environment and publishes a separate spectator on port 8766.
The first [Linux timing control](docs/experiments/0006-linux-docker-clock.md)
completed three laps but exceeded the 100 ms maximum-lateness limit at
104.26 ms. Jev remained held; Docker on this Mac has not established reliable timing.

An optional [Rust race-worker spike](docs/experiments/0007-rust-race-engine.md)
keeps Python/FastMCP and the existing physics contract. Build it with
`cargo build --release --locked --manifest-path rust-race/Cargo.toml`, then
start `uv run mcpkart-web --race-engine rust --port 8767`. The optional Docker
target `rust` includes the release binary; the default image only builds Python.
Parity passes, but control two exceeded the
timing limit at 117.09 ms; Rust is experimental and local paid tests remain held.

The [GCP follow-up](docs/experiments/0008-remote-linux-clock.md) passed all three
Rust controls and the 170.1 s check, with at most 0.86 ms lateness. A subsequent
Jev screen had valid timing (1.20 ms maximum), but reached only 50/120 gates
with 24 rescues. The temporary VM was deleted after collection. Local timing
remains unqualified.

The [Python-on-GCP comparison](docs/experiments/0009-python-on-gcp.md) then passed
the same three races and 170.1 s check using the existing isolated Python
worker with asyncio pacing. Worst race lateness was 2.22 ms; the long check
peaked at 3.28 ms with 1.30 ms p95. All races finished without rescues, and
independent replay passed. **Keep Python for the current solo PoC**; Rust's
lower jitter is not required for this workload. The temporary VM and boot disk
were deleted. Further Jev experiments can use the qualified GCP environment;
multiplayer capacity and Temporal integration remain to be measured.

```sh
uv run pytest
uv run ruff check src tests scripts
```

The [approved experiment](docs/experiments/0001-realtime-driving.md), [broader project plan](docs/plan.md), [API research](docs/research/decision-models.md), and [glossary](GLOSSARY.md) record the design. Temporal orchestration, multiplayer collisions, items, authentication, and matchmaking follow the solo-driving evidence.

The previous implementation and documentation are preserved in [`legacy/`](legacy/README.md). Run that project's documented commands from `legacy/`.
