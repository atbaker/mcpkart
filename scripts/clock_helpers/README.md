These are the frozen inputs for `scripts/package_remote_clock.py`. They make the
credential-free Linux clock experiment reproducible from a fresh checkout,
without downloading the ignored local experiment artifacts.

`PROVENANCE.json` records their origin and hashes. The three `.py.in` helpers are
byte-for-byte copies of the historical Rust spike helpers. Their old artifact
paths and Rust identity checks are intentional templates: the packager replaces
only the declared paths, labels, and runtime identity for the selected engine,
and records every substitution in the package manifest.

`reference.json` retains the original reference metadata and its unchanged
successful seed-zero, zero-delay trial (56.7 seconds), including the exact track
and handling contract. Other calibration trials were omitted. It contains no
credentials or machine-specific environment facts. New model comparisons
should generate their own multi-seed reference as described in the root README.

Package an experiment locally (this makes no network or model calls):

```sh
uv run python scripts/package_remote_clock.py --engine python --output /tmp/python-clock.tar.gz
```

Run the resulting package on an existing Linux Docker host with
`bash scripts/run_remote_clock.sh --engine python /path/to/fresh/results`.
The runner builds and validates both engines for the historical parity check;
its timed races use only the selected engine. It does not provision a VM or run
paid model trials. The original local recordings remain under ignored
`artifacts/` paths.

To check an existing Linux server directly, prepare the helpers and run them
from the repository root, in the same PID namespace as the server:

```sh
uv run python scripts/package_remote_clock.py --engine python --prepare-directory artifacts/clock-check
uv run python artifacts/clock-check/run_controls.py
uv run python artifacts/clock-check/long_clock.py
uv run python scripts/verify_clock_validation.py --engine python --directory artifacts/clock-check
```

The server must listen on `127.0.0.1:8765`, use the process backend with asyncio
pacing, and have the watchdog disabled. The control helper discovers and verifies
its parent PID before pausing it. The final verifier checks the saved timing gates
and the actual child worker provenance in all four final recordings. Each command
exits unsuccessfully if its gate fails. Stop on any failure; preserve the directory
and use a new output path for another declared attempt. Do not start paid model
trials until the final verifier passes.
