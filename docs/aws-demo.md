# Three kart Temporal and AgentCore demo

The next manually invoked demo run uses **regular Temporal Activities**. The
[activity-mode amendment and comparison](experiments/0088-regular-activity-amendment.md)
records the user's requested switch and the complete zero-model-call Cloud
qualification. Both earlier 0088 live entries remain recorded as Local Activities and are closed.

Work lives on `codex/aws-temporal-demo`. The agreed target is Jev, OpenAI
Decisions and Clef through OpenRouter, conventional Temporal workers, MCP game
tools, and three ghost karts. Physics runs at 60 Hz in a separate process.
The [design and research](research/2026-10-29-temporal-agentcore-demo.md) explain
the boundaries and prospective paid gates.

The [free preparation checkpoint](experiments/0086-aws-demo-preparation.md)
records the initial scripted rehearsals. The first live attempt is closed after
Clef's provider rejected a request; its charges and failure are retained in the
[0087 outcome](experiments/0087-aws-live-demo-outcome.md). The user then approved
retiring a provider-failed kart while the other drivers continue. The
[0088 registration](experiments/0088-provider-dnf-registration.md) bounded the
now-completed rehearsal and stage race. The new
[0089 registration](experiments/0089-regular-activity-registration.md) permits
one manually launched regular-Activity run. No request retries,
replacement races or fallback controls are allowed.

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
`artifacts/aws-demo-regular-release-v1/deployment.json`.

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

The conventional worker, broker, MCP server and separate 60 Hz physics process
run on this demo's dedicated Linux EC2 host, i-0ae1c7dce47ee05ae, in us-west-2.
The dedicated VPC, subnet, role and security group use the
mcpkart-aws-demo-20261029 prefix. There are no inbound ports. Other demos'
resources are unchanged. Instance credentials refresh through its own IAM role;
Temporal credentials live in this demo's scoped Secrets Manager secret and an
ignored private file on the host.

**The EC2 qualification and live rehearsal have passed root review.** Jev
finished in 99.03 seconds, OpenAI in 151.52 seconds, and Clef retired after a
transport failure. The [full result](experiments/0088-aws-demo-rehearsal.md)
includes rescues, latency, accounting and limitations. Both original entries
have completed; see the [stage outcome](experiments/0088-aws-stage-outcome.md).
The new 0089 regular-Activity entry is available for one manual launch and has
not started. The previous Mac Docker gates do not qualify this host.

To view the spectator, use Session Manager port forwarding with the task-local
plugin, keeping the terminal open:

    PATH="$PWD/artifacts/aws-demo-ssm-plugin/sessionmanager-bundle/bin:$PATH" aws ssm start-session --region us-west-2 --target i-0ae1c7dce47ee05ae --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["8771"],"localPortNumber":["17773"]}'

Open [the spectator](http://127.0.0.1:17773/). Click Live before starting the
stage command. The saved rehearsal is available in the Saved race menu.
Port forwarding is optional for the race itself. Keep the instance, container and server alive: restarting them
invalidates the source/boot/server-bound clock evidence.

After the regular-Activity qualification review, launch the single new run from this repo:

    .venv/bin/python scripts/run_aws_demo.py stage

This submits one SSM command to the dedicated host. It holds the local paid
writer lock, verifies the remote ledger matches before dispatch, observes the
remote exit, retrieves the explicit evidence directories and atomically copies
the cumulative ledger back to artifacts/budget.json. Unknown submissions are
never retried. If the operator is interrupted, inspect the saved SSM command and
reconcile its ledger before any further paid work. Never copy an older budget
file onto the host.

The worker uses namespace mcpkart-dev.iuiaz, regular Activities and the dedicated
AgentCore Runtime. The new execution ID is
mcpkart-aws-regular-stage-20261029, with red/blue/green child workflows.
Both older mcpkart-aws-dnf entries are consumed and cannot be reused.
They are conventional operator-managed workers. AgentCore hosts the model
adapter; inference comes from OpenRouter.

The release expires at midnight Pacific on 29 October; starting requires fifteen
minutes remaining. A consumed entry cannot be retried. Another model, start,
prompt, extra race or renewed release requires new authorization and prospective
registration. The new recording will be under
artifacts/aws-demo-regular-live-stage-v1/trial/. Both older recordings remain
under artifacts/aws-demo-dnf-live-rehearsal-v1/trial/ and
artifacts/aws-demo-dnf-live-stage-v1/trial/. Mock budgets remain separate.

MCP provides the actual start_duel, drive_duel and finish_duel operations.
Native model wheel/pedal choices map directly to MCP controls. Physics runs
independently, holding the previous input while a decision is pending. Temporal
coordinates three independent drivers and saves step receipts. Every driving
step now uses a regular Activity with its own service history. Durable broker
receipts prevent duplicate dispatch if a wrapper re-executes. Restarting the broker cannot resume this
race or silently resend an unresolved operation.

A provider failure retires only that driver's future requests. The kart keeps
its last model-selected input under unchanged physics and rescue rules. It has
no host-selected replacement controls. The UI marks the provider DNF; the
remaining drivers continue. Missing usage keeps the full reserved charge and
increments uncertainty. Invalid native answers and application errors still
stop the entire race. A provider DNF is an infrastructure result, not evidence
of a worse driving policy.

The full EC2 clock gate runs four complete free controls, pauses the HTTP parent
while physics continues, then records 170.1 seconds of neutral physics.
The exact Cloud interface check uses real Temporal, AgentCore and MCP with
scripted replies and zero model calls. Every paid result retains exact native
bytes, all physics frames, timing and the full budget transition chain.

The root .env reset investigation is documented in
[the investigation](env-file-investigation.md). No writer was conclusively
identified. The private demo snapshot protects the run from another root
.env reset. No other process was stopped or security setting changed.

## Recorded fallback

The actual rehearsal is also packaged as a standalone HTML file at
artifacts/aws-demo-delivery-v3/replay.html. It embeds the data and needs no
AWS, Temporal or model connection. The display export is 20 fps; all 3,038
visual frames preserve every displayed original value. The complete 9,112-frame
audit master remains unchanged. Unused model-observation facts were omitted
only from this presentation export.

A local-only fallback server is running at
[the recorded replay](http://127.0.0.1:17875/replay.html), paused at the start.
Click Play. To recreate that server after closing its terminal:

    .venv/bin/python -m http.server 17875 --bind 127.0.0.1 --directory artifacts/aws-demo-delivery-v3

Keep the dedicated EC2 host and its server alive for the stage qualification.
The local fallback server and SSM tunnel may be restarted independently.
