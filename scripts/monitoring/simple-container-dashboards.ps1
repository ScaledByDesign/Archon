# Create Individual and Aggregate Container Dashboards
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Creating Individual and Aggregate Container Dashboards..." -ForegroundColor Cyan

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# 1. INDIVIDUAL CONTAINER DASHBOARD
Write-Host "Creating Individual Container Dashboard..." -ForegroundColor Yellow
$individualDashboard = @{
    dashboard = @{
        id = $null
        title = "Individual Container Monitoring - Per Container Details"
        tags = @("containers", "individual", "detailed")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Container Count"
                type = "stat"
                targets = @(@{
                    expr = "count(container_last_seen)"
                    legendFormat = "Containers"
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
                title = "Individual Container Memory Usage"
                type = "timeseries"
                targets = @(@{
                    expr = "container_memory_usage_bytes / 1024 / 1024"
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
                title = "Individual Container CPU Usage"
                type = "timeseries"
                targets = @(@{
                    expr = "rate(container_cpu_usage_seconds_total[5m]) * 100"
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
                title = "Container Memory Table"
                type = "table"
                targets = @(@{
                    expr = "container_memory_usage_bytes / 1024 / 1024"
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
                                "id" = "Container ID"
                                "Value" = "Memory (MB)"
                            }
                        }
                    }
                )
                gridPos = @{h = 8; w = 24; x = 0; y = 12}
            }
        )
        time = @{ from = "now-1h"; to = "now" }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

try {
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $individualDashboard
    $result = ($response.Content | ConvertFrom-Json)
    Write-Host "Individual Container Dashboard Created!" -ForegroundColor Green
    Write-Host "URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
    $success1 = $true
} catch {
    Write-Host "Failed to create individual dashboard: $($_.Exception.Message)" -ForegroundColor Red
    $success1 = $false
}

# 2. AGGREGATE CONTAINER DASHBOARD
Write-Host "`nCreating Aggregate Container Dashboard..." -ForegroundColor Yellow
$aggregateDashboard = @{
    dashboard = @{
        id = $null
        title = "Aggregate Container Monitoring - System-Wide Totals"
        tags = @("containers", "aggregate", "totals")
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
                gridPos = @{h = 4; w = 4; x = 0; y = 0}
            },
            @{
                id = 2
                title = "Total Memory Usage"
                type = "stat"
                targets = @(@{
                    expr = "sum(container_memory_usage_bytes) / 1024 / 1024 / 1024"
                    legendFormat = "Total Memory (GB)"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "decgbytes"
                        decimals = 2
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 8},
                                @{color = "red"; value = 16}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 4; x = 4; y = 0}
            },
            @{
                id = 3
                title = "Total CPU Usage"
                type = "stat"
                targets = @(@{
                    expr = "sum(rate(container_cpu_usage_seconds_total[5m])) * 100"
                    legendFormat = "Total CPU %"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        decimals = 1
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 200},
                                @{color = "red"; value = 400}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 4; x = 8; y = 0}
            },
            @{
                id = 4
                title = "Total Network RX"
                type = "stat"
                targets = @(@{
                    expr = "sum(rate(container_network_receive_bytes_total[5m]))"
                    legendFormat = "Total RX"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "Bps"
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(@{color = "green"; value = $null})
                        }
                    }
                }
                gridPos = @{h = 4; w = 4; x = 12; y = 0}
            },
            @{
                id = 5
                title = "Aggregate Memory Over Time"
                type = "timeseries"
                targets = @(@{
                    expr = "sum(container_memory_usage_bytes) / 1024 / 1024 / 1024"
                    legendFormat = "Total Container Memory (GB)"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "decgbytes"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 0; y = 4}
            },
            @{
                id = 6
                title = "Aggregate CPU Over Time"
                type = "timeseries"
                targets = @(@{
                    expr = "sum(rate(container_cpu_usage_seconds_total[5m])) * 100"
                    legendFormat = "Total Container CPU %"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 12; y = 4}
            }
        )
        time = @{ from = "now-1h"; to = "now" }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

try {
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $aggregateDashboard
    $result = ($response.Content | ConvertFrom-Json)
    Write-Host "Aggregate Container Dashboard Created!" -ForegroundColor Green
    Write-Host "URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
    $success2 = $true
} catch {
    Write-Host "Failed to create aggregate dashboard: $($_.Exception.Message)" -ForegroundColor Red
    $success2 = $false
}

# Summary
Write-Host "`nContainer Dashboard Summary:" -ForegroundColor Green
if ($success1) { Write-Host "  Individual Container Dashboard: Created" -ForegroundColor Green }
if ($success2) { Write-Host "  Aggregate Container Dashboard: Created" -ForegroundColor Green }

Write-Host "`nPurposes:" -ForegroundColor Yellow
Write-Host "  Individual: Shows per-container details and metrics" -ForegroundColor White
Write-Host "  Aggregate: Shows system-wide container totals" -ForegroundColor White
Write-Host "`nAccess: $GrafanaUrl/dashboards" -ForegroundColor Cyan
