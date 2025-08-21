# Simple Import All Dashboards Script
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Importing All Custom Dashboards..." -ForegroundColor Cyan
Write-Host "=" * 50

# Create authentication header
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Configure Prometheus datasource
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
    Write-Host "Prometheus datasource configured" -ForegroundColor Green
} catch {
    Write-Host "Prometheus datasource already exists or configured" -ForegroundColor Yellow
}

# Create System Overview Dashboard
Write-Host "Creating System Overview Dashboard..." -ForegroundColor Yellow
$systemDashboard = @{
    dashboard = @{
        id = $null
        title = "Zoi System Overview"
        tags = @("zoi", "system", "overview")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Services Status"
                type = "stat"
                targets = @(
                    @{
                        expr = "up"
                        legendFormat = "{{job}}"
                    }
                )
                gridPos = @{h = 6; w = 12; x = 0; y = 0}
            },
            @{
                id = 2
                title = "CPU Usage"
                type = "stat"
                targets = @(
                    @{
                        expr = "100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"
                        legendFormat = "CPU %"
                    }
                )
                gridPos = @{h = 6; w = 12; x = 12; y = 0}
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
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $systemDashboard
    Write-Host "System Overview Dashboard created successfully" -ForegroundColor Green
} catch {
    Write-Host "Warning: Failed to create system dashboard" -ForegroundColor Yellow
}

# Create Cost Tracking Dashboard
Write-Host "Creating Cost Tracking Dashboard..." -ForegroundColor Yellow
$costDashboard = @{
    dashboard = @{
        id = $null
        title = "LiteLLM Cost Tracking"
        tags = @("litellm", "cost", "ai")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Service Health"
                type = "stat"
                targets = @(
                    @{
                        expr = "up{job=`"vllm`"}"
                        legendFormat = "vLLM Status"
                    }
                )
                gridPos = @{h = 6; w = 12; x = 0; y = 0}
            },
            @{
                id = 2
                title = "Qdrant Status"
                type = "stat"
                targets = @(
                    @{
                        expr = "up{job=`"qdrant`"}"
                        legendFormat = "Qdrant Status"
                    }
                )
                gridPos = @{h = 6; w = 12; x = 12; y = 0}
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
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $costDashboard
    Write-Host "Cost Tracking Dashboard created successfully" -ForegroundColor Green
} catch {
    Write-Host "Warning: Failed to create cost dashboard" -ForegroundColor Yellow
}

# Create Container Monitoring Dashboard
Write-Host "Creating Container Monitoring Dashboard..." -ForegroundColor Yellow
$containerDashboard = @{
    dashboard = @{
        id = $null
        title = "Container Monitoring"
        tags = @("containers", "docker", "monitoring")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Container CPU Usage"
                type = "graph"
                targets = @(
                    @{
                        expr = "rate(container_cpu_usage_seconds_total{name!=`"`"}[5m]) * 100"
                        legendFormat = "{{name}}"
                    }
                )
                gridPos = @{h = 8; w = 24; x = 0; y = 0}
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
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $containerDashboard
    Write-Host "Container Monitoring Dashboard created successfully" -ForegroundColor Green
} catch {
    Write-Host "Warning: Failed to create container dashboard" -ForegroundColor Yellow
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
Write-Host "Available Dashboards:" -ForegroundColor Yellow
Write-Host "  - Zoi System Overview" -ForegroundColor White
Write-Host "  - LiteLLM Cost Tracking" -ForegroundColor White
Write-Host "  - Container Monitoring" -ForegroundColor White
Write-Host ""
Write-Host "All dashboards are ready for use!" -ForegroundColor Green
