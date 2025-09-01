#!/bin/bash

# Refact Setup Test Script
# Validates the complete Refact setup and integration

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

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_fail() {
    echo -e "${RED}❌ $1${NC}"
}

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_command=$2
    
    print_status "Testing: $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        print_success "$test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        print_fail "$test_name"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to test HTTP endpoint
test_http() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    run_test "$name HTTP endpoint" "curl -f -s -o /dev/null -w '%{http_code}' '$url' | grep -q '$expected_status'"
}

# Function to test API endpoint with auth
test_api() {
    local name=$1
    local url=$2
    local auth_header=$3
    
    run_test "$name API endpoint" "curl -f -s -H '$auth_header' '$url' > /dev/null"
}

print_header "🧪 Refact Setup Test Suite"
echo "============================"
echo "Testing Refact.ai integration with Zoi ecosystem"
echo ""

# Test 1: Docker Compose Configuration
print_header "📋 Configuration Tests"
run_test "Docker Compose configuration" "docker compose config --quiet"
run_test "Coder stack configuration" "docker compose -f apps/coder/docker-compose.yml config --quiet"

echo ""

# Test 2: Network Configuration
print_header "🌐 Network Tests"
run_test "Zoi network exists" "docker network ls | grep -q zoi-network"

echo ""

# Test 3: Core Services (if running)
print_header "🔧 Core Services Tests"
if docker ps | grep -q postgres; then
    test_http "PostgreSQL health" "http://localhost:7063" "200"
    run_test "PostgreSQL refact database" "docker exec postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw refact"
else
    print_warning "PostgreSQL not running - skipping database tests"
fi

if docker ps | grep -q redis; then
    run_test "Redis connectivity" "docker exec redis redis-cli ping | grep -q PONG"
else
    print_warning "Redis not running - skipping cache tests"
fi

if docker ps | grep -q litellm; then
    test_http "LiteLLM health" "http://localhost:7010/health"
    test_api "LiteLLM models API" "http://localhost:7010/v1/models" "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw"
else
    print_warning "LiteLLM not running - skipping AI gateway tests"
fi

if docker ps | grep -q qdrant; then
    test_http "Qdrant health" "http://localhost:7060/health"
else
    print_warning "Qdrant not running - skipping vector database tests"
fi

echo ""

# Test 4: Refact Services (if running)
print_header "🤖 Refact Services Tests"
if docker ps | grep -q refact-server; then
    test_http "Refact Server health" "http://localhost:7400/health"
    test_api "Refact Server admin API" "http://localhost:7400/v1/models" "Authorization: Bearer refact-admin-token-zoi-2024-secure"
else
    print_warning "Refact Server not running - skipping server tests"
fi

if docker ps | grep -q refact-agent; then
    test_http "Refact Agent health" "http://localhost:7401/health"
    test_http "Refact Agent capabilities" "http://localhost:7401/v1/caps"
else
    print_warning "Refact Agent not running - skipping agent tests"
fi

if docker ps | grep -q refact-gui; then
    test_http "Refact GUI health" "http://localhost:7402/health"
else
    print_warning "Refact GUI not running - skipping GUI tests"
fi

if docker ps | grep -q refact-docs; then
    test_http "Refact Docs health" "http://localhost:7403/health"
else
    print_warning "Refact Docs not running - skipping docs tests"
fi

echo ""

# Test 5: File Structure Tests
print_header "📁 File Structure Tests"
run_test "Docker Compose file exists" "test -f apps/coder/docker-compose.yml"
run_test "Refact Server Dockerfile exists" "test -f apps/coder/refact-server/Dockerfile.postgres"
run_test "Refact Agent Dockerfile exists" "test -f apps/coder/refact-agent/engine/Dockerfile"
run_test "Refact GUI Dockerfile exists" "test -f apps/coder/refact-agent/gui/Dockerfile"
run_test "Configuration file exists" "test -f apps/coder/config/bring-your-own-key.yaml"
run_test "Integration documentation exists" "test -f apps/coder/INTEGRATION.md"
run_test "Setup scripts exist" "test -f apps/coder/start-refact.sh && test -f apps/coder/start-refact.bat"

echo ""

# Test 6: Environment Configuration Tests
print_header "⚙️ Environment Configuration Tests"
run_test "REFACT_SERVER_PORT defined" "grep -q 'REFACT_SERVER_PORT=7400' .env"
run_test "REFACT_AGENT_PORT defined" "grep -q 'REFACT_AGENT_PORT=7401' .env"
run_test "REFACT_GUI_PORT defined" "grep -q 'REFACT_GUI_PORT=7402' .env"
run_test "REFACT_DOCS_PORT defined" "grep -q 'REFACT_DOCS_PORT=7403' .env"
run_test "REFACT_ADMIN_TOKEN defined" "grep -q 'REFACT_ADMIN_TOKEN=' .env"

echo ""

# Test 7: Integration Tests (if services are running)
print_header "🔗 Integration Tests"
if docker ps | grep -q refact-agent && docker ps | grep -q litellm; then
    print_status "Testing code completion integration..."
    COMPLETION_TEST=$(curl -s -X POST "http://localhost:7401/v1/code-completion" \
        -H "Content-Type: application/json" \
        -d '{
            "inputs": {
                "sources": {"test.py": "def hello():"},
                "cursor": {"file": "test.py", "line": 0, "character": 12},
                "multiline": false
            },
            "stream": false,
            "parameters": {"temperature": 0.1, "max_new_tokens": 10}
        }' 2>/dev/null || echo "")
    
    if [ -n "$COMPLETION_TEST" ]; then
        print_success "Code completion integration working"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_fail "Code completion integration failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
else
    print_warning "Refact Agent or LiteLLM not running - skipping integration tests"
fi

echo ""

# Test Results Summary
print_header "📊 Test Results Summary"
echo "========================"
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "🎉 All tests passed! Refact setup is ready."
    echo ""
    echo "🚀 Next Steps:"
    echo "1. Start the services: ./start-refact.sh"
    echo "2. Configure your IDE to use: http://localhost:7401"
    echo "3. Set API key: refact-admin-token-zoi-2024-secure"
    echo "4. Access web interface: http://localhost:7402"
    exit 0
else
    print_error "❌ Some tests failed. Please check the issues above."
    echo ""
    echo "🔧 Troubleshooting:"
    echo "• Check service logs: docker compose logs <service-name>"
    echo "• Verify environment variables in .env file"
    echo "• Ensure all required services are running"
    echo "• Run health check: ./scripts/health-check.sh"
    exit 1
fi
