FROM debian:trixie-slim

WORKDIR /app

# Install curl for the install script
RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Install Mistral Vibe CLI using official installer
RUN curl -LsSf https://mistral.ai/vibe/install.sh | bash

# Add vibe to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy base vibe config and entrypoint
COPY vibe-config.toml /app/vibe-config.toml
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
