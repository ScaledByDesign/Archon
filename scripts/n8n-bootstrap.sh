#!/bin/bash
# n8n Bootstrap Script - Sets up default workflows and configurations

set -e

echo "🔧 n8n Bootstrap Setup..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[n8n]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Wait for n8n to be ready
print_status "Waiting for n8n to be ready..."
retries=0
max_retries=30
while [ $retries -lt $max_retries ]; do
    if curl -s http://localhost:5678/healthz > /dev/null 2>&1; then
        print_status "✓ n8n is ready"
        break
    fi
    retries=$((retries + 1))
    sleep 2
done

if [ $retries -eq $max_retries ]; then
    echo "❌ n8n not ready, skipping bootstrap"
    exit 1
fi

# Create starter workflow directory if it doesn't exist
mkdir -p config/n8n/workflows

# Create a sample webhook workflow
print_step "Creating sample webhook workflow..."
cat > config/n8n/workflows/sample-webhook.json << 'EOF'
{
  "name": "Sample Webhook Workflow",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "sample-webhook",
        "responseMode": "responseNode"
      },
      "id": "webhook-node",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300],
      "webhookId": "sample-webhook"
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "{\n  \"status\": \"success\",\n  \"message\": \"Webhook received successfully\",\n  \"timestamp\": \"{{ $now }}\",\n  \"data\": {{ $json }}\n}"
      },
      "id": "response-node",
      "name": "Respond to Webhook",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [460, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "Respond to Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "active": true,
  "settings": {},
  "versionId": "1"
}
EOF

# Create a health check workflow
print_step "Creating health check workflow..."
cat > config/n8n/workflows/health-check.json << 'EOF'
{
  "name": "System Health Check",
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "minutes",
              "minutesInterval": 5
            }
          ]
        }
      },
      "id": "schedule-node",
      "name": "Every 5 minutes",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "http://localhost:5678/healthz",
        "options": {}
      },
      "id": "http-node",
      "name": "Health Check",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4,
      "position": [460, 300]
    },
    {
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{ $json.statusCode }}",
              "operation": "equal",
              "value2": 200
            }
          ]
        }
      },
      "id": "if-node",
      "name": "Is Healthy?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [680, 300]
    }
  ],
  "connections": {
    "Every 5 minutes": {
      "main": [
        [
          {
            "node": "Health Check",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Health Check": {
      "main": [
        [
          {
            "node": "Is Healthy?",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "active": false,
  "settings": {},
  "versionId": "1"
}
EOF

# Create environment-specific configuration
print_step "Creating n8n environment configuration..."
cat > config/n8n/environment-config.json << EOF
{
  "nodes": [
    {
      "name": "System Environment",
      "type": "environment",
      "variables": {
        "AUTHENTIK_URL": "http://auth.zoi.local",
        "TRAEFIK_URL": "http://traefik.zoi.local", 
        "LITELLM_URL": "http://llm.zoi.local",
        "WEBHOOK_BASE_URL": "http://n8n.zoi.local/webhook",
        "API_BASE_URL": "http://n8n.zoi.local/api"
      }
    }
  ]
}
EOF

print_status "Creating workflow templates directory..."
mkdir -p config/n8n/templates

# Create template for Authentik integration
cat > config/n8n/templates/authentik-user-sync.json << 'EOF'
{
  "name": "Authentik User Sync Template",
  "description": "Template for syncing users from Authentik",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "authentik-sync",
        "responseMode": "responseNode"
      },
      "name": "Authentik Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "http://auth.zoi.local/api/v3/core/users/",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "options": {}
      },
      "name": "Get Authentik Users",
      "type": "n8n-nodes-base.httpRequest",
      "position": [460, 300]
    }
  ],
  "active": false
}
EOF

print_status "✓ n8n bootstrap configuration created"
print_status "Sample workflows available in config/n8n/workflows/"
print_status "Templates available in config/n8n/templates/"
print_status ""
print_status "To import workflows:"
print_status "1. Access n8n at http://n8n.zoi.local"
print_status "2. Go to Workflows > Import from File"
print_status "3. Select files from config/n8n/workflows/"
print_status ""
print_status "Test webhook: curl -X POST http://n8n.zoi.local/webhook/sample-webhook -d '{\"test\": \"data\"}'"
