# Update Dashboards with GPU Metrics and Fixed Container Monitoring
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Updating Dashboards with GPU Metrics and Fixed Container Monitoring..." -ForegroundColor Cyan
Write-Host "=" * 70

$auth = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${Username}:${Password}"))
$headers = @{
    "Authorization" = "Basic $auth"
    "Content-Type" = "application/json"
}

# Function to create/update dashboard
function Update-Dashboard {
    param($DashboardData, $DashboardName)
    
    try {
        $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/dashboards/db" -Method POST -Headers $headers -Body $DashboardData
        $result = ($response.Content | ConvertFrom-Json)
        Write-Host "  Updated: $DashboardName" -ForegroundColor Green
        Write-Host "  URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
        return $true
    } catch {
        Write-Host "  Failed to update $DashboardName`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 1. UPDATED SYSTEM OVERVIEW WITH GPU METRICS
Write-Host "`nUpdating System Overview with GPU metrics..." -ForegroundColor Yellow
$systemDashboard = @{
    dashboard = @{
        id = $null
        title = "Zoi System Overview with GPU - Live Data"
        tags = @("zoi", "system", "overview", "gpu")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Services Status"
                type = "stat"
                targets = @(@{
                    expr = "count(up == 1)"
                    legendFormat = "Services Up"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "red"; value = $null},
                                @{color = "yellow"; value = 6},
                                @{color = "green"; value = 8}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 3; x = 0; y = 0}
            },
            @{
                id = 2
                title = "CPU Usage"
                type = "stat"
                targets = @(@{
                    expr = "100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"
                    legendFormat = "CPU %"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0; max = 100
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 70},
                                @{color = "red"; value = 90}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 3; x = 3; y = 0}
            },
            @{
                id = 3
                title = "Memory Usage"
                type = "stat"
                targets = @(@{
                    expr = "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"
                    legendFormat = "Memory %"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0; max = 100
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 80},
                                @{color = "red"; value = 95}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 3; x = 6; y = 0}
            },
            @{
                id = 4
                title = "GPU Usage"
                type = "stat"
                targets = @(@{
                    expr = "nvidia_gpu_utilization_gpu"
                    legendFormat = "GPU %"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0; max = 100
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 70},
                                @{color = "red"; value = 90}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 3; x = 9; y = 0}
            },
            @{
                id = 5
                title = "GPU Memory"
                type = "stat"
                targets = @(@{
                    expr = "nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes * 100"
                    legendFormat = "GPU Memory %"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0; max = 100
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 80},
                                @{color = "red"; value = 95}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 3; x = 12; y = 0}
            },
            @{
                id = 6
                title = "GPU Temperature"
                type = "stat"
                targets = @(@{
                    expr = "nvidia_gpu_temperature_celsius"
                    legendFormat = "GPU Temp °C"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "celsius"
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 70},
                                @{color = "red"; value = 85}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 3; x = 15; y = 0}
            },
            @{
                id = 7
                title = "Redis Connections"
                type = "stat"
                targets = @(@{
                    expr = "redis_connected_clients"
                    legendFormat = "Connections"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 50},
                                @{color = "red"; value = 100}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 3; x = 18; y = 0}
            },
            @{
                id = 8
                title = "System Load"
                type = "stat"
                targets = @(@{
                    expr = "node_load1"
                    legendFormat = "Load 1m"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        decimals = 2
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 2},
                                @{color = "red"; value = 4}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 3; x = 21; y = 0}
            },
            @{
                id = 9
                title = "Service Status Table"
                type = "table"
                targets = @(@{
                    expr = "up"
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
                            }
                            renameByName = @{
                                "job" = "Service"
                                "Value" = "Status"
                            }
                        }
                    }
                )
                fieldConfig = @{
                    overrides = @(
                        @{
                            matcher = @{id = "byName"; options = "Status"}
                            properties = @(
                                @{
                                    id = "mappings"
                                    value = @(
                                        @{options = @{"0" = @{text = "DOWN"; color = "red"}}; type = "value"},
                                        @{options = @{"1" = @{text = "UP"; color = "green"}}; type = "value"}
                                    )
                                }
                            )
                        }
                    )
                }
                gridPos = @{h = 8; w = 8; x = 0; y = 4}
            },
            @{
                id = 10
                title = "CPU and GPU Usage Over Time"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"
                        legendFormat = "CPU Usage %"
                    },
                    @{
                        expr = "nvidia_gpu_utilization_gpu"
                        legendFormat = "GPU Usage %"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0; max = 100
                    }
                }
                gridPos = @{h = 8; w = 8; x = 8; y = 4}
            },
            @{
                id = 11
                title = "Memory Usage Over Time"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"
                        legendFormat = "System Memory %"
                    },
                    @{
                        expr = "nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes * 100"
                        legendFormat = "GPU Memory %"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0; max = 100
                    }
                }
                gridPos = @{h = 8; w = 8; x = 16; y = 4}
            }
        )
        time = @{ from = "now-1h"; to = "now" }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

$success1 = Update-Dashboard -DashboardData $systemDashboard -DashboardName "System Overview with GPU"

# 2. FIXED CONTAINER MONITORING DASHBOARD
Write-Host "`nUpdating Container Monitoring with working metrics..." -ForegroundColor Yellow
$containerDashboard = @{
    dashboard = @{
        id = $null
        title = "Container Monitoring - Fixed with Real Data"
        tags = @("containers", "docker", "monitoring", "fixed")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Total Containers"
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
                    expr = "sum(container_memory_usage_bytes) / 1024 / 1024 / 1024"
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
                    expr = "sum(rate(container_cpu_usage_seconds_total[5m])) * 100"
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
                title = "Container CPU Usage by Name"
                type = "timeseries"
                targets = @(@{
                    expr = "rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_service!=`"`"}[5m]) * 100"
                    legendFormat = "{{container_label_com_docker_compose_service}}"
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
                title = "Container Memory Usage by Name"
                type = "timeseries"
                targets = @(@{
                    expr = "container_memory_usage_bytes{container_label_com_docker_compose_service!=`"`"} / 1024 / 1024"
                    legendFormat = "{{container_label_com_docker_compose_service}}"
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
                title = "Container Network I/O"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "rate(container_network_receive_bytes_total{container_label_com_docker_compose_service!=`"`"}[5m])"
                        legendFormat = "RX - {{container_label_com_docker_compose_service}}"
                    },
                    @{
                        expr = "rate(container_network_transmit_bytes_total{container_label_com_docker_compose_service!=`"`"}[5m])"
                        legendFormat = "TX - {{container_label_com_docker_compose_service}}"
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
                title = "Top Containers by CPU"
                type = "table"
                targets = @(@{
                    expr = "topk(10, rate(container_cpu_usage_seconds_total{container_label_com_docker_compose_service!=`"`"}[5m]) * 100)"
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
                                "id" = $true
                                "image" = $true
                                "name" = $true
                            }
                            renameByName = @{
                                "container_label_com_docker_compose_service" = "Container"
                                "Value" = "CPU %"
                            }
                        }
                    }
                )
                gridPos = @{h = 8; w = 12; x = 0; y = 20}
            },
            @{
                id = 9
                title = "Top Containers by Memory"
                type = "table"
                targets = @(@{
                    expr = "topk(10, container_memory_usage_bytes{container_label_com_docker_compose_service!=`"`"} / 1024 / 1024)"
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
                                "id" = $true
                                "image" = $true
                                "name" = $true
                            }
                            renameByName = @{
                                "container_label_com_docker_compose_service" = "Container"
                                "Value" = "Memory (MB)"
                            }
                        }
                    }
                )
                gridPos = @{h = 8; w = 12; x = 12; y = 20}
            }
        )
        time = @{ from = "now-1h"; to = "now" }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

$success2 = Update-Dashboard -DashboardData $containerDashboard -DashboardName "Fixed Container Monitoring"

# Summary
Write-Host "`nDashboard Update Summary:" -ForegroundColor Green
Write-Host "=" * 40
$successCount = 0
if ($success1) { $successCount++; Write-Host "  System Overview with GPU: Updated" -ForegroundColor Green }
if ($success2) { $successCount++; Write-Host "  Fixed Container Monitoring: Updated" -ForegroundColor Green }

Write-Host "`nTotal: $successCount/2 dashboards updated successfully" -ForegroundColor Cyan
Write-Host "`nNew Features Added:" -ForegroundColor Yellow
Write-Host "  - GPU usage, memory, and temperature monitoring" -ForegroundColor White
Write-Host "  - Fixed container metrics with proper labels" -ForegroundColor White
Write-Host "  - Container network I/O monitoring" -ForegroundColor White
Write-Host "  - Top containers by CPU and memory usage" -ForegroundColor White
Write-Host "`nAccess your updated dashboards at: $GrafanaUrl/dashboards" -ForegroundColor Cyan
