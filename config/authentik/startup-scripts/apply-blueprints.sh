#!/bin/bash
set -e

echo "🚀 Starting Authentik blueprint auto-deployment..."

# Wait for Authentik server to be ready
echo "⏳ Waiting for Authentik server to be ready..."
until curl -f http://localhost:9000/if/admin/ >/dev/null 2>&1; do
    echo "   Waiting for Authentik server..."
    sleep 5
done

echo "✅ Authentik server is ready!"

# Apply blueprints using the management command
echo "📋 Applying custom blueprints..."

# Apply blueprints idempotently
/opt/goauthentik/bin/ak apply_blueprint /blueprints/custom/00-proxy-provider.yaml
/opt/goauthentik/bin/ak apply_blueprint /blueprints/custom/forward-auth.yaml

echo "✅ Blueprint auto-deployment completed successfully!"
echo "🎯 Authentik is ready for forward authentication!"
