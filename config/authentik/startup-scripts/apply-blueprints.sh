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
            sleep 5  # Wait longer between applications
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
apply_blueprint "dashy-forward-auth.yaml" "Dashy Forward Auth"

# Apply blueprints in sequence
# apply_blueprint "00-flows.yaml" "Flows"
# apply_blueprint "01-users.yaml" "Users and Groups"
# apply_blueprint "02-provider.yaml" "Proxy Provider and Application"  
# apply_blueprint "03-policies.yaml" "Policies and Bindings"
# apply_blueprint "04-outpost.yaml" "Outpost Binding"

echo "Blueprint auto-application completed."