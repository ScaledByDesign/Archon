#!/bin/bash

# Refact.ai Startup Script for Zoi Integration
# This script helps you get started with the Refact AI coding assistant

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the apps/coder directory"
    exit 1
fi

print_header "🤖 Refact.ai AI Coding Assistant - Zoi Integration"
echo "=================================================="

# Check prerequisites
print_status "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check NVIDIA Docker (optional but recommended)
if command -v nvidia-smi &> /dev/null; then
    print_status "NVIDIA GPU detected. Checking Docker GPU support..."
    if docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        print_status "✅ NVIDIA Docker runtime is working"
    else
        print_warning "⚠️  NVIDIA Docker runtime not working. GPU acceleration will be disabled."
    fi
else
    print_warning "⚠️  No NVIDIA GPU detected. Running in CPU-only mode."
fi

# Check if Zoi network exists
if ! docker network ls | grep -q "zoi-network"; then
    print_status "Creating Zoi network..."
    docker network create zoi-network
fi

# Check if core services are running
print_status "Checking core Zoi services..."

REQUIRED_SERVICES=("postgres" "redis" "litellm")
MISSING_SERVICES=()

for service in "${REQUIRED_SERVICES[@]}"; do
    if ! docker ps | grep -q "$service"; then
        MISSING_SERVICES+=("$service")
    fi
done

if [ ${#MISSING_SERVICES[@]} -gt 0 ]; then
    print_warning "Missing required services: ${MISSING_SERVICES[*]}"
    print_status "Starting core Zoi services..."
    
    # Go to root directory and start core services
    cd ../../
    docker compose up -d postgres redis litellm
    
    # Wait for services to be ready
    print_status "Waiting for core services to be ready..."
    sleep 10
    
    # Return to coder directory
    cd apps/coder
fi

# Build and start Refact services
print_status "Building Refact services..."
docker compose build

print_status "Starting Refact services..."
docker compose up -d

# Wait for services to be ready
print_status "Waiting for Refact services to start..."
sleep 30

# Check service health
print_status "Checking service health..."

SERVICES=("refact-server:7400" "refact-agent:7401" "refact-gui:7402" "refact-docs:7403")
HEALTHY_SERVICES=()
UNHEALTHY_SERVICES=()

for service_port in "${SERVICES[@]}"; do
    service=$(echo $service_port | cut -d: -f1)
    port=$(echo $service_port | cut -d: -f2)
    
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1 || curl -f -s "http://localhost:$port" > /dev/null 2>&1; then
        HEALTHY_SERVICES+=("$service")
    else
        UNHEALTHY_SERVICES+=("$service")
    fi
done

# Display results
echo ""
print_header "🎉 Refact.ai Setup Complete!"
echo "=============================="

if [ ${#HEALTHY_SERVICES[@]} -gt 0 ]; then
    print_status "✅ Healthy services:"
    for service in "${HEALTHY_SERVICES[@]}"; do
        echo "   - $service"
    done
fi

if [ ${#UNHEALTHY_SERVICES[@]} -gt 0 ]; then
    print_warning "⚠️  Services still starting:"
    for service in "${UNHEALTHY_SERVICES[@]}"; do
        echo "   - $service"
    done
    echo ""
    print_status "Services may take a few more minutes to fully initialize."
fi

echo ""
print_header "🌐 Access URLs"
echo "==============="
echo "• Refact Server:  http://refact.zoi.local (or http://localhost:7400)"
echo "• Refact Chat:    http://refact-chat.zoi.local (or http://localhost:7402)"
echo "• Refact Agent:   http://refact-agent.zoi.local (or http://localhost:7401)"
echo "• Documentation:  http://refact-docs.zoi.local (or http://localhost:7403)"

echo ""
print_header "🔧 IDE Integration"
echo "=================="
echo "For VS Code:"
echo "1. Install Refact.ai extension"
echo "2. Set Inference URL: http://localhost:7401"
echo "3. Set API Key: refact-admin-token-zoi-2024-secure"
echo ""
echo "For JetBrains IDEs:"
echo "1. Install Refact.ai plugin"
echo "2. Settings > Tools > Refact.ai > Advanced"
echo "3. Set Inference URL: http://localhost:7401"
echo "4. Set API Key: refact-admin-token-zoi-2024-secure"

echo ""
print_header "📊 Monitoring"
echo "=============="
echo "• View logs: docker compose logs -f"
echo "• Check status: docker compose ps"
echo "• Restart service: docker compose restart <service-name>"

echo ""
print_header "🆘 Troubleshooting"
echo "=================="
echo "• If services fail to start, check logs: docker compose logs"
echo "• For GPU issues, verify: docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi"
echo "• For database issues, check: docker compose exec postgres psql -U postgres -l"

echo ""
print_status "🚀 Refact.ai is ready! Happy coding with AI assistance!"

# Optional: Open browser
if command -v xdg-open &> /dev/null; then
    read -p "Open Refact Chat in browser? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open "http://localhost:7402"
    fi
elif command -v open &> /dev/null; then
    read -p "Open Refact Chat in browser? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "http://localhost:7402"
    fi
fi
