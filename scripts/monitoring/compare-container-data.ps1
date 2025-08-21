# Compare Individual vs Aggregate Container Data
Write-Host "INDIVIDUAL vs AGGREGATE CONTAINER DATA COMPARISON" -ForegroundColor Cyan
Write-Host "=" * 70

# 1. INDIVIDUAL CONTAINER DATA
Write-Host "`n📊 INDIVIDUAL CONTAINER DATA:" -ForegroundColor Yellow
Write-Host "Shows each container separately with its own metrics" -ForegroundColor Gray

try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=container_memory_usage_bytes / 1024 / 1024" -TimeoutSec 10
    $result = ($response.Content | ConvertFrom-Json)
    
    if ($result.data.result.Count -gt 0) {
        Write-Host "Found $($result.data.result.Count) individual containers:" -ForegroundColor Green
        
        foreach ($container in $result.data.result) {
            $memoryMB = [math]::Round([double]$container.value[1], 2)
            $containerName = $container.metric.id
            if ($containerName -eq "/") { $containerName = "System Root" }
            elseif ($containerName -eq "/docker") { $containerName = "Docker System" }
            
            Write-Host "  📦 Container: $containerName" -ForegroundColor Cyan
            Write-Host "     Memory: $memoryMB MB" -ForegroundColor White
        }
    }
} catch {
    Write-Host "Failed to get individual container data" -ForegroundColor Red
}

# 2. AGGREGATE CONTAINER DATA
Write-Host "`n📈 AGGREGATE CONTAINER DATA:" -ForegroundColor Yellow
Write-Host "Shows total combined metrics across all containers" -ForegroundColor Gray

try {
    # Total Memory
    $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=sum(container_memory_usage_bytes) / 1024 / 1024 / 1024" -TimeoutSec 10
    $result = ($response.Content | ConvertFrom-Json)
    
    if ($result.data.result.Count -gt 0) {
        $totalMemoryGB = [math]::Round([double]$result.data.result[0].value[1], 2)
        Write-Host "🔢 Total Memory Usage: $totalMemoryGB GB" -ForegroundColor Green
    }
    
    # Total CPU
    $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=sum(rate(container_cpu_usage_seconds_total[5m])) * 100" -TimeoutSec 10
    $result = ($response.Content | ConvertFrom-Json)
    
    if ($result.data.result.Count -gt 0) {
        $totalCPU = [math]::Round([double]$result.data.result[0].value[1], 2)
        Write-Host "🔢 Total CPU Usage: $totalCPU%" -ForegroundColor Green
    }
    
    # Container Count
    $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=count(container_last_seen)" -TimeoutSec 10
    $result = ($response.Content | ConvertFrom-Json)
    
    if ($result.data.result.Count -gt 0) {
        $containerCount = [math]::Round([double]$result.data.result[0].value[1], 0)
        Write-Host "🔢 Total Container Count: $containerCount containers" -ForegroundColor Green
    }
    
} catch {
    Write-Host "Failed to get aggregate container data" -ForegroundColor Red
}

# 3. COMPARISON AND USE CASES
Write-Host "`n🎯 WHEN TO USE EACH DASHBOARD:" -ForegroundColor Cyan

Write-Host "`n📊 Individual Container Dashboard:" -ForegroundColor Yellow
Write-Host "✅ Use when you want to:" -ForegroundColor Green
Write-Host "   - Troubleshoot a specific container" -ForegroundColor White
Write-Host "   - See which container is using the most resources" -ForegroundColor White
Write-Host "   - Monitor per-container performance trends" -ForegroundColor White
Write-Host "   - Identify resource-hungry containers" -ForegroundColor White
Write-Host "   - Debug container-specific issues" -ForegroundColor White

Write-Host "`n📈 Aggregate Container Dashboard:" -ForegroundColor Yellow
Write-Host "✅ Use when you want to:" -ForegroundColor Green
Write-Host "   - Monitor overall container system health" -ForegroundColor White
Write-Host "   - See total resource consumption by all containers" -ForegroundColor White
Write-Host "   - Compare container usage vs system capacity" -ForegroundColor White
Write-Host "   - Track system-wide container trends" -ForegroundColor White
Write-Host "   - Get high-level container infrastructure overview" -ForegroundColor White

Write-Host "`n🌐 DASHBOARD URLS:" -ForegroundColor Cyan
Write-Host "Individual Container Dashboard:" -ForegroundColor Yellow
Write-Host "  http://localhost:3000/d/bd0225aa-5b41-450d-ba9b-915c4a1f9dd2/individual-container-monitoring-per-container-details" -ForegroundColor White

Write-Host "Aggregate Container Dashboard:" -ForegroundColor Yellow
Write-Host "  http://localhost:3000/d/3ad2ea8a-7ee9-4344-ad8e-38f5aaba1534/aggregate-container-monitoring-system-wide-totals" -ForegroundColor White

Write-Host "`n✨ Both dashboards show real data and auto-refresh every 30 seconds!" -ForegroundColor Green
