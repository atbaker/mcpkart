# Linux container development

The image uses Python 3.14.8 and uv 0.12.23, matching the local interpreter and
dependency tool versions. `uv sync --locked` installs `uv.lock`, including test
tools, into `/opt/mcpkart-venv`. The source runs from `/app/src`; no host virtual
environment or project build-backend download is used. These commands follow
the [uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/).

Only locked dependency metadata, Python/Rust source, control scripts, and tests enter the image. `.dockerignore`
excludes environment files, credentials outside those allowlisted inputs, Git,
legacy code, recordings, and generated caches. Build arguments can pin the
Python and uv images to verified registry digests for a declared experiment;
record the resolved images and Docker VM resources with its results.

The default image runs Python and does not build Rust. Rust source and its
lockfile remain for historical experiment fingerprints. For the optional
comparison, build with `docker build --target rust --tag mcpkart-rust:dev .`.
That target builds Rust 1.96.0 with `cargo build --release --locked` and adds
the binary to the same Python base. Select it by appending
`python -m mcpkart.web --host 0.0.0.0 --port 8765 --race-engine rust` to
`docker run`; use `--clock-mode rust_fixed_step_wall_clock` with the control
harness. [Python passed the full GCP timing gate](experiments/0009-python-on-gcp.md)
and remains the chosen engine for the solo PoC.

Build and start from the repository root:

```sh
docker build --tag mcpkart-linux:dev .
mkdir -p artifacts
docker run --detach --name mcpkart-linux --init \
  --publish 127.0.0.1:8766:8765 \
  --mount "type=bind,source=$PWD/artifacts,target=/app/artifacts" \
  mcpkart-linux:dev
```

Open [the Linux spectator](http://127.0.0.1:8766). The existing macOS server on
port 8765 is separate. The image defaults to process isolation with asyncio
pacing. Native pacing remains an explicit diagnostic option.

Run **both server and benchmark/controller inside this same container**.
Container-side commands use `http://127.0.0.1:8765/mcp`, while the host browser
uses port 8766. `--init` keeps the HTTP server above PID 1, which the verified
parent-pause controller requires. Obtain that PID from the container's own
`/api/state`; do not substitute a host PID or compare host and Linux monotonic
timestamps.

```sh
docker exec mcpkart-linux python -m pytest -q
docker exec mcpkart-linux python -m mcpkart.bench live-reference \
  --url http://127.0.0.1:8765/mcp \
  --reference scripts/clock_helpers/reference.json \
  --output artifacts/linux-controls/manual-reference
```

The frozen seed-zero reference ships with the repository and image; the
validation harness is included at `/app/scripts/validate_clock.py`. Use a fresh output directory. Run the declared
consecutive controls and longer free clock control before any paid screen;
preserve the first failed control rather than retrying until a pass. The Linux
experiment document records the exact gate and outcomes.

The source and dependency files are copied into the image. Rebuild after source
changes and freeze the image during timed runs. For a read-only live source
mount, add `--mount "type=bind,source=$PWD/src,target=/app/src,readonly"`; retain
the container's `/opt/mcpkart-venv`. Do not mount the whole repository over
`/app`, since that would expose the host `.env`, Git metadata, and `.venv`.

## Optional development container

Create the local `artifacts/` directory, then open this project with a Dev
Containers client. `.devcontainer/devcontainer.json` builds the same image,
mounts source/tests read-only and artifacts writable, enables an init process,
and publishes the spectator on host port 8766. Stop the named CLI container
first if it is using that port. No race or model request starts automatically.

In a container terminal, start the server:

```sh
python -m mcpkart.web --host 0.0.0.0 --port 8765 \
  --clock-backend process --clock-pacing asyncio
```

Use a second terminal in that container for the driver. Edit source on the host
between runs; dependency changes require rebuilding. Use `python` directly for
tests and commands so a timed run cannot trigger an implicit dependency sync.

## OpenRouter access after the free gate

Free controls need no credentials. Keep the development server/container
credential-free, and pass API access only to the paid driver process after the
gate passes. With the key in the repository's ignored `.env` file:

```sh
docker exec --env-file .env mcpkart-linux \
  python -m mcpkart.bench screen \
  --url http://127.0.0.1:8765/mcp \
  --reference scripts/clock_helpers/reference.json \
  --models typesafe/jev-1.14 --telemetry road_navigation \
  --trials 1 --output artifacts/jev-linux-navigation-v1
```

Docker reads that file on the host and supplies its values only to this driver,
without putting the key in command text, build arguments, or the image.
Run from `/app` and bind the existing whole `artifacts/` directory
so the driver uses the shared `artifacts/budget.json` ledger and $10 cap. Finish
one paid experiment before starting another ledger writer. On a new checkout,
follow the [budget handoff instructions](cloud-development.md) first: a new
clone does not create a new spending allowance.

Stop and remove the named development container when finished:

```sh
docker stop mcpkart-linux
docker rm mcpkart-linux
```
