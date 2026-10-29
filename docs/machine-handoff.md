# Moving MCP Kart to another machine

The migration checkpoint is 29 October 2026. Code and findings through study
0085 are on `main`; the raw experiment evidence is a separate transfer archive.
All paid experiment windows are closed. No model calls are needed for setup,
tests, or viewing the exported replays.

## Restore

1. Clone this repository and check out `main`.
2. Download `mcpkart-transfer-2026-10-29.tar.zst` from the migration chat and check
   its SHA-256 against [the transfer receipt](machine-handoff-transfer.json).
3. Extract it from the repository root:

   ```sh
   tar --zstd -xf /path/to/mcpkart-transfer-2026-10-29.tar.zst
   ```

   Install `zstd` if needed. A portable alternative is
   `zstd -dc /path/to/mcpkart-transfer-2026-10-29.tar.zst | tar -xf -`.
   The archive is about 723 MB compressed and restores about 11.4 GB of files.

   This restores `artifacts/`, including the authoritative ledger, recordings,
   native requests/replies, frozen source, experiment helpers, clock evidence,
   videos and standalone replay bundles. Per-file hashes are recorded in
   `artifacts/transfer-manifest-2026-10-29.json`. Do not overwrite a ledger that
   has accumulated newer charges on another machine.
4. Install Python 3.14.8 and `uv`, then run `bash scripts/setup_cloud.sh` on
   Linux. Alternatively, run `uv sync --locked --dev --python 3.14.8`.
5. Configure `OPENROUTER_API_KEY` as a managed secret or ignored `.env` when
   new paid work is authorized. Credentials are not included in Git or the
   transfer archive. Preserve the managed proxy and CA settings in Cloud.
6. Run free checks:

   ```sh
   env -u OPENROUTER_API_KEY .venv/bin/pytest -q
   .venv/bin/ruff check src tests scripts
   ```

Python is the runtime for continuing this project. Rust is optional historical
comparison code; its tests can skip. Existing virtual environments and local
editor/tool installations are not part of the transfer.

## Current boundary

The authoritative `artifacts/budget.json` and versioned
[snapshot](experiments/model-budget-snapshot.json) agree:

| Field | Value |
| --- | ---: |
| Requests | 99,403 / 110,000 |
| Charged dollars | 11.520516764002778 / 20 |
| Charged tokens | 333,848,829 / 500,000,000 |
| Historical uncertain requests | 71 |
| Pending reservations | 0 |

Preserve every charge and uncertainty; do not reset or refund the ledger.
Use one authoritative copy and one paid writer. Remaining budget does not reopen
closed studies. New paid work needs a new finite prospective registration under
user authorization, with the existing admission floors and full reservations.

Historical server PIDs, process sessions and timing qualifications refer to the
old machine. They are evidence, not live services or valid qualification for the
new host. Before any new paid driving, start a fresh Python server and run a
complete current-source timing qualification bound to its boot and process,
plus the exact-interface free checks for the new study. Never rerun an old paid
helper to resume a closed experiment. Source-relative historical hashes remain
useful; some old helper paths are absolute `/workspace/mcpkart` paths.

## Findings and viewing

Start with [0085](experiments/0085-both-head-timing.md),
[0084](experiments/0084-motion-validation.md), the
[experiment index](experiments/README.md), and the
[two-kart guide](two-kart-driver.md). Goal-only driving stays the direction;
experimental motion, geometry and timing additions have not earned promotion.

For the latest interactive replays, extract
`artifacts/jev-both-head-timing-v1/mcpkart-both-head-timing-review.zip` and open
its `index.html`. Each exported replay embeds its data and needs no server or
model key. A live spectator can be started with:

```sh
env -u OPENROUTER_API_KEY .venv/bin/python -m mcpkart.duel_web --port 8770
```

A Cloud localhost URL needs forwarding to reach a browser on another machine.
