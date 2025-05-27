#!/bin/bash

# OAuth2 Setup via Authentik Container Management Commands

set -e

echo "🔧 Setting up OAuth2 applications via Authentik container..."

# Function to execute commands in Authentik container
ak_exec() {
    docker-compose exec -T authentik-server ak "$@"
}

echo "📋 Creating custom OAuth2 scopes..."

# Create custom scopes using management commands
ak_exec create_oauth2_scope \
    --name "rag:api" \
    --description "Access to RAG API endpoints"

ak_exec create_oauth2_scope \
    --name "rag:chat" \
    --description "Access to chat interface"

ak_exec create_oauth2_scope \
    --name "rag:workflow" \
    --description "Access to workflow automation"

echo "📱 Creating OAuth2 providers and applications..."

# Create FastAPI OAuth2 Provider
echo "Creating FastAPI OAuth2 provider..."
ak_exec create_oauth2_provider \
    --name "fastapi-oauth2" \
    --client-id "fastapi-client" \
    --redirect-uris "https://api.localhost/auth/callback" \
    --scopes "openid,email,profile,rag:api"

# Create WebUI OAuth2 Provider  
echo "Creating WebUI OAuth2 provider..."
ak_exec create_oauth2_provider \
    --name "webui-oauth2" \
    --client-id "webui-client" \
    --redirect-uris "https://chat.localhost/auth/callback" \
    --scopes "openid,email,profile,rag:chat"

# Create n8n OAuth2 Provider
echo "Creating n8n OAuth2 provider..."
ak_exec create_oauth2_provider \
    --name "n8n-oauth2" \
    --client-id "n8n-client" \
    --redirect-uris "https://n8n.localhost/rest/oauth2-credential/callback" \
    --scopes "openid,email,profile,rag:workflow"

echo "🏢 Creating applications..."

# Create FastAPI Application
ak_exec create_application \
    --name "FastAPI Backend" \
    --slug "fastapi-backend" \
    --provider "fastapi-oauth2"

# Create WebUI Application
ak_exec create_application \
    --name "Chat Interface" \
    --slug "chat-interface" \
    --provider "webui-oauth2"

# Create n8n Application
ak_exec create_application \
    --name "Workflow Automation" \
    --slug "workflow-automation" \
    --provider "n8n-oauth2"

echo "🎉 OAuth2 setup completed!"
echo ""
echo "🔍 Verify the setup by visiting:"
echo "  - Applications: https://localhost:9443/if/admin/#/core/applications"
echo "  - Providers: https://localhost:9443/if/admin/#/core/providers"
echo ""
echo "⚠️  Note: You'll need to extract client secrets manually from the admin interface"
echo "   Go to Applications → Providers and copy the client secrets for each provider"
