#!/bin/bash

# Authentik Application Registration Setup Script
# This script generates client secrets and updates environment variables for OAuth2 applications

set -e  # Exit on any error

echo "🔧 Setting up Authentik OAuth2 Application Registration..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please ensure you're in the project root directory."
    exit 1
fi

# Function to generate secure random string
generate_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Generate OAuth2 client secrets
echo "🔑 Generating OAuth2 client secrets..."

FASTAPI_CLIENT_SECRET=$(generate_secret)
WEBUI_CLIENT_SECRET=$(generate_secret)
N8N_CLIENT_SECRET=$(generate_secret)

echo "Generated client secrets:"
echo "- FastAPI Client Secret: ${FASTAPI_CLIENT_SECRET:0:8}..."
echo "- WebUI Client Secret: ${WEBUI_CLIENT_SECRET:0:8}..."
echo "- n8n Client Secret: ${N8N_CLIENT_SECRET:0:8}..."

# Update .env file with new secrets
echo "📝 Updating .env file with OAuth2 client secrets..."

# Function to update or add environment variable
update_env_var() {
    local var_name=$1
    local var_value=$2
    
    if grep -q "^${var_name}=" .env; then
        # Variable exists, update it
        sed -i.bak "s/^${var_name}=.*/${var_name}=${var_value}/" .env
    else
        # Variable doesn't exist, add it
        echo "${var_name}=${var_value}" >> .env
    fi
}

# Add OAuth2 client secrets to .env
update_env_var "FASTAPI_OAUTH_CLIENT_SECRET" "$FASTAPI_CLIENT_SECRET"
update_env_var "WEBUI_OAUTH_CLIENT_SECRET" "$WEBUI_CLIENT_SECRET"
update_env_var "N8N_OAUTH_CLIENT_SECRET" "$N8N_CLIENT_SECRET"

# Add OAuth2 client IDs to .env (these are fixed)
update_env_var "FASTAPI_OAUTH_CLIENT_ID" "fastapi-client"
update_env_var "WEBUI_OAUTH_CLIENT_ID" "webui-client"
update_env_var "N8N_OAUTH_CLIENT_ID" "n8n-client"

# Add Authentik URLs
DOMAIN=${DOMAIN:-localhost}
update_env_var "AUTHENTIK_URL" "https://auth.${DOMAIN}"
update_env_var "AUTHENTIK_ISSUER" "https://auth.${DOMAIN}/application/o"

echo "✅ Environment variables updated successfully!"

# Create client secrets file for reference
echo "📄 Creating client secrets reference file..."
cat > config/authentik/client-secrets.json << EOF
{
  "generated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "clients": {
    "fastapi": {
      "client_id": "fastapi-client",
      "client_secret": "$FASTAPI_CLIENT_SECRET",
      "type": "confidential",
      "scopes": ["openid", "email", "profile", "rag:api"]
    },
    "webui": {
      "client_id": "webui-client", 
      "client_secret": "$WEBUI_CLIENT_SECRET",
      "type": "public",
      "scopes": ["openid", "email", "profile", "rag:chat"]
    },
    "n8n": {
      "client_id": "n8n-client",
      "client_secret": "$N8N_CLIENT_SECRET", 
      "type": "confidential",
      "scopes": ["openid", "email", "profile", "rag:workflows"]
    }
  }
}
EOF

# Make sure the file is secure
chmod 600 config/authentik/client-secrets.json

echo "🔒 Client secrets stored securely in config/authentik/client-secrets.json"

# Create service configuration templates
echo "📋 Creating service configuration templates..."

# FastAPI OAuth2 configuration
mkdir -p config/fastapi
cat > config/fastapi/oauth2-config.yaml << EOF
oauth2:
  client_id: "\${FASTAPI_OAUTH_CLIENT_ID}"
  client_secret: "\${FASTAPI_OAUTH_CLIENT_SECRET}"
  server_metadata_url: "\${AUTHENTIK_ISSUER}/fastapi-oauth2/.well-known/openid_configuration"
  scopes: ["openid", "email", "profile", "rag:api"]
  redirect_uri: "https://api.\${DOMAIN:-localhost}/auth/callback"

authentik:
  base_url: "\${AUTHENTIK_URL}"
  issuer: "\${AUTHENTIK_ISSUER}"
  userinfo_endpoint: "\${AUTHENTIK_ISSUER}/userinfo/"
  
security:
  jwt_algorithm: "RS256"
  token_verification: true
  require_https: true
EOF

# Open WebUI OAuth2 configuration
mkdir -p config/openwebui
cat > config/openwebui/oauth2-config.yaml << EOF
oauth:
  client_id: "\${WEBUI_OAUTH_CLIENT_ID}"
  client_secret: "\${WEBUI_OAUTH_CLIENT_SECRET}"
  provider_name: "Authentik"
  authorization_url: "\${AUTHENTIK_ISSUER}/authorize/"
  token_url: "\${AUTHENTIK_ISSUER}/token/"
  userinfo_url: "\${AUTHENTIK_ISSUER}/userinfo/"
  scopes: ["openid", "email", "profile", "rag:chat"]
  redirect_uri: "https://chat.\${DOMAIN:-localhost}/auth/callback"
  
claims_mapping:
  username: "preferred_username"
  email: "email"
  name: "name"
  groups: "groups"
EOF

# n8n OAuth2 configuration  
mkdir -p config/n8n
cat > config/n8n/oauth2-config.yaml << EOF
credentials:
  oauth2:
    client_id: "\${N8N_OAUTH_CLIENT_ID}"
    client_secret: "\${N8N_OAUTH_CLIENT_SECRET}"
    authorization_url: "\${AUTHENTIK_ISSUER}/authorize/"
    token_url: "\${AUTHENTIK_ISSUER}/token/"
    userinfo_url: "\${AUTHENTIK_ISSUER}/userinfo/"
    scopes: ["openid", "email", "profile", "rag:workflows"]
    
workflow_access:
  require_authentication: true
  allowed_groups: ["admins"]
  token_validation: true
EOF

echo "📁 Configuration templates created in config/ directories"

# Display next steps
cat << EOF

🎉 Authentik Application Registration Setup Complete!

Next Steps:
1. Start Authentik services: docker-compose up -d authentik-db authentik-redis authentik-server authentik-worker
2. Wait for services to be healthy (check with: docker-compose ps)
3. Access Authentik admin: https://auth.${DOMAIN}/if/admin/
4. Login with bootstrap credentials from .env file
5. Apply blueprints to create applications and scopes
6. Configure individual services using the generated config templates

Files Created:
- config/authentik/client-secrets.json (SECURE - contains secrets)
- config/fastapi/oauth2-config.yaml
- config/openwebui/oauth2-config.yaml  
- config/n8n/oauth2-config.yaml

Environment Variables Added:
- FASTAPI_OAUTH_CLIENT_ID & FASTAPI_OAUTH_CLIENT_SECRET
- WEBUI_OAUTH_CLIENT_ID & WEBUI_OAUTH_CLIENT_SECRET
- N8N_OAUTH_CLIENT_ID & N8N_OAUTH_CLIENT_SECRET
- AUTHENTIK_URL & AUTHENTIK_ISSUER

⚠️  Security Note: Keep client-secrets.json secure and do not commit it to version control!

EOF

# Add client-secrets.json to .gitignore if not already there
if ! grep -q "client-secrets.json" .gitignore 2>/dev/null; then
    echo "config/authentik/client-secrets.json" >> .gitignore
    echo "📝 Added client-secrets.json to .gitignore"
fi

echo "✅ Setup script completed successfully!"
