# Verify Dashboard Data Connection
Write-Host "🔍 DASHBOARD DATA VERIFICATION" -ForegroundColor Cyan
Write-Host "=" * 50

# Test Prometheus connectivity
Write-Host "`n1. PROMETHEUS CONNECTIVITY:" -ForegroundColor Yellow
try {
    $promResponse = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=up" -TimeoutSec 5
    $promData = ($promResponse.Content | ConvertFrom-Json)
    Write-Host "   ✅ Prometheus responding: $($promData.data.result.Count) services" -ForegroundColor Green
    
    # Show current service status
    foreach ($result in $promData.data.result) {
        $job = $result.metric.job
        $status = if ($result.value[1] -eq "1") { "UP" } else { "DOWN" }
        $color = if ($result.value[1] -eq "1") { "Green" } else { "Red" }
        Write-Host "   - $job`: $status" -ForegroundColor $color
    }
} catch {
    Write-Host "   ❌ Prometheus not responding" -ForegroundColor Red
}

# Test Grafana datasource
Write-Host "`n2. GRAFANA DATASOURCE:" -ForegroundColor Yellow
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("admin:admin123"))
$headers = @{ "Authorization" = "Basic $auth" }

try {
    $dsResponse = Invoke-WebRequest -Uri "http://localhost:3000/api/datasources" -Headers $headers
    $datasources = ($dsResponse.Content | ConvertFrom-Json)
    
    $promDS = $datasources | Where-Object { $_.type -eq "prometheus" }
    if ($promDS) {
        Write-Host "   ✅ Prometheus datasource found (ID: $($promDS.id))" -ForegroundColor Green
        Write-Host "   📊 URL: $($promDS.url)" -ForegroundColor Cyan
        Write-Host "   🎯 Default: $($promDS.isDefault)" -ForegroundColor Cyan
    } else {
        Write-Host "   ❌ No Prometheus datasource found" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Cannot access Grafana datasources" -ForegroundColor Red
}

# Test specific metrics used in dashboard
Write-Host "`n3. DASHBOARD METRICS TEST:" -ForegroundColor Yellow
$testMetrics = @(
    @{Name="Service Count"; Query="count(up == 1)"},
    @{Name="CPU Usage"; Query="100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"},
    @{Name="Memory Usage"; Query="(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"},
    @{Name="Redis Connections"; Query="redis_connected_clients"}
)

foreach ($metric in $testMetrics) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$($metric.Query)" -TimeoutSec 5
        $result = ($response.Content | ConvertFrom-Json)
        
        if ($result.data.result.Count -gt 0 -and $result.data.result[0].value) {
            $value = [math]::Round([double]$result.data.result[0].value[1], 2)
            Write-Host "   ✅ $($metric.Name): $value" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  $($metric.Name): No data" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ $($metric.Name): Query failed" -ForegroundColor Red
    }
}

Write-Host "`n4. TROUBLESHOOTING STEPS:" -ForegroundColor Yellow
Write-Host "   If dashboard still shows no data:" -ForegroundColor White
Write-Host "   1. Go to http://localhost:3000/datasources" -ForegroundColor Gray
Write-Host "   2. Click on Prometheus datasource" -ForegroundColor Gray
Write-Host "   3. Verify URL is: http://host.docker.internal:9090" -ForegroundColor Gray
Write-Host "   4. Click 'Save & Test' button" -ForegroundColor Gray
Write-Host "   5. Should show 'Data source is working'" -ForegroundColor Gray
Write-Host "   6. Refresh dashboard: http://localhost:3000/d/cd888a69-3c0e-4ec6-a006-2a185298927d/zoi-complete-monitoring-dashboard" -ForegroundColor Gray

Write-Host "`n✨ Verification complete!" -ForegroundColor Green
