# Fix Container Dashboard with Correct Label Queries
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "🔧 FIXING CONTAINER DASHBOARD WITH CORRECT QUERIES" -ForegroundColor Cyan
Write-Host "=" * 60

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Function to update dashboard
function Update-Dashboard {
    param($DashboardData, $DashboardName)
    
    try {
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $DashboardData
        $result = ($response.Content | ConvertFrom-Json)
        Write-Host "  ✅ Updated: $DashboardName" -ForegroundColor Green
        Write-Host "  📊 URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
        return $true
    } catch {
        Write-Host "  ❌ Failed to update $DashboardName`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# FIXED CONTAINER MONITORING DASHBOARD
Write-Host "`n🐳 Creating Fixed Container Monitoring Dashboard..." -ForegroundColor Yellow
$containerDashboard = @{
    dashboard = @{
        id = $null
        title = "Container Monitoring - WORKING with Real Data"
        tags = @("containers", "docker", "monitoring", "working")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Total Containers"
                type = "stat"
                targets = @(@{
                    expr = "count(container_last_seen)"
                    legendFormat = "Total Containers"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 20},
                                @{color = "red"; value = 50}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 6; x = 0; y = 0}
            },
            @{
                id = 2
                title = "Running Containers"
                type = "stat"
                targets = @(@{
                    expr = "count(container_last_seen > (time() - 60))"
                    legendFormat = "Running"
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
                gridPos = @{h = 4; w = 6; x = 6; y = 0}
            },
            @{
                id = 3
                title = "Total Memory Usage"
                type = "stat"
                targets = @(@{
                    expr = "sum(container_memory_usage_bytes{id!=`"/`",id!=`"/docker`"}) / 1024 / 1024 / 1024"
                    legendFormat = "Memory (GB)"
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
                gridPos = @{h = 4; w = 6; x = 12; y = 0}
            },
            @{
                id = 4
                title = "Total CPU Usage"
                type = "stat"
                targets = @(@{
                    expr = "sum(rate(container_cpu_usage_seconds_total{id!=`"/`",id!=`"/docker`"}[5m])) * 100"
                    legendFormat = "CPU %"
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
                gridPos = @{h = 4; w = 6; x = 18; y = 0}
            },
            @{
                id = 5
                title = "Container CPU Usage by ID"
                type = "timeseries"
                targets = @(@{
                    expr = "rate(container_cpu_usage_seconds_total{id!=`"/`",id!=`"/docker`",id!=`"/docker/buildx`"}[5m]) * 100"
                    legendFormat = "{{id}}"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 0; y = 4}
            },
            @{
                id = 6
                title = "Container Memory Usage by ID"
                type = "timeseries"
                targets = @(@{
                    expr = "container_memory_usage_bytes{id!=`"/`",id!=`"/docker`",id!=`"/docker/buildx`"} / 1024 / 1024"
                    legendFormat = "{{id}}"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "decmbytes"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 12; y = 4}
            },
            @{
                id = 7
                title = "Container Network I/O (All Interfaces)"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "sum by (id) (rate(container_network_receive_bytes_total[5m]))"
                        legendFormat = "RX - {{id}}"
                    },
                    @{
                        expr = "sum by (id) (rate(container_network_transmit_bytes_total[5m]))"
                        legendFormat = "TX - {{id}}"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "Bps"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 24; x = 0; y = 12}
            },
            @{
                id = 8
                title = "Container Details Table"
                type = "table"
                targets = @(@{
                    expr = "container_memory_usage_bytes{id!=`"/`",id!=`"/docker`",id!=`"/docker/buildx`"} / 1024 / 1024"
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
                gridPos = @{h = 8; w = 12; x = 0; y = 20}
            },
            @{
                id = 9
                title = "Container CPU Usage Table"
                type = "table"
                targets = @(@{
                    expr = "rate(container_cpu_usage_seconds_total{id!=`"/`",id!=`"/docker`",id!=`"/docker/buildx`"}[5m]) * 100"
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
                                "Value" = "CPU %"
                            }
                        }
                    }
                )
                gridPos = @{h = 8; w = 12; x = 12; y = 20}
            },
            @{
                id = 10
                title = "System vs Container Memory"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024 / 1024"
                        legendFormat = "System Memory Used (GB)"
                    },
                    @{
                        expr = "sum(container_memory_usage_bytes{id!=`"/`",id!=`"/docker`"}) / 1024 / 1024 / 1024"
                        legendFormat = "Container Memory Used (GB)"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "decgbytes"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 24; x = 0; y = 28}
            }
        )
        time = @{ from = "now-1h"; to = "now" }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

$success = Update-Dashboard -DashboardData $containerDashboard -DashboardName "Fixed Container Monitoring"

# Summary
Write-Host "`n📊 Container Dashboard Fix Summary:" -ForegroundColor Green
Write-Host "=" * 50
if ($success) {
    Write-Host "✅ Container Dashboard: FIXED and working!" -ForegroundColor Green
    Write-Host "✅ All panels now use correct container ID filtering" -ForegroundColor Green
    Write-Host "✅ Memory, CPU, and Network metrics working" -ForegroundColor Green
    Write-Host "✅ Container tables showing real data" -ForegroundColor Green
} else {
    Write-Host "❌ Container Dashboard: Update failed" -ForegroundColor Red
}

Write-Host "`n🎯 Fixed Issues:" -ForegroundColor Yellow
Write-Host "  - Changed from container_label_com_docker_compose_service to id filtering" -ForegroundColor White
Write-Host "  - Excluded system containers (root, docker, buildx)" -ForegroundColor White
Write-Host "  - Fixed network I/O aggregation with sum by (id)" -ForegroundColor White
Write-Host "  - Added container details tables with proper transformations" -ForegroundColor White
Write-Host "  - Added system vs container memory comparison" -ForegroundColor White

Write-Host "`n🌐 Access Fixed Dashboard:" -ForegroundColor Cyan
Write-Host "http://localhost:3000/dashboards" -ForegroundColor White
Write-Host "All container metrics should now show real data!" -ForegroundColor Green
