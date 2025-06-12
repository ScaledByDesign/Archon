#!/bin/bash
# Bootstrap initialization script for Zoi system
# This script sets up the complete environment on first run

set -e

echo "🚀 Starting Zoi System Bootstrap..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the root of the Zoi project directory"
    exit 1
fi

print_step "1. Setting up local DNS entries..."
# Add missing DNS entries to /etc/hosts if not present
DOMAINS=("n8n.zoi.local" "auth.zoi.local" "dashy.zoi.local" "traefik.zoi.local" "llm.zoi.local")
for domain in "${DOMAINS[@]}"; do
    if ! grep -q "$domain" /etc/hosts; then
        print_status "Adding $domain to /etc/hosts"
        echo "127.0.0.1 $domain" | sudo tee -a /etc/hosts > /dev/null
    else
        print_status "$domain already in /etc/hosts"
    fi
done

print_step "2. Creating required directories..."
# Create directories if they don't exist
mkdir -p config/n8n/workflows
mkdir -p config/n8n/credentials
mkdir -p config/authentik/media
mkdir -p config/authentik/templates
mkdir -p data/n8n
mkdir -p logs

print_step "3. Starting core services..."
# Start services in dependency order
print_status "Starting infrastructure services..."
docker compose up -d traefik postgres redis

print_status "Waiting for database to be ready..."
sleep 10

print_status "Starting authentication services..."
docker compose up -d authentik-worker authentik-server

print_status "Waiting for Authentik to be ready..."
sleep 15

print_step "4. Applying Authentik blueprints..."
# Apply blueprints in order
BLUEPRINTS=(
    "00-flows.yaml"
    "01-users.yaml"
    "02-provider.yaml"
    "03-simple-policy.yaml"
    "04-outpost-provider-assignment.yaml"
    "05-outpost-permissions.yaml"
    "litellm-oauth-integration.yaml"
    "n8n-oauth-integration.yaml"
)

for blueprint in "${BLUEPRINTS[@]}"; do
    if [ -f "config/authentik/blueprints/$blueprint" ]; then
        print_status "Applying blueprint: $blueprint"
        if docker compose exec authentik-server ak apply_blueprint "/blueprints/custom/$blueprint" > /dev/null 2>&1; then
            print_status "✓ $blueprint applied successfully"
        else
            print_warning "⚠ Failed to apply $blueprint (may already exist)"
        fi
    else
        print_warning "Blueprint $blueprint not found, skipping"
    fi
done

print_step "5. Starting application services..."
print_status "Starting LiteLLM..."
docker compose up -d litellm

print_status "Starting n8n..."
docker compose up -d n8n

print_status "Starting Dashy..."
docker compose up -d dashy

print_step "6. Performing health checks..."
# Wait for services to be healthy
SERVICES=("traefik" "postgres" "authentik-server" "litellm" "n8n" "dashy")
for service in "${SERVICES[@]}"; do
    print_status "Checking $service health..."
    retries=0
    max_retries=30
    while [ $retries -lt $max_retries ]; do
        if docker compose ps $service | grep -q "healthy\|running"; then
            print_status "✓ $service is healthy"
            break
        fi
        retries=$((retries + 1))
        sleep 2
    done
    if [ $retries -eq $max_retries ]; then
        print_warning "⚠ $service may not be fully ready"
    fi
done

print_step "7. System verification..."
# Test key endpoints
print_status "Testing service accessibility..."

# Test Authentik
if curl -s -I http://auth.zoi.local > /dev/null 2>&1; then
    print_status "✓ Authentik accessible at http://auth.zoi.local"
else
    print_warning "⚠ Authentik may not be ready"
fi

# Test Traefik
if curl -s -I http://traefik.zoi.local > /dev/null 2>&1; then
    print_status "✓ Traefik dashboard accessible at http://traefik.zoi.local"
else
    print_warning "⚠ Traefik may not be ready"
fi

# Test services through Traefik
for service in "dashy" "llm" "n8n"; do
    if curl -s -I "http://$service.zoi.local" > /dev/null 2>&1; then
        print_status "✓ $service accessible at http://$service.zoi.local"
    else
        print_warning "⚠ $service may not be ready"
    fi
done

print_step "8. Bootstrap completed!"
echo
echo -e "${GREEN}🎉 Zoi System Bootstrap Complete!${NC}"
echo
echo "Access your services:"
echo "• Authentik:  http://auth.zoi.local"
echo "• Traefik:    http://traefik.zoi.local"
echo "• Dashy:      http://dashy.zoi.local"
echo "• LiteLLM:    http://llm.zoi.local"
echo "• n8n:        http://n8n.zoi.local"
echo
echo "Default credentials:"
echo "• Authentik admin: admin / password123"
echo "• LiteLLM: Uses master key authentication"
echo "• n8n: Uses Authentik SSO"
echo
echo "Next steps:"
echo "1. Change default passwords"
echo "2. Configure your LLM models in LiteLLM"
echo "3. Create your first workflow in n8n"
echo "4. Customize your dashboard in Dashy"
echo
print_status "System ready for use! 🚀"
