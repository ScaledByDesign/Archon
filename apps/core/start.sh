#!/usr/bin/env bash
set -euo pipefail
# Remove quarantine (mac Gatekeeper) just in case
xattr -dr com.apple.quarantine . 2>/dev/null || true
docker compose up -d
echo "Stack is starting. Try: curl -s http://localhost:${LITELLM_PORT}/health || true"
