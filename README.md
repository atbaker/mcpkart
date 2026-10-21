# MCP Kart

A Python experiment in autonomous kart racing: can low-latency decision models drive a kart in real time through MCP?

Python physics runs continuously at 60 Hz in a separate worker process, independent of the HTTP/MCP event loop. Models select one of 15 steering/throttle/brake combinations through OpenRouter's Decisions API, and a driver submits those controls to a real MCP server. A browser spectator shows the live race and saved replays. After three continuous seconds off-road, a rescue returns the kart near its departure point, stopped and facing along the road. Rescues are counted; the race clock keeps running.

## Current progress

The opt-in **question-local driver** completed 14/14 useful Jev races, 13 clean,
on a 24 m stadium and its clockwise mirror. OpenAI GPT-6 Luna Decisions finished
both matched comparison starts cleanly. Three-lap times are about 79 seconds.
The models execute an explicit bearing/pedal policy from structured current
facts; these runs cover one solo course family and small starting-pose variation.
Clef is set aside after driving failures and a separate post-top-up timeout.

Read the [findings checkpoint](docs/experiments/2026-10-21-progress-checkpoint.md)
for the tested changes, limitations and actual prompt/response excerpts. The
[experiment index](docs/experiments/README.md) preserves successful, failed and
interrupted studies. The [driver guide](docs/question-context-driver.md) explains
how to run the validated 15 m setup after its free timing/interface checks.
Original application defaults and the joint `damped` baseline remain available.

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

All prior paid study windows are closed. New paid collection needs a finite
experiment plan and the existing timing, evidence and budget checks. The
[question-context CLI](docs/question-context-driver.md) runs one Jev race and
preserves saved budget caps. It requires a qualified server, existing ledger,
new output directory and configured OpenRouter key; it does not run the
preflight checks for you.

The generic benchmark and probe commands retain observation profiles, custom
course/handling flags, physical control descriptions and joint/factored menus
for further research. Use their `--help` output and freeze each comparison's
settings. Their older Budget constructors use a 250-million-token default;
do not run those paid commands against the expanded 500-million ledger without
reviewing that limit. No model retries or provider fallbacks are enabled.

There is one shared cumulative $10 / 75,000-request / 500-million-token cap,
with $8.563495772000609 charged, 71,160 requests and 70 uncertainties at this
checkpoint. Keep `artifacts/budget.json`: deleting it discards spending history.
Transfer the latest ledger when switching hosts and run only one paid writer.
Setup seeds a missing ledger from the versioned [snapshot](docs/experiments/model-budget-snapshot.json);
it cannot synchronize balances across hosts. Raw runs, videos and credentials
stay ignored; curated prompts, reports and response excerpts are versioned.

The spectator supports live races and saved replay playback. A Cloud localhost
URL belongs to its environment; browser access needs supported forwarding or
an explicitly configured tunnel. See the [Cloud guide](docs/cloud-development.md).

## Development

The current solo PoC uses Python; no Rust compiler or Docker is required.

```sh
env -u OPENROUTER_API_KEY .venv/bin/pytest -q
.venv/bin/ruff check src tests scripts
```

The checkpoint passes 474 tests with three optional Rust tests skipped. The
[Linux/container guide](docs/linux-container.md) and historical runtime studies
in the [experiment index](docs/experiments/README.md) preserve the Docker, Rust
and GCP comparisons. Python passed the remote and Cloud timing gates for this
solo workload; every new environment still needs its own qualification.

An optional Rust worker remains available with
`cargo build --release --locked --manifest-path rust-race/Cargo.toml` and
`.venv/bin/mcpkart-web --race-engine rust --port 8767`. It is a historical
comparison; configurable race setups currently require the Python engine.

The [project plan](docs/plan.md), [original experiment](docs/experiments/0001-realtime-driving.md),
[API research](docs/research/decision-models.md) and [glossary](GLOSSARY.md) record
the design. Temporal orchestration, traffic, collisions, items, authentication
and matchmaking remain later work. The previous implementation and its run
instructions are preserved under [legacy](legacy/README.md).
