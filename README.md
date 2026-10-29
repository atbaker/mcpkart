# MCP Kart

A Python experiment in autonomous kart racing: can low-latency decision models drive a kart in real time through MCP?

Python physics runs continuously at 60 Hz in a separate worker process, independent of the HTTP/MCP event loop. Models select one of 15 steering/throttle/brake combinations through OpenRouter's Decisions API, and a driver submits those controls to a real MCP server. A browser spectator shows the live race and saved replays. After three continuous seconds off-road, a rescue returns the kart near its departure point, stopped and facing along the road. Rescues are counted; the race clock keeps running.

## Current progress

Moving machines: follow the [migration handoff](docs/machine-handoff.md) to
restore recordings, audit evidence and the current budget ledger alongside Git.

The [both-question timing study](docs/experiments/0085-both-head-timing.md)
completed 22 episodes. Baseline recovered 4/8 delayed episodes versus 1/8 with
factual timing in both questions; both passed 3/3 ordinary checks. The added
facts did not improve this sample; defaults remain off. Physics, rules and
controls stayed fixed. [All outcomes](docs/experiments/figures/0085-both-head-timing-results.svg).

The [motion-only validation](docs/experiments/0084-motion-validation.md)
completed all 22 episodes. Baseline and motion-only tied: 1/4 each on the
original delayed state, 0/2 on the additional blue state, 2/2 on the additional
red state, and 3/3 ordinary-latency checks. The earlier 2/2 motion advantage
did not repeat; defaults remain off. All 26 source files stayed unchanged.
[All outcomes](docs/experiments/figures/0084-motion-validation-results.svg).

The [wheel-observability ablation](docs/experiments/0083-wheel-observability.md)
compared baseline, motion-only, timing-only and combined facts on the frozen
recovery bank. Delayed post-contact recovery scored 0/2, 2/2, 1/2 and 1/2;
all profiles failed severe drift. All four normal checks passed. Motion-only
is a candidate, with contact and native pedal-choice caveats; defaults remain
off. [All 28 outcomes](docs/experiments/figures/0083-wheel-observability-results.svg).
Only wheel measurements/descriptive timing facts changed; no driving rules
were added. All 18,543 prior question sets remained byte-exact with flags off.

The [harder recovery/delay study](docs/experiments/0082-harder-recovery.md)
completed sixteen checkpoint episodes: both fact profiles recovered the
post-contact state 2/2 at normal latency, 0/2 with an added second; severe drift
was 0/2 for both profiles at either delay. Legal free recoveries exist in all
conditions. Gate geometry has no demonstrated success-rate advantage.
[All outcomes](docs/experiments/figures/0082-harder-recovery-results.svg).
Current request ceiling is110,000; dollar/token caps remain $20 / 500 million.

The [recovery benchmark](docs/experiments/0081-recovery-benchmark.md) restored
three recorded problem states and Jev recovered without rescue in all twelve
bounded episodes. Both baseline and factual gate geometry passed; the small
500 ms added-delay comparison favored geometry on recovery time, with no
success-rate separation. [Results chart](docs/experiments/figures/0081-recovery-results.svg)
and [recorded paths](docs/experiments/figures/0081-missed-gate-paths.svg).
This establishes selected unassisted recoveries, not twelve full-race finishes
or general reliability. Python physics and goal-only action selection remain fixed.

The [fresh baseline attempt after overload](docs/experiments/0080-jev-overload-retry.md)
finished both karts with 575 valid replies and no further HTTP 529. Both needed
rescue; substantially slower API replies limit comparison with gate geometry.

The latest [gate-facts pilot](docs/experiments/0079-factual-next-gate-geometry.md)
adds factual gate coordinates/orientation without action instructions.
Geometry finished four attempts cleanly, but only one matched duel pair
completed; the second baseline duel was interrupted by provider overload.
Recovery benefit is unproven and the default prompt remains unchanged.

The [two-kart prototype](docs/experiments/2026-10-22-two-kart-checkpoint.md)
now supports Jev versus Jev and Jev versus OpenAI on one shared Python track,
with physical contact, independent decision loops and a live/replay spectator.
All 48 kart attempts across 24 duels finished; 30 were clean. Jev was clean in
29/40 attempts and won all eight paired model comparisons; OpenAI was clean
in 1/8. Nearby-grid validation exposed recovery and missed-gate limits.
These are small, setup-specific cohorts, not a general model ranking.

The questions supply goals, mechanics and measured road/opponent facts without
steering/braking rules, action suggestions or a host fallback. The game and
prompts stayed fixed throughout the comparison. See the
[two-kart guide](docs/two-kart-driver.md) for the server, free practice,
one-match command, clock qualification and standalone replay export.

Earlier solo recovery work follows.

The [road-geometry comparison](docs/experiments/0075-goal-only-wheel-road-geometry.md)
finished all four races, but none earned a gate before rescue. Minimal needed
one rescue per race; added heading/edge facts needed two and one. The factual
bundle did not demonstrate better recovery. Python physics and goal-only rules
stayed fixed, and all audits passed. The study is closed.

The [eight-race repeatability check](docs/experiments/0074-goal-only-wheel-motion-repeats.md)
finished all eight races: both fact sets were clean in all four clockwise runs,
and every recovery run needed one rescue. Added wheel motion reduced no paired
rescues and was slower in all four pairs. The earlier apparent advantage did
not reproduce. No supplied action rules were added; all audits passed.

The latest [challenge study](docs/experiments/0072-goal-only-challenge.md) exposed
limits: both harder goal-only starts finished, but recovery needed two rescues
and the larger-error start needed one. Neither was clean. The ordinary holdout
remained unrun at the existing budget floor. Unassisted recovery is not established.

The preceding [goal-only follow-up](docs/experiments/0071-goal-only-recovery-domain.md):
Jev finished all four starts cleanly in 79.52–81.63 seconds, using objectives,
mechanics and question-local measurements without supplied action rules.
The old pose-domain stops were relaxed, but no race entered the newly allowed
domain; recovery remains untested. Median API latency was 226 ms, with one
1.38-second reply. The preceding [pilot](docs/experiments/0070-question-local-policy-ablation.md)
retains its clean finish, inherited-domain stop and two clean policy controls.
The following checkpoint counts describe the earlier policy-equipped runs.


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

The `codex/aws-temporal-demo` branch adds an opt-in three-ghost-kart demo with
conventional Temporal workers, Local Activities, MCP controls, and an AgentCore
adapter for OpenRouter. See the [demo runbook](docs/aws-demo.md) and
[finite live registration](docs/experiments/0087-aws-live-demo-registration.md).
Scripted mocks remain explicit; live admission requires source/server-bound
Linux qualification and a complete Temporal Cloud / AgentCore / MCP rehearsal.

Install [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync --locked --dev
.venv/bin/mcpkart-web
```

Open [the spectator](http://127.0.0.1:8765/). The MCP endpoint is `http://127.0.0.1:8765/mcp`. Put your own `OPENROUTER_API_KEY` in the ignored `.env` file when running paid model experiments; see `.env.example`. The server and scripted reference do not require an API key.

For the two-kart spectator on port 8766, use:

```sh
env -u OPENROUTER_API_KEY .venv/bin/python -m mcpkart.duel_web --port 8766
```

Open `http://127.0.0.1:8766/?replay=featured` for the curated saved race, or run
one free practice match in another terminal:

```sh
env -u OPENROUTER_API_KEY .venv/bin/python -m mcpkart.duel_run \
  --free --output artifacts/my-duel-free-v1
```

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
preserves saved budget caps within its historical $10 ceiling; it rejects the
current expanded $20 ledger. The [two-kart CLI](docs/two-kart-driver.md) handles
the current caps. The solo command requires a qualified server, existing ledger,
new output directory and configured OpenRouter key; it does not run the
preflight checks for you.

The generic benchmark and probe commands retain observation profiles, custom
course/handling flags, physical control descriptions and joint/factored menus
for further research. Use their `--help` output and freeze each comparison's
settings. Their older Budget constructors use $10 and 250-million-token defaults;
do not run those paid commands against the expanded ledger without reviewing
both limits. No model retries or provider fallbacks are enabled.

There is one shared cumulative $20 / 100,000-request / 500-million-token cap,
with $10.983352472002839 charged, 94,598 requests and 70 uncertainties at this
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

The latest full run passes 602 tests with three optional Rust tests skipped
and no warnings. An earlier Python 3.14 multiprocessing finalizer warning did
not recur in either the focused strict-warning checks or the final full run. The
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
the design. Two-kart traffic and contact are implemented; larger fields,
items, authentication and matchmaking remain later work. The opt-in demo
branch adds a three-kart ghost field and Temporal orchestration. The previous implementation and its run
instructions are preserved under [legacy](legacy/README.md).
