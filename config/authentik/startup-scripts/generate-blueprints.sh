#!/bin/bash
set -e

echo "🔧 Generating blueprints from templates using DOMAIN=${DOMAIN}..."

# Source environment variables if not already loaded
if [ -z "$DOMAIN" ]; then
    if [ -f "/app/.env" ]; then
        export $(grep -v '^#' /app/.env | xargs)
    elif [ -f "/.env" ]; then
        export $(grep -v '^#' /.env | xargs)
    else
        echo "⚠️  DOMAIN environment variable not set and .env file not found"
        DOMAIN="localhost"
        echo "   Using fallback: DOMAIN=${DOMAIN}"
    fi
fi

# Create blueprints directory if it doesn't exist
mkdir -p /blueprints/custom

# Generate proxy provider blueprint from template
if [ -f "/blueprints/custom/00-proxy-provider.yaml.template" ]; then
    echo "   Generating 00-proxy-provider.yaml from template..."
    sed "s/{{DOMAIN}}/${DOMAIN}/g" /blueprints/custom/00-proxy-provider.yaml.template > /blueprints/custom/00-proxy-provider.yaml
    echo "   ✅ Generated: external_host: https://auth.${DOMAIN}"
else
    echo "   ⚠️  Template not found: 00-proxy-provider.yaml.template"
fi

# List generated blueprints
echo "📋 Generated blueprints:"
ls -la /blueprints/custom/*.yaml 2>/dev/null || echo "   No YAML blueprints found"

echo "✅ Blueprint generation completed!"
