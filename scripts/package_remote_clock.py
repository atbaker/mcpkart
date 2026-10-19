"""Create an allowlisted, credential-free Linux clock experiment bundle.

This only writes a local archive or prepares local clock controls. It never
connects, provisions, uploads, starts Docker, or reads credentials. The remote
runner preserves failed experiments.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "mcpkart-remote-clock"
EXCLUDED_COMPONENTS = frozenset({".git", ".venv", "venv", "legacy", "target", "__pycache__",
                                  ".pytest_cache", ".ruff_cache", "artifacts"})
ROOT_FILES = ("Dockerfile", ".dockerignore", "pyproject.toml", "uv.lock")
TREES = ("src", "tests", "scripts", "rust-race/src")
RUST_FILES = ("rust-race/Cargo.toml", "rust-race/Cargo.lock")
HELPERS = {
    "remote-clock/reference.json": "scripts/clock_helpers/reference.json",
    "remote-clock/run_controls.py": "scripts/clock_helpers/run_controls.py.in",
    "remote-clock/long_clock.py": "scripts/clock_helpers/long_clock.py.in",
    "remote-clock/environment.py": "scripts/clock_helpers/environment.py.in",
}
CLOCK_MODES = {"rust": "rust_fixed_step_wall_clock", "python": "fixed_step_wall_clock"}


def transform_helper(content: bytes, destination: str, engine: str,
                     artifact_directory: str | None = None) -> tuple[bytes, list[dict]]:
    """Adapt only artifact paths, labels, and runtime identity in frozen helpers."""
    substitutions = []

    def replace(old: bytes, new: bytes, count: int) -> None:
        nonlocal content
        if content.count(old) != count:
            raise ValueError(f"Helper changed; review {destination}: {old!r}")
        content = content.replace(old, new)
        substitutions.append({"from": old.decode(), "to": new.decode(), "count": count})

    directory = "remote-python-clock-v1" if engine == "python" else "remote-clock-v1"
    mode = CLOCK_MODES[engine]
    identity = f"info.get('engine', 'python') == '{engine}'".encode()
    if destination.endswith("run_controls.py"):
        if artifact_directory is None:
            replace(b"artifacts/rust-clock-v1/", f"artifacts/{directory}/".encode(), 2)
        else:
            for name in ("reference.json", "controls"):
                replace(repr(f"artifacts/rust-clock-v1/{name}").encode(),
                        repr(str(Path(artifact_directory) / name)).encode(), 1)
        replace(b"assert info['backend']=='process' and info['clock_mode']=='rust_fixed_step_wall_clock'",
                b"assert info['backend']=='process' and info['clock_mode']=='" + mode.encode()
                + b"' and " + identity, 1)
        replace(b"'--clock-mode','rust_fixed_step_wall_clock'",
                f"'--clock-mode','{mode}'".encode(), 1)
    elif destination.endswith("long_clock.py"):
        replace(b"info['clock_mode'] == 'rust_fixed_step_wall_clock' and info.get('engine') == 'rust'",
                b"info['clock_mode'] == '" + mode.encode() + b"' and " + identity, 1)
        if engine == "python":
            replace(b"Rust", b"Python", 2)
    elif destination.endswith("environment.py"):
        replace(b"assert info['process_pid'] > 1 and info['clock_mode'] == 'rust_fixed_step_wall_clock'",
                b"assert info['process_pid'] > 1 and info['backend'] == 'process' and "
                b"info['clock_mode'] == '" + mode.encode() + b"' and " + identity, 1)
    return content, substitutions


def prepare_validation(root: Path, output: Path, engine: str = "python") -> dict:
    """Materialize only the frozen free controls beside their future results.

    Run the generated helpers from the repository root, in the same Linux PID
    namespace as its process-backend server listening on localhost:8765.
    """
    if engine not in CLOCK_MODES:
        raise ValueError(f"Unknown engine: {engine}")
    if output.exists():
        raise ValueError(f"Refusing to overwrite validation directory: {output}")
    files, sources = {}, {}
    for destination, source in HELPERS.items():
        content = read_regular(root, source)
        transformed, substitutions = transform_helper(content, destination, engine, str(output.resolve()))
        name = Path(destination).name
        files[name] = transformed
        sources[name] = {"source": source, "source_sha256": hashlib.sha256(content).hexdigest(),
                         "substitutions": substitutions}
    manifest = {"engine": engine, "expected_clock_mode": CLOCK_MODES[engine], "model_requests": 0,
                "helper_sources": sources}
    output.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        (output / name).write_bytes(content)
    (output / "HELPER-MANIFEST.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    return {"directory": str(output), **manifest}


def allowed_source(path: Path) -> bool:
    return not any(part in EXCLUDED_COMPONENTS or part == ".env" or part.startswith(".env.")
                   for part in path.parts) and path.suffix not in {".pyc", ".pyo"}


def read_regular(root: Path, relative: str) -> bytes:
    path = root/relative
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Bundle source must be a regular file inside the repo: {relative}")
    return path.read_bytes()


def selected_files(root: Path) -> dict[str, bytes]:
    selected = {relative: read_regular(root, relative) for relative in (*ROOT_FILES, *RUST_FILES)}
    for tree in TREES:
        directory = root/tree
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"Missing regular source directory: {tree}")
        for path in sorted(directory.rglob("*")):
            relative = path.relative_to(root)
            if not allowed_source(relative):
                continue
            if path.is_symlink():
                raise ValueError(f"Refusing source symlink: {relative}")
            if path.is_file():
                selected[relative.as_posix()] = read_regular(root, relative.as_posix())
    return selected


def package(root: Path, output: Path, engine: str = "rust") -> dict:
    if engine not in CLOCK_MODES:
        raise ValueError(f"Unknown engine: {engine}")
    if output.exists():
        raise ValueError(f"Refusing to overwrite bundle: {output}")
    files = selected_files(root)
    helper_sources = {}
    for destination, source in HELPERS.items():
        content = read_regular(root, source)
        helper_sources[destination] = {"source": source, "source_sha256": hashlib.sha256(content).hexdigest()}
        content, substitutions = transform_helper(content, destination, engine)
        helper_sources[destination]["substitutions"] = substitutions
        files[destination] = content
    reference = json.loads(files["remote-clock/reference.json"])
    zero_delay = [row["elapsed"] for row in reference["trials"]
                  if row["seed"] == 0 and row["delay_s"] == 0 and row["finished"]]
    if len(zero_delay) != 1 or abs(zero_delay[0]-56.7) > 1e-6:
        raise ValueError("Expected the frozen successful 56.7 second seed-zero reference")
    manifest = {"format": 2, "purpose": f"credential-free remote Linux {engine} clock comparison",
                "engine": engine, "expected_clock_mode": CLOCK_MODES[engine],
                "experiment_directory": "remote-python-clock-v1" if engine == "python" else "remote-clock-v1",
                "model_requests": 0, "reference_s": zero_delay[0], "long_clock_s": zero_delay[0]*3,
                "helper_sources": helper_sources,
                "files": {name: {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
                          for name, content in sorted(files.items())}}
    files["PACKAGE-MANIFEST.json"] = (json.dumps(manifest, indent=2, allow_nan=False)+"\n").encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("xb") as stream, tarfile.open(fileobj=stream, mode="w:gz") as archive:
            for relative, content in sorted(files.items()):
                entry = tarfile.TarInfo(f"{ARCHIVE_ROOT}/{relative}")
                entry.size = len(content)
                entry.mode = 0o755 if relative == "scripts/run_remote_clock.sh" else 0o644
                entry.mtime = 0
                archive.addfile(entry, io.BytesIO(content))
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return {"archive": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            "files": len(files), "bytes": output.stat().st_size,
            "reference_s": manifest["reference_s"], "long_clock_s": manifest["long_clock_s"],
            "engine": engine, "expected_clock_mode": CLOCK_MODES[engine]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--output", type=Path, help="Write a credential-free remote source archive")
    destination.add_argument("--prepare-directory", type=Path,
                             help="Prepare free controls to run against an existing local Linux server")
    parser.add_argument("--engine", choices=tuple(CLOCK_MODES), default="rust")
    args = parser.parse_args()
    if args.prepare_directory:
        print(json.dumps(prepare_validation(ROOT, args.prepare_directory.resolve(), args.engine)))
    else:
        print(json.dumps(package(ROOT, args.output.resolve(), args.engine)))


if __name__ == "__main__":
    main()
