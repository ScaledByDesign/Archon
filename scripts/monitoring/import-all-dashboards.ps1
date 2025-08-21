# Import All Custom Dashboards to Grafana
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Importing All Custom Dashboards to Grafana..." -ForegroundColor Cyan
Write-Host "=" * 60

# Create authentication header
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Function to import dashboard
function Import-Dashboard {
    param($DashboardPath, $DashboardName)
    
    try {
        if (!(Test-Path $DashboardPath)) {
            Write-Host "  ❌ Dashboard file not found: $DashboardPath" -ForegroundColor Red
            return $false
        }
        
        $dashboardContent = Get-Content $DashboardPath -Raw | ConvertFrom-Json
        
        # Prepare import payload
        $importData = @{
            dashboard = $dashboardContent.dashboard
            overwrite = $true
        } | ConvertTo-Json -Depth 20
        
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $importData
        Write-Host "  ✅ Imported: $DashboardName" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ❌ Failed to import $DashboardName`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Configure Prometheus datasource
Write-Host "🔗 Configuring Prometheus datasource..." -ForegroundColor Yellow
try {
    $datasourceData = @{
        name = "Prometheus"
        type = "prometheus"
        url = "http://host.docker.internal:9090"
        access = "proxy"
        isDefault = $true
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/datasources" -Method POST -Headers $headers -Body $datasourceData -ErrorAction SilentlyContinue
    Write-Host "✅ Prometheus datasource configured" -ForegroundColor Green
} catch {
    if ($_.Exception.Response.StatusCode -eq 409) {
        Write-Host "📊 Prometheus datasource already exists" -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  Failed to configure datasource: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Import all dashboards
Write-Host "`n📊 Importing custom dashboards..." -ForegroundColor Yellow

$dashboards = @(
    @{
        Name = "System Overview"
        Path = "config/grafana/dashboards/system/system-overview.json"
    },
    @{
        Name = "Database Monitoring"
        Path = "config/grafana/dashboards/system/database-monitoring.json"
    },
    @{
        Name = "Container Monitoring"
        Path = "config/grafana/dashboards/system/container-monitoring.json"
    },
    @{
        Name = "Alerts Overview"
        Path = "config/grafana/dashboards/system/alerts-overview.json"
    },
    @{
        Name = "LiteLLM Cost Tracking"
        Path = "config/grafana/dashboards/litellm/cost-tracking.json"
    },
    @{
        Name = "AI Services Monitoring"
        Path = "config/grafana/dashboards/litellm/ai-services-monitoring.json"
    }
)

$successCount = 0
$totalCount = $dashboards.Count

foreach ($dashboard in $dashboards) {
    Write-Host "`nImporting: $($dashboard.Name)" -ForegroundColor Cyan
    if (Import-Dashboard -DashboardPath $dashboard.Path -DashboardName $dashboard.Name) {
        $successCount++
    }
}

# Create a comprehensive overview dashboard
Write-Host "`nCreating Zoi Overview Dashboard..." -ForegroundColor Cyan
$overviewDashboard = @{
    dashboard = @{
        id = $null
        title = "Zoi System Overview"
        tags = @("zoi", "overview", "monitoring")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "System Health"
                type = "stat"
                targets = @(
                    @{
                        expr = "up"
                        legendFormat = "{{job}}"
                    }
                )
                gridPos = @{h = 8; w = 12; x = 0; y = 0}
            },
            @{
                id = 2
                title = "CPU Usage"
                type = "stat"
                targets = @(
                    @{
                        expr = "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"
                        legendFormat = "CPU Usage %"
                    }
                )
                gridPos = @{h = 8; w = 12; x = 12; y = 0}
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
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $overviewDashboard
    Write-Host "  ✅ Zoi Overview Dashboard created" -ForegroundColor Green
    $successCount++
    $totalCount++
} catch {
    Write-Host "  ❌ Failed to create overview dashboard: $($_.Exception.Message)" -ForegroundColor Red
}

# Display results
Write-Host "`n🎉 Dashboard Import Complete!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host "📊 Successfully imported: $successCount/$totalCount dashboards" -ForegroundColor Cyan

Write-Host "`n🌐 Access Information:" -ForegroundColor Yellow
Write-Host "  Grafana URL: $GrafanaUrl" -ForegroundColor White
Write-Host "  Username: $Username" -ForegroundColor White
Write-Host "  Password: $Password" -ForegroundColor White

Write-Host "`n📈 Available Dashboards:" -ForegroundColor Yellow
Write-Host "  • Zoi System Overview (main dashboard)" -ForegroundColor White
Write-Host "  • System Overview (CPU, memory, disk)" -ForegroundColor White
Write-Host "  • Database Monitoring (PostgreSQL, Redis)" -ForegroundColor White
Write-Host "  • Container Monitoring (Docker containers)" -ForegroundColor White
Write-Host "  • AI Services Monitoring (LiteLLM, vLLM, Qdrant)" -ForegroundColor White
Write-Host "  • LiteLLM Cost Tracking (real-time costs)" -ForegroundColor White
Write-Host "  • Alerts Overview (system health)" -ForegroundColor White

Write-Host "`n✨ All dashboards are ready for use!" -ForegroundColor Green
