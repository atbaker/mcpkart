# Working on MCP Kart

This repository contains a Python proof of concept for autonomous, realtime
kart racing through MCP. The current goal is solo three-lap driving by Jev;
model driving viability is not established. Read `docs/plan.md` and the latest
experiment notes before changing experiment assumptions.

- Use the process-isolated Python engine with asyncio pacing by default.
  `rust-race/` is an optional historical comparison, not a build requirement.
- `legacy/` preserves the previous application. Work in `src/mcpkart/` and
  `tests/` unless a task explicitly concerns the legacy version.
- Setup: `bash scripts/setup_cloud.sh`, or `uv sync --locked --dev` with
  Python 3.14.8. Cloud environment instructions are in
  `docs/cloud-development.md`.
- Verify with `.venv/bin/pytest -q` and
  `.venv/bin/ruff check src tests scripts`. Rust-dependent tests may skip if
  its optional release binary is absent.
- Start the spectator and MCP server with `.venv/bin/mcpkart-web`. Use the
  environment's forwarded port for the browser; keep clients and server on
  the same host for monotonic-clock comparisons.
- Keep physics independent of inference and HTTP. Models choose direct
  controls, with no automatic steering. Freeze handling, track and timing
  limits within a comparison, and keep failed attempts.
- Before paid driving in a new environment, run the complete free timing gate.
  Do not build, install packages or run heavy analysis alongside timed trials.
- Model calls cost money. Keep `OPENROUTER_API_KEY` in an environment secret
  or ignored `.env`, never in Git, logs, command arguments or Docker images.
  The project has one shared $10 experiment cap, not a new allowance per clone.
  Preserve/transfer the latest `artifacts/budget.json` when switching hosts;
  never run paid experiments concurrently across separate ledger copies.
- Recordings, downloaded infrastructure evidence and live budget ledgers stay
  under ignored `artifacts/`. Versioned experiment summaries and the dated
  budget snapshot preserve the handoff context without publishing raw runs.
- For open-web research, use Exa search/fetch first. Prefer purpose-built
  connectors and authoritative documentation tools where available.
