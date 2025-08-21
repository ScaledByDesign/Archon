#!/bin/bash
# Simple Container Metrics Check for WSL2

echo "Container Metrics Verification - WSL2"
echo "====================================="

# Test basic connectivity
echo "Testing Prometheus..."
curl -s "http://localhost:9090/api/v1/query?query=up" | head -1

# Check container count
echo "Container Count:"
curl -s "http://localhost:9090/api/v1/query?query=count(container_last_seen)" | grep -o '"value":\["[^"]*","[^"]*"\]' | cut -d'"' -f6

# Check container memory (simple)
echo "Container Memory Check:"
curl -s "http://localhost:9090/api/v1/query?query=container_memory_usage_bytes" | grep -c '"id":'

# Check if jq is available
if command -v jq >/dev/null 2>&1; then
    echo "jq is available - can do advanced parsing"
    
    # Get total memory with jq
    echo "Total Container Memory (GB):"
    curl -s "http://localhost:9090/api/v1/query?query=sum(container_memory_usage_bytes)/1024/1024/1024" | jq -r '.data.result[0].value[1] | tonumber | floor'
    
else
    echo "jq not available - using basic parsing"
fi

echo "Container metrics check complete!"
