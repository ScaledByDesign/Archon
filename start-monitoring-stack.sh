#!/bin/bash
# Start Monitoring Stack - Zoi Ecosystem

echo "🚀 STARTING ZOI MONITORING STACK"
echo "================================="

# Create required network
echo "📡 Creating 'zoi-network'..."
docker network create zoi-network 2>/dev/null || echo "Network 'zoi-network' already exists"

# Check if alertmanager config exists
echo ""
echo "📝 Checking Alertmanager configuration..."
if [ -f "config/alertmanager/alertmanager.yml" ]; then
    echo "✅ Alertmanager config exists"
else
    echo "❌ Alertmanager config missing - creating it..."
    mkdir -p config/alertmanager
    cat > config/alertmanager/alertmanager.yml << 'EOF'
# Alertmanager Configuration for Zoi Monitoring
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alertmanager@zoi.local'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'
        send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF
    echo "✅ Created alertmanager.yml"
fi

# Stop any conflicting containers
echo ""
echo "🛑 Stopping any conflicting containers..."
docker stop prometheus-test grafana-test 2>/dev/null || true
docker rm prometheus-test grafana-test 2>/dev/null || true

# Start the monitoring stack
echo ""
echo "🚀 Starting monitoring stack..."
cd apps/monitor && docker compose up -d

# Wait for services to start
echo ""
echo "⏳ Waiting for services to initialize..."
sleep 20

# Check status
echo ""
echo "📊 Checking monitoring stack status..."
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -E "(prometheus|grafana|alertmanager|cadvisor|node-exporter)" || echo "No monitoring containers found"

# Test key services
echo ""
echo "🧪 Testing key services..."
services=(
    "Prometheus:9090"
    "Grafana:3000"
    "Alertmanager:9093"
)

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if curl -s "http://localhost:$port" >/dev/null 2>&1; then
        echo "✅ $name: UP (http://localhost:$port)"
    else
        echo "❌ $name: DOWN (Port $port)"
    fi
done

echo ""
echo "🎯 Monitoring stack startup complete!"
echo ""
echo "🌐 Access URLs:"
echo "   Prometheus: http://prometheus.zoi.local (or http://localhost:7100)"
echo "   Grafana: http://grafana.zoi.local (or http://localhost:7101)"
echo "   Alertmanager: http://alertmanager.zoi.local (or http://localhost:7106)"
echo ""
echo "📊 Use 'make logs-monitor' to view monitoring stack logs"
echo "🔍 Use 'make health' to check all service health"
