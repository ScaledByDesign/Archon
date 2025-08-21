# Create Fresh Working Dashboards with Real Data
param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)

Write-Host "Creating Fresh Working Dashboards with Real Data..." -ForegroundColor Cyan
Write-Host "=" * 60

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
        Write-Host "  Created: $DashboardName" -ForegroundColor Green
        Write-Host "  URL: $GrafanaUrl$($result.url)" -ForegroundColor Cyan
        return $true
    } catch {
        Write-Host "  Failed to create $DashboardName`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 1. MAIN SYSTEM OVERVIEW DASHBOARD
Write-Host "`nCreating Main System Overview Dashboard..." -ForegroundColor Yellow
$mainDashboard = @{
    dashboard = @{
        id = $null
        title = "Zoi System Overview - Live Data"
        tags = @("zoi", "system", "overview", "main")
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
                                @{color = "yellow"; value = 4},
                                @{color = "green"; value = 6}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 4; x = 0; y = 0}
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
                gridPos = @{h = 4; w = 4; x = 4; y = 0}
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
                gridPos = @{h = 4; w = 4; x = 8; y = 0}
            },
            @{
                id = 4
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
                gridPos = @{h = 4; w = 4; x = 12; y = 0}
            },
            @{
                id = 5
                title = "PostgreSQL Status"
                type = "stat"
                targets = @(@{
                    expr = "pg_up"
                    legendFormat = "PostgreSQL"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        mappings = @(
                            @{options = @{"0" = @{text = "DOWN"; color = "red"}}; type = "value"},
                            @{options = @{"1" = @{text = "UP"; color = "green"}}; type = "value"}
                        )
                    }
                }
                gridPos = @{h = 4; w = 4; x = 16; y = 0}
            },
            @{
                id = 6
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
                gridPos = @{h = 4; w = 4; x = 20; y = 0}
            },
            @{
                id = 7
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
                id = 8
                title = "CPU Usage Over Time"
                type = "timeseries"
                targets = @(@{
                    expr = "100 - (avg(irate(node_cpu_seconds_total{mode=`"idle`"}[5m])) * 100)"
                    legendFormat = "CPU Usage %"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0; max = 100
                    }
                }
                gridPos = @{h = 8; w = 8; x = 8; y = 4}
            },
            @{
                id = 9
                title = "Memory Usage Over Time"
                type = "timeseries"
                targets = @(@{
                    expr = "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100"
                    legendFormat = "Memory Usage %"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0; max = 100
                    }
                }
                gridPos = @{h = 8; w = 8; x = 16; y = 4}
            },
            @{
                id = 10
                title = "Container CPU Usage"
                type = "timeseries"
                targets = @(@{
                    expr = "rate(container_cpu_usage_seconds_total{name!=`"`"}[5m]) * 100"
                    legendFormat = "{{name}}"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 24; x = 0; y = 12}
            }
        )
        time = @{ from = "now-1h"; to = "now" }
        refresh = "30s"
    }
    overwrite = $true
} | ConvertTo-Json -Depth 15

$success1 = Create-Dashboard -DashboardData $mainDashboard -DashboardName "Main System Overview"

# 2. CONTAINER MONITORING DASHBOARD
Write-Host "`nCreating Container Monitoring Dashboard..." -ForegroundColor Yellow
$containerDashboard = @{
    dashboard = @{
        id = $null
        title = "Container Monitoring - Live Data"
        tags = @("containers", "docker", "monitoring")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "Total Containers"
                type = "stat"
                targets = @(@{
                    expr = "count(container_last_seen{name!=`"`"})"
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
                title = "Total Memory Usage"
                type = "stat"
                targets = @(@{
                    expr = "sum(container_memory_usage_bytes{name!=`"`"}) / 1024 / 1024 / 1024"
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
                gridPos = @{h = 4; w = 6; x = 6; y = 0}
            },
            @{
                id = 3
                title = "Total CPU Usage"
                type = "stat"
                targets = @(@{
                    expr = "sum(rate(container_cpu_usage_seconds_total{name!=`"`"}[5m])) * 100"
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
                gridPos = @{h = 4; w = 6; x = 12; y = 0}
            },
            @{
                id = 4
                title = "Running Containers"
                type = "stat"
                targets = @(@{
                    expr = "count(container_last_seen{name!=`"`"} > (time() - 60))"
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
                gridPos = @{h = 4; w = 6; x = 18; y = 0}
            },
            @{
                id = 5
                title = "Container CPU Usage"
                type = "timeseries"
                targets = @(@{
                    expr = "rate(container_cpu_usage_seconds_total{name!=`"`"}[5m]) * 100"
                    legendFormat = "{{name}}"
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
                title = "Container Memory Usage"
                type = "timeseries"
                targets = @(@{
                    expr = "container_memory_usage_bytes{name!=`"`"} / 1024 / 1024"
                    legendFormat = "{{name}}"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "decmbytes"
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

$success2 = Create-Dashboard -DashboardData $containerDashboard -DashboardName "Container Monitoring"

# 3. DATABASE MONITORING DASHBOARD
Write-Host "`nCreating Database Monitoring Dashboard..." -ForegroundColor Yellow
$databaseDashboard = @{
    dashboard = @{
        id = $null
        title = "Database Monitoring - PostgreSQL & Redis"
        tags = @("database", "postgresql", "redis")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "PostgreSQL Status"
                type = "stat"
                targets = @(@{
                    expr = "pg_up"
                    legendFormat = "PostgreSQL"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        mappings = @(
                            @{options = @{"0" = @{text = "DOWN"; color = "red"}}; type = "value"},
                            @{options = @{"1" = @{text = "UP"; color = "green"}}; type = "value"}
                        )
                    }
                }
                gridPos = @{h = 4; w = 6; x = 0; y = 0}
            },
            @{
                id = 2
                title = "Redis Status"
                type = "stat"
                targets = @(@{
                    expr = "up{job=`"redis`"}"
                    legendFormat = "Redis"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        mappings = @(
                            @{options = @{"0" = @{text = "DOWN"; color = "red"}}; type = "value"},
                            @{options = @{"1" = @{text = "UP"; color = "green"}}; type = "value"}
                        )
                    }
                }
                gridPos = @{h = 4; w = 6; x = 6; y = 0}
            },
            @{
                id = 3
                title = "Redis Connected Clients"
                type = "stat"
                targets = @(@{
                    expr = "redis_connected_clients"
                    legendFormat = "Clients"
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
                gridPos = @{h = 4; w = 6; x = 12; y = 0}
            },
            @{
                id = 4
                title = "Redis Memory Usage"
                type = "stat"
                targets = @(@{
                    expr = "redis_memory_used_bytes / 1024 / 1024"
                    legendFormat = "Memory (MB)"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "decmbytes"
                        decimals = 1
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "green"; value = $null},
                                @{color = "yellow"; value = 100},
                                @{color = "red"; value = 500}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 6; x = 18; y = 0}
            },
            @{
                id = 5
                title = "Redis Operations Rate"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "rate(redis_commands_processed_total[5m])"
                        legendFormat = "Commands/sec"
                    },
                    @{
                        expr = "rate(redis_keyspace_hits_total[5m])"
                        legendFormat = "Cache Hits/sec"
                    },
                    @{
                        expr = "rate(redis_keyspace_misses_total[5m])"
                        legendFormat = "Cache Misses/sec"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "ops"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 0; y = 4}
            },
            @{
                id = 6
                title = "Redis Key Statistics"
                type = "timeseries"
                targets = @(
                    @{
                        expr = "redis_db_keys"
                        legendFormat = "Total Keys"
                    },
                    @{
                        expr = "redis_db_keys_expiring"
                        legendFormat = "Expiring Keys"
                    }
                )
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
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

$success3 = Create-Dashboard -DashboardData $databaseDashboard -DashboardName "Database Monitoring"

# 4. AI SERVICES MONITORING DASHBOARD
Write-Host "`nCreating AI Services Monitoring Dashboard..." -ForegroundColor Yellow
$aiDashboard = @{
    dashboard = @{
        id = $null
        title = "AI Services Monitoring - vLLM & Qdrant"
        tags = @("ai", "vllm", "qdrant", "services")
        timezone = "browser"
        panels = @(
            @{
                id = 1
                title = "vLLM Status"
                type = "stat"
                targets = @(@{
                    expr = "up{job=`"vllm`"}"
                    legendFormat = "vLLM"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        mappings = @(
                            @{options = @{"0" = @{text = "DOWN"; color = "red"}}; type = "value"},
                            @{options = @{"1" = @{text = "UP"; color = "green"}}; type = "value"}
                        )
                    }
                }
                gridPos = @{h = 4; w = 8; x = 0; y = 0}
            },
            @{
                id = 2
                title = "Qdrant Status"
                type = "stat"
                targets = @(@{
                    expr = "up{job=`"qdrant`"}"
                    legendFormat = "Qdrant"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "short"
                        mappings = @(
                            @{options = @{"0" = @{text = "DOWN"; color = "red"}}; type = "value"},
                            @{options = @{"1" = @{text = "UP"; color = "green"}}; type = "value"}
                        )
                    }
                }
                gridPos = @{h = 4; w = 8; x = 8; y = 0}
            },
            @{
                id = 3
                title = "AI Services Health"
                type = "stat"
                targets = @(@{
                    expr = "(up{job=`"vllm`"} + up{job=`"qdrant`"}) / 2 * 100"
                    legendFormat = "Health %"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "percent"
                        min = 0; max = 100
                        color = @{ mode = "thresholds" }
                        thresholds = @{
                            steps = @(
                                @{color = "red"; value = $null},
                                @{color = "yellow"; value = 50},
                                @{color = "green"; value = 80}
                            )
                        }
                    }
                }
                gridPos = @{h = 4; w = 8; x = 16; y = 0}
            },
            @{
                id = 4
                title = "vLLM Response Time"
                type = "timeseries"
                targets = @(@{
                    expr = "histogram_quantile(0.95, rate(vllm_request_duration_seconds_bucket[5m]))"
                    legendFormat = "95th percentile"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "s"
                        min = 0
                    }
                }
                gridPos = @{h = 8; w = 12; x = 0; y = 4}
            },
            @{
                id = 5
                title = "Qdrant Operations"
                type = "timeseries"
                targets = @(@{
                    expr = "rate(qdrant_rest_responses_total[5m])"
                    legendFormat = "REST API Requests/sec"
                })
                fieldConfig = @{
                    defaults = @{
                        unit = "ops"
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

$success4 = Create-Dashboard -DashboardData $aiDashboard -DashboardName "AI Services Monitoring"

# Summary
Write-Host "`nDashboard Creation Summary:" -ForegroundColor Green
Write-Host "=" * 40
$successCount = 0
if ($success1) { $successCount++; Write-Host "  Main System Overview: Created" -ForegroundColor Green }
if ($success2) { $successCount++; Write-Host "  Container Monitoring: Created" -ForegroundColor Green }
if ($success3) { $successCount++; Write-Host "  Database Monitoring: Created" -ForegroundColor Green }
if ($success4) { $successCount++; Write-Host "  AI Services Monitoring: Created" -ForegroundColor Green }

Write-Host "`nTotal: $successCount/4 dashboards created successfully" -ForegroundColor Cyan
Write-Host "`nAccess your dashboards at: $GrafanaUrl/dashboards" -ForegroundColor Yellow
Write-Host "All dashboards are configured with real data and 30-second refresh!" -ForegroundColor Green
