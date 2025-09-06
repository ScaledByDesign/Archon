# Zoi Monitoring Stack Status Report
# Comprehensive status check for all monitoring components

Write-Host "ZOI MONITORING STACK - STATUS REPORT" -ForegroundColor Cyan
Write-Host "=" * 60
Write-Host ""

# Check running containers
Write-Host "CONTAINER STATUS:" -ForegroundColor Yellow
$monitoringContainers = @(
    "prometheus-test",
    "grafana-test", 
    "node-exporter",
    "redis-exporter",
    "postgres-exporter",
    "cadvisor"
)

$runningContainers = docker ps --format "{{.Names}}" 2>$null
foreach ($container in $monitoringContainers) {
    if ($runningContainers -contains $container) {
        $status = docker ps --filter "name=$container" --format "{{.Status}}" 2>$null
        Write-Host "  ✅ $container - $status" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $container - Not running" -ForegroundColor Red
    }
}

Write-Host ""

# Check service endpoints
Write-Host "SERVICE ENDPOINTS:" -ForegroundColor Yellow
$endpoints = @(
    @{Name="Prometheus"; URL="http://localhost:9090"; Description="Metrics collection"},
    @{Name="Grafana"; URL="http://localhost:3000"; Description="Dashboards & visualization"},
    @{Name="Node Exporter"; URL="http://localhost:9100/metrics"; Description="System metrics"},
    @{Name="Redis Exporter"; URL="http://localhost:9121/metrics"; Description="Redis metrics"},
    @{Name="Postgres Exporter"; URL="http://localhost:9187/metrics"; Description="PostgreSQL metrics"},
    @{Name="cAdvisor"; URL="http://localhost:8080/metrics"; Description="Container metrics"}
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.URL -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  ✅ $($endpoint.Name) ($($response.StatusCode)) - $($endpoint.Description)" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ $($endpoint.Name) - $($endpoint.Description) - FAILED" -ForegroundColor Red
    }
}

Write-Host ""

# Check Prometheus targets
Write-Host "PROMETHEUS TARGETS:" -ForegroundColor Yellow
try {
    $targetsResponse = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/targets" -TimeoutSec 10
    $targets = ($targetsResponse.Content | ConvertFrom-Json).data.activeTargets
    
    $upTargets = ($targets | Where-Object { $_.health -eq "up" }).Count
    $totalTargets = $targets.Count
    
    Write-Host "  📊 Total Targets: $totalTargets" -ForegroundColor White
    Write-Host "  ✅ Healthy Targets: $upTargets" -ForegroundColor Green
    Write-Host "  ❌ Unhealthy Targets: $($totalTargets - $upTargets)" -ForegroundColor Red
    
    Write-Host ""
    Write-Host "  Target Details:" -ForegroundColor Gray
    foreach ($target in $targets) {
        $status = if ($target.health -eq "up") { "✅" } else { "❌" }
        $job = $target.labels.job
        $instance = $target.labels.instance
        Write-Host "    $status $job ($instance)" -ForegroundColor $(if ($target.health -eq "up") { "Green" } else { "Red" })
    }
} catch {
    Write-Host "  ❌ Failed to retrieve Prometheus targets" -ForegroundColor Red
}

Write-Host ""

# Check LiteLLM cost tracking
Write-Host "COST TRACKING STATUS:" -ForegroundColor Yellow
try {
    $headers = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer sk-wqn0xwq_vha4MVM2yzw"
    }
    
    $body = @{
        model = "zoi-coder"
        messages = @(@{
            role = "user"
            content = "Test cost tracking"
        })
        max_tokens = 5
    } | ConvertTo-Json -Depth 3
    
    $response = Invoke-WebRequest -Uri "http://localhost:7010/v1/chat/completions" -Method POST -Headers $headers -Body $body -TimeoutSec 30
    
    $costHeader = $response.Headers["x-litellm-response-cost"]
    $spendHeader = $response.Headers["x-litellm-key-spend"]
    
    Write-Host "  ✅ LiteLLM API responding (Status: $($response.StatusCode))" -ForegroundColor Green
    Write-Host "  💰 Cost tracking active" -ForegroundColor Green
    Write-Host "    - Response cost: $costHeader" -ForegroundColor Cyan
    Write-Host "    - Total spend: $spendHeader" -ForegroundColor Cyan
} catch {
    Write-Host "  ❌ LiteLLM cost tracking test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# System resource summary
Write-Host "SYSTEM RESOURCES:" -ForegroundColor Yellow
try {
    $cpuResponse = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=100%20-%20(avg%20by(instance)%20(irate(node_cpu_seconds_total%7Bmode%3D%22idle%22%7D%5B5m%5D))%20*%20100)" -TimeoutSec 10
    $cpuData = ($cpuResponse.Content | ConvertFrom-Json).data.result
    if ($cpuData) {
        $cpuUsage = [math]::Round([double]$cpuData[0].value[1], 2)
        Write-Host "  🖥️  CPU Usage: $cpuUsage%" -ForegroundColor $(if ($cpuUsage -lt 80) { "Green" } elseif ($cpuUsage -lt 90) { "Yellow" } else { "Red" })
    }
    
    $memResponse = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=(node_memory_MemTotal_bytes%20-%20node_memory_MemAvailable_bytes)%20%2F%20node_memory_MemTotal_bytes%20*%20100" -TimeoutSec 10
    $memData = ($memResponse.Content | ConvertFrom-Json).data.result
    if ($memData) {
        $memUsage = [math]::Round([double]$memData[0].value[1], 2)
        Write-Host "  💾 Memory Usage: $memUsage%" -ForegroundColor $(if ($memUsage -lt 80) { "Green" } elseif ($memUsage -lt 90) { "Yellow" } else { "Red" })
    }
} catch {
    Write-Host "  ⚠️  Could not retrieve system metrics" -ForegroundColor Yellow
}

Write-Host ""

# Access information
Write-Host "ACCESS INFORMATION:" -ForegroundColor Yellow
Write-Host "  🌐 Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "  📊 Grafana: http://localhost:3000 (admin/admin123)" -ForegroundColor White
Write-Host "  🐳 cAdvisor: http://localhost:8080" -ForegroundColor White
Write-Host "  📈 Node Exporter: http://localhost:9100/metrics" -ForegroundColor White

Write-Host ""

# Management commands
Write-Host "MANAGEMENT COMMANDS:" -ForegroundColor Yellow
Write-Host "  Start all: docker start prometheus-test grafana-test node-exporter redis-exporter postgres-exporter cadvisor" -ForegroundColor White
Write-Host "  Stop all: docker stop prometheus-test grafana-test node-exporter redis-exporter postgres-exporter cadvisor" -ForegroundColor White
Write-Host "  View logs: docker logs -f [container-name]" -ForegroundColor White
Write-Host "  Restart: docker restart [container-name]" -ForegroundColor White

Write-Host ""

# Summary
$healthyServices = 0
$totalServices = $endpoints.Count

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.URL -TimeoutSec 3 -ErrorAction Stop
        $healthyServices++
    } catch {
        # Service is down
    }
}

$healthPercentage = [math]::Round(($healthyServices / $totalServices) * 100, 1)
$healthColor = if ($healthPercentage -ge 90) { "Green" } elseif ($healthPercentage -ge 70) { "Yellow" } else { "Red" }

Write-Host "OVERALL HEALTH: $healthPercentage% ($healthyServices/$totalServices services healthy)" -ForegroundColor $healthColor
Write-Host "=" * 60

if ($healthPercentage -eq 100) {
    Write-Host "All monitoring services are operational!" -ForegroundColor Green
} elseif ($healthPercentage -ge 80) {
    Write-Host "Most services are running, some issues detected" -ForegroundColor Yellow
} else {
    Write-Host "Multiple services are down, investigation needed" -ForegroundColor Red
}
