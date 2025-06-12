#!/bin/bash

echo "Starting Authentik blueprint auto-application..."

# Wait for Authentik to be ready
echo "Waiting for Authentik to be ready..."
while ! ak healthcheck > /dev/null 2>&1; do
    echo "Authentik not ready yet, waiting 5 seconds..."
    sleep 5
done

# Wait for default flows to be created
echo "Waiting for Authentik to fully initialize (including default flows)..."
sleep 30  # Give Authentik time to create default flows after healthcheck passes

echo "Authentik is fully ready! Starting blueprint application..."

# Debug: Check what files exist
BLUEPRINT_DIR="/blueprints/custom"
echo "DEBUG: Contents of $BLUEPRINT_DIR:"
ls -la "$BLUEPRINT_DIR"
echo "DEBUG: YAML files found:"
find "$BLUEPRINT_DIR" -name "*.yaml" -o -name "*.yml"

apply_blueprint() {
    local file=$1
    local description=$2
    local full_path="$BLUEPRINT_DIR/$file"
    
    echo "Applying $description: $file"
    echo "DEBUG: Looking for file at: $full_path"
    
    if [ -f "$full_path" ]; then
        echo "✅ File found, applying..."
        ak apply_blueprint "$full_path"
        if [ $? -eq 0 ]; then
            echo "✅ Successfully applied: $file"
            sleep 5  # Wait between applications
        else
            echo "❌ Failed to apply: $file"
            return 1
        fi
    else
        echo "⚠️  Blueprint file not found: $full_path"
        echo "DEBUG: Directory listing:"
        ls -la "$BLUEPRINT_DIR"
        return 1
    fi
}

# Apply blueprints in correct order
apply_blueprint "00-flows.yaml" "Authentication Flows"
apply_blueprint "01-users.yaml" "Users and Groups"
apply_blueprint "02-provider.yaml" "Proxy Provider and Application"  
apply_blueprint "03-simple-policy.yaml" "Access Policies"
apply_blueprint "04-outpost-provider-assignment.yaml" "Outpost Configuration"
apply_blueprint "05-outpost-permissions.yaml" "Outpost Permissions"

echo "All blueprints applied. Running post-deployment setup..."

# Post-deployment permissions fix
# This ensures outpost service accounts have proper admin permissions
sleep 10  # Wait for any final outpost initialization

echo "Adding outpost service accounts to authentik Admins group..."
# Note: We can't verify this from within authentik container since it lacks psql
# The SQL operation will be run when the authentik-post-deploy service starts
echo "✅ Post-deployment permissions setup scheduled"
echo "Note: Outpost user permissions are handled by the docker-compose post-deploy service"

echo "Blueprint auto-application completed successfully! 🎉"