#!/bin/bash
# Diagnose Alertmanager Health Check Issues - WSL2

echo "🚨 ALERTMANAGER HEALTH CHECK DIAGNOSIS"
echo "======================================"

# Check if Alertmanager container is running
echo "🔍 Checking Alertmanager container status..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -i alert || echo "No Alertmanager container found"

# Check all containers for any alert-related services
echo ""
echo "🔍 Checking for any alert-related containers..."
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -i alert || echo "No alert containers found"

# Check if Alertmanager port is accessible
echo ""
echo "🔍 Testing Alertmanager connectivity..."
ALERTMANAGER_PORTS=(9093 9094)

for port in "${ALERTMANAGER_PORTS[@]}"; do
    echo "Testing port $port..."
    if curl -s "http://localhost:$port/api/v1/status" >/dev/null 2>&1; then
        echo "✅ Alertmanager responding on port $port"
        curl -s "http://localhost:$port/api/v1/status" | head -3
    else
        echo "❌ Alertmanager not responding on port $port"
    fi
done

# Check Docker Compose services
echo ""
echo "🔍 Checking Docker Compose services..."
if [ -f "docker-compose.yml" ]; then
    echo "Docker Compose file found. Checking services..."
    grep -A 5 -B 2 -i "alert" docker-compose.yml || echo "No alertmanager service in docker-compose.yml"
else
    echo "No docker-compose.yml found"
fi

# Check if Prometheus is configured for Alertmanager
echo ""
echo "🔍 Checking Prometheus Alertmanager configuration..."
if [ -f "config/prometheus/prometheus.yml" ]; then
    echo "Prometheus config found. Checking alerting section..."
    grep -A 10 -B 2 "alerting\|alertmanagers" config/prometheus/prometheus.yml || echo "No alertmanager config in Prometheus"
else
    echo "No Prometheus config found"
fi

# Check for alert rules
echo ""
echo "🔍 Checking for alert rules..."
find . -name "*.rules" -o -name "*alert*" -o -name "rules.yml" 2>/dev/null | head -5

echo ""
echo "🎯 Alertmanager diagnosis complete!"
echo ""
echo "💡 Common solutions:"
echo "1. Start Alertmanager container if missing"
echo "2. Check Alertmanager configuration file"
echo "3. Verify port accessibility"
echo "4. Check Docker Compose alertmanager service"
