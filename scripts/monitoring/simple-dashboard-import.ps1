# Simple Grafana Dashboard Import Script
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Importing Grafana Dashboards..." -ForegroundColor Cyan
Write-Host "=" * 50

# Create authentication header
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Wait for Grafana to be ready
Write-Host "Checking Grafana availability..." -ForegroundColor Yellow
$maxRetries = 10
$retryCount = 0

do {
    try {
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/health" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "Grafana is ready!" -ForegroundColor Green
            break
        }
    } catch {
        $retryCount++
        if ($retryCount -ge $maxRetries) {
            Write-Host "Grafana is not responding after $maxRetries attempts" -ForegroundColor Red
            exit 1
        }
        Write-Host "Waiting for Grafana... (attempt $retryCount/$maxRetries)" -ForegroundColor Gray
        Start-Sleep -Seconds 3
    }
} while ($retryCount -lt $maxRetries)

# Configure Prometheus datasource first
Write-Host "Configuring Prometheus datasource..." -ForegroundColor Yellow
try {
    $datasourceData = @{
        name = "Prometheus"
        type = "prometheus"
        url = "http://host.docker.internal:9090"
        access = "proxy"
        isDefault = $true
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/datasources" -Method POST -Headers $headers -Body $datasourceData -ErrorAction SilentlyContinue
    Write-Host "Prometheus datasource configured successfully" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "Prometheus datasource already exists" -ForegroundColor Yellow
    } else {
        Write-Host "Warning: Failed to configure datasource: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Import a simple dashboard
Write-Host "Creating sample dashboard..." -ForegroundColor Yellow
$sampleDashboard = @{
    dashboard = @{
        id = $null
        title = "Zoi Monitoring Overview"
        tags = @("zoi", "monitoring")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "System CPU Usage"
                type = "stat"
                targets = @(
                    @{
                        expr = "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"
                        legendFormat = "CPU Usage %"
                    }
                )
                gridPos = @{h = 8; w = 12; x = 0; y = 0}
            }
        )
        time = @{
            from = "now-1h"
            to = "now"
        }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $sampleDashboard
    Write-Host "Sample dashboard created successfully" -ForegroundColor Green
} catch {
    Write-Host "Warning: Failed to create dashboard: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Dashboard Import Complete!" -ForegroundColor Green
Write-Host "=" * 50
Write-Host ""
Write-Host "Access Information:" -ForegroundColor Cyan
Write-Host "  Grafana URL: $GrafanaUrl" -ForegroundColor White
Write-Host "  Username: $Username" -ForegroundColor White
Write-Host "  Password: $Password" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open Grafana in your browser" -ForegroundColor White
Write-Host "  2. Navigate to Dashboards > Browse" -ForegroundColor White
Write-Host "  3. Create custom dashboards as needed" -ForegroundColor White
Write-Host ""
Write-Host "Monitoring setup is complete!" -ForegroundColor Green
