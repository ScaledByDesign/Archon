#!/bin/bash
# Verify Container Metrics with WSL2
# Much cleaner than PowerShell!

echo "🐧 CONTAINER METRICS VERIFICATION - WSL2 VERSION"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if required tools are available
echo -e "\n${YELLOW}🔧 Checking required tools...${NC}"
command -v curl >/dev/null 2>&1 || { echo -e "${RED}❌ curl not found. Install with: sudo apt install curl${NC}"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}❌ jq not found. Install with: sudo apt install jq${NC}"; exit 1; }
echo -e "${GREEN}✅ curl and jq are available${NC}"

# Test Prometheus connectivity
echo -e "\n${YELLOW}🔍 Testing Prometheus connectivity...${NC}"
if curl -s "http://localhost:9090/api/v1/query?query=up" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Prometheus is accessible${NC}"
else
    echo -e "${RED}❌ Prometheus not accessible at localhost:9090${NC}"
    exit 1
fi

# Check individual container metrics
echo -e "\n${YELLOW}📊 Individual Container Metrics:${NC}"
echo "Shows each container separately with its own resource usage"

# Get container memory usage
echo -e "\n${CYAN}Memory Usage by Container:${NC}"
curl -s "http://localhost:9090/api/v1/query?query=container_memory_usage_bytes" | \
jq -r '.data.result[] | select(.metric.id != "/" and .metric.id != "/docker") | 
"\(.metric.id): \((.value[1] | tonumber / 1024 / 1024) | floor)MB"' | \
while read line; do
    echo -e "  📦 ${line}"
done

# Get container CPU usage
echo -e "\n${CYAN}CPU Usage by Container:${NC}"
curl -s "http://localhost:9090/api/v1/query?query=rate(container_cpu_usage_seconds_total[5m])*100" | \
jq -r '.data.result[] | select(.metric.id != "/" and .metric.id != "/docker") | 
"\(.metric.id): \((.value[1] | tonumber * 100) | floor / 100)%"' | \
while read line; do
    echo -e "  🔥 ${line}"
done

# Check aggregate container metrics
echo -e "\n${YELLOW}📈 Aggregate Container Metrics:${NC}"
echo "Shows total combined metrics across all containers"

# Total container count
CONTAINER_COUNT=$(curl -s "http://localhost:9090/api/v1/query?query=count(container_last_seen)" | \
jq -r '.data.result[0].value[1]')
echo -e "  🔢 Total Containers: ${GREEN}${CONTAINER_COUNT}${NC}"

# Total memory usage
TOTAL_MEMORY=$(curl -s "http://localhost:9090/api/v1/query?query=sum(container_memory_usage_bytes)/1024/1024/1024" | \
jq -r '.data.result[0].value[1] | tonumber | floor * 100 / 100')
echo -e "  💾 Total Memory: ${GREEN}${TOTAL_MEMORY}GB${NC}"

# Total CPU usage
TOTAL_CPU=$(curl -s "http://localhost:9090/api/v1/query?query=sum(rate(container_cpu_usage_seconds_total[5m]))*100" | \
jq -r '.data.result[0].value[1] | tonumber | floor * 100 / 100')
echo -e "  🔥 Total CPU: ${GREEN}${TOTAL_CPU}%${NC}"

# Network metrics
echo -e "\n${CYAN}Network I/O:${NC}"
NETWORK_RX=$(curl -s "http://localhost:9090/api/v1/query?query=sum(rate(container_network_receive_bytes_total[5m]))" | \
jq -r '.data.result[0].value[1] | tonumber | floor')
NETWORK_TX=$(curl -s "http://localhost:9090/api/v1/query?query=sum(rate(container_network_transmit_bytes_total[5m]))" | \
jq -r '.data.result[0].value[1] | tonumber | floor')
echo -e "  📥 Network RX: ${GREEN}${NETWORK_RX} Bps${NC}"
echo -e "  📤 Network TX: ${GREEN}${NETWORK_TX} Bps${NC}"

# Check LiteLLM services from config
echo -e "\n${YELLOW}🤖 LiteLLM Service Health Check:${NC}"
echo "Based on your litellm-config.yaml"

# Check vLLM (port 8000 internal, should be accessible)
if curl -s "http://localhost:7030/health" >/dev/null 2>&1; then
    echo -e "  ✅ vLLM: ${GREEN}UP${NC} (Qwen/Qwen3-0.6B)"
else
    echo -e "  ❌ vLLM: ${RED}DOWN${NC}"
fi

# Check Ollama (port 11434 internal)
if curl -s "http://localhost:7040/api/tags" >/dev/null 2>&1; then
    echo -e "  ✅ Ollama: ${GREEN}UP${NC} (qwen2.5:7b, qwen2.5-coder:7b-instruct)"
else
    echo -e "  ❌ Ollama: ${RED}DOWN${NC}"
fi

# Check LiteLLM proxy (port 7010)
if curl -s "http://localhost:7010/health" >/dev/null 2>&1; then
    echo -e "  ✅ LiteLLM Proxy: ${GREEN}UP${NC} (port 7010)"
else
    echo -e "  ❌ LiteLLM Proxy: ${RED}DOWN${NC}"
fi

# Check Redis (for caching)
if curl -s "http://localhost:9090/api/v1/query?query=redis_connected_clients" | jq -r '.data.result[0].value[1]' >/dev/null 2>&1; then
    REDIS_CLIENTS=$(curl -s "http://localhost:9090/api/v1/query?query=redis_connected_clients" | jq -r '.data.result[0].value[1]')
    echo -e "  ✅ Redis: ${GREEN}UP${NC} (${REDIS_CLIENTS} clients)"
else
    echo -e "  ❌ Redis: ${RED}DOWN${NC}"
fi

# Check Qdrant (vector store)
if curl -s "http://localhost:7060/health" >/dev/null 2>&1; then
    echo -e "  ✅ Qdrant: ${GREEN}UP${NC} (vector store)"
else
    echo -e "  ❌ Qdrant: ${RED}DOWN${NC}"
fi

echo -e "\n${GREEN}🎯 Container metrics verification complete!${NC}"
echo -e "${CYAN}Next: Use these metrics to create working Grafana dashboards${NC}"
