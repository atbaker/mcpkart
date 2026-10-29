# Three kart Temporal and AgentCore demo

Work lives on `codex/aws-temporal-demo`. The agreed target is Jev, OpenAI
Decisions and Clef through OpenRouter, conventional Temporal workers, MCP game
tools, and three ghost karts. Physics runs at 60 Hz in a separate process.
The [design and research](research/2026-10-29-temporal-agentcore-demo.md) explain
the boundaries and prospective paid gates.

The [free preparation checkpoint](experiments/0086-aws-demo-preparation.md)
records two complete audited rehearsals. The current executable path is
**scripted mocks only**. It can exercise a real
Temporal service and real AgentCore Runtime without a provider request. Every
card and recording labels those controls as mocks. Paid trio admission fails
closed; no historical experiment window is reused.

## Local free race

Install the optional demo dependencies. The development checks on this Mac used
Python 3.14.3 because the historical 3.14.8 interpreter was unavailable. This is
not a transfer of the old machine's timing qualification.

```sh
UV_CACHE_DIR=/tmp/mcpkart-uv-cache uv sync --locked --dev --extra demo --python 3.14
```

Start a dedicated conventional Temporal development service:

```sh
temporal server start-dev --ip 127.0.0.1 --port 7241 --ui-port 8241
```

Start the three-kart spectator and MCP server in another terminal:

```sh
env -u OPENROUTER_API_KEY .venv/bin/python -m mcpkart.duel_web \
  --trio --port 8771 --replay-root artifacts/aws-demo-replays
```

Run one free race in another terminal. Use a fresh logical ID and output
directory for each attempt; the task queue uses that same dedicated ID.

```sh
env -u OPENROUTER_API_KEY \
  TEMPORAL_ADDRESS=127.0.0.1:7241 TEMPORAL_NAMESPACE=default \
  .venv/bin/python -m mcpkart.demo_run \
  --free --local --race-id mcpkart-local-trio-001 \
  --output artifacts/aws-demo-replays/run-local-001
```

Open [the spectator](http://127.0.0.1:8771/) and
[Temporal UI](http://127.0.0.1:8241/). Omitting `--local` selects regular
Activities for comparison. Both paths use three child workflows, one shared
budget journal, actual MCP commands, exact native-response validation, saved
physics frames, and an offline audit. The mock budget is separate from the
authoritative cumulative model ledger.

The operator process owns the ordinary Temporal worker and the broker for this
one race. The workflow and receipt journal survive task replay, but restarting
the broker/physics process is not a supported way to resume a paid live race.
No secrets or driver capabilities enter workflow inputs/history.

## AgentCore free race

The isolated mock Runtime is deployed in the company sandbox in us-west-2.
Its name starts with `mcpkart_aws_demo_20261029`; the exact account, ARN and
created bucket/role are recorded in ignored
`artifacts/aws-demo-package-v3/aws-resources.json`. Another demo's resources
were not changed. The role has no Bedrock inference or secret-read permission;
the application rejects paid mode and contains no provider dispatch code.

Pass that receipt's Runtime ARN to the same command:

```sh
env -u OPENROUTER_API_KEY \
  TEMPORAL_ADDRESS=127.0.0.1:7241 TEMPORAL_NAMESPACE=default \
  .venv/bin/python -m mcpkart.demo_run \
  --free --local --race-id mcpkart-agentcore-trio-001 \
  --output artifacts/aws-demo-replays/run-agentcore-001 \
  --agentcore-arn YOUR_DEDICATED_RUNTIME_ARN --region us-west-2
```

Before starting physics, three explicit mock probes initialize the three racer
sessions. During driving the adapter preserves the original Decisions body bytes
and returned native bytes. Per-racer `agentcore-wire/` evidence records the outer
request/response, AWS request metadata and session. AWS SDK invocation retries
are disabled. AgentCore compute/network charges are separate from model charges;
the mocks make zero provider calls.

When an AgentCore rehearsal is complete, stop only its recorded sessions:

```sh
.venv/bin/python scripts/stop_demo_sessions.py artifacts/aws-demo-replays/run-agentcore-001
```

The Runtime definition, code bucket and scoped role remain for the next demo run.
Their exact identities are in `aws-resources.json`; delete only those resources
when the demo is no longer needed. The runtime idle timeout is five minutes and
its maximum session lifetime is thirty minutes.

To target `agent-kart.iuiaz`, configure `TEMPORAL_NAMESPACE`, the exact
`TEMPORAL_ADDRESS` from its connection settings, and `TEMPORAL_API_KEY` in a
local secret environment. Do not put keys in arguments, Git or the runbook.
The same command runs a conventional worker; it does not provision a serverless
Temporal worker or change namespace settings.

## Evidence and verification

Each run preserves raw question packets, raw/native replies, the single budget
transition chain, applied controls, full physics frames, a recording and a final
receipt. Temporal parent and child histories are exported after collection.
Source snapshots and historical failed attempts remain intact.

Export a compact standalone replay after collection:

```sh
.venv/bin/python scripts/export_duel_replay.py \
  artifacts/aws-demo-replays/run-local-001/race.json \
  artifacts/aws-demo-replays/run-local-001/replay.html
```

The HTML embeds its data and needs no model key. It can be served by a local
HTTP server if browser policy does not allow local file navigation.

```sh
env -u OPENROUTER_API_KEY .venv/bin/pytest -q
env -u OPENROUTER_API_KEY MCPKART_TEMPORAL_TESTS=1 \
  .venv/bin/pytest -q tests/test_demo_temporal.py
.venv/bin/ruff check src tests scripts
```

The opt-in tests launch the installed Temporal development server. They cover
ordinary/Local Activity races and a deliberate workflow-task failure after a
Local Activity has completed but before its marker is persisted. The wrapper
runs again, while the model dispatch and native command occur once. An unknown
dispatch state remains unresolved rather than being retried.

## Remaining paid readiness work

The missing ledger was seeded from the versioned handoff snapshot with all
99,403 requests, $11.520516764002778, 333,848,829 tokens and 71 uncertainties
preserved. A newer authoritative ledger must take precedence if one exists.

Before live models: configure the OpenRouter secret, confirm the latest
authoritative ledger, qualify the final source and server on Linux, validate the
three native routes and exact distributed interfaces, freeze a new finite
registration, and enable the paid adapter under that registration. Do not label
mock finish order as model capability. Cloud latency, rescues and failures belong
in the result even if they make the demo less tidy.

The Linux clock command for the final trio server is:

```sh
env -u OPENROUTER_API_KEY .venv/bin/python -m mcpkart.duel_clock \
  --trio --url http://127.0.0.1:8771/mcp \
  --output artifacts/aws-demo-trio-clock-001 --neutral-seconds 170.1
```

This is a full four-control gate plus the parent-pause and neutral checks. The
separate complete local/cloud mock rehearsals do not substitute for it.
