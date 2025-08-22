# Zoi Ecosystem Makefile
# Stack-based management for the complete Zoi ecosystem

.PHONY: help bootstrap start stop restart logs clean status health
.PHONY: start-llm start-platform start-tools start-archon start-monitor
.PHONY: stop-llm stop-platform stop-tools stop-archon stop-monitor
.PHONY: logs-llm logs-platform logs-tools logs-archon logs-monitor

# Default target
help:
	@echo "🌐 Zoi Ecosystem Management Commands"
	@echo "===================================="
	@echo ""
	@echo "🚀 Full System:"
	@echo "  make bootstrap     - Complete system bootstrap (first-time setup)"
	@echo "  make start         - Start all service stacks in correct order"
	@echo "  make stop          - Stop all service stacks"
	@echo "  make restart       - Restart all service stacks"
	@echo "  make status        - Show status of all services"
	@echo "  make logs          - Show logs from all stacks"
	@echo "  make clean         - Clean up all containers and volumes"
	@echo ""
	@echo "🏗️ Individual Stacks:"
	@echo "  make start-llm     - Start LLM stack (foundation)"
	@echo "  make start-platform - Start platform stack (infrastructure)"
	@echo "  make start-tools   - Start tools stack (applications)"
	@echo "  make start-archon  - Start Archon MCP stack (knowledge)"
	@echo "  make start-monitor - Start monitoring stack (observability)"
	@echo ""
	@echo "📊 Stack Management:"
	@echo "  make stop-<stack>  - Stop specific stack"
	@echo "  make logs-<stack>  - Show logs for specific stack"
	@echo ""
	@echo "🔍 Health & Testing:"
	@echo "  make health        - Check all service health"
	@echo "  make test-endpoints - Test all service endpoints"

# Complete system bootstrap
bootstrap:
	@echo "🚀 Starting complete Zoi ecosystem bootstrap..."
	@echo "Creating zoi-network..."
	@docker network create zoi-network 2>/dev/null || echo "Network already exists"
	@chmod +x scripts/bootstrap-init.sh
	@./scripts/bootstrap-init.sh

# Start all stacks in correct order
start:
	@echo "🌐 Starting Zoi ecosystem in correct order..."
	@make start-llm
	@echo "⏳ Waiting for LLM stack to stabilize..."
	@sleep 30
	@make start-platform
	@echo "⏳ Waiting for platform stack to stabilize..."
	@sleep 20
	@make start-tools
	@make start-archon
	@make start-monitor
	@echo "✅ All stacks started successfully!"

# Stop all stacks
stop:
	@echo "⏹️ Stopping all Zoi stacks..."
	@make stop-monitor
	@make stop-archon
	@make stop-tools
	@make stop-platform
	@make stop-llm
	@echo "✅ All stacks stopped"

# Restart all stacks
restart:
	@echo "🔄 Restarting Zoi ecosystem..."
	@make stop
	@sleep 10
	@make start

# Show status of all services
status:
	@echo "📊 Zoi Ecosystem Status"
	@echo "======================="
	@echo ""
	@echo "🧠 LLM Stack:"
	@cd apps/llm-local && docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Stack not running"
	@echo ""
	@echo "🏛️ Platform Stack:"
	@cd apps/platform && docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Stack not running"
	@echo ""
	@echo "🛠️ Tools Stack:"
	@cd apps/tools && docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Stack not running"
	@echo ""
	@echo "🤖 Archon MCP Stack:"
	@cd apps/archon-mcp && docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Stack not running"
	@echo ""
	@echo "📊 Monitoring Stack:"
	@cd apps/monitor && docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Stack not running"

# Show logs from all stacks
logs:
	@echo "📋 Showing logs from all stacks (last 20 lines each)..."
	@echo ""
	@echo "🧠 LLM Stack Logs:"
	@cd apps/llm-local && docker compose logs --tail=20 2>/dev/null || echo "No logs available"
	@echo ""
	@echo "🏛️ Platform Stack Logs:"
	@cd apps/platform && docker compose logs --tail=20 2>/dev/null || echo "No logs available"
	@echo ""
	@echo "🛠️ Tools Stack Logs:"
	@cd apps/tools && docker compose logs --tail=20 2>/dev/null || echo "No logs available"

# Individual stack management
start-llm:
	@echo "🧠 Starting LLM stack..."
	@cd apps/llm-local && docker compose up -d

start-platform:
	@echo "🏛️ Starting platform stack..."
	@cd apps/platform && docker compose up -d

start-tools:
	@echo "🛠️ Starting tools stack..."
	@cd apps/tools && docker compose up -d

start-archon:
	@echo "🤖 Starting Archon MCP stack..."
	@cd apps/archon-mcp && docker compose up -d

start-monitor:
	@echo "📊 Starting monitoring stack..."
	@cd apps/monitor && docker compose up -d

# Stop individual stacks
stop-llm:
	@echo "⏹️ Stopping LLM stack..."
	@cd apps/llm-local && docker compose down

stop-platform:
	@echo "⏹️ Stopping platform stack..."
	@cd apps/platform && docker compose down

stop-tools:
	@echo "⏹️ Stopping tools stack..."
	@cd apps/tools && docker compose down

stop-archon:
	@echo "⏹️ Stopping Archon MCP stack..."
	@cd apps/archon-mcp && docker compose down

stop-monitor:
	@echo "⏹️ Stopping monitoring stack..."
	@cd apps/monitor && docker compose down

# Individual stack logs
logs-llm:
	@echo "🧠 LLM Stack Logs:"
	@cd apps/llm-local && docker compose logs -f --tail=50

logs-platform:
	@echo "🏛️ Platform Stack Logs:"
	@cd apps/platform && docker compose logs -f --tail=50

logs-tools:
	@echo "🛠️ Tools Stack Logs:"
	@cd apps/tools && docker compose logs -f --tail=50

logs-archon:
	@echo "🤖 Archon MCP Stack Logs:"
	@cd apps/archon-mcp && docker compose logs -f --tail=50

logs-monitor:
	@echo "📊 Monitoring Stack Logs:"
	@cd apps/monitor && docker compose logs -f --tail=50

# Clean up system
clean:
	@echo "🧹 Cleaning up Zoi ecosystem..."
	@make stop
	@docker system prune -f
	@docker volume prune -f
	@docker network rm zoi-network 2>/dev/null || true
	@echo "✅ System cleaned. Use 'make bootstrap' to start fresh."

# Health check all services
health:
	@echo "🏥 Checking Zoi ecosystem health..."
	@echo ""
	@echo "🌐 Core Infrastructure:"
	@curl -s -I http://traefik.zoi.local >/dev/null 2>&1 && echo "✅ Traefik: OK" || echo "❌ Traefik: Failed"
	@curl -s -I http://auth.zoi.local >/dev/null 2>&1 && echo "✅ Authentik: OK" || echo "❌ Authentik: Failed"
	@echo ""
	@echo "🧠 AI Services:"
	@curl -s -I http://litellm.zoi.local >/dev/null 2>&1 && echo "✅ LiteLLM: OK" || echo "❌ LiteLLM: Failed"
	@curl -s -I http://ollama.zoi.local >/dev/null 2>&1 && echo "✅ Ollama: OK" || echo "❌ Ollama: Failed"
	@curl -s -I http://langflow.zoi.local >/dev/null 2>&1 && echo "✅ LangFlow: OK" || echo "❌ LangFlow: Failed"
	@echo ""
	@echo "🛠️ Tools:"
	@curl -s -I http://n8n.zoi.local >/dev/null 2>&1 && echo "✅ n8n: OK" || echo "❌ n8n: Failed"
	@curl -s -I http://openwebui.zoi.local >/dev/null 2>&1 && echo "✅ OpenWebUI: OK" || echo "❌ OpenWebUI: Failed"
	@curl -s -I http://lobechat.zoi.local >/dev/null 2>&1 && echo "✅ LobeChat: OK" || echo "❌ LobeChat: Failed"
	@echo ""
	@echo "📊 Monitoring:"
	@curl -s -I http://prometheus.zoi.local >/dev/null 2>&1 && echo "✅ Prometheus: OK" || echo "❌ Prometheus: Failed"
	@curl -s -I http://grafana.zoi.local >/dev/null 2>&1 && echo "✅ Grafana: OK" || echo "❌ Grafana: Failed"

# Test all endpoints
test-endpoints:
	@echo "🧪 Testing Zoi ecosystem endpoints..."
	@echo ""
	@echo "🔗 API Endpoints (direct access):"
	@curl -s -I http://litellm.zoi.local/v1/models 2>/dev/null | head -1 || echo "❌ LiteLLM API: Failed"
	@curl -s -I http://n8n.zoi.local/api/v1/workflows 2>/dev/null | head -1 || echo "❌ n8n API: Failed"
	@curl -s -I http://prometheus.zoi.local/api/v1/query 2>/dev/null | head -1 || echo "❌ Prometheus API: Failed"
	@echo ""
	@echo "🌐 Frontend UIs (should redirect to auth):"
	@curl -s -I http://dashy.zoi.local 2>/dev/null | head -1 || echo "❌ Dashy UI: Failed"
	@curl -s -I http://grafana.zoi.local 2>/dev/null | head -1 || echo "❌ Grafana UI: Failed"
