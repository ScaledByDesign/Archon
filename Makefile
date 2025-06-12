# Zoi System Makefile
# Provides easy commands for bootstrapping and managing the system

.PHONY: help bootstrap start stop restart logs clean dev-start prod-start

# Default target
help:
	@echo "Zoi System Management Commands:"
	@echo ""
	@echo "Bootstrap & Setup:"
	@echo "  make bootstrap     - Complete system bootstrap (first-time setup)"
	@echo "  make dev-start     - Start with development/bootstrap features"
	@echo "  make start         - Start all services"
	@echo ""
	@echo "Management:"
	@echo "  make stop          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - Show logs for all services"
	@echo "  make status        - Show service status"
	@echo ""
	@echo "Development:"
	@echo "  make n8n-bootstrap - Bootstrap n8n workflows and config"
	@echo "  make auth-reset    - Reset Authentik and reapply blueprints"
	@echo "  make clean         - Clean up containers and volumes"
	@echo ""
	@echo "Health Checks:"
	@echo "  make health        - Check all service health"
	@echo "  make test-endpoints - Test all service endpoints"

# Complete system bootstrap
bootstrap:
	@echo "🚀 Starting complete Zoi system bootstrap..."
	@chmod +x scripts/bootstrap-init.sh
	@./scripts/bootstrap-init.sh

# Development start with bootstrap features
dev-start:
	@echo "🔧 Starting development environment..."
	@docker compose -f docker-compose.yml -f docker-compose.bootstrap.yml up -d
	@echo "Waiting for services to start..."
	@sleep 15
	@make n8n-bootstrap

# Standard start
start:
	@echo "▶️ Starting Zoi services..."
	@docker compose up -d
	@echo "Services started. Use 'make logs' to monitor startup."

# Stop all services
stop:
	@echo "⏹️ Stopping Zoi services..."
	@docker compose down

# Restart all services
restart:
	@echo "🔄 Restarting Zoi services..."
	@docker compose restart

# Show logs
logs:
	@docker compose logs -f --tail=50

# Show service status
status:
	@echo "📊 Service Status:"
	@docker compose ps

# Bootstrap n8n specifically
n8n-bootstrap:
	@echo "🔧 Bootstrapping n8n..."
	@chmod +x scripts/n8n-bootstrap.sh
	@./scripts/n8n-bootstrap.sh

# Reset Authentik and reapply blueprints
auth-reset:
	@echo "🔐 Resetting Authentik configuration..."
	@docker compose restart authentik-server
	@sleep 10
	@chmod +x scripts/authentik-bootstrap.sh
	@docker compose exec authentik-server /blueprints/startup-scripts/apply-blueprints.sh

# Clean up system
clean:
	@echo "🧹 Cleaning up Zoi system..."
	@docker compose down -v
	@docker system prune -f
	@echo "System cleaned. Use 'make bootstrap' to start fresh."

# Health check all services
health:
	@echo "🏥 Checking service health..."
	@echo "Traefik:" && curl -s -I http://traefik.zoi.local > /dev/null && echo "✓ OK" || echo "✗ Failed"
	@echo "Authentik:" && curl -s -I http://auth.zoi.local > /dev/null && echo "✓ OK" || echo "✗ Failed"
	@echo "Dashy:" && curl -s -I http://dashy.zoi.local > /dev/null && echo "✓ OK" || echo "✗ Failed"
	@echo "LiteLLM:" && curl -s -I http://llm.zoi.local > /dev/null && echo "✓ OK" || echo "✗ Failed"
	@echo "n8n:" && curl -s -I http://n8n.zoi.local > /dev/null && echo "✓ OK" || echo "✗ Failed"

# Test all endpoints
test-endpoints:
	@echo "🧪 Testing service endpoints..."
	@echo ""
	@echo "Frontend UI (should redirect to auth):"
	@curl -s -I http://dashy.zoi.local | head -1
	@curl -s -I http://llm.zoi.local | head -1  
	@curl -s -I http://n8n.zoi.local | head -1
	@echo ""
	@echo "API endpoints (should be direct access):"
	@curl -s -I http://llm.zoi.local/v1/models | head -1
	@curl -s -I http://n8n.zoi.local/webhook/test | head -1
	@curl -s -I http://n8n.zoi.local/api/v1/workflows | head -1

# Production start (without development tools)
prod-start:
	@echo "🚀 Starting production environment..."
	@docker compose up -d --scale dev-tools=0 --scale bootstrap=0
