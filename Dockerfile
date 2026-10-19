ARG PYTHON_IMAGE=python:3.14.8-slim-bookworm
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.12.23
ARG RUST_IMAGE=rust:1.96.0-slim-bookworm

FROM ${UV_IMAGE} AS uv
FROM ${RUST_IMAGE} AS race-builder
WORKDIR /build/rust-race
COPY rust-race/Cargo.toml rust-race/Cargo.lock ./
COPY rust-race/src ./src
RUN cargo build --release --locked

FROM ${PYTHON_IMAGE} AS python-base

COPY --from=uv /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    UV_PROJECT_ENVIRONMENT=/opt/mcpkart-venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH=/opt/mcpkart-venv/bin:$PATH

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Install the lock's runtime and development dependencies into a Linux-only
# environment. Source is imported directly, preserving benchmark fingerprints
# and avoiding an unpinned build-backend download for an editable project.
RUN uv sync --locked --no-install-project --no-cache --python /usr/local/bin/python

COPY src ./src
COPY scripts ./scripts
COPY tests ./tests
# Packaging tests exercise the same credential-free source allowlist in-image.
COPY Dockerfile .dockerignore ./
COPY rust-race/Cargo.toml rust-race/Cargo.lock ./rust-race/
COPY rust-race/src ./rust-race/src
RUN mkdir /app/artifacts

EXPOSE 8765
CMD ["python", "-m", "mcpkart.web", "--host", "0.0.0.0", "--port", "8765", "--clock-backend", "process", "--clock-pacing", "asyncio"]

# Keep the historical Rust comparison available without building it for normal
# Python development. Select explicitly with `docker build --target rust`.
FROM python-base AS rust
COPY --from=race-builder /build/rust-race/target/release/mcpkart-race /usr/local/bin/mcpkart-race
ENV MCPKART_RUST_WORKER=/usr/local/bin/mcpkart-race

# The last stage is the default target; BuildKit skips the unused Rust builder.
FROM python-base AS python
