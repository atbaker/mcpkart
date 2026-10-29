# Codex Cloud development

For moving machines, use the [migration handoff](machine-handoff.md), including
the separate archive for ignored recordings and audit evidence.

Use the process-isolated Python engine with asyncio pacing for both modes.
The [two-kart checkpoint](experiments/2026-10-22-two-kart-checkpoint.md) records
the shared-track prototype; the [earlier checkpoint](experiments/2026-10-21-progress-checkpoint.md)
covers solo driving through 0069. Current budget and operations are below. Historical
runtime and model studies are indexed in [experiments](experiments/README.md).

All paid experiment windows through 0085 are closed. The latest ledger is
99,403 requests / 333,848,829 charged tokens / $11.520516764002778, with 71
uncertainties and no pending reservation. Caps are $20 / 110,000 requests /
500 million tokens. The original [authorization](experiments/0076-two-kart-session-authorization.json)
and [request amendment](experiments/0082-request-ceiling-amendment.json) preserve
all charges. A provider-account top-up alone does not raise caps.

For the current multiplayer mode, follow the [two-kart guide](two-kart-driver.md).
It provides the port-8766 server, free practice command, complete free shared-
clock qualifier and standalone replay export. A local address on this machine
still needs forwarding to work in a remote browser. Embedded replay HTML and
MP4 files allow review without a live model call or an exposed service.

The current 15 m question-local driver passed repeated solo 24 m stadium and
mirror runs. Its [run guide](question-context-driver.md) describes the opt-in
CLI. It preserves saved budget caps within its historical $10 ceiling and
rejects the expanded $20 ledger. Older generic benchmark paid commands
construct Budget with $10 / 250-million-token defaults; do not use them against
the expanded real ledger without reviewing both limits. Direct constructors
must explicitly pass all authorized saved caps; the two-kart CLI does so.

Clock qualifications are machine/source/boot/server-specific. A successful
GCP or earlier Cloud gate does not qualify a fresh environment. The historical
solo gate is `artifacts/jev-goal-challenge-v1/clock/qualification.json`;
check its binding rather than assuming its PID or boot still applies. It
passed three controls, a parent-pause independence check, a 170.1 s neutral
check and exact replay. New candidates also need their exact-interface free
controls and declared native checks before paid use. Study 0072 ran a fresh
complete engine gate after adding optional explicit stationary start poses
and restarting the server. Three new exact-start free controls qualified.
There are 10,597 request slots left at the current boundary. Remaining budget
does not reopen any closed experiment; new collection still needs a finite
prospective study and explicit scope within the user's authorization.

## Prepare the environment

Create an environment for the repository branch containing this checkpoint, then ask its setup
conversation to run the following from the repository root:

```sh
bash scripts/setup_cloud.sh
.venv/bin/pytest -q
.venv/bin/ruff check src tests scripts
```

The script uses uv 0.12.23, selects Python 3.14.8, and installs the runtime and
development dependencies from `uv.lock` with `--locked`. It seeds a missing
ignored spending ledger from the recorded snapshot and preserves an existing
ledger. If the pinned uv is missing, it installs to a versioned user directory
without changing shell profiles or replacing another uv installation. It starts no server, race,
Docker container, VM, or model request. Normal Python development needs no
Rust compiler or Docker. Tests that execute the optional Rust worker skip
when its release binary is absent.

In the current Cloud environment setup, save
`bash scripts/setup_cloud.sh` as the **Install script**. Configure a **Start
skill** to start services only when a task needs them, using the server command
below. Review the setup report and publish the environment. New tasks use the
published filesystem; republish dependency changes before starting a fresh
task. A script in this repository is a command to configure, not an
automatically discovered Codex environment configuration.
[Official OpenAI documentation](https://learn.chatgpt.com/docs/environments/cloud-environments#customize-installation-and-startup)
describes installation, startup, and saved state.

Enable the environment's **Package managers** network preset. If uv must be
bootstrapped, also allow `astral.sh`; its installer and managed Python downloads
use the GitHub release hosts included in that preset. PyPI dependencies need
`pypi.org` and `files.pythonhosted.org`, also included. Keep the environment's
proxy and certificate configuration in place for dependency and API requests.
See [Cloud networking](https://learn.chatgpt.com/docs/environments/cloud-environments#connect-to-services)
and the [uv installer](https://docs.astral.sh/uv/reference/installer/).

## Start the Python server

Run commands from the repository root. Use the installed interpreter directly
after setup so a timed experiment cannot trigger dependency installation.

```sh
env -u OPENROUTER_API_KEY .venv/bin/python -m mcpkart.web \
  --host 127.0.0.1 --port 8765 \
  --race-engine python --clock-backend process --clock-pacing asyncio
```

The MCP endpoint is `http://127.0.0.1:8765/mcp`; the spectator and JSON state
are `/` and `/api/state` on the same host. Run server and controller in the
same Cloud environment, with the same monotonic clock and process namespace.
The localhost URL belongs to that environment, not your Mac. Use any preview
or forwarding capability the environment actually provides; save recordings
for local replay if a browser preview is unavailable.

In a second terminal, generate a paired seed-zero reference and run one free
MCP smoke test:

```sh
.venv/bin/python -m mcpkart.bench reference \
  --seeds 1 --delays 0 --output artifacts/cloud-reference.json
.venv/bin/python -m mcpkart.bench live-reference \
  --url http://127.0.0.1:8765/mcp \
  --reference artifacts/cloud-reference.json \
  --output artifacts/cloud-smoke-v1
```

The frozen handling and rescue settings should retain the 56.7-second offline
reference. Preserve a new output directory for each attempt. A single smoke
test is not the full timing gate.

## Qualify the clock before paid trials

Prepare the versioned seed-zero reference and helpers. These use the same
frozen controls as the GCP comparison, without requiring Docker or GCP
credentials. Use a fresh directory for each attempt.

```sh
.venv/bin/python scripts/package_remote_clock.py \
  --engine python --prepare-directory artifacts/cloud-clock-v1
```

In a third terminal, start the 5 Hz spectator poller before the batch:

```sh
.venv/bin/python scripts/poll_remote_clock.py artifacts/cloud-clock-v1
```

In the second terminal, run the batch:

```sh
.venv/bin/python artifacts/cloud-clock-v1/run_controls.py && \
  .venv/bin/python artifacts/cloud-clock-v1/long_clock.py && \
  .venv/bin/python scripts/verify_clock_validation.py \
    --directory artifacts/cloud-clock-v1 --engine python
```

When the batch stops, press Ctrl-C in the poller terminal to save
`host-spectator.json`. Keep that report with the race evidence. The three
races also have an internal 20 Hz spectator poller; the external 5 Hz poller
continues through the neutral check. Unlike the GCP Docker comparison, both
the server and poller here run directly in the Cloud environment.

Keep the server on port 8765 in the same environment. The control helper
reads `/api/state`, requires the Python process backend with
`fixed_step_wall_clock` and watchdog disabled, and checks the HTTP parent's
identity before pausing it. It resumes the parent during cleanup. Do not
substitute another environment's PID or the physics worker's PID.

All three must complete 120 gates with maximum lateness at most 100 ms,
exact final p95 at most 25 ms, and absolute final drift at most 100 ms. Race
two must record at least twelve physics samples during the HTTP-parent pause.
Stop at the first failure and preserve it; investigate the cause before a
new declared attempt. The `&&` runs the 170.1-second free neutral clock check
only after all three pass. Review `controls/validation.json`, the individual recordings, `long-clock.json`,
the final verification report, and `HELPER-MANIFEST.json` in the prepared
directory before any paid screen. The final verification checks the actual
child entrypoint and all four recordings, including timing and parent-pause
evidence, rather than trusting the initial server response alone.
See the [declared GCP protocol](experiments/0009-python-on-gcp.md).

Do builds, tests, source changes, and heavy analysis between timed runs. Keep
the server free of model credentials. Record the actual Cloud VM resources,
Python version, source fingerprint, runtime identity, timing evidence, and
results; the GCP result alone does not establish Cloud timing.

## Optional OpenRouter access

Model-free setup and controls do not require an API key. Add API access only
when the timing gate passes and the spending ledger is ready for migration.

In the current Cloud environment, configure `OPENROUTER_API_KEY` as a
**Network secret** with `openrouter.ai` as its allowed domain, and allow
HTTPS access to that host. Do not configure the same key as both a direct
environment variable and a network secret. Programs receive a placeholder;
the managed proxy replaces it in HTTPS requests to the allowed service,
during both setup and task execution. This project's HTTP client reads
`OPENROUTER_API_KEY` from its environment and uses the configured proxy.
Use the Personal vault if the value should belong to your account rather
than the shared environment.
[Official secret guidance](https://learn.chatgpt.com/docs/environments/cloud-environments#configure-environment-variables-and-network-secrets)
explains these choices.

If your account instead shows **Codex Cloud (Legacy)**, its **Secrets** are
available only during setup and removed before the agent phase. A setup-only
secret therefore cannot directly supply a later paid driver. Use the access
mechanism supported by that environment and verify availability without
printing the key. Do not write a secret into a prepared image or commit it to
the repository to bridge those phases. See the
[legacy secret lifecycle](https://learn.chatgpt.com/docs/environments/cloud-environment#environment-variables-and-secrets).

`artifacts/`, including the cumulative spending ledger and recordings, is
ignored by Git. Setup initializes a missing `artifacts/budget.json` from the
versioned [spending snapshot](experiments/model-budget-snapshot.json), whose
current boundary is documented in the [migration handoff](machine-handoff.md). Setup never
overwrites an existing ledger.
This snapshot does not synchronize balances across machines:
copy the latest ledger when switching environments after further paid work,
and run only one paid experiment at a time. Do not reset the ledger or start
parallel paid writers with separate balances. Keep `.env` and raw credentials
out of commits, setup logs, and saved recordings.

### Recovery after many experiment recordings

The October 20 renewed session observed a cloud reboot at about 11:17 UTC. All
completed records and the shared budget survived; active processes did not.
Preserve incomplete per-query files and do not score them as completed races.
The old boot's clock qualification must be rejected even when source matches.

With a large artifacts tree, the first MCPstart can exceed its 30-second timeout
while the spectator replay catalog is cold. Race admission warms that catalog
before starting physics, so an orphan neutral race can exist even when the
client times out. Inspect and finish that exact race before further controls.
The failed first recovery gate is retained in
artifacts/jev-six-hour-v2/restart-clock-v1. Explicitly warm `/api/replays` while
idle before a new gate; do not scan recordings alongside an active timed trial.
For example, `curl --fail --max-time 120 --output /dev/null http://127.0.0.1:8765/api/replays`. This local request uses no
model credential and makes no model call. A new complete source/boot/PID-bound
clock gate is still required; warming alone does not qualify timing.
