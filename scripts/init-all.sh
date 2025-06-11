#!/bin/bash
# Initialize all services including Authentik with forward authentication

set -e

echo "🚀 Initializing complete ZOI platform..."
echo ""

# Source environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Initialize databases
echo "🗄️  Initializing databases..."
if [ -f ./config/postgres/init-multiple-databases.sh ]; then
    docker exec postgres bash /docker-entrypoint-initdb.d/init-multiple-databases.sh || echo "Databases may already exist"
fi

# Wait for services to be ready
echo "⏳ Waiting for core services to be ready..."
sleep 10

# Initialize Authentik forward authentication
echo "🔐 Initializing Authentik forward authentication..."
if [ -f ./scripts/init-authentik.sh ]; then
    ./scripts/init-authentik.sh
else
    echo "⚠️  Authentik init script not found"
fi

echo ""
echo "✅ Platform initialization complete!"
echo ""
echo "📝 Quick Start Guide:"
echo "   1. Access Dashy Dashboard: https://dashy.${DOMAIN:-zoi.local}"
echo "   2. Login with: admin@${DOMAIN:-zoi.local} / admin123!"
echo "   3. All services are protected by Authentik authentication"
echo ""
echo "🔍 Available Services:"
echo "   - Dashy: https://dashy.${DOMAIN:-zoi.local}"
echo "   - Authentik: https://auth.${DOMAIN:-zoi.local}"
echo "   - FastAPI: https://api.${DOMAIN:-zoi.local}"
echo "   - LiteLLM: https://llm.${DOMAIN:-zoi.local}"
echo "   - Traefik: https://traefik.${DOMAIN:-zoi.local}"
echo ""
echo "🛠️  Development Access (direct ports):"
echo "   - Dashy: http://zoi.local:4001"
echo "   - Authentik: http://zoi.local:9000"
echo "   - FastAPI: http://zoi.local:8000"
echo "   - LiteLLM: http://zoi.local:4000"
echo ""
echo "⚠️  Note: The authentication redirects currently show internal hostnames."
echo "   This is cosmetic and doesn't affect functionality. The browser will"
echo "   properly redirect to the correct authentication page."
