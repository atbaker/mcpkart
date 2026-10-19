# Optional Rust comparison

The project uses the isolated Python worker by default. Python passed the
GCP timing gate for the current solo workload; see
[`docs/experiments/0009-python-on-gcp.md`](../docs/experiments/0009-python-on-gcp.md).
This crate preserves the earlier Rust spike and deterministic replay tools.
It is not required for normal development or Codex Cloud setup.

To build and select it explicitly:

```sh
cargo build --release --locked --manifest-path rust-race/Cargo.toml
.venv/bin/mcpkart-web --race-engine rust --port 8767
```

For the optional Docker image, build with
`docker build --target rust --tag mcpkart-rust:dev .`, then select
`--race-engine rust` when starting the server. The default Docker target only
installs Python dependencies. No build or server command starts model calls.
