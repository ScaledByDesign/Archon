#!/usr/bin/env pwsh
# Setup script for integrating Archon MCP with LiteLLM
# This script connects Archon's Docker network to LiteLLM's network

Write-Host "🔗 Setting up Archon MCP integration with LiteLLM..." -ForegroundColor Green

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if LiteLLM network exists
$litellmNetwork = docker network ls --filter name=zoi-llm_ai --format "{{.Name}}"
if (-not $litellmNetwork) {
    Write-Host "❌ LiteLLM network 'zoi-llm_ai' not found. Please start your LLM stack first:" -ForegroundColor Red
    Write-Host "   cd apps/llm-local && docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found LiteLLM network: $litellmNetwork" -ForegroundColor Green

# Check if Archon network exists
$archonNetwork = docker network ls --filter name=archon_app-network --format "{{.Name}}"
if (-not $archonNetwork) {
    Write-Host "❌ Archon network 'archon_app-network' not found. Please start Archon first:" -ForegroundColor Red
    Write-Host "   cd apps/Archon && docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found Archon network: $archonNetwork" -ForegroundColor Green

# Connect Archon containers to LiteLLM network
$archonContainers = @("Archon-MCP", "Archon-Server", "Archon-Agents", "Archon-UI")

foreach ($container in $archonContainers) {
    $containerExists = docker ps --filter name=$container --format "{{.Names}}"
    if ($containerExists) {
        Write-Host "🔗 Connecting $container to LiteLLM network..." -ForegroundColor Blue
        try {
            docker network connect zoi-llm_ai $container 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Connected $container to LiteLLM network" -ForegroundColor Green
            } else {
                Write-Host "⚠️  $container already connected to LiteLLM network" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️  Could not connect $container (may already be connected)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Container $container not found or not running" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 Archon MCP integration setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart LiteLLM to pick up the new MCP configuration:" -ForegroundColor White
Write-Host "   cd apps/llm-local && docker-compose restart litellm" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Test the MCP connection:" -ForegroundColor White
Write-Host "   curl -H 'Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw' http://localhost:7010/v1/models" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Use Archon MCP in your applications:" -ForegroundColor White
Write-Host "   - Model: zoi-auto (with intelligent routing)" -ForegroundColor Yellow
Write-Host "   - MCP Tools: archon, knowledge, tasks, docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "🔍 Check Archon MCP status:" -ForegroundColor Cyan
Write-Host "   curl http://localhost:8051/health" -ForegroundColor Yellow