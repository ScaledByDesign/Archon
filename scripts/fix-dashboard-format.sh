#!/bin/bash
# Fix Grafana Dashboard Format
# Converts dashboards from {dashboard: {...}} format to {...} format

echo "🔧 Fixing Grafana Dashboard Format"
echo "=================================="

# Find all dashboard JSON files
dashboards=$(find config/grafana/dashboards -name "*.json")

for dashboard in $dashboards; do
    echo "📝 Processing: $dashboard"
    
    # Check if file has nested dashboard structure
    if jq -e '.dashboard' "$dashboard" > /dev/null 2>&1; then
        echo "  ✅ Converting nested dashboard format"
        
        # Extract the dashboard content and save to temp file
        jq '.dashboard' "$dashboard" > "${dashboard}.tmp"
        
        # Replace original file with fixed content
        mv "${dashboard}.tmp" "$dashboard"
        
        echo "  ✅ Fixed: $dashboard"
    else
        echo "  ℹ️  Already in correct format: $dashboard"
    fi
done

echo ""
echo "🎯 Dashboard format fix complete!"
echo "Now restart Grafana to reload dashboards:"
echo "  docker restart grafana"
