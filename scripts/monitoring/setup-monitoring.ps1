# Zoi Monitoring Stack Setup Script
# Sets up Prometheus, Grafana, and related monitoring infrastructure

param(
    [switch]$SkipNetworkCheck,
    [switch]$StartServices,
    [string]$Domain = "zoi.local"
)

Write-Host "🔧 Setting up Zoi Monitoring Stack..." -ForegroundColor Cyan
Write-Host "=" * 60

# Check if Docker is running
Write-Host "📋 Checking Docker status..." -ForegroundColor Yellow
try {
    $dockerStatus = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker is not running"
    }
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

# Create necessary directories
Write-Host "📁 Creating monitoring directories..." -ForegroundColor Yellow
$directories = @(
    "config/prometheus/rules",
    "config/alertmanager",
    "config/grafana/provisioning/datasources",
    "config/grafana/provisioning/dashboards",
    "config/grafana/dashboards/system",
    "config/grafana/dashboards/litellm"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}
Write-Host "✅ Directories created" -ForegroundColor Green

# Check if monitoring network exists
if (!$SkipNetworkCheck) {
    Write-Host "🌐 Checking Docker networks..." -ForegroundColor Yellow
    $networks = docker network ls --format "{{.Name}}"
    
    $requiredNetworks = @("zoi_monitoring_network", "zoi_backend_network", "zoi_database_network", "zoi_frontend_network")
    
    foreach ($network in $requiredNetworks) {
        if ($networks -notcontains $network) {
            Write-Host "  Creating network: $network" -ForegroundColor Gray
            docker network create $network 2>$null
        }
    }
    Write-Host "✅ Networks verified" -ForegroundColor Green
}

# Validate configuration files
Write-Host "📝 Validating configuration files..." -ForegroundColor Yellow
$configFiles = @(
    "config/prometheus/prometheus.yml",
    "config/prometheus/rules/zoi-alerts.yml",
    "config/alertmanager/alertmanager.yml",
    "config/grafana/provisioning/datasources/prometheus.yml",
    "config/grafana/provisioning/dashboards/dashboards.yml"
)

$missingFiles = @()
foreach ($file in $configFiles) {
    if (!(Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Missing configuration files:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    Write-Host "Please ensure all configuration files are created first." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Configuration files validated" -ForegroundColor Green

# Check if main services are running
Write-Host "🔍 Checking main services..." -ForegroundColor Yellow
$mainServices = @("postgres", "redis", "litellm", "traefik")
$runningServices = docker ps --format "{{.Names}}"

foreach ($service in $mainServices) {
    if ($runningServices -contains $service) {
        Write-Host "  ✅ $service is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $service is not running" -ForegroundColor Yellow
    }
}

# Start monitoring services if requested
if ($StartServices) {
    Write-Host "🚀 Starting monitoring services..." -ForegroundColor Yellow
    
    try {
        # Pull latest images
        Write-Host "  📥 Pulling latest images..." -ForegroundColor Gray
        docker-compose -f docker-compose.monitoring.yml pull
        
        # Start services
        Write-Host "  🔄 Starting services..." -ForegroundColor Gray
        docker-compose -f docker-compose.monitoring.yml up -d
        
        # Wait for services to be healthy
        Write-Host "  ⏳ Waiting for services to be healthy..." -ForegroundColor Gray
        Start-Sleep -Seconds 30
        
        # Check service health
        $monitoringServices = @("prometheus", "grafana", "node-exporter", "cadvisor")
        foreach ($service in $monitoringServices) {
            $status = docker ps --filter "name=$service" --format "{{.Status}}"
            if ($status -like "*healthy*" -or $status -like "*Up*") {
                Write-Host "  ✅ $service is healthy" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  $service status: $status" -ForegroundColor Yellow
            }
        }
        
        Write-Host "✅ Monitoring services started" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to start monitoring services: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Display access information
Write-Host ""
Write-Host "🎯 Monitoring Stack Setup Complete!" -ForegroundColor Green
Write-Host "=" * 60
Write-Host ""
Write-Host "📊 Access URLs:" -ForegroundColor Cyan
Write-Host "  Prometheus:    http://prometheus.$Domain (or http://localhost:9090)" -ForegroundColor White
Write-Host "  Grafana:       http://grafana.$Domain (or http://localhost:3000)" -ForegroundColor White
Write-Host "  AlertManager:  http://alertmanager.$Domain (or http://localhost:9093)" -ForegroundColor White
Write-Host "  cAdvisor:      http://cadvisor.$Domain (or http://localhost:8080)" -ForegroundColor White
Write-Host ""
Write-Host "🔑 Default Credentials:" -ForegroundColor Cyan
Write-Host "  Grafana: admin / admin123" -ForegroundColor White
Write-Host ""
Write-Host "📈 Key Metrics:" -ForegroundColor Cyan
Write-Host "  • System resources (CPU, Memory, Disk)" -ForegroundColor White
Write-Host "  • Container metrics" -ForegroundColor White
Write-Host "  • LiteLLM cost tracking and performance" -ForegroundColor White
Write-Host "  • Database metrics (PostgreSQL, Redis)" -ForegroundColor White
Write-Host "  • Load balancer metrics (Traefik)" -ForegroundColor White
Write-Host ""
Write-Host "🚨 Alerting:" -ForegroundColor Cyan
Write-Host "  • High resource usage alerts" -ForegroundColor White
Write-Host "  • Service downtime alerts" -ForegroundColor White
Write-Host "  • LiteLLM cost and performance alerts" -ForegroundColor White
Write-Host "  • Database connection alerts" -ForegroundColor White
Write-Host ""

if (!$StartServices) {
    Write-Host "💡 Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Start monitoring services:" -ForegroundColor White
    Write-Host "     docker-compose -f docker-compose.monitoring.yml up -d" -ForegroundColor Gray
    Write-Host "  2. Or run this script with -StartServices flag" -ForegroundColor White
    Write-Host ""
}

Write-Host "🔧 Management Commands:" -ForegroundColor Cyan
Write-Host "  Start:   docker-compose -f docker-compose.monitoring.yml up -d" -ForegroundColor White
Write-Host "  Stop:    docker-compose -f docker-compose.monitoring.yml down" -ForegroundColor White
Write-Host "  Logs:    docker-compose -f docker-compose.monitoring.yml logs -f" -ForegroundColor White
Write-Host "  Status:  docker-compose -f docker-compose.monitoring.yml ps" -ForegroundColor White
Write-Host ""
Write-Host "✨ Monitoring setup complete!" -ForegroundColor Green
