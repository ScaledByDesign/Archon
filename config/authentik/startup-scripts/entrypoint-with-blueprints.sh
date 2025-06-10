#!/bin/bash
set -e

echo "🚀 Starting Authentik server with dynamic blueprint deployment..."

# Generate blueprints from templates first
echo "🔧 Generating blueprints from templates..."
/blueprints/startup-scripts/generate-blueprints.sh

# Start Authentik server in background
echo "📡 Starting Authentik server..."
exec /lifecycle/ak server &
SERVER_PID=$!

# Function to cleanup on exit
cleanup() {
    echo "🔄 Shutting down Authentik server..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}
trap cleanup EXIT

# Wait for server to be ready
echo "⏳ Waiting for Authentik server to be ready..."
timeout=120
elapsed=0
until timeout 5 bash -c '</dev/tcp/localhost/9000' 2>/dev/null; do
    if [ $elapsed -ge $timeout ]; then
        echo "❌ Timeout waiting for Authentik server"
        exit 1
    fi
    echo "   Server starting... (${elapsed}s)"
    sleep 5
    elapsed=$((elapsed + 5))
done

echo "✅ Authentik server is ready!"

# Apply blueprints
echo "📋 Applying generated blueprints..."
if [ -d "/blueprints/custom" ]; then
    for blueprint in /blueprints/custom/*.yaml; do
        if [ -f "$blueprint" ]; then
            echo "   Applying: $(basename $blueprint)"
            /lifecycle/ak apply_blueprint "$blueprint" || echo "⚠️  Failed to apply $(basename $blueprint)"
        fi
    done
    echo "✅ Blueprint auto-deployment completed!"
else
    echo "⚠️  No custom blueprints directory found"
fi

# Keep server running in foreground
echo "🎯 Authentik is ready for forward authentication with domain: ${DOMAIN:-localhost}!"
wait $SERVER_PID
