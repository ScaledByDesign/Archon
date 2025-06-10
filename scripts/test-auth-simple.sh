#!/bin/bash
# Simple test of authentication flow using curl

echo "🔐 Testing Authentik Forward Authentication"
echo "=========================================="

# Test from inside the Docker network
echo ""
echo "📍 Test 1: Accessing Dashy through Traefik (should redirect to auth)"
docker exec traefik sh -c 'curl -s -I -H "Host: dashy.localhost" https://localhost:443 --insecure' | head -10

echo ""
echo "📍 Test 2: Direct test of forward auth endpoint"
curl -s -I -H "X-Forwarded-Proto: https" -H "X-Forwarded-Host: dashy.localhost" http://localhost:9000/application/o/traefik-forward-auth/ 2>&1 | head -10

echo ""
echo "📍 Test 3: Check if Authentik is accessible"
docker exec traefik sh -c 'curl -s -I -H "Host: auth.localhost" https://localhost:443 --insecure' | head -10

echo ""
echo "📍 Test 4: List available routes in Traefik"
curl -s http://localhost:8081/api/http/routers | jq -r '.[] | select(.rule | contains("dashy")) | {name, rule, middlewares, status}' 2>/dev/null || echo "   (Install jq for formatted output)"

echo ""
echo "=========================================="
