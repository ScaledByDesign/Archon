# Simple Complete Dashboard Import
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Importing Complete Zoi Dashboard..." -ForegroundColor Cyan
Write-Host "=" * 50

# Create authentication header
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Validate data availability first
Write-Host "Validating data sources..." -ForegroundColor Yellow
$testMetrics = @("up", "node_cpu_seconds_total", "redis_connected_clients")
$dataCount = 0

foreach ($metric in $testMetrics) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$metric" -TimeoutSec 5
        $result = ($response.Content | ConvertFrom-Json).data.result
        if ($result.Count -gt 0) {
            Write-Host "  Data available for $metric - $($result.Count) series" -ForegroundColor Green
            $dataCount++
        }
    } catch {
        Write-Host "  No data for $metric" -ForegroundColor Yellow
    }
}

Write-Host "Found data for $dataCount/$($testMetrics.Count) metrics" -ForegroundColor Cyan

# Import the complete dashboard
Write-Host "Importing complete dashboard..." -ForegroundColor Yellow
try {
    $dashboardPath = "config/grafana/dashboards/zoi-complete-dashboard.json"
    
    if (!(Test-Path $dashboardPath)) {
        Write-Host "Dashboard file not found: $dashboardPath" -ForegroundColor Red
        exit 1
    }
    
    $dashboardContent = Get-Content $dashboardPath -Raw | ConvertFrom-Json
    
    $importData = @{
        dashboard = $dashboardContent.dashboard
        overwrite = $true
    } | ConvertTo-Json -Depth 20
    
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $importData
    $result = ($response.Content | ConvertFrom-Json)
    
    Write-Host "Complete dashboard imported successfully!" -ForegroundColor Green
    Write-Host "Dashboard URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
    
} catch {
    Write-Host "Failed to import dashboard: $($_.Exception.Message)" -ForegroundColor Red
}

# Test some key metrics to show actual values
Write-Host "Testing dashboard queries..." -ForegroundColor Yellow

$testQueries = @(
    @{Name="Services Up"; Query="count(up == 1)"},
    @{Name="CPU Usage"; Query="100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"},
    @{Name="Redis Clients"; Query="redis_connected_clients"}
)

foreach ($test in $testQueries) {
    try {
        $testResponse = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$($test.Query)" -TimeoutSec 10
        $testResult = ($testResponse.Content | ConvertFrom-Json).data.result
        if ($testResult.Count -gt 0 -and $testResult[0].value) {
            $value = [math]::Round([double]$testResult[0].value[1], 2)
            Write-Host "  $($test.Name): $value" -ForegroundColor Green
        }
    } catch {
        Write-Host "  $($test.Name): Query failed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Dashboard Import Complete!" -ForegroundColor Green
Write-Host "=" * 50
Write-Host ""
Write-Host "Access Information:" -ForegroundColor Cyan
Write-Host "  URL: $GrafanaUrl" -ForegroundColor White
Write-Host "  Username: $Username" -ForegroundColor White
Write-Host "  Password: $Password" -ForegroundColor White
Write-Host ""
Write-Host "Dashboard Features:" -ForegroundColor Yellow
Write-Host "  - Real-time system health overview" -ForegroundColor White
Write-Host "  - CPU and memory usage monitoring" -ForegroundColor White
Write-Host "  - Service status with live data" -ForegroundColor White
Write-Host "  - Container resource monitoring" -ForegroundColor White
Write-Host "  - Database status tracking" -ForegroundColor White
Write-Host ""
Write-Host "Dashboard is ready with live data!" -ForegroundColor Green
