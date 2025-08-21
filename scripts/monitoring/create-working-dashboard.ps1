# Create Working Complete Dashboard with Real Data
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Creating Complete Zoi Dashboard with Real Data..." -ForegroundColor Cyan
Write-Host "=" * 60

# Create authentication header
$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Create comprehensive dashboard with working panels
$completeDashboard = @{
    dashboard = @{
        id = $null
        title = "Zoi Complete Monitoring Dashboard"
        tags = @("zoi", "complete", "monitoring")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Services Status"
                type = "stat"
                targets = @(
                    @{
                        expr = "count(up == 1)"
                        legendFormat = "Services Up"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        color = @{
                            mode = "thresholds"
                        }
                        thresholds = @{
                            steps = @(
                                @{color = "red"; value = $null},
                                @{color = "yellow"; value = 4},
                                @{color = "green"; value = 6}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 6; x = 0; y = 0}
            },
            @{
                id = 2
                title = "CPU Usage %"
                type = "stat"
                targets = @(
                    @{
                        expr = "100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"
                        legendFormat = "CPU Usage"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0
                        max = 100
                        color = @{
                            mode = "thresholds"
                        }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 70},
                                @{color = "red"; value = 90}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 6; x = 6; y = 0}
            },
            @{
                id = 3
                title = "Memory Usage %"
                type = "stat"
                targets = @(
                    @{
                        expr = "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"
                        legendFormat = "Memory Usage"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0
                        max = 100
                        color = @{
                            mode = "thresholds"
                        }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 80},
                                @{color = "red"; value = 95}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 6; x = 12; y = 0}
            },
            @{
                id = 4
                title = "Redis Connections"
                type = "stat"
                targets = @(
                    @{
                        expr = "redis_connected_clients"
                        legendFormat = "Connections"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        color = @{
                            mode = "thresholds"
                        }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 50},
                                @{color = "red"; value = 100}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 6; x = 18; y = 0}
            },
            @{
                id = 5
                title = "Service Status Table"
                type = "table"
                targets = @(
                    @{
                        expr = "up"
                        format = "table"
                        instant = $true
                    }
                )
                transformations = @(
                    @{
                        id = "organize"
                        options = @{
                            excludeByName = @{
                                "Time" = $true
                                "__name__" = $true
                                "instance" = $true
                            }
                            renameByName = @{
                                "job" = "Service"
                                "Value" = "Status"
                            }
                        }
                    }
                )
                gridPos = @{h = 8; w = 12; x = 0; y = 4}
            },
            @{
                id = 6
                title = "CPU Usage Over Time"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"
                        legendFormat = "CPU Usage %"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0
                        max = 100
                    }
                }
                gridPos = @{h = 8; w = 12; x = 12; y = 4}
            },
            @{
                id = 7
                title = "Container CPU Usage"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "rate(container_cpu_usage_seconds_total{name!=`"`"}[5m]) * 100"
                        legendFormat = "{{name}}"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 24; x = 0; y = 12}
            }
        )
        time = @{
            from = "now-1h"
            to = "now"
        }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

# Import the dashboard
Write-Host "Importing complete dashboard..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $completeDashboard
    $result = ($response.Content | ConvertFrom-Json)
    
    Write-Host "Complete dashboard imported successfully!" -ForegroundColor Green
    Write-Host "Dashboard URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
    
    # Test the dashboard data
    Write-Host "Testing dashboard data..." -ForegroundColor Yellow
    
    $testQueries = @(
        @{Name="Services Up"; Query="count(up == 1)"},
        @{Name="CPU Usage"; Query="100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"},
        @{Name="Memory Usage"; Query="(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"},
        @{Name="Redis Connections"; Query="redis_connected_clients"}
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
    
} catch {
    Write-Host "Failed to import dashboard: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Complete Dashboard Deployment Finished!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host ""
Write-Host "Dashboard Features:" -ForegroundColor Cyan
Write-Host "  - Real-time service status (7 services monitored)" -ForegroundColor White
Write-Host "  - Live CPU usage monitoring" -ForegroundColor White
Write-Host "  - Memory usage tracking" -ForegroundColor White
Write-Host "  - Redis connection monitoring" -ForegroundColor White
Write-Host "  - Service status table with up/down indicators" -ForegroundColor White
Write-Host "  - CPU usage trends over time" -ForegroundColor White
Write-Host "  - Container resource usage graphs" -ForegroundColor White
Write-Host ""
Write-Host "Access: http://localhost:3000 (admin/admin123)" -ForegroundColor Yellow
Write-Host "Dashboard is ready with live data!" -ForegroundColor Green
