# GPU Diagnostics Script for vLLM Docker Setup
# Run this script to diagnose GPU issues

Write-Host "🔍 GPU Diagnostics for vLLM Docker Setup" -ForegroundColor Cyan
Write-Host "=" * 50

# 1. Check NVIDIA Driver
Write-Host "`n1. 🎯 NVIDIA Driver Status:" -ForegroundColor Yellow
try {
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used --format=csv,noheader,nounits
    Write-Host "✅ NVIDIA drivers are working" -ForegroundColor Green
} catch {
    Write-Host "❌ NVIDIA drivers not found or not working" -ForegroundColor Red
    Write-Host "   Install NVIDIA drivers from: https://www.nvidia.com/drivers" -ForegroundColor Yellow
}

# 2. Check Docker Runtime
Write-Host "`n2. 🐳 Docker Runtime Status:" -ForegroundColor Yellow
$dockerInfo = docker info 2>$null
if ($dockerInfo -match "nvidia") {
    Write-Host "✅ NVIDIA Docker runtime is available" -ForegroundColor Green
    $dockerInfo | Select-String -Pattern "nvidia|gpu|runtime" -CaseSensitive:$false
} else {
    Write-Host "❌ NVIDIA Docker runtime not found" -ForegroundColor Red
    Write-Host "   Install NVIDIA Container Toolkit:" -ForegroundColor Yellow
    Write-Host "   https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html" -ForegroundColor Yellow
}

# 3. Test GPU Access in Container
Write-Host "`n3. 🧪 Testing GPU Access in Container:" -ForegroundColor Yellow
try {
    $testResult = docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.0-base-ubuntu20.04 nvidia-smi --query-gpu=name --format=csv,noheader 2>$null
    if ($testResult) {
        Write-Host "✅ GPU accessible in containers: $testResult" -ForegroundColor Green
    } else {
        Write-Host "❌ GPU not accessible in containers" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to test GPU in container" -ForegroundColor Red
}

# 4. Check GPU Memory Usage
Write-Host "`n4. 💾 GPU Memory Usage:" -ForegroundColor Yellow
try {
    $memInfo = nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits
    Write-Host "Current GPU Memory: $memInfo" -ForegroundColor White
    
    $used, $total = $memInfo -split ', '
    $usedGB = [math]::Round($used / 1024, 2)
    $totalGB = [math]::Round($total / 1024, 2)
    $freeGB = [math]::Round(($total - $used) / 1024, 2)
    
    Write-Host "Used: ${usedGB}GB / Total: ${totalGB}GB / Free: ${freeGB}GB" -ForegroundColor White
    
    if ($freeGB -lt 4) {
        Write-Host "⚠️  Warning: Less than 4GB free GPU memory" -ForegroundColor Yellow
        Write-Host "   Consider closing other GPU applications (LM Studio, games, etc.)" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Sufficient GPU memory available" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Could not check GPU memory" -ForegroundColor Red
}

# 5. Check Running GPU Processes
Write-Host "`n5. 🔄 GPU Processes:" -ForegroundColor Yellow
try {
    $processes = nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader,nounits
    if ($processes) {
        Write-Host "Active GPU processes:" -ForegroundColor White
        $processes | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "No active GPU compute processes" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Could not check GPU processes" -ForegroundColor Red
}

# 6. Recommendations
Write-Host "`n6. 💡 Recommendations:" -ForegroundColor Yellow

Write-Host "`n🚀 To start with GPU support:" -ForegroundColor Green
Write-Host "   docker-compose up -d" -ForegroundColor White

Write-Host "`n🖥️  To start in CPU-only mode:" -ForegroundColor Green
Write-Host "   docker-compose -f docker-compose.yml -f docker-compose.cpu.yml up -d" -ForegroundColor White

Write-Host "`n🔧 To restart just vLLM:" -ForegroundColor Green
Write-Host "   docker-compose restart vllm" -ForegroundColor White

Write-Host "`n📊 To check vLLM logs:" -ForegroundColor Green
Write-Host "   docker-compose logs -f vllm" -ForegroundColor White

Write-Host "`n" -ForegroundColor White
Write-Host "=" * 50
Write-Host "Diagnostics complete!" -ForegroundColor Cyan
