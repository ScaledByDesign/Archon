#!/bin/bash

# Live Testing Script for Production RAG System
# Tests against actual Docker services instead of mocks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.yml"
DOCKER_COMPOSE_TEST_FILE="docker-compose.test.yml"
TEST_TIMEOUT=300  # 5 minutes
SERVICE_WAIT_TIME=30
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USE_CONTAINER_TESTS=${USE_CONTAINER_TESTS:-false}

# Required services for testing
REQUIRED_SERVICES=(
    "authentik-server"
    "authentik-db"
    "authentik-redis"
    "fastapi-1"
    "redis"
    "vault"
    "qdrant"
    "mongo-episodic"
    "mongo-procedural"
    "litellm"
)

echo -e "${BLUE}🧪 Production RAG System - Live Testing Suite${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to check if Docker is running
check_docker() {
    print_status "Checking Docker status..."
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if docker-compose file exists
check_compose_file() {
    print_status "Checking docker-compose configuration..."
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        print_error "docker-compose.yml not found in current directory"
        exit 1
    fi
    
    # Validate compose file
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" config &> /dev/null; then
        print_error "Invalid docker-compose.yml configuration"
        exit 1
    fi
    print_success "Docker Compose configuration is valid"
}

# Function to start required services
start_services() {
    print_status "Starting required services..."
    
    # Start core infrastructure first
    print_status "Starting infrastructure services..."
    docker-compose up -d authentik-db authentik-redis vault redis mongo-episodic mongo-procedural qdrant
    
    # Wait for databases to be ready
    print_status "Waiting for databases to initialize..."
    sleep 15
    
    # Start application services
    print_status "Starting application services..."
    docker-compose up -d authentik-server fastapi-1 litellm
    
    print_success "Services started"
}

# Function to wait for service health
wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=1
    
    print_status "Waiting for $service_name to be healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f --max-time 5 "$url" &> /dev/null; then
            print_success "$service_name is healthy"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_warning "$service_name may not be fully ready (timeout after $max_attempts attempts)"
    return 1
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    # Check individual services
    wait_for_service "FastAPI" "http://localhost:8000/health" 20
    wait_for_service "Authentik" "http://localhost:9443" 30
    wait_for_service "Vault" "http://localhost:8200/v1/sys/health" 15
    wait_for_service "Qdrant" "http://localhost:6333" 15
    wait_for_service "LiteLLM" "http://localhost:4000/health" 20
    
    # Check Redis (different approach)
    print_status "Checking Redis connectivity..."
    if docker-compose exec -T redis redis-cli -a "change-me-redis-pass" ping &> /dev/null; then
        print_success "Redis is healthy"
    else
        print_warning "Redis may not be fully ready"
    fi
    
    # Check MongoDB
    print_status "Checking MongoDB connectivity..."
    if docker-compose exec -T mongo-episodic mongosh --eval "db.runCommand('ping')" &> /dev/null; then
        print_success "MongoDB (episodic) is healthy"
    else
        print_warning "MongoDB (episodic) may not be fully ready"
    fi
    
    print_success "Service health check completed"
}

# Function to setup test environment
setup_test_environment() {
    print_status "Setting up test environment..."
    
    # Export environment variables for live testing
    export LIVE_TESTING=true
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    
    # Ensure test dependencies are available
    if [ -f "requirements.txt" ]; then
        print_status "Installing test dependencies..."
        pip install -r requirements.txt &> /dev/null
        print_success "Dependencies installed"
    fi
    
    print_success "Test environment ready"
}

# Function to run tests in containers
run_containerized_tests() {
    local test_type=$1
    
    print_status "Running tests in Docker container..."
    
    # Build test image if needed
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" -f "$DOCKER_COMPOSE_TEST_FILE" build fastapi-test; then
        print_error "Failed to build test container"
        return 1
    fi
    
    case $test_type in
        "unit")
            print_status "Running unit tests in container..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" -f "$DOCKER_COMPOSE_TEST_FILE" run --rm fastapi-unit-tests
            ;;
        *)
            print_status "Running integration tests in container..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" -f "$DOCKER_COMPOSE_TEST_FILE" run --rm \
                -e LIVE_TESTING=true \
                fastapi-test pytest tests/ -v -m "live and $test_type" --tb=short
            ;;
    esac
}

# Function to run specific test categories
run_test_category() {
    local category=$1
    local description=$2
    
    print_status "Running $description..."
    
    # Check if we should use containerized tests
    if [ "$USE_CONTAINER_TESTS" = "true" ]; then
        run_containerized_tests "$category"
        return $?
    fi
    
    # Set environment for live testing
    export LIVE_TESTING=true
    
    # Run tests with proper markers
    if pytest tests/ -v \
        --tb=short \
        --maxfail=5 \
        --timeout=$TEST_TIMEOUT \
        -m "live and $category" \
        --junit-xml="test-results-live-$category.xml" \
        --cov=src \
        --cov-report=term-missing; then
        print_success "$description completed successfully"
        return 0
    else
        print_error "$description failed"
        return 1
    fi
}

# Function to run all live tests
run_all_tests() {
    print_status "Running complete live test suite..."
    
    local failed_categories=()
    
    # Authentication tests
    if ! run_test_category "auth" "Authentication Tests"; then
        failed_categories+=("auth")
    fi
    
    # Database tests
    if ! run_test_category "database" "Database Integration Tests"; then
        failed_categories+=("database")
    fi
    
    # LLM tests  
    if ! run_test_category "llm" "LLM Integration Tests"; then
        failed_categories+=("llm")
    fi
    
    # General integration tests
    if ! run_test_category "integration" "General Integration Tests"; then
        failed_categories+=("integration")
    fi
    
    # Component tests
    if pytest tests/component/ -v \
        --tb=short \
        --maxfail=5 \
        --timeout=$TEST_TIMEOUT \
        --junit-xml="test-results-live-component.xml" \
        --cov=src \
        --cov-report=term-missing; then
        print_success "Component tests completed successfully"
    else
        failed_categories+=("component")
    fi
    
    # Report results
    if [ ${#failed_categories[@]} -eq 0 ]; then
        print_success "All live tests passed! 🎉"
        return 0
    else
        print_error "Failed test categories: ${failed_categories[*]}"
        return 1
    fi
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    export LIVE_TESTING=true
    
    if pytest tests/ -v \
        --tb=short \
        -m "live and performance" \
        --benchmark-only \
        --benchmark-json=benchmark-results.json; then
        print_success "Performance tests completed"
    else
        print_warning "Performance tests had issues (may be expected)"
    fi
}

# Function to generate test report
generate_report() {
    print_status "Generating test report..."
    
    echo ""
    echo -e "${BLUE}📊 Live Testing Results Summary${NC}"
    echo -e "${BLUE}==============================${NC}"
    
    # Count test result files
    local result_files=(test-results-live-*.xml)
    if [ -f "${result_files[0]}" ]; then
        echo -e "${GREEN}Test result files generated:${NC}"
        for file in test-results-live-*.xml; do
            if [ -f "$file" ]; then
                echo "  - $file"
            fi
        done
    fi
    
    # Show coverage summary if available
    if [ -f ".coverage" ]; then
        echo ""
        echo -e "${GREEN}Coverage Summary:${NC}"
        coverage report --show-missing | tail -n 5
    fi
    
    # Show service status
    echo ""
    echo -e "${GREEN}Service Status:${NC}"
    docker-compose ps --format table
    
    echo ""
    print_success "Test report generated"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up test environment..."
    
    # Remove test data from services
    if docker-compose ps -q redis &> /dev/null; then
        print_status "Cleaning Redis test data..."
        docker-compose exec -T redis redis-cli -a "change-me-redis-pass" FLUSHDB &> /dev/null || true
    fi
    
    # Optional: Stop services (uncomment if desired)
    # print_status "Stopping test services..."
    # docker-compose down
    
    print_success "Cleanup completed"
}

# Main execution
main() {
    local test_type=${1:-"all"}
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Check prerequisites
    check_docker
    check_compose_file
    
    # Start services
    start_services
    
    # Wait for services to be ready
    sleep $SERVICE_WAIT_TIME
    check_service_health
    
    # Setup test environment
    setup_test_environment
    
    # Run tests based on type
    case $test_type in
        "auth")
            run_test_category "auth" "Authentication Tests"
            ;;
        "database")
            run_test_category "database" "Database Tests"
            ;;
        "llm")
            run_test_category "llm" "LLM Tests"
            ;;
        "integration")
            run_test_category "integration" "Integration Tests"
            ;;
        "performance")
            run_performance_tests
            ;;
        "unit")
            run_test_category "unit" "Unit Tests"
            ;;
        "all")
            run_all_tests
            ;;
        *)
            print_error "Unknown test type: $test_type"
            echo "Available types: auth, database, llm, integration, performance, unit, all"
            exit 1
            ;;
    esac
    
    # Generate report
    generate_report
    
    print_success "Live testing completed!"
}

# Show usage if help requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [test_type]"
    echo ""
    echo "Test Types:"
    echo "  auth         - Authentication tests only"
    echo "  database     - Database integration tests"
    echo "  llm          - LLM integration tests"
    echo "  integration  - General integration tests"
    echo "  performance  - Performance benchmarks"
    echo "  unit         - Unit tests only (fast)"
    echo "  all          - All live tests (default)"
    echo ""
    echo "Environment Variables:"
    echo "  LIVE_TESTING=true       - Enable live testing mode"
    echo "  USE_CONTAINER_TESTS=true - Run tests in Docker containers"
    echo ""
    echo "Examples:"
    echo "  $0           # Run all tests"
    echo "  $0 auth      # Run only authentication tests"
    echo "  $0 database  # Run only database tests"
    echo "  USE_CONTAINER_TESTS=true $0 auth  # Run auth tests in container"
    echo ""
    echo "Requirements:"
    echo "  - Docker and docker-compose installed and running"
    echo "  - All required services defined in docker-compose.yml"
    echo "  - Python with pytest and test dependencies installed"
    echo "  - For containerized tests: docker-compose.test.yml"
    exit 0
fi

# Run main function
main "$@"
