#!/usr/bin/env bash
# Run an extracted package on an existing Linux Docker host. No model API calls.
# Usage: bash scripts/run_remote_clock.sh [--engine rust|python] [RESULTS_PARENT_DIRECTORY]
set -Eeuo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
ENGINE=rust
if [[ ${1:-} == --engine ]]; then
    ENGINE=${2:-}
    shift 2
fi
case "$ENGINE" in
    rust) EXPERIMENT=remote-clock-v1; CLOCK_MODE=rust_fixed_step_wall_clock ;;
    python) EXPERIMENT=remote-python-clock-v1; CLOCK_MODE=fixed_step_wall_clock ;;
    *) echo 'Expected --engine rust or --engine python.' >&2; exit 2 ;;
esac
if [[ $# -gt 1 ]]; then
    echo 'Expected at most one results parent directory.' >&2
    exit 2
fi
if [[ $(uname -s) != Linux ]]; then
    echo 'Run this experiment on the existing remote Linux host.' >&2
    exit 2
fi
command -v docker >/dev/null
command -v python3 >/dev/null
command -v tar >/dev/null
cd "$ROOT"
python3 - "$ENGINE" "$CLOCK_MODE" "$EXPERIMENT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

manifest = json.loads(Path('PACKAGE-MANIFEST.json').read_text())
engine, mode, experiment = sys.argv[1:]
assert manifest['engine'] == engine and manifest['expected_clock_mode'] == mode
assert manifest['experiment_directory'] == experiment
assert manifest['model_requests'] == 0 and abs(manifest['reference_s']-56.7) < 1e-6
for name, metadata in manifest['files'].items():
    path = Path(name)
    assert not path.is_absolute() and '..' not in path.parts
    assert not path.is_symlink() and path.is_file(), name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == metadata['sha256'], name
assert not Path('.env').exists(), 'This bundle must not contain credentials'
print(f"Verified {len(manifest['files'])} package files; no model requests authorized.")
PY

RESULTS_PARENT=${1:-"$ROOT/artifacts"}
mkdir -p -- "$RESULTS_PARENT"
RESULTS_PARENT=$(cd -- "$RESULTS_PARENT" && pwd)
OUTPUT="$RESULTS_PARENT/$EXPERIMENT"
ARCHIVE="$OUTPUT.tar.gz"
if [[ -e "$OUTPUT" || -e "$ARCHIVE" ]]; then
    echo 'Refusing to overwrite an experiment; choose a fresh results parent.' >&2
    exit 2
fi
mkdir -- "$OUTPUT"
cp -- "$ROOT/remote-clock/"* "$OUTPUT/"
cp -- "$ROOT/PACKAGE-MANIFEST.json" "$OUTPUT/package-manifest.json"
CONTAINER="mcpkart-remote-clock-$$"
IMAGE="mcpkart-remote-clock:run-$$"
CONTAINER_STARTED=0
SPECTATOR_PID=
PHASE=build

collect() {
    STATUS=$?
    trap - EXIT INT TERM HUP
    set +e
    if [[ $CONTAINER_STARTED == 1 ]]; then
        # The helper records the verified server PID before any SIGSTOP can run.
        # This exec is inside our private container PID namespace, never the host.
        docker exec -i "$CONTAINER" python - "$ENGINE" "$CLOCK_MODE" "$EXPERIMENT" <<'PY' >"$OUTPUT/resume-cleanup.log" 2>&1
import json
import os
import signal
import sys
from pathlib import Path

engine, mode, experiment = sys.argv[1:]
path = Path('/app/artifacts') / experiment / 'linux-environment.json'
if path.exists():
    info = json.loads(path.read_text())['runtime_info']
    pid = info['process_pid']
    assert pid > 1 and pid != os.getpid() and info['backend'] == 'process'
    assert info.get('engine', 'python') == engine and info['clock_mode'] == mode
    assert not info['watchdog_enabled']
    try:
        os.kill(pid, signal.SIGCONT)
    except ProcessLookupError:
        pass
PY
    fi
    if [[ -n "$SPECTATOR_PID" ]]; then
        touch "$OUTPUT/host-spectator.stop"
        for _ in {1..40}; do
            kill -0 "$SPECTATOR_PID" 2>/dev/null || break
            sleep .1
        done
        if kill -0 "$SPECTATOR_PID" 2>/dev/null; then
            kill -TERM "$SPECTATOR_PID" 2>/dev/null
            for _ in {1..40}; do
                kill -0 "$SPECTATOR_PID" 2>/dev/null || break
                sleep .1
            done
        fi
        kill -0 "$SPECTATOR_PID" 2>/dev/null && kill -KILL "$SPECTATOR_PID" 2>/dev/null
        wait "$SPECTATOR_PID"
    fi
    if [[ $CONTAINER_STARTED == 1 ]]; then
        docker logs --timestamps "$CONTAINER" >"$OUTPUT/server.log" 2>&1
        docker exec "$CONTAINER" python -c 'import json; from pathlib import Path; print(json.dumps({p.name:p.read_text() for p in (Path("/sys/fs/cgroup")/n for n in ("cpu.max","cpu.stat","memory.max","memory.current","memory.events","cpuset.cpus.effective")) if p.exists()}))' >"$OUTPUT/cgroup-after.json" 2>&1
        docker stop --time 10 "$CONTAINER" >"$OUTPUT/container-stop.log" 2>&1 || docker kill "$CONTAINER" >>"$OUTPUT/container-stop.log" 2>&1
        docker rm "$CONTAINER" >"$OUTPUT/container-remove.log" 2>&1
    fi
    python3 - "$OUTPUT/execution.json" "$STATUS" "$PHASE" "$CONTAINER" "$IMAGE" "$ENGINE" "$CLOCK_MODE" <<'PY'
import json
import sys
from pathlib import Path

path, status, phase, container, image, engine, mode = sys.argv[1:]
Path(path).write_text(json.dumps({'exit_status': int(status), 'last_phase': phase,
    'passes': int(status) == 0 and phase == 'complete', 'model_requests': 0,
    'container_name': container, 'image_tag': image, 'engine': engine,
    'expected_clock_mode': mode}, indent=2)+'\n')
PY
    if ! tar -czf "$ARCHIVE" -C "$RESULTS_PARENT" "$EXPERIMENT"; then
        echo "Result archive failed; individual files remain in $OUTPUT" >&2
        [[ $STATUS == 0 ]] && STATUS=1
    fi
    echo "Results: $OUTPUT"
    echo "Retrieve: $ARCHIVE"
    exit "$STATUS"
}
trap collect EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

docker version --format '{{json .}}' >"$OUTPUT/docker-version.json"
docker info --format '{"operating_system":{{json .OperatingSystem}},"kernel":{{json .KernelVersion}},"architecture":{{json .Architecture}},"cpus":{{.NCPU}},"memory_bytes":{{.MemTotal}},"os_type":{{json .OSType}}}' >"$OUTPUT/docker-host.json"
python3 - "$OUTPUT/host.json" <<'PY'
import json
import os
import platform
import sys
import time
from pathlib import Path

Path(sys.argv[1]).write_text(json.dumps({'platform':platform.platform(), 'machine':platform.machine(),
    'cpu_count':os.cpu_count(), 'cpu_affinity':sorted(os.sched_getaffinity(0)),
    'clock_info':vars(time.get_clock_info('monotonic'))}, indent=2)+'\n')
PY
docker build --target rust --tag "$IMAGE" \
    --build-arg 'RUST_IMAGE=rust:1.96.0-slim-bookworm@sha256:4732ca96fd086cb9be682050c3f0176288eebaac2b80aa2bcefccfaf198e1950' \
    --build-arg 'PYTHON_IMAGE=python:3.14.8-slim-bookworm@sha256:48b13b003dda20b16f9442b8475aa05fe21bf6579a8c881db92ffb4d8fd20f83' \
    --build-arg 'UV_IMAGE=ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21' \
    "$ROOT" >"$OUTPUT/build.log" 2>&1
PHASE=start
if docker container inspect "$CONTAINER" >/dev/null 2>&1; then
    echo "Refusing to reuse an existing container: $CONTAINER" >&2
    exit 2
fi
CONTAINER_STARTED=1
docker run --detach --init --name "$CONTAINER" --publish 127.0.0.1:8765:8765 \
    --mount "type=bind,source=$OUTPUT,target=/app/artifacts/$EXPERIMENT" \
    "$IMAGE" python -m mcpkart.web --host 0.0.0.0 --port 8765 \
    --clock-backend process --clock-pacing asyncio --race-engine "$ENGINE" >"$OUTPUT/container-id.txt"
docker inspect --format '{"id":{{json .Id}},"image":{{json .Image}},"init":{{json .HostConfig.Init}},"memory_limit":{{.HostConfig.Memory}},"nano_cpus":{{.HostConfig.NanoCpus}},"cpu_quota":{{.HostConfig.CpuQuota}},"cpu_period":{{.HostConfig.CpuPeriod}},"cpuset":{{json .HostConfig.CpusetCpus}},"ports":{{json .NetworkSettings.Ports}}}' "$CONTAINER" >"$OUTPUT/container.json"
docker exec "$CONTAINER" python -c 'import time, urllib.request; start=time.monotonic(); ready=False
while time.monotonic()-start<30:
 try:
  with urllib.request.urlopen("http://127.0.0.1:8765/api/state",timeout=1): ready=True; break
 except OSError: time.sleep(.1)
assert ready, "Spectator did not become ready"' >"$OUTPUT/readiness.log" 2>&1

PHASE=preflight
docker exec "$CONTAINER" timeout --signal=INT --kill-after=15s 300s python -m pytest -q >"$OUTPUT/tests.log" 2>&1
docker exec "$CONTAINER" python -m ruff check src tests scripts >"$OUTPUT/lint.log" 2>&1
docker exec "$CONTAINER" timeout --signal=INT --kill-after=15s 120s python scripts/validate_rust_parity.py \
    --output "artifacts/$EXPERIMENT/parity.json" >"$OUTPUT/parity.log" 2>&1
docker exec "$CONTAINER" python -c 'import json, sys; from pathlib import Path; from mcpkart.bench import reference_durations; values=reference_durations(Path(sys.argv[1])); assert abs(values[0]-56.7)<1e-6; print(json.dumps({"reference_durations":values,"deadline_s":values[0]*3}))' "artifacts/$EXPERIMENT/reference.json" >"$OUTPUT/reference-check.json" 2>&1
docker exec "$CONTAINER" python "artifacts/$EXPERIMENT/environment.py" >"$OUTPUT/environment.log" 2>&1

PHASE=scripted-controls
python3 scripts/poll_remote_clock.py "$OUTPUT" >"$OUTPUT/host-spectator.log" 2>&1 &
SPECTATOR_PID=$!
docker exec "$CONTAINER" python "artifacts/$EXPERIMENT/run_controls.py" >"$OUTPUT/controls.log" 2>&1
docker exec -i "$CONTAINER" python - "artifacts/$EXPERIMENT/controls/validation.json" "$ENGINE" "$CLOCK_MODE" <<'PY' >"$OUTPUT/control-gate.log" 2>&1
import json
import sys
from pathlib import Path

path, engine, mode = sys.argv[1:]
value = json.loads(Path(path).read_text())
assert value['passes'] and len(value['controls']) == 3 and value['model_requests'] == 0
module = 'mcpkart.physics_worker' if engine == 'python' else 'mcpkart-rust-worker'
for row in value['controls']:
    race = json.loads(Path(row['trial']).read_text())['race']
    info, provenance = race['runtime_info'], race['process_provenance']
    assert info['backend'] == 'process' and info.get('engine', 'python') == engine
    assert info['clock_mode'] == mode and not info['watchdog_enabled']
    assert provenance['worker_module'] == module and provenance['child_clock_mode'] == mode
    assert provenance['child_web_modules_loaded'] == []
    assert provenance['child_pid'] > 1 and provenance['parent_pid'] == info['process_pid'] > 1
    assert provenance['child_pid'] != provenance['parent_pid']
print(json.dumps({'passes': True, 'engine': engine, 'expected_clock_mode': mode,
                  'verified_worker_module': module, 'controls': 3, 'model_requests': 0}))
PY
PHASE=long-clock
docker exec "$CONTAINER" timeout --signal=INT --kill-after=15s 240s python "artifacts/$EXPERIMENT/long_clock.py" >"$OUTPUT/long-clock.log" 2>&1
docker exec -i "$CONTAINER" python - "artifacts/$EXPERIMENT/long-clock.json" "$ENGINE" "$CLOCK_MODE" <<'PY' >"$OUTPUT/long-clock-gate.log" 2>&1
import json
import sys
from pathlib import Path

path, engine, mode = sys.argv[1:]
value = json.loads(Path(path).read_text())
assert value['passes'] and value['model_requests'] == 0 and abs(value['required_duration_s']-170.1) < 1e-6
info, provenance = value['race']['runtime_info'], value['race']['process_provenance']
module = 'mcpkart.physics_worker' if engine == 'python' else 'mcpkart-rust-worker'
assert info['backend'] == 'process' and info.get('engine', 'python') == engine
assert info['clock_mode'] == mode and not info['watchdog_enabled']
assert provenance['worker_module'] == module and provenance['child_clock_mode'] == mode
assert provenance['child_web_modules_loaded'] == []
assert provenance['child_pid'] > 1 and provenance['parent_pid'] == info['process_pid'] > 1
assert provenance['child_pid'] != provenance['parent_pid']
print(json.dumps({'passes': True, 'engine': engine, 'expected_clock_mode': mode,
                  'verified_worker_module': module, 'model_requests': 0}))
PY
PHASE=complete
