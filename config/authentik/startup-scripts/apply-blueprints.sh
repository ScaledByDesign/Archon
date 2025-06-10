#!/bin/bash

# Authentik Blueprint Auto-Application Script
# This script ensures blueprints are applied during container startup

echo "Starting Authentik blueprint auto-application..."

# Wait for Authentik to be ready
echo "Waiting for Authentik to be ready..."
until ak healthcheck > /dev/null 2>&1; do
    echo "Authentik not ready yet, waiting 5 seconds..."
    sleep 5
done

echo "Authentik is ready, applying blueprints..."

# Apply all custom blueprints
for blueprint in /blueprints/custom/*.yaml; do
    if [ -f "$blueprint" ]; then
        echo "Applying blueprint: $blueprint"
        ak apply_blueprint "$blueprint" || echo "Failed to apply blueprint: $blueprint"
    fi
done

echo "Blueprint auto-application completed."
