# Simple Monitoring Status Check
Write-Host "ZOI MONITORING STACK - STATUS REPORT" -ForegroundColor Cyan
Write-Host "=" * 60

# Check running containers
Write-Host "`nCONTAINER STATUS:" -ForegroundColor Yellow
$containers = @("prometheus-test", "grafana-test", "node-exporter", "redis-exporter", "postgres-exporter", "cadvisor")
$runningContainers = docker ps --format "{{.Names}}" 2>$null

foreach ($container in $containers) {
    if ($runningContainers -contains $container) {
        Write-Host "  ✅ $container - Running" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $container - Not running" -ForegroundColor Red
    }
}

# Check service endpoints
Write-Host "`nSERVICE ENDPOINTS:" -ForegroundColor Yellow
$endpoints = @(
    @{Name="Prometheus"; URL="http://localhost:9090"},
    @{Name="Grafana"; URL="http://localhost:3000"},
    @{Name="Node Exporter"; URL="http://localhost:9100/metrics"},
    @{Name="cAdvisor"; URL="http://localhost:8080/metrics"}
)

$healthyCount = 0
foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.URL -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  ✅ $($endpoint.Name) - Healthy" -ForegroundColor Green
        $healthyCount++
    } catch {
        Write-Host "  ❌ $($endpoint.Name) - Failed" -ForegroundColor Red
    }
}

# Test LiteLLM cost tracking
Write-Host "`nCOST TRACKING TEST:" -ForegroundColor Yellow
try {
    $headers = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer sk-wqn0xwq_vha4MVM2yzw"
    }
    
    $body = @{
        model = "zoi-coder"
        messages = @(@{
            role = "user"
            content = "Test"
        })
        max_tokens = 5
    } | ConvertTo-Json -Depth 3
    
    $response = Invoke-WebRequest -Uri "http://localhost:7010/v1/chat/completions" -Method POST -Headers $headers -Body $body -TimeoutSec 30
    $cost = $response.Headers["x-litellm-response-cost"]
    
    Write-Host "  ✅ LiteLLM API responding" -ForegroundColor Green
    Write-Host "  💰 Cost tracking active - Last request cost: $cost" -ForegroundColor Green
} catch {
    Write-Host "  ❌ LiteLLM cost tracking failed" -ForegroundColor Red
}

# Access information
Write-Host "`nACCESS URLS:" -ForegroundColor Yellow
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "  Grafana: http://localhost:3000 (admin/admin123)" -ForegroundColor White
Write-Host "  cAdvisor: http://localhost:8080" -ForegroundColor White

# Summary
$totalServices = $endpoints.Count
$healthPercentage = [math]::Round(($healthyCount / $totalServices) * 100, 1)

Write-Host "`n" -NoNewline
Write-Host "OVERALL HEALTH: $healthPercentage% " -NoNewline
Write-Host "($healthyCount/$totalServices services)" -ForegroundColor White

if ($healthPercentage -eq 100) {
    Write-Host "🎉 All monitoring services operational!" -ForegroundColor Green
} elseif ($healthPercentage -ge 75) {
    Write-Host "⚠️  Most services running, some issues detected" -ForegroundColor Yellow
} else {
    Write-Host "❌ Multiple services down, investigation needed" -ForegroundColor Red
}

Write-Host "=" * 60
