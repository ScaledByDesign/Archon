# Create Both Individual and Aggregate Container Dashboards
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "🐳 CREATING INDIVIDUAL AND AGGREGATE CONTAINER DASHBOARDS" -ForegroundColor Cyan
Write-Host "=" * 70

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Function to create dashboard
function Create-Dashboard {
    param($DashboardData, $DashboardName)
    
    try {
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $DashboardData
        $result = ($response.Content | ConvertFrom-Json)
        Write-Host "  ✅ Created: $DashboardName" -ForegroundColor Green
        Write-Host "  📊 URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
        return $true
    } catch {
        Write-Host "  ❌ Failed: $DashboardName - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 1. INDIVIDUAL CONTAINER MONITORING DASHBOARD
Write-Host "`n📊 Creating Individual Container Monitoring Dashboard..." -ForegroundColor Yellow
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
                    expr = "count(container_last_seen{id!=`"/`",id!=`"/docker`"})"
                    legendFormat = "Individual Containers"
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
                    expr = "container_memory_usage_bytes{id!=`"/`",id!=`"/docker`",id!=`"/docker/buildx`"} / 1024 / 1024"
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
                    expr = "rate(container_cpu_usage_seconds_total{id!=`"/`",id!=`"/docker`",id!=`"/docker/buildx`"}[5m]) * 100"
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
                title = "Individual Container Network I/O"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "rate(container_network_receive_bytes_total{id!=`"/`",id!=`"/docker`"}[5m])"
                        legendFormat = "RX {{id}}"
                    },
                    @{
                        expr = "rate(container_network_transmit_bytes_total{id!=`"/`",id!=`"/docker`"}[5m])"
                        legendFormat = "TX {{id}}"
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
                id = 5
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
                gridPos = @{h = 8; w = 24; x = 0; y = 20}
            }
        )
        time = @{ from = "now-1h"; to = "now" }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

$success1 = Create-Dashboard -DashboardData $individualDashboard -DashboardName "Individual Container Monitoring"

# 2. AGGREGATE CONTAINER MONITORING DASHBOARD
Write-Host "`n📈 Creating Aggregate Container Monitoring Dashboard..." -ForegroundColor Yellow
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
                    legendFormat = "Total Containers"
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
                    expr = "sum(container_memory_usage_bytes{id!=`"/`",id!=`"/docker`"}) / 1024 / 1024 / 1024"
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
                    expr = "sum(rate(container_cpu_usage_seconds_total{id!=`"/`",id!=`"/docker`"}[5m])) * 100"
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
                title = "Total Network TX"
                type = "stat"
                targets = @(@{
                    expr = "sum(rate(container_network_transmit_bytes_total[5m]))"
                    legendFormat = "Total TX"
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
                gridPos = @{h = 4; w = 4; x = 16; y = 0}
            },
            @{
                id = 6
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
                gridPos = @{h = 4; w = 4; x = 20; y = 0}
            },
            @{
                id = 7
                title = "Aggregate Memory Usage Over Time"
                type = "timeseries"
                targets = @(@{
                    expr = "sum(container_memory_usage_bytes{id!=`"/`",id!=`"/docker`"}) / 1024 / 1024 / 1024"
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
                id = 8
                title = "Aggregate CPU Usage Over Time"
                type = "timeseries"
                targets = @(@{
                    expr = "sum(rate(container_cpu_usage_seconds_total{id!=`"/`",id!=`"/docker`"}[5m])) * 100"
                    legendFormat = "Total Container CPU %"
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
                id = 9
                title = "Aggregate Network I/O Over Time"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "sum(rate(container_network_receive_bytes_total[5m]))"
                        legendFormat = "Total RX"
                    },
                    @{
                        expr = "sum(rate(container_network_transmit_bytes_total[5m]))"
                        legendFormat = "Total TX"
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
                id = 10
                title = "System vs Container Resource Comparison"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024 / 1024"
                        legendFormat = "System Memory Used (GB)"
                    },
                    @{
                        expr = "sum(container_memory_usage_bytes{id!=`"/`",id!=`"/docker`"}) / 1024 / 1024 / 1024"
                        legendFormat = "Container Memory Used (GB)"
                    },
                    @{
                        expr = "100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"
                        legendFormat = "System CPU %"
                    },
                    @{
                        expr = "sum(rate(container_cpu_usage_seconds_total{id!=`"/`",id!=`"/docker`"}[5m])) * 100"
                        legendFormat = "Container CPU %"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        min = 0
                    }
                    overrides = @(
                        @{
                            matcher = @{id = "byRegexp"; options = ".*Memory.*"}
                            properties = @(@{id = "unit"; value = "decgbytes"})
                        },
                        @{
                            matcher = @{id = "byRegexp"; options = ".*CPU.*"}
                            properties = @(@{id = "unit"; value = "percent"})
                        }
                    )
                }
                gridPos = @{h = 8; w = 24; x = 0; y = 20}
            }
        )
        time = @{ from = "now-1h"; to = "now" }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

$success2 = Create-Dashboard -DashboardData $aggregateDashboard -DashboardName "Aggregate Container Monitoring"

# Summary
Write-Host "`n📊 CONTAINER DASHBOARD CREATION SUMMARY:" -ForegroundColor Green
Write-Host "=" * 60
$successCount = 0
if ($success1) {
    $successCount++
    Write-Host "✅ Individual Container Monitoring: Created" -ForegroundColor Green
    Write-Host "   - Shows per-container details and metrics" -ForegroundColor White
    Write-Host "   - Individual memory, CPU, network usage" -ForegroundColor White
    Write-Host "   - Container details table" -ForegroundColor White
}
if ($success2) {
    $successCount++
    Write-Host "✅ Aggregate Container Monitoring: Created" -ForegroundColor Green
    Write-Host "   - Shows system-wide container totals" -ForegroundColor White
    Write-Host "   - Total memory, CPU, network usage" -ForegroundColor White
    Write-Host "   - System vs container comparison" -ForegroundColor White
}

Write-Host "`nTotal: $successCount/2 container dashboards created" -ForegroundColor Cyan

Write-Host "`n🎯 DASHBOARD PURPOSES:" -ForegroundColor Yellow
Write-Host "📊 Individual Container Dashboard:" -ForegroundColor Cyan
Write-Host "   - Use when you want to see specific container performance" -ForegroundColor White
Write-Host "   - Troubleshoot individual container issues" -ForegroundColor White
Write-Host "   - Monitor per-container resource usage" -ForegroundColor White

Write-Host "📈 Aggregate Container Dashboard:" -ForegroundColor Cyan
Write-Host "   - Use for overall system container health" -ForegroundColor White
Write-Host "   - Monitor total container resource consumption" -ForegroundColor White
Write-Host "   - Compare container vs system resource usage" -ForegroundColor White

Write-Host "`n🌐 Access Your Container Dashboards:" -ForegroundColor Green
Write-Host "$GrafanaUrl/dashboards" -ForegroundColor White
Write-Host "Both dashboards show real data with 30-second refresh!" -ForegroundColor Cyan
