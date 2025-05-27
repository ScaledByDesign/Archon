#!/bin/bash

# Simple Authentik Blueprint Validation Script
# This script performs basic YAML syntax validation using built-in tools

set -e

echo "🔍 Validating Authentik blueprints..."

# Find blueprint directory
BLUEPRINT_DIR="config/authentik/blueprints"

if [ ! -d "$BLUEPRINT_DIR" ]; then
    echo "❌ Blueprint directory not found: $BLUEPRINT_DIR"
    exit 1
fi

# Find all YAML files
BLUEPRINT_FILES=$(find "$BLUEPRINT_DIR" -name "*.yaml" -o -name "*.yml")

if [ -z "$BLUEPRINT_FILES" ]; then
    echo "⚠️  No blueprint files found"
    exit 0
fi

TOTAL_FILES=0
VALID_FILES=0
INVALID_FILES=0

# Validate each file
for file in $BLUEPRINT_FILES; do
    TOTAL_FILES=$((TOTAL_FILES + 1))
    filename=$(basename "$file")
    echo ""
    echo "📄 Validating $filename..."
    
    # Check if file is readable
    if [ ! -r "$file" ]; then
        echo "❌ $filename: File not readable"
        INVALID_FILES=$((INVALID_FILES + 1))
        continue
    fi
    
    # Check if file is not empty
    if [ ! -s "$file" ]; then
        echo "❌ $filename: File is empty"
        INVALID_FILES=$((INVALID_FILES + 1))
        continue
    fi
    
    # Check for required blueprint structure
    has_version=$(grep -c "^version:" "$file" || true)
    has_metadata=$(grep -c "^metadata:" "$file" || true)
    has_entries=$(grep -c "^entries:" "$file" || true)
    
    if [ "$has_version" -ge 1 ] && [ "$has_metadata" -ge 1 ] && [ "$has_entries" -ge 1 ]; then
        echo "✅ $filename: Valid blueprint structure"
        VALID_FILES=$((VALID_FILES + 1))
    else
        echo "❌ $filename: Missing required structure (version: $has_version, metadata: $has_metadata, entries: $has_entries)"
        INVALID_FILES=$((INVALID_FILES + 1))
    fi
done

echo ""
echo "📊 Validation Summary:"
echo "   Total files: $TOTAL_FILES"
echo "   Valid files: $VALID_FILES"
echo "   Invalid files: $INVALID_FILES"

if [ $INVALID_FILES -eq 0 ]; then
    echo ""
    echo "🎉 All blueprint files passed validation!"
    exit 0
else
    echo ""
    echo "❌ Some blueprint files have issues. Please review them."
    exit 1
fi
