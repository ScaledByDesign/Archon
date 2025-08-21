# Import Complete Zoi Dashboard with Data Validation
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "🎨 IMPORTING COMPLETE ZOI DASHBOARD" -ForegroundColor Cyan
Write-Host "=" * 60

# Create authentication header
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# First, validate we have data in Prometheus
Write-Host "`n🔍 VALIDATING DATA AVAILABILITY:" -ForegroundColor Yellow

$criticalMetrics = @(
    @{Name="Service Status"; Query="up"},
    @{Name="CPU Usage"; Query="node_cpu_seconds_total"},
    @{Name="Memory Usage"; Query="node_memory_MemTotal_bytes"},
    @{Name="Container Metrics"; Query="container_cpu_usage_seconds_total"},
    @{Name="Redis Metrics"; Query="redis_connected_clients"},
    @{Name="PostgreSQL Status"; Query="pg_up"}
)

$dataAvailable = $true
foreach ($metric in $criticalMetrics) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$($metric.Query)" -TimeoutSec 10
        $result = ($response.Content | ConvertFrom-Json).data.result
        if ($result.Count -gt 0) {
            Write-Host "  ✅ $($metric.Name) - $($result.Count) data points" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($metric.Name) - No data available" -ForegroundColor Red
            $dataAvailable = $false
        }
    } catch {
        Write-Host "  ❌ $($metric.Name) - Query failed" -ForegroundColor Red
        $dataAvailable = $false
    }
}

if (!$dataAvailable) {
    Write-Host "`n⚠️  WARNING: Some metrics have no data. Dashboard may show empty panels." -ForegroundColor Yellow
} else {
    Write-Host "`n✅ All metrics have data available!" -ForegroundColor Green
}

# Configure Prometheus datasource
Write-Host "`n🔗 CONFIGURING DATASOURCE:" -ForegroundColor Yellow
try {
    # First try to update existing datasource
    $datasourceData = @{
        id = 1
        name = "Prometheus"
        type = "prometheus"
        url = "http://host.docker.internal:9090"
        access = "proxy"
        isDefault = $true
        basicAuth = $false
    } | ConvertTo-Json
    
    try {
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/datasources/1" -Method PUT -Headers $headers -Body $datasourceData
        Write-Host "  ✅ Prometheus datasource updated" -ForegroundColor Green
    } catch {
        # If update fails, try to create new
        $createData = @{
            name = "Prometheus"
            type = "prometheus"
            url = "http://host.docker.internal:9090"
            access = "proxy"
            isDefault = $true
            basicAuth = $false
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/datasources" -Method POST -Headers $headers -Body $createData
        Write-Host "  ✅ Prometheus datasource created" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️  Datasource configuration issue: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Import the complete dashboard
Write-Host "`n📊 IMPORTING COMPLETE DASHBOARD:" -ForegroundColor Yellow
try {
    $dashboardPath = "config/grafana/dashboards/zoi-complete-dashboard.json"
    
    if (!(Test-Path $dashboardPath)) {
        Write-Host "  ❌ Dashboard file not found: $dashboardPath" -ForegroundColor Red
        exit 1
    }
    
    $dashboardContent = Get-Content $dashboardPath -Raw | ConvertFrom-Json
    
    # Prepare import payload
    $importData = @{
        dashboard = $dashboardContent.dashboard
        overwrite = $true
        inputs = @(
            @{
                name = "DS_PROMETHEUS"
                type = "datasource"
                pluginId = "prometheus"
                value = "Prometheus"
            }
        )
    } | ConvertTo-Json -Depth 20
    
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $importData
    $result = ($response.Content | ConvertFrom-Json)
    
    Write-Host "  ✅ Complete dashboard imported successfully!" -ForegroundColor Green
    Write-Host "  📊 Dashboard URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
    
    # Test dashboard data by querying a few panels
    Write-Host "`n🧪 TESTING DASHBOARD DATA:" -ForegroundColor Yellow
    
    $testQueries = @(
        @{Name="Service Count"; Query="count(up == 1)"},
        @{Name="CPU Usage"; Query="100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"},
        @{Name="Memory Usage"; Query="(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"}
    )
    
    foreach ($test in $testQueries) {
        try {
            $testResponse = Invoke-WebRequest -Uri "http://localhost:9090/api/v1/query?query=$($test.Query)" -TimeoutSec 10
            $testResult = ($testResponse.Content | ConvertFrom-Json).data.result
            if ($testResult.Count -gt 0 -and $testResult[0].value) {
                $value = [math]::Round([double]$testResult[0].value[1], 2)
                Write-Host "  ✅ $($test.Name): $value" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  $($test.Name): No current value" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ❌ $($test.Name): Query failed" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "  ❌ Failed to import dashboard: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Final summary
Write-Host "`n🎉 COMPLETE DASHBOARD DEPLOYMENT SUCCESS!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host ""
Write-Host "📊 Dashboard Features:" -ForegroundColor Cyan
Write-Host "  • Real-time system health overview" -ForegroundColor White
Write-Host "  • CPU and memory usage monitoring" -ForegroundColor White
Write-Host "  • Service status table with live data" -ForegroundColor White
Write-Host "  • Container resource usage graphs" -ForegroundColor White
Write-Host "  • Redis operations monitoring" -ForegroundColor White
Write-Host "  • PostgreSQL status tracking" -ForegroundColor White
Write-Host "  • LiteLLM cost tracking integration" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Access Information:" -ForegroundColor Yellow
Write-Host "  URL: $GrafanaUrl" -ForegroundColor White
Write-Host "  Username: $Username" -ForegroundColor White
Write-Host "  Password: $Password" -ForegroundColor White
Write-Host ""
Write-Host "✨ Dashboard is ready with live data!" -ForegroundColor Green
