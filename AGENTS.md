# Working on MCP Kart

## Current checkpoint

The user asked to tidy, commit and push the existing progress. No new paid
experiment is authorized by that cleanup request. Clef is set aside.
Start with [the progress checkpoint](docs/experiments/2026-10-21-progress-checkpoint.md),
[experiment index](docs/experiments/README.md), and [project plan](docs/plan.md).
Individual reports preserve failed gates, exploratory results and limitations.

The opt-in `src/mcpkart/question_context*.py` driver uses the validated 15 m
question-local policy. Jev has 14/14 useful finishes, 13/14 clean, including
12 consecutive fresh clean starts across 0053/0054/0068. OpenAI GPT-6 Luna
Decisions finished both matched 0068 starts cleanly with the same setup.
These are solo 24 m stadium/mirror runs with small initial-pose variation.
Application defaults and the historical joint `damped` baseline are unchanged.

Clef's two 0068 attempts ended at 20/120 gates. The separate post-top-up 0069
attempt returned two valid replies, then timed out at the unchanged 5 s limit.
It stopped at 6.55 s; its second planned race was never admitted. Keep its
full 75,366-token/$0.00393216 reservation: actual billing is unknown. No cache
metadata establishes a cache effect. Study 0069 is closed after this failure.

The experimental 22 m package passed free physical and static native screens
(0063/0065), but actual 500 ms Jev driving remains UNRUN. Study 0066 was
interrupted during free controls by a reboot; preserve its partial evidence.
Free post-restart 0067 controls are not model races. Do not promote this
package or substitute it for the successful 15 m driver.

## Runtime and experiments

- Retain the process-isolated Python engine with asyncio pacing. Rust is an
  optional historical comparison, not a build requirement. Physics runs at
  60 Hz independently of model requests and holds the last native input.
- The current experiment setup is 24 m road, 12 m/s maximum, 0.12 rad maximum
  wheel, three laps and a three-second off-road rescue. Freeze handling,
  track, prompts, routing and timing limits within a comparison.
- Models choose every paid steering/pedal input. No host policy evaluation,
  action filtering, smoothing, fallback steering or silent response repair.
- Register new paid work prospectively after user authorization. Preserve
  all failed and interrupted attempts; use fresh output directories.
- Root alone collects and reviews unless the user explicitly authorizes
  delegation. One paid writer and one POST in flight; launch one actual paid
  race per explicit process. Observe its exit and fully audit raw/native,
  factual, physics, timing and accounting evidence before another admission.
- Keep source/controller hashes, exact per-request questions, actual route
  identities and budget transitions. Old frozen helpers are evidence, not
  reusable current authorization. The new controller modules have separate
  hashes; the core fingerprint does not include them.
- Before paid driving in a new environment or after a reboot/source change,
  run the complete free timing gate and bind it to source, boot and server
  PID/start ticks. Also run the exact-interface free controls and native
  checks declared by the new study. No builds, tests or heavy analysis during
  timed collection. Prewarm the idle replay catalog as described in the
  [Cloud guide](docs/cloud-development.md); do not scan it during a race.
- The last full clock gate in this workspace is
  `artifacts/jev-six-hour-v2/restart-clock-v2/qualification.json`, bound to
  boot `4b247f0d-313e-4038-ac10-acff9274db8e`, server PID 558/start ticks 8475.
  These identify historical evidence, not an assumption about a fresh host.

## Credentials, budget and evidence

- Keep `OPENROUTER_API_KEY` in an environment secret or ignored `.env`.
  Never put keys in Git, command arguments, logs, recordings or images.
  Preserve Cloud proxy and certificate trust; the default HTTPX transport
  honors network-secret injection. Free commands unset the model key.
- There is ONE shared cumulative $10/75,000-request/500,000,000-token cap.
  Latest boundary: 71,160 requests, 267,423,949 charged tokens,
  $8.563495772000609, 70 uncertainties (69 historical plus the 0069 timeout),
  pending empty. Preserve all charges and uncertainty; do not reset/refund.
- `artifacts/budget.json` is authoritative in this workspace. The versioned
  [snapshot](docs/experiments/model-budget-snapshot.json) seeds a missing
  ledger only. Transfer the latest ledger between hosts; never run concurrent
  paid writers against separate copies. Old experiment windows are closed.
- Pass `max_tokens=500000000` explicitly to direct `Budget` constructors:
  their older 250-million default would lower the saved ceiling. The opt-in
  question-context CLI preserves saved caps. Do not run generic benchmark
  paid commands against the expanded ledger without reviewing this limit.
- Retain the 1,000-request/5,000,000-token/15-minute live-admission floors and
  full route-specific reservations. Old helpers pinned to 69 uncertainties
  must not run against the current 70-uncertainty boundary.
- Recordings, videos, live ledgers and downloaded infrastructure evidence
  stay under ignored `artifacts/`. Version experiment reports, prompt archives,
  curated excerpts and the budget snapshot. Preserve `legacy/` separately.

## Development

- Work in `src/mcpkart/` and `tests/`; do not alter `legacy/` for the solo PoC.
- Setup: `bash scripts/setup_cloud.sh`, or `uv sync --locked --dev` with Python
  3.14.8. Read [Cloud development](docs/cloud-development.md) for setup and access.
- Check: `env -u OPENROUTER_API_KEY .venv/bin/pytest -q` and
  `.venv/bin/ruff check src tests scripts`. Optional Rust tests may skip.
  If the default uv cache is read-only, set `UV_CACHE_DIR` to a writable `/tmp`
  directory. Do not change HOME or bypass the managed network proxy.
- Start the spectator/MCP server with `.venv/bin/mcpkart-web`; server and
  controller must share a host for monotonic-clock comparisons. A Cloud
  localhost URL is not a public browser URL; use supported forwarding or an
  explicitly configured tunnel and preserve recordings for replay.
- For open-web research, prefer available authoritative connectors and Exa.
