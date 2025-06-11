#!/bin/bash

# Authentik-Traefik Integration Test Script
# This script provides a complete workflow for testing the Authentik/Traefik integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN=${DOMAIN:-zoi.local}
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.core.yml}
TIMEOUT=${TIMEOUT:-120}

echo -e "${BLUE}🚀 Authentik-Traefik Integration Test Script${NC}"
echo -e "${BLUE}=============================================${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm is not installed"
        exit 1
    fi
    
    print_status "✅ All prerequisites are installed"
}

# Setup hosts file entries
setup_hosts() {
    print_status "Checking hosts file configuration..."
    
    hosts_entries=(
        "127.0.0.1 dashy.${DOMAIN}"
        "127.0.0.1 auth.${DOMAIN}"
        "127.0.0.1 traefik.${DOMAIN}"
        "127.0.0.1 api.${DOMAIN}"
        "127.0.0.1 llm.${DOMAIN}"
        "127.0.0.1 qdrant.${DOMAIN}"
    )
    
    missing_entries=()
    
    for entry in "${hosts_entries[@]}"; do
        if ! grep -q "$entry" /etc/hosts 2>/dev/null; then
            missing_entries+=("$entry")
        fi
    done
    
    if [ ${#missing_entries[@]} -gt 0 ]; then
        print_warning "Missing hosts file entries. You may need to add:"
        for entry in "${missing_entries[@]}"; do
            echo "  $entry"
        done
        print_warning "Add these to /etc/hosts or tests may fail"
    else
        print_status "✅ Hosts file configuration is correct"
    fi
}

# Start Docker services
start_services() {
    print_status "Starting Docker services..."
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "Docker compose file '$COMPOSE_FILE' not found"
        exit 1
    fi
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    print_status "Waiting for services to be healthy..."
    
    # Wait for services to be healthy
    local start_time=$(date +%s)
    local end_time=$((start_time + TIMEOUT))
    
    while [ $(date +%s) -lt $end_time ]; do
        if docker-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "authentik-server"; then
            if docker-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "traefik"; then
                if docker-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "dashy"; then
                    print_status "✅ All services are running"
                    return 0
                fi
            fi
        fi
        
        echo -n "."
        sleep 5
    done
    
    print_error "Services did not start within $TIMEOUT seconds"
    docker-compose -f "$COMPOSE_FILE" ps
    exit 1
}

# Wait for service health
wait_for_health() {
    print_status "Waiting for services to be healthy..."
    
    local services=(
        "http://zoi.local:8080/ping:Traefik"
        "http://zoi.local:9000/if/flow/default-authentication-flow/:Authentik" 
        "http://zoi.local:4001:Dashy"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service"
        print_status "Checking $name health..."
        
        local attempt=0
        local max_attempts=24  # 2 minutes with 5-second intervals
        
        while [ $attempt -lt $max_attempts ]; do
            if curl -s -f "$url" >/dev/null 2>&1; then
                print_status "✅ $name is healthy"
                break
            fi
            
            attempt=$((attempt + 1))
            echo -n "."
            sleep 5
        done
        
        if [ $attempt -eq $max_attempts ]; then
            print_warning "⚠️ $name health check timed out"
        fi
    done
}

# Setup test environment
setup_test_environment() {
    print_status "Setting up test environment..."
    
    # Navigate to e2e-tests directory
    cd e2e-tests
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing test dependencies..."
        npm install
    fi
    
    # Install Playwright browsers if needed
    if [ ! -d "node_modules/@playwright/test" ]; then
        print_status "Installing Playwright..."
        npx playwright install
    fi
    
    # Set environment variables
    export BASE_URL="https://dashy.${DOMAIN}"
    export AUTHENTIK_USER="${AUTHENTIK_USER:-admin}"
    export AUTHENTIK_PASSWORD="${AUTHENTIK_PASSWORD:-admin123!}"
    export DOMAIN="$DOMAIN"
    
    print_status "✅ Test environment ready"
}

# Run environment checks
run_environment_checks() {
    print_status "Running environment checks..."
    
    if node test-setup.js; then
        print_status "✅ Environment checks passed"
    else
        print_warning "⚠️ Environment checks found issues, but continuing with tests"
    fi
}

# Run tests
run_tests() {
    print_status "Running Playwright tests..."
    
    # Create results directory
    mkdir -p test-results
    
    # Run tests with proper environment
    if npm test; then
        print_status "✅ All tests passed!"
        return 0
    else
        print_error "❌ Some tests failed"
        return 1
    fi
}

# Generate test report
generate_report() {
    print_status "Generating test report..."
    
    if [ -f "test-results/results.json" ]; then
        echo
        echo -e "${BLUE}📊 Test Results Summary${NC}"
        echo -e "${BLUE}======================${NC}"
        
        # Extract test results (basic parsing)
        local total=$(grep -o '"tests":\[' test-results/results.json | wc -l)
        local passed=$(grep -o '"status":"passed"' test-results/results.json | wc -l)
        local failed=$(grep -o '"status":"failed"' test-results/results.json | wc -l)
        
        echo "📋 Total Tests: $total"
        echo "✅ Passed: $passed"
        echo "❌ Failed: $failed"
        
        if [ -f "playwright-report/index.html" ]; then
            echo
            echo "📄 Detailed report available at: playwright-report/index.html"
            echo "💡 Run 'npm run show-report' to view the HTML report"
        fi
    fi
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    cd ..
}

# Main execution
main() {
    echo "Starting integration test at $(date)"
    echo
    
    # Run all steps
    check_prerequisites
    setup_hosts
    start_services
    wait_for_health
    setup_test_environment
    run_environment_checks
    
    # Run tests and capture result
    local test_result=0
    if ! run_tests; then
        test_result=1
    fi
    
    generate_report
    cleanup
    
    echo
    if [ $test_result -eq 0 ]; then
        print_status "🎉 Integration test completed successfully!"
        echo -e "${GREEN}All systems are working correctly.${NC}"
    else
        print_error "💥 Integration test failed!"
        echo -e "${RED}Please check the test results and fix any issues.${NC}"
    fi
    
    echo "Test completed at $(date)"
    
    exit $test_result
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Authentik-Traefik Integration Test Script"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --setup-only        Only setup services, don't run tests"
        echo "  --test-only         Only run tests (assume services are running)"
        echo "  --no-cleanup        Don't cleanup after tests"
        echo
        echo "Environment Variables:"
        echo "  DOMAIN              Domain to use (default: zoi.local)"
        echo "  COMPOSE_FILE        Docker compose file (default: docker-compose.core.yml)"
        echo "  TIMEOUT             Service startup timeout in seconds (default: 120)"
        echo "  AUTHENTIK_USER      Authentik admin username (default: admin)"
        echo "  AUTHENTIK_PASSWORD  Authentik admin password (default: admin123!)"
        exit 0
        ;;
    --setup-only)
        check_prerequisites
        setup_hosts
        start_services
        wait_for_health
        print_status "🏗️ Setup completed. Services are ready for testing."
        exit 0
        ;;
    --test-only)
        setup_test_environment
        run_environment_checks
        if run_tests; then
            print_status "🎉 Tests completed successfully!"
            exit 0
        else
            print_error "💥 Tests failed!"
            exit 1
        fi
        ;;
    *)
        main
        ;;
esac 