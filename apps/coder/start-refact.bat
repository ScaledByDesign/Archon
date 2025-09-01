@echo off
setlocal enabledelayedexpansion

REM Refact.ai Startup Script for Zoi Integration (Windows)
REM This script helps you get started with the Refact AI coding assistant

echo.
echo ================================================
echo 🤖 Refact.ai AI Coding Assistant - Zoi Integration
echo ================================================
echo.

REM Check if we're in the right directory
if not exist "docker-compose.yml" (
    echo [ERROR] Please run this script from the apps\coder directory
    pause
    exit /b 1
)

echo [INFO] Checking prerequisites...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check Docker Compose
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not available. Please update Docker Desktop.
    pause
    exit /b 1
)

REM Check NVIDIA Docker (optional)
nvidia-smi >nul 2>&1
if not errorlevel 1 (
    echo [INFO] NVIDIA GPU detected. Checking Docker GPU support...
    docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] ✅ NVIDIA Docker runtime is working
    ) else (
        echo [WARN] ⚠️  NVIDIA Docker runtime not working. GPU acceleration will be disabled.
    )
) else (
    echo [WARN] ⚠️  No NVIDIA GPU detected. Running in CPU-only mode.
)

REM Check if Zoi network exists
docker network ls | findstr "zoi-network" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Creating Zoi network...
    docker network create zoi-network
)

REM Check core services
echo [INFO] Checking core Zoi services...

set "missing_services="
docker ps | findstr "postgres" >nul 2>&1
if errorlevel 1 set "missing_services=!missing_services! postgres"

docker ps | findstr "redis" >nul 2>&1
if errorlevel 1 set "missing_services=!missing_services! redis"

docker ps | findstr "litellm" >nul 2>&1
if errorlevel 1 set "missing_services=!missing_services! litellm"

if not "!missing_services!"=="" (
    echo [WARN] Missing required services:!missing_services!
    echo [INFO] Starting core Zoi services...
    
    REM Go to root directory and start core services
    cd ..\..\
    docker compose up -d postgres redis litellm
    
    REM Wait for services to be ready
    echo [INFO] Waiting for core services to be ready...
    timeout /t 10 /nobreak >nul
    
    REM Return to coder directory
    cd apps\coder
)

REM Build and start Refact services
echo [INFO] Building Refact services...
docker compose build

echo [INFO] Starting Refact services...
docker compose up -d

REM Wait for services to be ready
echo [INFO] Waiting for Refact services to start...
timeout /t 30 /nobreak >nul

REM Check service health
echo [INFO] Checking service health...

set "healthy_services="
set "unhealthy_services="

REM Check each service
curl -f -s "http://localhost:7400/health" >nul 2>&1
if not errorlevel 1 (
    set "healthy_services=!healthy_services! refact-server"
) else (
    set "unhealthy_services=!unhealthy_services! refact-server"
)

curl -f -s "http://localhost:7401/health" >nul 2>&1
if not errorlevel 1 (
    set "healthy_services=!healthy_services! refact-agent"
) else (
    set "unhealthy_services=!unhealthy_services! refact-agent"
)

curl -f -s "http://localhost:7402" >nul 2>&1
if not errorlevel 1 (
    set "healthy_services=!healthy_services! refact-gui"
) else (
    set "unhealthy_services=!unhealthy_services! refact-gui"
)

curl -f -s "http://localhost:7403" >nul 2>&1
if not errorlevel 1 (
    set "healthy_services=!healthy_services! refact-docs"
) else (
    set "unhealthy_services=!unhealthy_services! refact-docs"
)

REM Display results
echo.
echo ==============================
echo 🎉 Refact.ai Setup Complete!
echo ==============================

if not "!healthy_services!"=="" (
    echo [INFO] ✅ Healthy services:!healthy_services!
)

if not "!unhealthy_services!"=="" (
    echo [WARN] ⚠️  Services still starting:!unhealthy_services!
    echo.
    echo [INFO] Services may take a few more minutes to fully initialize.
)

echo.
echo ===============
echo 🌐 Access URLs
echo ===============
echo • Refact Server:  http://refact.zoi.local (or http://localhost:7400)
echo • Refact Chat:    http://refact-chat.zoi.local (or http://localhost:7402)
echo • Refact Agent:   http://refact-agent.zoi.local (or http://localhost:7401)
echo • Documentation:  http://refact-docs.zoi.local (or http://localhost:7403)

echo.
echo ==================
echo 🔧 IDE Integration
echo ==================
echo For VS Code:
echo 1. Install Refact.ai extension
echo 2. Set Inference URL: http://localhost:7401
echo 3. Set API Key: refact-admin-token-zoi-2024-secure
echo.
echo For JetBrains IDEs:
echo 1. Install Refact.ai plugin
echo 2. Settings ^> Tools ^> Refact.ai ^> Advanced
echo 3. Set Inference URL: http://localhost:7401
echo 4. Set API Key: refact-admin-token-zoi-2024-secure

echo.
echo ==============
echo 📊 Monitoring
echo ==============
echo • View logs: docker compose logs -f
echo • Check status: docker compose ps
echo • Restart service: docker compose restart ^<service-name^>

echo.
echo ==================
echo 🆘 Troubleshooting
echo ==================
echo • If services fail to start, check logs: docker compose logs
echo • For GPU issues, verify: docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
echo • For database issues, check: docker compose exec postgres psql -U postgres -l

echo.
echo [INFO] 🚀 Refact.ai is ready! Happy coding with AI assistance!

REM Optional: Open browser
set /p "open_browser=Open Refact Chat in browser? (y/N): "
if /i "!open_browser!"=="y" (
    start http://localhost:7402
)

pause
