#!/bin/bash
"""
Complete OAuth2 Automation Setup for Authentik
This script automates the entire OAuth2 application creation process.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

echo -e "${BLUE}🚀 OAuth2 Automation Setup for Authentik${NC}"
echo "=" * 50

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}🔍 $1${NC}"
}

# Check if Docker is running
check_docker() {
    print_info "Checking Docker status..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_status "Docker is running"
}

# Check if Authentik is accessible
check_authentik() {
    print_info "Checking Authentik accessibility..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -k -s -o /dev/null -w "%{http_code}" https://localhost:9443 | grep -q "200\|302\|403"; then
            print_status "Authentik is accessible"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "Authentik is not accessible after $max_attempts attempts"
    print_info "Make sure Authentik is running: docker-compose up -d authentik-server"
    exit 1
}

# Check if FastAPI is running
check_fastapi() {
    print_info "Checking FastAPI status..."
    
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
        print_status "FastAPI is running"
    else
        print_warning "FastAPI is not running. Starting FastAPI services..."
        cd "$PROJECT_ROOT"
        docker-compose up -d fastapi-1 fastapi-2 fastapi-3
        
        # Wait for FastAPI to be ready
        local max_attempts=15
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
                print_status "FastAPI is now running"
                break
            fi
            
            echo -n "."
            sleep 2
            ((attempt++))
            
            if [ $attempt -gt $max_attempts ]; then
                print_error "FastAPI failed to start"
                exit 1
            fi
        done
    fi
}

# Install Python dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -q requests urllib3
    
    print_status "Dependencies installed"
}

# Get or create API token
get_api_token() {
    print_info "Checking for existing API token..."
    
    # Source environment file if it exists
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
    fi
    
    if [ -n "$AUTHENTIK_API_TOKEN" ]; then
        print_status "API token found in environment"
        return 0
    fi
    
    print_info "No API token found. Creating new token..."
    print_warning "You will need to provide Authentik admin credentials"
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    if python scripts/get-authentik-token.py; then
        print_status "API token created successfully"
        # Reload environment
        source "$ENV_FILE"
    else
        print_error "Failed to create API token"
        print_info "You can manually create a token at: https://localhost:9443/if/admin/#/core/tokens"
        print_info "Then add it to .env as: AUTHENTIK_API_TOKEN=your_token_here"
        exit 1
    fi
}

# Create OAuth2 application
create_oauth2_app() {
    print_info "Creating OAuth2 application..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    source "$ENV_FILE"
    
    # Set environment variables for the script
    export AUTHENTIK_URL="https://localhost:9443"
    export OAUTH_APP_NAME="FastAPI Client"
    export OAUTH_CLIENT_ID="fastapi-client"
    export OAUTH_REDIRECT_URIS="http://localhost:8000/api/auth/callback"
    export OAUTH_SCOPES="openid,email,profile,rag:api"
    
    if python scripts/auto-create-oauth2-app.py; then
        print_status "OAuth2 application created successfully"
    else
        print_error "Failed to create OAuth2 application"
        exit 1
    fi
}

# Restart FastAPI services
restart_fastapi() {
    print_info "Restarting FastAPI services to apply new configuration..."
    
    cd "$PROJECT_ROOT"
    docker-compose restart fastapi-1 fastapi-2 fastapi-3
    
    # Wait for services to be ready
    local max_attempts=15
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
            print_status "FastAPI services restarted successfully"
            break
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
        
        if [ $attempt -gt $max_attempts ]; then
            print_error "FastAPI services failed to restart"
            exit 1
        fi
    done
}

# Test OAuth2 integration
test_oauth2() {
    print_info "Testing OAuth2 integration..."
    
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    
    if python scripts/test-oauth2-flow.py; then
        print_status "OAuth2 integration test passed"
    else
        print_error "OAuth2 integration test failed"
        exit 1
    fi
}

# Main execution
main() {
    echo
    print_info "Starting OAuth2 automation setup..."
    echo
    
    # Run all setup steps
    check_docker
    check_authentik
    check_fastapi
    install_dependencies
    get_api_token
    create_oauth2_app
    restart_fastapi
    test_oauth2
    
    echo
    echo -e "${GREEN}🎉 OAuth2 automation setup completed successfully!${NC}"
    echo
    echo -e "${BLUE}📋 What was accomplished:${NC}"
    echo "   ✅ Authentik API token created and saved"
    echo "   ✅ OAuth2 application created in Authentik"
    echo "   ✅ Client secret updated in .env file"
    echo "   ✅ FastAPI services restarted with new configuration"
    echo "   ✅ OAuth2 integration tested and verified"
    echo
    echo -e "${BLUE}🎯 Next steps:${NC}"
    echo "   1. Open http://localhost:8000/api/auth/login in your browser"
    echo "   2. Complete the authentication flow"
    echo "   3. Access Authentik admin: https://localhost:9443/if/admin/"
    echo "   4. View your application: https://localhost:9443/if/admin/#/core/applications"
    echo
    echo -e "${BLUE}📖 Documentation:${NC}"
    echo "   - Manual setup guide: docs/manual-oauth2-setup.md"
    echo "   - Test script: scripts/test-oauth2-flow.py"
    echo "   - API automation: scripts/auto-create-oauth2-app.py"
    echo
}

# Run main function
main "$@"
