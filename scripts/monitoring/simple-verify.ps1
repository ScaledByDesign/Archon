# Simple Dashboard Data Verification
Write-Host "Dashboard Data Verification" -ForegroundColor Cyan
Write-Host "=" * 40

# Test Prometheus
Write-Host "Testing Prometheus..." -ForegroundColor Yellow
try {
    $promResponse = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=up" -TimeoutSec 5
    $promData = ($promResponse.Content | ConvertFrom-Json)
    Write-Host "Prometheus OK: $($promData.data.result.Count) services" -ForegroundColor Green
} catch {
    Write-Host "Prometheus FAILED" -ForegroundColor Red
}

# Test key metrics
Write-Host "Testing dashboard metrics..." -ForegroundColor Yellow
$metrics = @(
    @{Name="Services"; Query="count(up == 1)"},
    @{Name="CPU"; Query="100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"},
    @{Name="Redis"; Query="redis_connected_clients"}
)

foreach ($metric in $metrics) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$($metric.Query)" -TimeoutSec 5
        $result = ($response.Content | ConvertFrom-Json)
        
        if ($result.data.result.Count -gt 0 -and $result.data.result[0].value) {
            $value = [math]::Round([double]$result.data.result[0].value[1], 2)
            Write-Host "$($metric.Name): $value" -ForegroundColor Green
        } else {
            Write-Host "$($metric.Name): No data" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "$($metric.Name): Failed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "MANUAL STEPS TO FIX DASHBOARD:" -ForegroundColor Yellow
Write-Host "1. Open: http://localhost:3000/datasources" -ForegroundColor White
Write-Host "2. Click Prometheus datasource" -ForegroundColor White
Write-Host "3. Change URL to: http://host.docker.internal:9090" -ForegroundColor White
Write-Host "4. Click 'Save & Test'" -ForegroundColor White
Write-Host "5. Refresh dashboard" -ForegroundColor White
Write-Host ""
Write-Host "Dashboard URL:" -ForegroundColor Cyan
Write-Host "http://localhost:3000/d/cd888a69-3c0e-4ec6-a006-2a185298927d/zoi-complete-monitoring-dashboard" -ForegroundColor White
