#!/bin/bash

# Vault Initialization Script
# This script sets up Vault with initial configuration for the RAG system

set -e

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

VAULT_ADDR=${VAULT_ADDR:-http://localhost:8200}
VAULT_TOKEN=${VAULT_ROOT_TOKEN:-vault-root-token}

echo " Initializing HashiCorp Vault for RAG System..."
echo " Using token: ${VAULT_TOKEN:0:10}..."

# Wait for Vault to be ready
echo " Waiting for Vault to be ready..."
sleep 10

# Check if Vault is accessible
echo " Checking Vault status..."
if ! curl -s -o /dev/null -w "%{http_code}" "$VAULT_ADDR/v1/sys/health" | grep -q "200"; then
    echo " Vault is not ready. Please check if it's running."
    exit 1
fi

echo " Vault is ready"

# Function to run vault commands in Docker container
vault_exec() {
    docker exec -e VAULT_TOKEN="$VAULT_TOKEN" -e VAULT_ADDR="http://localhost:8200" zoi-vault-1 vault "$@"
}

# Set Vault token
export VAULT_TOKEN=$VAULT_TOKEN

echo " Creating Vault policies..."

# Apply application policy
echo " Applying app policy..."
vault_exec policy write app-policy /vault/config/policies/app-policy.hcl
echo " App policy created"

# Apply admin policy  
echo " Applying admin policy..."
vault_exec policy write admin-policy /vault/config/policies/admin-policy.hcl
echo " Admin policy created"

# Enable AppRole auth method
echo " Enabling AppRole authentication..."
if ! vault_exec auth enable approle 2>/dev/null; then
    echo " AppRole already enabled, continuing..."
fi

# Create AppRole for applications
echo " Creating AppRole for applications..."
vault_exec write auth/approle/role/rag-app \
    token_policies="app-policy" \
    token_ttl=1h \
    token_max_ttl=4h \
    bind_secret_id=true

# Get role_id (this will be used by applications)
ROLE_ID=$(vault_exec read -field=role_id auth/approle/role/rag-app/role-id)
echo " Application Role ID: $ROLE_ID"

# Generate secret_id (this should be securely distributed to applications)
SECRET_ID=$(vault_exec write -force -field=secret_id auth/approle/role/rag-app/secret-id)
echo " Application Secret ID: $SECRET_ID"

# Enable KV v2 secrets engine
echo " Enabling KV v2 secrets engine..."
if ! vault_exec secrets enable -path=secret kv-v2 2>/dev/null; then
    echo " KV v2 already enabled, continuing..."
fi

# Create initial secrets structure
echo " Creating initial secrets structure..."

# Application secrets
vault_exec kv put secret/app/database \
    host="postgres" \
    port="5432" \
    username="app_user" \
    password="secure_db_password" \
    database="rag_system"

vault_exec kv put secret/app/redis \
    host="redis" \
    port="6379" \
    password="secure_redis_password"

vault_exec kv put secret/app/rabbitmq \
    host="rabbitmq" \
    port="5672" \
    username="admin" \
    password="secure_rabbitmq_password" \
    vhost="/"

vault_exec kv put secret/app/qdrant \
    url="http://qdrant:6333" \
    api_key="" \
    timeout="30"

vault_exec kv put secret/app/mongodb \
    episodic_url="mongodb://mongo-episodic:27017" \
    procedural_url="mongodb://mongo-procedural:27017" \
    username="mongo_user" \
    password="secure_mongo_password"

# LLM API keys
vault_exec kv put secret/app/llm \
    openai_api_key="sk-your-openai-key-here" \
    anthropic_api_key="sk-ant-your-anthropic-key-here" \
    litellm_master_key="sk-your-litellm-master-key"

# Authentik secrets
vault_exec kv put secret/app/authentik \
    secret_key="your-long-authentik-secret-key" \
    bootstrap_password="secure-admin-password" \
    bootstrap_token="your-bootstrap-token" \
    bootstrap_email="admin@yourdomain.com"

# Environment-specific secrets
vault_exec kv put secret/env/development \
    debug="true" \
    log_level="debug" \
    environment="development"

vault_exec kv put secret/env/production \
    debug="false" \
    log_level="info" \
    environment="production"

# JWT secrets
vault_exec kv put secret/app/jwt \
    secret_key="your-jwt-secret-key-here" \
    algorithm="HS256" \
    expiration="24h"

echo " Vault initialization complete!"
echo ""
echo " Important Information:"
echo "   - Root Token: $VAULT_TOKEN"
echo "   - Role ID: $ROLE_ID"
echo "   - Secret ID: $SECRET_ID"
echo "   - Vault UI: $VAULT_ADDR/ui"
echo ""
echo "  Security Notice:"
echo "   - Store the Role ID and Secret ID securely"
echo "   - Consider rotating the Secret ID regularly"
echo "   - Use different Secret IDs for different environments"
echo "   - Never log or expose these credentials"
echo ""
echo " Next Steps:"
echo "   1. Update application configurations to use Vault"
echo "   2. Replace hardcoded secrets with Vault references"
echo "   3. Implement proper secret rotation policies"
echo "   4. Set up backup and disaster recovery for Vault data"
