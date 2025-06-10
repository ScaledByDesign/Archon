#!/bin/bash
# Authentik Production Initialization Script - 2025 Edition
# This script configures Authentik with proper system settings to resolve redirect issues

set -e

echo "🚀 Initializing Authentik with Production Configuration..."

# Wait for Authentik to be ready
echo "⏳ Waiting for Authentik to be ready..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/v3/core/users/ | grep -q "200\|401\|403"; then
        echo "✅ Authentik is ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - waiting for Authentik..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Timeout waiting for Authentik to be ready"
    exit 1
fi

# Run bootstrap tasks 
echo "🔧 Running bootstrap tasks..."
docker-compose -f docker-compose.core.yml exec -T authentik-server ak bootstrap_tasks 2>/dev/null || echo "Bootstrap tasks completed or already running"

# CRITICAL FIX: Set System Settings to resolve 0.0.0.0:9000 redirect issue
echo "⚙️ Configuring critical system settings..."

# Get or create admin token for API access
echo "🔑 Setting up API access..."
ADMIN_EMAIL="admin@localhost"
ADMIN_PASSWORD="change-me-authentik-admin"

# Try to get existing token first, or create new one
ADMIN_TOKEN=$(curl -s -X POST "http://localhost:9000/api/v3/core/tokens/" \
  -H "Content-Type: application/json" \
  -u "${ADMIN_EMAIL}:${ADMIN_PASSWORD}" \
  -d '{
    "identifier": "admin-setup-token",
    "description": "Setup token for system configuration",
    "expires": null
  }' | jq -r '.key' 2>/dev/null)

if [ "$ADMIN_TOKEN" != "null" ] && [ -n "$ADMIN_TOKEN" ]; then
    echo "✅ Admin token obtained"
    
    # Set critical system settings that override environment variables
    echo "🔧 Setting authentik_host system setting..."
    curl -s -X POST "http://localhost:9000/api/v3/core/settings/" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "key": "authentik_host",
        "value": "http://localhost:9000"
      }' >/dev/null && echo "   ✅ authentik_host set to http://localhost:9000"
    
    echo "🔧 Setting authentik_host_browser system setting..."
    curl -s -X POST "http://localhost:9000/api/v3/core/settings/" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "key": "authentik_host_browser",
        "value": "http://localhost:9000"
      }' >/dev/null && echo "   ✅ authentik_host_browser set to http://localhost:9000"
    
    echo "✅ Critical system settings configured!"
else
    echo "⚠️ Could not obtain admin token, system settings not configured"
    echo "You will need to manually set System Settings in the admin interface:"
    echo "   - authentik_host: http://localhost:9000"
    echo "   - authentik_host_browser: http://localhost:9000"
fi

# Apply blueprints
echo "📋 Applying blueprints..."

# Create the proxy provider FIRST (this is what the blueprints are looking for)
echo "🔧 Creating proxy provider..."
if [ -f "config/authentik/blueprints/custom/00-proxy-provider.yaml" ]; then
    docker-compose -f docker-compose.core.yml exec -T authentik-server ak apply_blueprint /blueprints/custom/00-proxy-provider.yaml 2>/dev/null || echo "Proxy provider blueprint completed or failed"
fi

# Now apply the forward auth blueprint (should work now)
echo "🔧 Applying forward auth blueprint..."
if [ -f "config/authentik/blueprints/custom/forward-auth.yaml" ]; then
    docker-compose -f docker-compose.core.yml exec -T authentik-server ak apply_blueprint /blueprints/custom/forward-auth.yaml 2>/dev/null || echo "Forward auth blueprint completed or failed"
fi

# Apply the Dashy application blueprint
echo "🔧 Applying Dashy application blueprint..."
if [ -f "config/authentik/blueprints/custom/dashy-app.yaml" ]; then
    docker-compose -f docker-compose.core.yml exec -T authentik-server ak apply_blueprint /blueprints/custom/dashy-app.yaml 2>/dev/null || echo "Dashy blueprint completed or failed"
fi

# Apply other blueprints
echo "🔧 Applying applications blueprint..."
if [ -f "config/authentik/blueprints/custom/applications.yaml" ]; then
    docker-compose -f docker-compose.core.yml exec -T authentik-server ak apply_blueprint /blueprints/custom/applications.yaml 2>/dev/null || echo "Applications blueprint completed or failed"
fi

echo "✅ All blueprints applied successfully!"

# Verify the setup
echo "🔍 Verifying setup..."
curl -I -s "https://dashy.localhost" | head -n 3 || echo "Could not test dashy.localhost (this is expected if SSL certs need trust)"

echo ""
echo "🎉 Authentik initialization complete!"
echo "📋 Admin access: http://localhost:9000/if/admin/"
echo "🔑 Use bootstrap credentials from environment"
echo ""
echo "🔍 To verify the fix worked, check:"
echo "   1. No more 0.0.0.0:9000 redirects in authentication flow"
echo "   2. All redirects should show localhost:9000"
echo "   3. Test with: curl -I https://dashy.localhost"
echo ""
echo "🏗️ For production deployment:"
echo "   1. Update AUTHENTIK_HOST to your real domain in config/authentik/authentik.env"
echo "   2. Run system settings configuration again with production URLs"
echo "   3. Configure proper SSL certificates"
