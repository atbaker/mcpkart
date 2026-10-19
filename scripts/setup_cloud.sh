#!/usr/bin/env bash
# Install the Python PoC without starting services or making model requests.
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

UV_VERSION=0.12.23
PYTHON_VERSION=3.14.8

if command -v uv >/dev/null 2>&1 && [[ "$(uv --version)" == "uv $UV_VERSION "* ]]; then
  UV_BIN="$(command -v uv)"
else
  # A versioned user directory leaves any existing uv installation alone.
  UV_DIRECTORY="${XDG_DATA_HOME:-$HOME/.local/share}/mcpkart/uv/$UV_VERSION"
  UV_BIN="$UV_DIRECTORY/uv"
  if [[ ! -x "$UV_BIN" ]]; then
    INSTALLER="$(mktemp)"
    trap 'rm -f "$INSTALLER"' EXIT
    curl --fail --silent --show-error --location \
      "https://astral.sh/uv/$UV_VERSION/install.sh" --output "$INSTALLER"
    UV_UNMANAGED_INSTALL="$UV_DIRECTORY" sh "$INSTALLER"
    rm -f "$INSTALLER"
    trap - EXIT
  fi
fi

[[ "$("$UV_BIN" --version)" == "uv $UV_VERSION "* ]]
UV_PROJECT_ENVIRONMENT="$PROJECT_ROOT/.venv" "$UV_BIN" sync --locked --dev --python "$PYTHON_VERSION"
.venv/bin/python -c 'import sys; from mcpkart.sim import Simulation; assert sys.version_info[:3] == (3, 14, 8); assert Simulation().observation()["tick"] == 0; print("Python setup ready; no race or model request started.")'

# Carry forward the recorded spend on a clean clone, never replace a live ledger.
.venv/bin/python - <<'PY'
import json
from pathlib import Path

snapshot = Path("docs/experiments/model-budget-snapshot.json")
payload = snapshot.read_bytes()
state = json.loads(payload)
assert state["schema_version"] == 1 and state["pending"] == {}
assert 0 <= state["charged_usd"] <= state["cap_usd"] <= 10
ledger = Path("artifacts/budget.json")
ledger.parent.mkdir(exist_ok=True)
try:
    with ledger.open("xb") as output:
        output.write(payload)
    print("Initialized ignored budget ledger from the recorded spending snapshot.")
except FileExistsError:
    print("Kept the existing budget ledger unchanged.")
PY

cat <<'EOF'
Model-free checks:
  .venv/bin/pytest -q
  .venv/bin/ruff check src tests scripts

Start the Python server in a separate terminal:
  env -u OPENROUTER_API_KEY .venv/bin/python -m mcpkart.web --host 127.0.0.1 --port 8765 --race-engine python --clock-backend process --clock-pacing asyncio

See docs/cloud-development.md before starting timed or paid experiments.
EOF
