#!/bin/bash

# Verify Docker Timezone Synchronization
# This script checks that all Docker containers are using America/Chicago timezone

set -e

echo "🕐 Verifying Docker Container Timezone Synchronization"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Target timezone
TARGET_TZ="America/Chicago"

# Function to check if a service is running
check_service_running() {
    local service_name=$1
    if docker-compose ps --services --filter "status=running" | grep -q "^${service_name}$"; then
        return 0
    else
        return 1
    fi
}

# Function to check timezone in a container
check_container_timezone() {
    local service_name=$1
    local container_name=$(docker-compose ps -q $service_name | head -1)
    
    if [ -z "$container_name" ]; then
        echo -e "${RED}❌ Container for service '$service_name' not found${NC}"
        return 1
    fi
    
    # Try multiple methods to get timezone
    local tz_env=$(docker exec $container_name sh -c 'echo $TZ' 2>/dev/null || echo "")
    local tz_file=$(docker exec $container_name sh -c 'cat /etc/timezone' 2>/dev/null || echo "")
    local date_output=$(docker exec $container_name sh -c 'date' 2>/dev/null || echo "")
    
    echo -e "${YELLOW}📦 Service: $service_name${NC}"
    echo "   Container ID: $container_name"
    
    if [ "$tz_env" = "$TARGET_TZ" ]; then
        echo -e "   TZ Environment: ${GREEN}✅ $tz_env${NC}"
    elif [ -n "$tz_env" ]; then
        echo -e "   TZ Environment: ${RED}❌ $tz_env (expected: $TARGET_TZ)${NC}"
    else
        echo -e "   TZ Environment: ${YELLOW}⚠️  Not set${NC}"
    fi
    
    if echo "$date_output" | grep -q "CST\|CDT"; then
        echo -e "   Date Output: ${GREEN}✅ $date_output${NC}"
    else
        echo -e "   Date Output: ${YELLOW}⚠️  $date_output${NC}"
    fi
    
    echo ""
}

# List of all services that should have timezone configuration
services=(
    "authentik-db"
    "authentik-redis" 
    "authentik-server"
    "authentik-worker"
    "traefik"
    "redis"
    "redis-insight"
    "rabbitmq"
    "fastapi-1"
    "fastapi-2"
    "fastapi-3"
    "worker"
    "litellm"
    "ollama"
    "mongo-episodic"
    "mongo-procedural"
    "qdrant"
    "open-webui"
    "n8n"
    "aim"
    "healthchecks"
    "backrest"
    "vault"
)

echo "Checking timezone configuration for all services..."
echo ""

# Check each service
for service in "${services[@]}"; do
    if check_service_running "$service"; then
        check_container_timezone "$service"
    else
        echo -e "${YELLOW}📦 Service: $service${NC}"
        echo -e "   Status: ${YELLOW}⚠️  Not running${NC}"
        echo ""
    fi
done

echo "=================================================="
echo "🕐 Timezone Verification Complete"
echo ""
echo "Expected timezone: $TARGET_TZ"
echo "All running containers should show CST/CDT in date output"
echo "and have TZ environment variable set to $TARGET_TZ"
