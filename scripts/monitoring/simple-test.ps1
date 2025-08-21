# Simple Container Metrics Test
Write-Host "Container Metrics Test" -ForegroundColor Cyan
Write-Host "======================"

# Test basic container metrics
$testQueries = @(
    @{Name="Container Count"; Query="count(container_last_seen)"},
    @{Name="Container Memory"; Query="container_memory_usage_bytes / 1024 / 1024"},
    @{Name="Container CPU"; Query="rate(container_cpu_usage_seconds_total[5m]) * 100"},
    @{Name="Network RX"; Query="rate(container_network_receive_bytes_total[5m])"}
)

$workingCount = 0
foreach ($test in $testQueries) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$($test.Query)" -TimeoutSec 10
        $result = ($response.Content | ConvertFrom-Json)
        
        if ($result.data.result.Count -gt 0) {
            Write-Host "$($test.Name): $($result.data.result.Count) series" -ForegroundColor Green
            $workingCount++
            
            if ($result.data.result[0].value) {
                $value = [math]::Round([double]$result.data.result[0].value[1], 2)
                Write-Host "  Sample: $value" -ForegroundColor Cyan
            }
        } else {
            Write-Host "$($test.Name): No data" -ForegroundColor Red
        }
    } catch {
        Write-Host "$($test.Name): Failed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Working metrics: $workingCount/4" -ForegroundColor Cyan

if ($workingCount -eq 4) {
    Write-Host "ALL CONTAINER METRICS WORKING!" -ForegroundColor Green
} elseif ($workingCount -gt 2) {
    Write-Host "Most container metrics working!" -ForegroundColor Yellow
} else {
    Write-Host "Container metrics need attention" -ForegroundColor Red
}

Write-Host ""
Write-Host "Dashboard: http://localhost:3000/dashboards" -ForegroundColor White
Write-Host "Container dashboard should now show real data!" -ForegroundColor Green
