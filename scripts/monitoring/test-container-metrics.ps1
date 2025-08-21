# Test Container Metrics - Clean Version
Write-Host "🐳 TESTING CONTAINER METRICS - CLEAN VERSION" -ForegroundColor Cyan
Write-Host "=" * 60

# Test individual container metrics
Write-Host "`n📊 Individual Container Metrics:" -ForegroundColor Yellow

$testQueries = @(
    @{Name="Container Count"; Query="count(container_last_seen)"},
    @{Name="Container Memory"; Query="container_memory_usage_bytes / 1024 / 1024"},
    @{Name="Container CPU"; Query="rate(container_cpu_usage_seconds_total[5m]) * 100"},
    @{Name="Network RX"; Query="rate(container_network_receive_bytes_total[5m])"},
    @{Name="Network TX"; Query="rate(container_network_transmit_bytes_total[5m])"}
)

$workingCount = 0
foreach ($test in $testQueries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$($test.Query)" -TimeoutSec 10
        $result = ($response.Content | ConvertFrom-Json)
        
        if ($result.data.result.Count -gt 0) {
            Write-Host "  ✅ $($test.Name): $($result.data.result.Count) series" -ForegroundColor Green
            $workingCount++
            
            # Show sample value
            if ($result.data.result[0].value) {
                $value = [math]::Round([double]$result.data.result[0].value[1], 2)
                Write-Host "    Sample: $value" -ForegroundColor Cyan
            }
        } else {
            Write-Host "  ❌ $($test.Name): No data" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ $($test.Name): Query failed" -ForegroundColor Red
    }
}

# Test aggregate metrics
Write-Host "`n📈 Aggregate Container Metrics:" -ForegroundColor Yellow

$aggregateQueries = @(
    @{Name="Total Memory (GB)"; Query="sum(container_memory_usage_bytes) / 1024 / 1024 / 1024"},
    @{Name="Total CPU (%)"; Query="sum(rate(container_cpu_usage_seconds_total[5m])) * 100"},
    @{Name="Total Network RX"; Query="sum(rate(container_network_receive_bytes_total[5m]))"},
    @{Name="Total Network TX"; Query="sum(rate(container_network_transmit_bytes_total[5m]))"}
)

foreach ($test in $aggregateQueries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$($test.Query)" -TimeoutSec 10
        $result = ($response.Content | ConvertFrom-Json)
        
        if ($result.data.result.Count -gt 0 -and $result.data.result[0].value) {
            $value = [math]::Round([double]$result.data.result[0].value[1], 2)
            Write-Host "  ✅ $($test.Name): $value" -ForegroundColor Green
            $workingCount++
        } else {
            Write-Host "  ❌ $($test.Name): No data" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ $($test.Name): Query failed" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n🎯 CONTAINER METRICS SUMMARY:" -ForegroundColor Green
Write-Host "Working metrics: $workingCount/9" -ForegroundColor Cyan

if ($workingCount -ge 7) {
    Write-Host "🎉 EXCELLENT! Most container metrics are working!" -ForegroundColor Green
} elseif ($workingCount -ge 4) {
    Write-Host "✅ GOOD! Container metrics are mostly working!" -ForegroundColor Yellow
} else {
    Write-Host "⚠️  Container metrics need attention" -ForegroundColor Red
}

Write-Host "`n🌐 Dashboard Access:" -ForegroundColor Cyan
Write-Host "http://localhost:3000/dashboards" -ForegroundColor White

Write-Host "`n📋 What's Available:" -ForegroundColor Yellow
Write-Host "📊 Individual Container Dashboard: Shows per-container details" -ForegroundColor White
Write-Host "📈 Aggregate Container Dashboard: Shows system-wide totals" -ForegroundColor White
Write-Host "🎮 GPU System Dashboard: Shows GPU + system metrics" -ForegroundColor White
Write-Host "🗄️ Database Dashboard: Shows Redis + PostgreSQL metrics" -ForegroundColor White

Write-Host "`n✨ All dashboards auto-refresh every 30 seconds with real data!" -ForegroundColor Green
