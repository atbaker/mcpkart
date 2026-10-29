# Three kart Temporal and AgentCore demo

Work lives on `codex/aws-temporal-demo`. The agreed target is Jev, OpenAI
Decisions and Clef through OpenRouter, conventional Temporal workers, MCP game
tools, and three ghost karts. Physics runs at 60 Hz in a separate process.
The [design and research](research/2026-10-29-temporal-agentcore-demo.md) explain
the boundaries and prospective paid gates.

The [free preparation checkpoint](experiments/0086-aws-demo-preparation.md)
records two complete audited scripted rehearsals. The
[latest checkpoint](experiments/0087-aws-live-demo-checkpoint.md) records the
final Linux qualification and remaining live checks. Live driving is separately
bounded by the [0087 registration](experiments/0087-aws-live-demo-registration.md):
one rehearsal and one manually launched stage race, with no retries or
replacement races. Admission requires fresh Linux timing and exact Cloud
interface evidence. No historical experiment window is reused.

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

The isolated demo Runtime is deployed in the company sandbox in us-west-2.
Its name starts with `mcpkart_aws_demo_20261029`; the exact account, ARN and
created bucket/role are recorded in ignored
`artifacts/aws-demo-package-v3/aws-resources.json`. Another demo's resources
were not changed. Version 1 was mock-only. The live-capable versions can forward native
OpenRouter requests under a hash-bound, expiring release. Its role reads only
this demo's dedicated Secrets Manager secret, code objects and logs; it has no
Bedrock inference permission. The live deployment receipt is in
`artifacts/aws-demo-live-release-v3/deployment.json`.

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

To target `mcpkart-dev.iuiaz`, add `TEMPORAL_API_KEY` and the exact
`TEMPORAL_ADDRESS` from its connection settings to the repo-root `.env`.
That file initially holds `OPENROUTER_API_KEY`, which the live Runtime reads
from this demo's dedicated AWS secret. The operator helper preserves restored
Temporal settings in ignored `artifacts/aws-demo-temporal-private.json` (0600),
because the root `.env` unexpectedly reverted during preparation. It loads that
copy inside the worker without putting keys in argv. The generic demo command
reads Temporal settings from `.env`; environment variables take precedence. Explicit local
namespace overrides do not inherit the Cloud key. Do not put keys in arguments,
Git or the runbook.
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

## Tonight's operator path

The preserved Linux container is `mcpkart-demo-linux-20261029`. Its physics and
conventional Temporal worker share one Linux clock; the Mac exposes only the
spectator at [localhost:8773](http://127.0.0.1:8773/). Keep this container and
server running: recreating them invalidates the saved timing qualification.
The server process is held awake by `caffeinate` while it runs.

After the rehearsal's observed exit and full root audit, launch the one stage
entry from the repo root:

```sh
.venv/bin/python scripts/run_aws_demo.py stage
```

This refreshes only the demo's private AWS credential file and starts the
registered conventional worker against `mcpkart-dev.iuiaz`, using Local
Activities and the dedicated AgentCore Runtime. It refuses an already consumed
entry, changed source/evidence, expired release, changed server or new ledger
uncertainty. No secrets enter command arguments or Temporal history.

The release expires at midnight Pacific on 29 October; starting requires fifteen
minutes remaining. A failed entry is preserved and cannot be retried. Another
model, start, prompt, extra race or renewed release requires new authorization
and prospective registration. The real model ledger remains
`artifacts/budget.json`; mock budgets are separate.

The rehearsal and stage recordings are saved under
`artifacts/aws-demo-live-rehearsal-v1/trial/` and
`artifacts/aws-demo-live-stage-v1/trial/`. Watch Temporal Cloud's execution list
for `mcpkart-aws-demo-rehearsal-20261029` or
`mcpkart-aws-demo-stage-20261029` and their three children. These are conventional
operator-managed workers, not Temporal serverless workers.

MCP provides the actual `start_duel`, `drive_duel` and `finish_duel` operations.
Native model wheel/pedal choices map directly to MCP controls. AgentCore runs the
model adapter; OpenRouter supplies inference. Physics runs independently at
60 Hz, holding each kart's previous input while its next decision is pending.
Temporal coordinates the three independent drivers and saves step receipts.
Local Activities reduce service scheduling round trips; broker receipts prevent
duplicate dispatch during workflow-task replay. Restarting the broker cannot
resume this live race and never silently resends an unresolved operation.

The full Linux qualifier is:

```sh
docker exec mcpkart-demo-linux-20261029 python -m mcpkart.duel_clock \
  --trio --url http://127.0.0.1:8771/mcp \
  --output artifacts/A_NEW_CLOCK_DIRECTORY --neutral-seconds 170.1
```

It performs four full controls, the parent pause, and a neutral-clock trace.
Running it again creates new evidence; it does not expand the finite live release.
Mock finish order is never a model result. Cloud latency, rescues and failures
belong in the result even if they make the demo less tidy.
