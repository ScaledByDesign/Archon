#!/bin/bash
# Diagnose GPU Monitoring Issues - WSL2 Clean Version

echo "🎮 GPU MONITORING DIAGNOSIS - WSL2"
echo "=================================="

# Check if nvidia-smi is available
echo "🔍 Checking NVIDIA GPU availability..."
if command -v nvidia-smi >/dev/null 2>&1; then
    echo "✅ nvidia-smi found"
    echo "GPU Information:"
    nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw --format=csv,noheader,nounits
else
    echo "❌ nvidia-smi not found in WSL2"
    echo "Checking from Windows host..."
fi

# Check if GPU exporter is running
echo ""
echo "🔍 Checking GPU exporter status..."
if curl -s "http://localhost:9445/metrics" >/dev/null 2>&1; then
    echo "✅ GPU exporter responding on port 9445"
    echo "Sample GPU metrics:"
    curl -s "http://localhost:9445/metrics" | grep "nvidia_gpu" | head -5
else
    echo "❌ GPU exporter not responding on port 9445"
fi

# Check if Prometheus is scraping GPU metrics
echo ""
echo "🔍 Checking Prometheus GPU metrics..."
GPU_METRICS=(
    "nvidia_gpu_utilization_gpu"
    "nvidia_gpu_memory_used_bytes"
    "nvidia_gpu_memory_total_bytes"
    "nvidia_gpu_temperature_celsius"
    "nvidia_gpu_power_draw_watts"
)

for metric in "${GPU_METRICS[@]}"; do
    if curl -s "http://localhost:9090/api/v1/query?query=$metric" | grep -q '"result":\['; then
        result=$(curl -s "http://localhost:9090/api/v1/query?query=$metric" | grep -o '"value":\["[^"]*","[^"]*"\]' | head -1)
        if [ ! -z "$result" ]; then
            echo "✅ $metric: Found data"
        else
            echo "⚠️  $metric: No current data"
        fi
    else
        echo "❌ $metric: Not found in Prometheus"
    fi
done

# Check Docker containers for GPU exporter
echo ""
echo "🔍 Checking Docker containers..."
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep -E "(gpu|nvidia|9445)"

echo ""
echo "🎯 GPU diagnosis complete!"
