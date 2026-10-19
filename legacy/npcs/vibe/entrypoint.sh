#!/bin/bash
set -e

# Required env vars: MCP_SERVER_URL, MCP_AUTH_TOKEN, RACE_ID

# Create vibe home directory
VIBE_HOME="${VIBE_HOME:-/root/.vibe}"
mkdir -p "$VIBE_HOME/logs/session"

# Copy base config
cp /app/vibe-config.toml "$VIBE_HOME/config.toml"

# Append MCP server config with auth token
cat >> "$VIBE_HOME/config.toml" << EOF

[[mcp_servers]]
name = "mcpkart"
transport = "http"
url = "${MCP_SERVER_URL}"
headers = { "Authorization" = "Bearer ${MCP_AUTH_TOKEN}" }
EOF

# Run vibe with the race prompt - must explicitly pass race_id to join the correct race
exec vibe -p "You are racing in MCP Kart. Call join_race with race_id=\"${RACE_ID}\" to join this race, then use the control tool to race. Don't stop to chat with me, I want you to race on your own. While the race is in preparation phase, you should just sleep until the race begins. Play to win!"
