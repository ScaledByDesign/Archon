#!/bin/bash

# Direct OAuth2 Application Creation Script
# This script creates OAuth2 applications directly using Authentik's API

set -e

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

echo "🔧 Creating OAuth2 applications in Authentik..."

# Configuration
AUTHENTIK_BASE_URL=${AUTHENTIK_BASE_URL:-https://localhost:9443}
ADMIN_USERNAME=${AUTHENTIK_BOOTSTRAP_EMAIL:-admin@localhost}
ADMIN_PASSWORD=${AUTHENTIK_BOOTSTRAP_PASSWORD:-change-me-authentik-admin}

# Check if Authentik is accessible
if ! curl -k -s "$AUTHENTIK_BASE_URL" > /dev/null; then
    echo "❌ Authentik is not accessible at $AUTHENTIK_BASE_URL"
    echo "Please ensure Authentik services are running."
    exit 1
fi

# Function to get session token by logging in
get_session_token() {
    echo "🔐 Authenticating with Authentik..."
    
    # Get the login page to extract CSRF token
    login_page=$(curl -k -s -c cookies.txt "$AUTHENTIK_BASE_URL/if/admin/")
    csrf_token=$(echo "$login_page" | grep -o 'csrfmiddlewaretoken[^>]*value="[^"]*"' | sed 's/.*value="\([^"]*\)".*/\1/')
    
    if [ -z "$csrf_token" ]; then
        echo "❌ Could not extract CSRF token"
        return 1
    fi
    
    # Perform login
    login_response=$(curl -k -s -b cookies.txt -c cookies.txt \
        -d "csrfmiddlewaretoken=$csrf_token" \
        -d "uid_field=$ADMIN_USERNAME" \
        -d "password=$ADMIN_PASSWORD" \
        -X POST \
        "$AUTHENTIK_BASE_URL/flows/default/authentication/")
    
    if echo "$login_response" | grep -q "Invalid credentials"; then
        echo "❌ Invalid credentials"
        return 1
    fi
    
    echo "✅ Successfully authenticated"
    return 0
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
        "client_secret": "",
        "access_code_validity": "minutes=1",
        "access_token_validity": "minutes=5",
        "refresh_token_validity": "days=30",
        "include_claims_in_id_token": true,
        "issuer_mode": "per_provider",
        "sub_mode": "hashed_user_id",
        "redirect_uris": "'$redirect_uris'",
        "signing_key": null
    }'
    
    # Get CSRF token for API call
    csrf_token=$(curl -k -s -b cookies.txt "$AUTHENTIK_BASE_URL/api/v3/" | grep -o 'csrfToken":"[^"]*' | cut -d'"' -f3)
    
    # Create provider
    provider_response=$(curl -k -s -b cookies.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRFToken: $csrf_token" \
        -d "$provider_data" \
        -X POST \
        "$AUTHENTIK_BASE_URL/api/v3/providers/oauth2/")
    
    provider_pk=$(echo "$provider_response" | jq -r '.pk // empty')
    
    if [ -z "$provider_pk" ]; then
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
        "meta_description": "",
        "meta_publisher": "",
        "policy_engine_mode": "any",
        "group": ""
    }'
    
    app_response=$(curl -k -s -b cookies.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRFToken: $csrf_token" \
        -d "$app_data" \
        -X POST \
        "$AUTHENTIK_BASE_URL/api/v3/core/applications/")
    
    app_slug=$(echo "$app_response" | jq -r '.slug // empty')
    
    if [ -z "$app_slug" ]; then
        echo "❌ Failed to create application for $app_name"
        echo "Response: $app_response"
        return 1
    fi
    
    echo "✅ Created application: $app_name (slug: $app_slug)"
    
    # Extract and display client secret
    client_secret=$(echo "$provider_response" | jq -r '.client_secret // empty')
    if [ -n "$client_secret" ]; then
        echo "🔑 Client Secret for $client_id: $client_secret"
        echo "export ${client_id^^}_CLIENT_SECRET=\"$client_secret\"" >> client_secrets.sh
    fi
    
    return 0
}

# Function to create scopes
create_scope() {
    local scope_name="$1"
    local scope_description="$2"
    
    echo "🎯 Creating scope: $scope_name"
    
    csrf_token=$(curl -k -s -b cookies.txt "$AUTHENTIK_BASE_URL/api/v3/" | grep -o 'csrfToken":"[^"]*' | cut -d'"' -f3)
    
    scope_data='{
        "name": "'$scope_name'",
        "description": "'$scope_description'"
    }'
    
    scope_response=$(curl -k -s -b cookies.txt \
        -H "Content-Type: application/json" \
        -H "X-CSRFToken: $csrf_token" \
        -d "$scope_data" \
        -X POST \
        "$AUTHENTIK_BASE_URL/api/v3/providers/oauth2/scopes/")
    
    if echo "$scope_response" | jq -e '.name' > /dev/null; then
        echo "✅ Created scope: $scope_name"
    else
        echo "⚠️  Scope $scope_name may already exist or creation failed"
    fi
}

# Cleanup function
cleanup() {
    rm -f cookies.txt client_secrets.sh
}

# Set trap for cleanup
trap cleanup EXIT

# Main execution
echo "🚀 Starting OAuth2 application setup..."

# Authenticate
if ! get_session_token; then
    echo "❌ Authentication failed"
    exit 1
fi

# Create custom scopes
echo ""
echo "📋 Creating custom OAuth2 scopes..."
create_scope "rag:api" "Access to RAG API endpoints"
create_scope "rag:chat" "Access to chat interface"
create_scope "rag:workflow" "Access to workflow automation"

echo ""
echo "📱 Creating OAuth2 applications..."

# Create applications
create_oauth_app "FastAPI Backend" "fastapi-client" "https://api.localhost/auth/callback" "openid email profile rag:api"
create_oauth_app "Chat Interface" "webui-client" "https://chat.localhost/auth/callback" "openid email profile rag:chat"
create_oauth_app "Workflow Automation" "n8n-client" "https://n8n.localhost/rest/oauth2-credential/callback" "openid email profile rag:workflow"

echo ""
echo "🎉 OAuth2 application setup completed!"
echo ""
echo "📄 Client secrets have been saved to client_secrets.sh"
echo "Run 'source client_secrets.sh' to export the secrets to your environment"
echo ""
echo "🔍 Verify the setup by visiting:"
echo "  - Applications: $AUTHENTIK_BASE_URL/if/admin/#/core/applications"
echo "  - Providers: $AUTHENTIK_BASE_URL/if/admin/#/core/providers"
echo "  - Scopes: $AUTHENTIK_BASE_URL/if/admin/#/providers/oauth2/scopes"
