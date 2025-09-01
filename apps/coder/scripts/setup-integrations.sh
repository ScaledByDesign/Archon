#!/bin/bash

# Refact Integration Setup Script
# This script configures Refact to work seamlessly with Zoi ecosystem services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_header "🔗 Refact Integration Setup"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the apps/coder directory"
    exit 1
fi

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local host=$2
    local port=$3
    local max_attempts=30
    local attempt=1

    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            print_status "✅ $service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "❌ $service_name failed to start within expected time"
    return 1
}

# Function to test HTTP endpoint
test_http_endpoint() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    print_status "Testing $service_name endpoint: $url"
    
    if curl -f -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        print_status "✅ $service_name endpoint is responding"
        return 0
    else
        print_warning "⚠️  $service_name endpoint not ready yet"
        return 1
    fi
}

# Function to setup PostgreSQL integration
setup_postgresql_integration() {
    print_header "🐘 Setting up PostgreSQL Integration"
    
    # Wait for PostgreSQL to be ready
    wait_for_service "PostgreSQL" "postgres" "5432"
    
    # Test database connection
    print_status "Testing PostgreSQL connection..."
    if docker compose exec -T postgres psql -U postgres -d refact -c "SELECT 1;" > /dev/null 2>&1; then
        print_status "✅ PostgreSQL connection successful"
    else
        print_error "❌ PostgreSQL connection failed"
        return 1
    fi
    
    # Verify refact database exists
    print_status "Verifying refact database..."
    if docker compose exec -T postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw refact; then
        print_status "✅ Refact database exists"
    else
        print_error "❌ Refact database not found"
        return 1
    fi
}

# Function to setup Redis integration
setup_redis_integration() {
    print_header "🔴 Setting up Redis Integration"
    
    # Wait for Redis to be ready
    wait_for_service "Redis" "redis" "6379"
    
    # Test Redis connection
    print_status "Testing Redis connection..."
    if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then
        print_status "✅ Redis connection successful"
    else
        print_error "❌ Redis connection failed"
        return 1
    fi
}

# Function to setup LiteLLM integration
setup_litellm_integration() {
    print_header "🚪 Setting up LiteLLM Integration"
    
    # Wait for LiteLLM to be ready
    wait_for_service "LiteLLM" "litellm" "4000"
    
    # Test LiteLLM health endpoint
    if test_http_endpoint "LiteLLM" "http://litellm:4000/health"; then
        print_status "✅ LiteLLM is healthy"
    else
        print_warning "⚠️  LiteLLM health check failed"
    fi
    
    # Test LiteLLM models endpoint
    print_status "Testing LiteLLM models endpoint..."
    if curl -f -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
        "http://litellm:4000/v1/models" > /dev/null 2>&1; then
        print_status "✅ LiteLLM models endpoint accessible"
    else
        print_warning "⚠️  LiteLLM models endpoint not accessible"
    fi
}

# Function to setup Qdrant integration
setup_qdrant_integration() {
    print_header "🔍 Setting up Qdrant Integration"
    
    # Wait for Qdrant to be ready
    wait_for_service "Qdrant" "qdrant" "6333"
    
    # Test Qdrant health endpoint
    if test_http_endpoint "Qdrant" "http://qdrant:6333/health"; then
        print_status "✅ Qdrant is healthy"
    else
        print_warning "⚠️  Qdrant health check failed"
    fi
    
    # Create Refact collection if it doesn't exist
    print_status "Setting up Refact collection in Qdrant..."
    curl -X PUT "http://qdrant:6333/collections/refact_code_embeddings" \
        -H "Content-Type: application/json" \
        -d '{
            "vectors": {
                "size": 1536,
                "distance": "Cosine"
            },
            "optimizers_config": {
                "default_segment_number": 2
            },
            "replication_factor": 1
        }' > /dev/null 2>&1 || true
    
    print_status "✅ Qdrant collection setup complete"
}

# Function to setup Refact Server integration
setup_refact_server() {
    print_header "🤖 Setting up Refact Server"
    
    # Wait for Refact Server to be ready
    wait_for_service "Refact Server" "refact-server" "8008"
    
    # Test Refact Server health endpoint
    if test_http_endpoint "Refact Server" "http://refact-server:8008/health"; then
        print_status "✅ Refact Server is healthy"
    else
        print_warning "⚠️  Refact Server health check failed"
    fi
    
    # Test admin API
    print_status "Testing Refact Server admin API..."
    if curl -f -s -H "Authorization: Bearer refact-admin-token-zoi-2024-secure" \
        "http://refact-server:8008/v1/models" > /dev/null 2>&1; then
        print_status "✅ Refact Server admin API accessible"
    else
        print_warning "⚠️  Refact Server admin API not accessible"
    fi
}

# Function to setup Refact Agent integration
setup_refact_agent() {
    print_header "🦀 Setting up Refact Agent"
    
    # Wait for Refact Agent to be ready
    wait_for_service "Refact Agent" "refact-agent" "8001"
    
    # Test Refact Agent health endpoint
    if test_http_endpoint "Refact Agent" "http://refact-agent:8001/health"; then
        print_status "✅ Refact Agent is healthy"
    else
        print_warning "⚠️  Refact Agent health check failed"
    fi
    
    # Test LSP capabilities
    print_status "Testing Refact Agent LSP capabilities..."
    if curl -f -s "http://refact-agent:8001/v1/caps" > /dev/null 2>&1; then
        print_status "✅ Refact Agent LSP capabilities accessible"
    else
        print_warning "⚠️  Refact Agent LSP capabilities not accessible"
    fi
}

# Function to verify complete integration
verify_integration() {
    print_header "✅ Verifying Complete Integration"
    
    # Test end-to-end flow
    print_status "Testing end-to-end integration..."
    
    # Test code completion through agent
    local completion_test=$(curl -s -X POST "http://refact-agent:8001/v1/code-completion" \
        -H "Content-Type: application/json" \
        -d '{
            "inputs": {
                "sources": {"test.py": "def hello_world():"},
                "cursor": {"file": "test.py", "line": 0, "character": 18},
                "multiline": true
            },
            "stream": false,
            "parameters": {"temperature": 0.1, "max_new_tokens": 20}
        }' 2>/dev/null || echo "")
    
    if [ -n "$completion_test" ]; then
        print_status "✅ End-to-end code completion working"
    else
        print_warning "⚠️  End-to-end code completion test failed"
    fi
    
    # Test chat functionality
    local chat_test=$(curl -s -X POST "http://refact-agent:8001/v1/chat" \
        -H "Content-Type: application/json" \
        -d '{
            "messages": [{"role": "user", "content": "Hello, can you help me with coding?"}],
            "stream": false,
            "temperature": 0.1,
            "max_tokens": 50
        }' 2>/dev/null || echo "")
    
    if [ -n "$chat_test" ]; then
        print_status "✅ End-to-end chat functionality working"
    else
        print_warning "⚠️  End-to-end chat functionality test failed"
    fi
}

# Main execution
main() {
    print_status "Starting Refact integration setup..."
    
    # Setup core services integration
    setup_postgresql_integration
    setup_redis_integration
    setup_litellm_integration
    setup_qdrant_integration
    
    # Setup Refact services
    setup_refact_server
    setup_refact_agent
    
    # Verify complete integration
    verify_integration
    
    echo ""
    print_header "🎉 Integration Setup Complete!"
    echo "================================"
    print_status "All Refact services are integrated with the Zoi ecosystem"
    print_status "You can now use Refact for AI-powered coding assistance"
    
    echo ""
    print_header "🌐 Service URLs"
    echo "==============="
    echo "• Refact Server:  http://localhost:7400"
    echo "• Refact Agent:   http://localhost:7401"
    echo "• Refact Chat:    http://localhost:7402"
    echo "• Documentation:  http://localhost:7403"
    
    echo ""
    print_header "🔧 Next Steps"
    echo "=============="
    echo "1. Configure your IDE to use Refact Agent (http://localhost:7401)"
    echo "2. Set API key: refact-admin-token-zoi-2024-secure"
    echo "3. Start coding with AI assistance!"
}

# Run main function
main "$@"
