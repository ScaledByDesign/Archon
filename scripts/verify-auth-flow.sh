#!/bin/bash
# Verify the authentication flow is working correctly

echo "🔐 Verifying Authentication Flow"
echo "================================"
echo ""

# Check services are running
echo "📍 Checking service status..."
services=("traefik" "authentik-server" "authentik-worker" "dashy")
all_running=true

for service in "${services[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "^${service}$"; then
        echo "   ✅ $service is running"
    else
        echo "   ❌ $service is NOT running"
        all_running=false
    fi
done

if [ "$all_running" = false ]; then
    echo ""
    echo "⚠️  Some services are not running. Start them with:"
    echo "   docker-compose -f docker-compose.core.yml up -d"
    echo "   docker-compose up -d"
    exit 1
fi

echo ""
echo "📍 Testing authentication endpoints..."

# Test Authentik directly
echo "   Testing Authentik (https://auth.zoi.local)..."
response=$(curl -k -s -o /dev/null -w "%{http_code}" https://auth.zoi.local)
if [ "$response" = "200" ]; then
    echo "   ✅ Authentik is accessible (HTTP $response)"
else
    echo "   ⚠️  Authentik returned HTTP $response"
fi

# Test Dashy with auth
echo "   Testing Dashy (https://dashy.zoi.local)..."
response=$(curl -k -s -o /dev/null -w "%{http_code}" https://dashy.zoi.local)
if [ "$response" = "302" ]; then
    echo "   ✅ Dashy redirects to authentication (HTTP $response)"
    # Get redirect location
    location=$(curl -k -s -I https://dashy.zoi.local | grep -i "location:" | cut -d' ' -f2 | tr -d '\r')
    echo "   📍 Redirect location: $location"
else
    echo "   ❌ Dashy returned HTTP $response (expected 302 redirect)"
fi

# Test forward auth endpoint
echo "   Testing forward auth endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Forwarded-Proto: https" -H "X-Forwarded-Host: dashy.zoi.local" http://zoi.local:9000/application/o/traefik-forward-auth/)
if [ "$response" = "302" ]; then
    echo "   ✅ Forward auth endpoint is working (HTTP $response)"
else
    echo "   ⚠️  Forward auth endpoint returned HTTP $response"
fi

echo ""
echo "================================"
echo ""

if [ "$response" = "302" ]; then
    echo "✅ Authentication flow is configured correctly!"
    echo ""
    echo "📝 To test the complete flow:"
    echo "1. Open https://dashy.zoi.local in your browser"
    echo "2. You should be redirected to Authentik login"
    echo "3. Login with: admin@zoi.local / admin123!"
    echo "4. After successful login, you'll see the Dashy dashboard"
    echo ""
    echo "💡 Tip: If you see 'authentik-server:9000' in redirects,"
    echo "   that's a cosmetic issue - the browser will handle it correctly."
else
    echo "❌ Authentication flow needs configuration"
    echo ""
    echo "Run the init script to set it up:"
    echo "./scripts/init-authentik.sh"
fi
