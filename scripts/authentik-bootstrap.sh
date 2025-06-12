#!/bin/bash
# Authentik Bootstrap Script - Auto-applies blueprints on startup

set -e

echo "🔐 Authentik Bootstrap Setup..."

# Wait for Authentik to be ready
echo "Waiting for Authentik to be ready..."
retries=0
max_retries=30
while [ $retries -lt $max_retries ]; do
    if curl -s http://localhost:9000/if/admin/ > /dev/null 2>&1; then
        echo "✓ Authentik is ready"
        break
    fi
    retries=$((retries + 1))
    sleep 2
done

if [ $retries -eq $max_retries ]; then
    echo "❌ Authentik not ready, skipping blueprint application"
    exit 1
fi

# Apply blueprints in order
BLUEPRINT_DIR="/blueprints/custom"
BLUEPRINTS=(
    "00-flows.yaml"
    "01-users.yaml" 
    "02-provider.yaml"
    "03-simple-policy.yaml"
    "04-outpost-provider-assignment.yaml"
    "05-outpost-permissions.yaml"
    "litellm-oauth-integration.yaml"
    "n8n-oauth-integration.yaml"
)

echo "Applying Authentik blueprints..."
for blueprint in "${BLUEPRINTS[@]}"; do
    if [ -f "$BLUEPRINT_DIR/$blueprint" ]; then
        echo "Applying blueprint: $blueprint"
        if ak apply_blueprint "$BLUEPRINT_DIR/$blueprint"; then
            echo "✓ $blueprint applied successfully"
        else
            echo "⚠ Failed to apply $blueprint (may already exist)"
        fi
    else
        echo "⚠ Blueprint $blueprint not found, skipping"
    fi
done

echo "✓ Authentik bootstrap completed"
