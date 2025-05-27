#!/bin/bash

# Authentik Blueprint Application Script
# This script applies Authentik blueprints via the API in the correct order

set -e

echo "🔧 Applying Authentik blueprints..."

# Configuration
AUTHENTIK_URL="${AUTHENTIK_URL:-https://auth.localhost}"
AUTHENTIK_TOKEN="${AUTHENTIK_BOOTSTRAP_TOKEN:-}"
BLUEPRINT_DIR="config/authentik/blueprints"

# Check if Authentik URL is accessible
if ! curl -k -s "$AUTHENTIK_URL" > /dev/null; then
    echo "❌ Authentik is not accessible at $AUTHENTIK_URL"
    echo "Please ensure Authentik services are running."
    exit 1
fi

# Check if bootstrap token is available
if [ -z "$AUTHENTIK_TOKEN" ]; then
    echo "⚠️  No AUTHENTIK_BOOTSTRAP_TOKEN found in environment"
    echo "Please set AUTHENTIK_BOOTSTRAP_TOKEN or apply blueprints manually via web interface"
    echo "Web interface: $AUTHENTIK_URL/if/admin/"
    exit 1
fi

# Function to apply a single blueprint
apply_blueprint() {
    local blueprint_file="$1"
    local blueprint_name=$(basename "$blueprint_file" .yaml)
    
    echo "📄 Applying blueprint: $blueprint_name"
    
    # Upload blueprint via API
    response=$(curl -k -s -w "%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $AUTHENTIK_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$blueprint_name\",
            \"content\": $(cat "$blueprint_file" | jq -Rs .)
        }" \
        "$AUTHENTIK_URL/api/v3/managed/blueprints/")
    
    http_code="${response: -3}"
    response_body="${response%???}"
    
    if [ "$http_code" -eq 201 ] || [ "$http_code" -eq 200 ]; then
        echo "✅ Successfully applied: $blueprint_name"
    else
        echo "❌ Failed to apply: $blueprint_name (HTTP $http_code)"
        echo "   Response: $response_body"
        return 1
    fi
}

# Function to check if blueprint exists
check_blueprint_exists() {
    local blueprint_name="$1"
    
    response=$(curl -k -s \
        -H "Authorization: Bearer $AUTHENTIK_TOKEN" \
        "$AUTHENTIK_URL/api/v3/managed/blueprints/?name=$blueprint_name")
    
    count=$(echo "$response" | jq -r '.pagination.count // 0')
    [ "$count" -gt 0 ]
}

# Check if jq is available for JSON processing
if ! command -v jq > /dev/null; then
    echo "❌ jq is required for JSON processing but not installed"
    echo "Install with: brew install jq"
    exit 1
fi

# Check if blueprint directory exists
if [ ! -d "$BLUEPRINT_DIR" ]; then
    echo "❌ Blueprint directory not found: $BLUEPRINT_DIR"
    exit 1
fi

# Apply blueprints in correct order
BLUEPRINT_ORDER=(
    "oauth2-flows.yaml"
    "oauth2-scopes.yaml"
    "users.yaml"
    "applications.yaml"
    "access-policies.yaml"
)

echo "🚀 Starting blueprint application process..."

for blueprint in "${BLUEPRINT_ORDER[@]}"; do
    blueprint_file="$BLUEPRINT_DIR/$blueprint"
    blueprint_name=$(basename "$blueprint" .yaml)
    
    if [ ! -f "$blueprint_file" ]; then
        echo "⚠️  Blueprint file not found: $blueprint_file"
        continue
    fi
    
    echo ""
    echo "Processing: $blueprint"
    
    # Check if blueprint already exists
    if check_blueprint_exists "$blueprint_name"; then
        echo "⚠️  Blueprint '$blueprint_name' already exists"
        read -p "Do you want to update it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "⏭️  Skipping $blueprint_name"
            continue
        fi
    fi
    
    # Apply the blueprint
    if apply_blueprint "$blueprint_file"; then
        echo "✅ Successfully processed: $blueprint"
    else
        echo "❌ Failed to process: $blueprint"
        echo "Would you like to continue with remaining blueprints? (y/N): "
        read -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Brief pause between applications
    sleep 2
done

echo ""
echo "🎉 Blueprint application process completed!"
echo ""
echo "Next steps:"
echo "1. Verify applications in Authentik admin: $AUTHENTIK_URL/if/admin/"
echo "2. Test OAuth2 flows with configured applications"
echo "3. Create additional users and assign to appropriate groups"
echo ""
echo "Blueprint locations:"
echo "- Flows: System → Flows"
echo "- Applications: Applications → Applications"
echo "- Providers: Applications → Providers"
echo "- Users & Groups: Directory → Users/Groups"
echo "- Policies: Policies → Policies"
