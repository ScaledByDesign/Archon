#!/bin/bash
# Create Working Container Dashboard - WSL2 Clean Version
# This fixes the "no data" issue with proper queries

GRAFANA_URL="http://localhost:3000"
AUTH=$(echo -n "admin:admin123" | base64)

echo "🐳 Creating Working Container Dashboard with WSL2"
echo "================================================="

# Create Individual Container Dashboard with working queries
echo "Creating Individual Container Dashboard..."

curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "id": null,
      "title": "Container Monitoring - WSL2 Fixed",
      "tags": ["containers", "wsl2", "working"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "Container Count",
          "type": "stat",
          "targets": [
            {
              "expr": "count(container_last_seen)",
              "legendFormat": "Total Containers"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "short",
              "color": {"mode": "thresholds"},
              "thresholds": {
                "steps": [{"color": "green", "value": null}]
              }
            }
          },
          "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
        },
        {
          "id": 2,
          "title": "Container Memory Usage",
          "type": "timeseries",
          "targets": [
            {
              "expr": "container_memory_usage_bytes / 1024 / 1024",
              "legendFormat": "{{id}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "decmbytes",
              "min": 0
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
        },
        {
          "id": 3,
          "title": "Container CPU Usage",
          "type": "timeseries",
          "targets": [
            {
              "expr": "rate(container_cpu_usage_seconds_total[5m]) * 100",
              "legendFormat": "{{id}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "min": 0
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4}
        },
        {
          "id": 4,
          "title": "Container Network I/O",
          "type": "timeseries",
          "targets": [
            {
              "expr": "rate(container_network_receive_bytes_total[5m])",
              "legendFormat": "RX {{id}}"
            },
            {
              "expr": "rate(container_network_transmit_bytes_total[5m])",
              "legendFormat": "TX {{id}}"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "Bps",
              "min": 0
            }
          },
          "gridPos": {"h": 8, "w": 24, "x": 0, "y": 12}
        }
      ],
      "time": {"from": "now-1h", "to": "now"},
      "refresh": "30s"
    },
    "overwrite": true
  }' | jq -r '.url // "Dashboard creation failed"'

echo ""
echo "Creating Aggregate Container Dashboard..."

# Create Aggregate Container Dashboard
curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": {
      "id": null,
      "title": "Aggregate Container Monitoring - WSL2",
      "tags": ["containers", "aggregate", "wsl2"],
      "timezone": "browser",
      "panels": [
        {
          "id": 1,
          "title": "Total Containers",
          "type": "stat",
          "targets": [
            {
              "expr": "count(container_last_seen)",
              "legendFormat": "Total"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "short",
              "color": {"mode": "thresholds"},
              "thresholds": {
                "steps": [{"color": "green", "value": null}]
              }
            }
          },
          "gridPos": {"h": 4, "w": 4, "x": 0, "y": 0}
        },
        {
          "id": 2,
          "title": "Total Memory Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "sum(container_memory_usage_bytes) / 1024 / 1024 / 1024",
              "legendFormat": "Total Memory (GB)"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "decgbytes",
              "decimals": 2,
              "color": {"mode": "thresholds"},
              "thresholds": {
                "steps": [
                  {"color": "green", "value": null},
                  {"color": "yellow", "value": 8},
                  {"color": "red", "value": 16}
                ]
              }
            }
          },
          "gridPos": {"h": 4, "w": 4, "x": 4, "y": 0}
        },
        {
          "id": 3,
          "title": "Total CPU Usage",
          "type": "stat",
          "targets": [
            {
              "expr": "sum(rate(container_cpu_usage_seconds_total[5m])) * 100",
              "legendFormat": "Total CPU %"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "decimals": 1,
              "color": {"mode": "thresholds"},
              "thresholds": {
                "steps": [
                  {"color": "green", "value": null},
                  {"color": "yellow", "value": 200},
                  {"color": "red", "value": 400}
                ]
              }
            }
          },
          "gridPos": {"h": 4, "w": 4, "x": 8, "y": 0}
        },
        {
          "id": 4,
          "title": "Aggregate Memory Over Time",
          "type": "timeseries",
          "targets": [
            {
              "expr": "sum(container_memory_usage_bytes) / 1024 / 1024 / 1024",
              "legendFormat": "Total Container Memory (GB)"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "decgbytes",
              "min": 0
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4}
        },
        {
          "id": 5,
          "title": "Aggregate CPU Over Time",
          "type": "timeseries",
          "targets": [
            {
              "expr": "sum(rate(container_cpu_usage_seconds_total[5m])) * 100",
              "legendFormat": "Total Container CPU %"
            }
          ],
          "fieldConfig": {
            "defaults": {
              "unit": "percent",
              "min": 0
            }
          },
          "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4}
        }
      ],
      "time": {"from": "now-1h", "to": "now"},
      "refresh": "30s"
    },
    "overwrite": true
  }' | jq -r '.url // "Dashboard creation failed"'

echo ""
echo "✅ Container dashboards created with WSL2!"
echo "🌐 Access at: http://localhost:3000/dashboards"
echo ""
echo "📊 Individual Dashboard: Shows per-container details"
echo "📈 Aggregate Dashboard: Shows system-wide totals"
