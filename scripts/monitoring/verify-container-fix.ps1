# Verify Container Dashboard Fix
Write-Host "VERIFYING CONTAINER DASHBOARD FIX" -ForegroundColor Cyan
Write-Host "=" * 50

# Test the specific metrics that were failing
$testMetrics = @(
    @{Name="Container Memory"; Query="container_memory_usage_bytes{id!=`"/`",id!=`"/docker`"} / 1024 / 1024"},
    @{Name="Container CPU"; Query="rate(container_cpu_usage_seconds_total{id!=`"/`",id!=`"/docker`"}[5m]) * 100"},
    @{Name="Network RX"; Query="rate(container_network_receive_bytes_total[5m])"},
    @{Name="Network TX"; Query="rate(container_network_transmit_bytes_total[5m])"},
    @{Name="Container Count"; Query="count(container_last_seen)"}
)

$workingCount = 0
foreach ($metric in $testMetrics) {
    Write-Host "Testing: $($metric.Name)" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$($metric.Query)" -TimeoutSec 10
        $result = ($response.Content | ConvertFrom-Json)
        
        if ($result.data.result.Count -gt 0) {
            Write-Host "  Working: $($result.data.result.Count) series" -ForegroundColor Green
            $workingCount++
            
            # Show sample values
            if ($result.data.result[0].value) {
                $value = [math]::Round([double]$result.data.result[0].value[1], 2)
                Write-Host "  Sample value: $value" -ForegroundColor Cyan
            }
        } else {
            Write-Host "  No data" -ForegroundColor Red
        }
    } catch {
        Write-Host "  Query failed" -ForegroundColor Red
    }
}

Write-Host "`nContainer Metrics Results:" -ForegroundColor Green
Write-Host "Working metrics: $workingCount/$($testMetrics.Count)" -ForegroundColor Cyan

if ($workingCount -eq $testMetrics.Count) {
    Write-Host "ALL CONTAINER METRICS ARE NOW WORKING!" -ForegroundColor Green
} elseif ($workingCount -gt 0) {
    Write-Host "Most container metrics are working" -ForegroundColor Yellow
} else {
    Write-Host "Container metrics still need attention" -ForegroundColor Red
}

Write-Host "`nFixed Dashboard:" -ForegroundColor Cyan
Write-Host "http://localhost:3000/d/ec29da17-8e82-4976-a865-62a991833269/container-monitoring-working-real-data" -ForegroundColor White

Write-Host "`nWhat was fixed:" -ForegroundColor Yellow
Write-Host "- Changed from container_label_com_docker_compose_service to id filtering" -ForegroundColor White
Write-Host "- Excluded system containers using id!=`"/`" and id!=`"/docker`"" -ForegroundColor White
Write-Host "- Fixed memory, CPU, and network queries" -ForegroundColor White
Write-Host "- Added container details table" -ForegroundColor White
