# Development helper script for Windows PowerShell
param(
    [Parameter(Position=0)]
    [string]$Command = "up"
)

switch ($Command) {
    "up" {
        Write-Host "🚀 Starting voice chat service in development mode..." -ForegroundColor Green
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
    }
    "build" {
        Write-Host "🔨 Building voice chat service..." -ForegroundColor Yellow
        $env:DOCKER_BUILDKIT=1
        docker build --progress=plain --build-arg BUILDKIT_INLINE_CACHE=1 --cache-from realtime-voice-chat:latest -t realtime-voice-chat:latest .
    }
    "rebuild" {
        Write-Host "🔨 Rebuilding voice chat service..." -ForegroundColor Yellow
        $env:DOCKER_BUILDKIT=1
        docker build --progress=plain --no-cache -t realtime-voice-chat:latest .
    }
    "down" {
        Write-Host "🛑 Stopping voice chat service..." -ForegroundColor Red
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
    }
    "logs" {
        Write-Host "📋 Showing logs..." -ForegroundColor Cyan
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f app
    }
    "shell" {
        Write-Host "🐚 Opening shell in container..." -ForegroundColor Magenta
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml exec app bash
    }
    "restart" {
        Write-Host "🔄 Restarting voice chat service..." -ForegroundColor Blue
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml restart app
    }
    default {
        Write-Host "Usage: .\dev.ps1 [command]" -ForegroundColor White
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Yellow
        Write-Host "  up       - Start in development mode (default)" -ForegroundColor White
        Write-Host "  build    - Build with cache" -ForegroundColor White
        Write-Host "  rebuild  - Full rebuild without cache" -ForegroundColor White
        Write-Host "  down     - Stop services" -ForegroundColor White
        Write-Host "  logs     - Show logs" -ForegroundColor White
        Write-Host "  shell    - Open shell in container" -ForegroundColor White
        Write-Host "  restart  - Restart app service" -ForegroundColor White
    }
}
