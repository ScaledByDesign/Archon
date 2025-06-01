#!/bin/bash

echo "🔍 DOCKER REBUILD READINESS VERIFICATION"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Not in project root directory (docker-compose.yml not found)"
    exit 1
fi

echo "✅ Project root directory confirmed"

# Check critical environment variables
echo ""
echo "🔧 CHECKING ENVIRONMENT VARIABLES..."

required_vars=(
    "ENCRYPTION_KEY"
    "AI_DEVELOPER_DB_NAME" 
    "AI_DEVELOPER_DB_HOST"
    "AI_DEVELOPER_DB_PASSWORD"
    "REDIS_PASSWORD"
    "MONGODB_URI"
    "POSTGRES_PASSWORD"
)

missing_vars=()

for var in "${required_vars[@]}"; do
    if grep -q "^${var}=" .env; then
        value=$(grep "^${var}=" .env | cut -d'=' -f2)
        if [ -n "$value" ] && [ "$value" != "your_value_here" ]; then
            echo "✅ $var = $value"
        else
            echo "⚠️  $var is empty or has placeholder value"
            missing_vars+=("$var")
        fi
    else
        echo "❌ $var is missing from .env"
        missing_vars+=("$var")
    fi
done

# Check critical configuration files
echo ""
echo "📁 CHECKING CONFIGURATION FILES..."

config_files=(
    "config/superagi/config.yaml"
    "config/supercoder/startup.sh"
    "config/supercoder/startup-worker.sh"
    "config/postgres/init-multiple-databases.sh"
    "config/mongodb/init-multiple-databases.js"
)

missing_files=()

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
        missing_files+=("$file")
    fi
done

# Check SuperAGI auth.py fix
echo ""
echo "🐍 CHECKING SUPERAGI AUTH FIX..."

if [ -f "superagi/superagi/helper/auth.py" ]; then
    if grep -q "from fastapi import.*Request" "superagi/superagi/helper/auth.py"; then
        echo "✅ SuperAGI auth.py has correct FastAPI imports"
    else
        echo "❌ SuperAGI auth.py missing FastAPI Request import"
        missing_files+=("superagi auth fix")
    fi
else
    echo "❌ SuperAGI auth.py file not found"
    missing_files+=("superagi/superagi/helper/auth.py")
fi

# Check Docker Compose syntax
echo ""
echo "🐳 CHECKING DOCKER COMPOSE SYNTAX..."

if docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml syntax is valid"
else
    echo "❌ docker-compose.yml has syntax errors"
    echo "Run 'docker-compose config' for details"
    exit 1
fi

# Summary
echo ""
echo "📊 VERIFICATION SUMMARY"
echo "======================"

if [ ${#missing_vars[@]} -eq 0 ] && [ ${#missing_files[@]} -eq 0 ]; then
    echo "🎉 ALL CHECKS PASSED - READY FOR CLEAN REBUILD!"
    echo ""
    echo "🚀 Recommended rebuild command:"
    echo "docker-compose down && docker-compose build --no-cache && docker-compose up -d"
    exit 0
else
    echo "⚠️  ISSUES FOUND - PLEASE FIX BEFORE REBUILD:"
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo ""
        echo "Missing/Empty Environment Variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
    fi
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        echo ""
        echo "Missing/Invalid Files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
    fi
    
    echo ""
    echo "📖 See docs/REBUILD_CHECKLIST.md for detailed configuration requirements"
    exit 1
fi
