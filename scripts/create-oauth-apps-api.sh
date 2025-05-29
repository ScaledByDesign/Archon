#!/bin/bash

# OAuth2 Application Creation Script using Authentik API Token
# This script creates OAuth2 applications using Authentik's API with token authentication

set -e

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

echo "🔧 Creating OAuth2 applications in Authentik using API token..."

# Configuration
AUTHENTIK_BASE_URL=${AUTHENTIK_BASE_URL:-https://localhost:9443}
API_TOKEN=${AUTHENTIK_BOOTSTRAP_TOKEN:-change-me-authentik-bootstrap-token-32-chars}

# Check if Authentik is accessible
if ! curl -k -s "$AUTHENTIK_BASE_URL" > /dev/null; then
    echo "❌ Authentik is not accessible at $AUTHENTIK_BASE_URL"
    echo "Please ensure Authentik services are running."
    exit 1
fi

echo "✅ Authentik is accessible at $AUTHENTIK_BASE_URL"

# Function to make authenticated API calls
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    
    if [ -n "$data" ]; then
        curl -k -s \
            -H "Authorization: Bearer $API_TOKEN" \
            -H "Content-Type: application/json" \
            -X "$method" \
            -d "$data" \
            "$AUTHENTIK_BASE_URL/api/v3/$endpoint"
    else
        curl -k -s \
            -H "Authorization: Bearer $API_TOKEN" \
            -H "Content-Type: application/json" \
            -X "$method" \
            "$AUTHENTIK_BASE_URL/api/v3/$endpoint"
    fi
}

# Function to create OAuth2 provider and application
create_oauth_app() {
    local app_name="$1"
    local client_id="$2"
    local redirect_uris="$3"
    local scopes="$4"
    
    echo "📱 Creating OAuth2 application: $app_name"
    
    # Create OAuth2 provider
    provider_data='{
        "name": "'$app_name' OAuth2 Provider",
        "authentication_flow": null,
        "authorization_flow": "default-authorization-flow",
        "client_id": "'$client_id'",
        "client_type": "confidential",
        "access_code_validity": "minutes=1",
        "access_token_validity": "minutes=5",
        "refresh_token_validity": "days=30",
        "include_claims_in_id_token": true,
        "issuer_mode": "per_provider",
        "sub_mode": "hashed_user_id",
        "redirect_uris": "'$redirect_uris'",
        "signing_key": null
    }'
    
    # Create provider
    echo "🔧 Creating OAuth2 provider..."
    provider_response=$(api_call "POST" "providers/oauth2/" "$provider_data")
    
    provider_pk=$(echo "$provider_response" | jq -r '.pk // empty')
    
    if [ -z "$provider_pk" ] || [ "$provider_pk" = "null" ]; then
        echo "❌ Failed to create provider for $app_name"
        echo "Response: $provider_response"
        return 1
    fi
    
    echo "✅ Created OAuth2 provider (pk: $provider_pk)"
    
    # Create application
    app_data='{
        "name": "'$app_name'",
        "slug": "'$(echo $app_name | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')'",
        "provider": '$provider_pk',
        "backchannel_providers": [],
        "open_in_new_tab": false,
        "meta_launch_url": "",
        "meta_description": "OAuth2 application for '$app_name'",
        "meta_publisher": "ZOI RAG System",
        "policy_engine_mode": "any",
        "group": ""
    }'
    
    echo "🔧 Creating application..."
    app_response=$(api_call "POST" "core/applications/" "$app_data")
    
    app_slug=$(echo "$app_response" | jq -r '.slug // empty')
    
    if [ -z "$app_slug" ] || [ "$app_slug" = "null" ]; then
        echo "❌ Failed to create application for $app_name"
        echo "Response: $app_response"
        return 1
    fi
    
    echo "✅ Created application: $app_name (slug: $app_slug)"
    
    # Extract and display client secret
    client_secret=$(echo "$provider_response" | jq -r '.client_secret // empty')
    if [ -n "$client_secret" ] && [ "$client_secret" != "null" ]; then
        echo "🔑 Client ID: $client_id"
        echo "🔑 Client Secret: $client_secret"
        echo ""
        echo "# $app_name OAuth2 Credentials" >> oauth_credentials.env
        echo "export ${client_id^^}_CLIENT_ID=\"$client_id\"" >> oauth_credentials.env
        echo "export ${client_id^^}_CLIENT_SECRET=\"$client_secret\"" >> oauth_credentials.env
        echo "" >> oauth_credentials.env
    fi
    
    return 0
}

# Function to create scopes
create_scope() {
    local scope_name="$1"
    local scope_description="$2"
    
    echo "🎯 Creating scope: $scope_name"
    
    scope_data='{
        "name": "'$scope_name'",
        "description": "'$scope_description'"
    }'
    
    scope_response=$(api_call "POST" "providers/oauth2/scopes/" "$scope_data")
    
    if echo "$scope_response" | jq -e '.name' > /dev/null 2>&1; then
        echo "✅ Created scope: $scope_name"
    else
        echo "⚠️  Scope $scope_name may already exist or creation failed"
        echo "Response: $scope_response"
    fi
}

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up temporary files..."
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution
echo "🚀 Starting OAuth2 application setup..."

# Test API connectivity
echo "🔍 Testing API connectivity..."
api_test=$(api_call "GET" "core/applications/")
if echo "$api_test" | jq -e '.results' > /dev/null 2>&1; then
    echo "✅ API authentication successful"
else
    echo "❌ API authentication failed"
    echo "Response: $api_test"
    echo "Please check your AUTHENTIK_BOOTSTRAP_TOKEN in .env file"
    exit 1
fi

# Create custom scopes
echo ""
echo "📋 Creating custom OAuth2 scopes..."
create_scope "rag:api" "Access to RAG API endpoints"
create_scope "rag:chat" "Access to chat interface"
create_scope "rag:workflow" "Access to workflow automation"
create_scope "rag:admin" "Administrative access to RAG system"

echo ""
echo "📱 Creating OAuth2 applications..."

# Create applications with proper redirect URIs
create_oauth_app "FastAPI Backend" "fastapi-client" "http://localhost:8000/auth/callback,https://api.localhost/auth/callback" "openid email profile rag:api"
create_oauth_app "Chat Interface" "webui-client" "http://localhost:3000/auth/callback,https://chat.localhost/auth/callback" "openid email profile rag:chat"
create_oauth_app "Workflow Automation" "n8n-client" "http://localhost:5678/rest/oauth2-credential/callback,https://n8n.localhost/rest/oauth2-credential/callback" "openid email profile rag:workflow"
create_oauth_app "Admin Dashboard" "admin-client" "http://localhost:8080/auth/callback,https://admin.localhost/auth/callback" "openid email profile rag:admin"

echo ""
echo "🎉 OAuth2 application setup completed!"
echo ""
echo "📄 Client credentials have been saved to oauth_credentials.env"
echo "Run 'source oauth_credentials.env' to export the credentials to your environment"
echo ""
echo "🔍 Verify the setup by visiting:"
echo "  - Applications: $AUTHENTIK_BASE_URL/if/admin/#/core/applications"
echo "  - Providers: $AUTHENTIK_BASE_URL/if/admin/#/core/providers"
echo "  - Scopes: $AUTHENTIK_BASE_URL/if/admin/#/providers/oauth2/scopes"
echo ""
echo "🔐 Next steps:"
echo "1. Update your application configurations with the client credentials"
echo "2. Configure your applications to use Authentik as the OAuth2 provider"
echo "3. Test the OAuth2 flows with your applications"
