# Simple Fix for Container Dashboard
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Fixing Container Dashboard with Correct Queries..." -ForegroundColor Cyan

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# FIXED CONTAINER MONITORING DASHBOARD
Write-Host "Creating Fixed Container Monitoring Dashboard..." -ForegroundColor Yellow
$containerDashboard = @{
    dashboard = @{
        id = $null
        title = "Container Monitoring - WORKING Real Data"
        tags = @("containers", "docker", "working")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Total Containers"
                type = "stat"
                targets = @(@{
                    expr = "count(container_last_seen)"
                    legendFormat = "Total"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(@{color = "green"; value = $null})
                        }
                    }
                }
                gridPos = @{h = 4; w = 6; x = 0; y = 0}
            },
            @{
                id = 2
                title = "Container Memory Usage"
                type = "timeseries"
                targets = @(@{
                    expr = "container_memory_usage_bytes{id!=`"/`",id!=`"/docker`"} / 1024 / 1024"
                    legendFormat = "{{id}}"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "decmbytes"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 0; y = 4}
            },
            @{
                id = 3
                title = "Container CPU Usage"
                type = "timeseries"
                targets = @(@{
                    expr = "rate(container_cpu_usage_seconds_total{id!=`"/`",id!=`"/docker`"}[5m]) * 100"
                    legendFormat = "{{id}}"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 12; y = 4}
            },
            @{
                id = 4
                title = "Container Network RX"
                type = "timeseries"
                targets = @(@{
                    expr = "rate(container_network_receive_bytes_total[5m])"
                    legendFormat = "RX {{id}}"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "Bps"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 0; y = 12}
            },
            @{
                id = 5
                title = "Container Network TX"
                type = "timeseries"
                targets = @(@{
                    expr = "rate(container_network_transmit_bytes_total[5m])"
                    legendFormat = "TX {{id}}"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "Bps"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 12; y = 12}
            },
            @{
                id = 6
                title = "Container Memory Table"
                type = "table"
                targets = @(@{
                    expr = "container_memory_usage_bytes{id!=`"/`",id!=`"/docker`"} / 1024 / 1024"
                    format = "table"
                    instant = $true
                })
                transformations = @(
                    @{
                        id = "organize"
                        options = @{
                            excludeByName = @{
                                "Time" = $true
                                "__name__" = $true
                                "instance" = $true
                                "job" = $true
                            }
                            renameByName = @{
                                "id" = "Container"
                                "Value" = "Memory MB"
                            }
                        }
                    }
                )
                gridPos = @{h = 8; w = 24; x = 0; y = 20}
            }
        )
        time = @{ from = "now-1h"; to = "now" }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

try {
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $containerDashboard
    $result = ($response.Content | ConvertFrom-Json)
    Write-Host "Container Dashboard Fixed Successfully!" -ForegroundColor Green
    Write-Host "URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
} catch {
    Write-Host "Failed to update dashboard: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Container dashboard fix complete!" -ForegroundColor Green
