#!/bin/bash

# Production RAG System - Docker Test Runner
# This script runs tests inside the FastAPI Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print usage
usage() {
    echo "Usage: $0 [test-type] [options]"
    echo ""
    echo "Test Types:"
    echo "  unit          - Run unit tests only (no dependencies)"
    echo "  integration   - Run integration tests (requires services)"
    echo "  component     - Run component tests (requires external services)"
    echo "  all           - Run all tests (default)"
    echo "  shell         - Open shell in test container"
    echo ""
    echo "Options:"
    echo "  --build       - Force rebuild of Docker images"
    echo "  --verbose     - Verbose output"
    echo "  --coverage    - Run with coverage report"
    echo "  --help        - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 unit --build"
    echo "  $0 integration --verbose"
    echo "  $0 all --coverage"
    echo "  $0 shell"
}

# Default values
TEST_TYPE="all"
BUILD_FLAG=""
VERBOSE_FLAG=""
COVERAGE_FLAG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        unit|integration|component|all|shell)
            TEST_TYPE="$1"
            shift
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --verbose)
            VERBOSE_FLAG="-v"
            shift
            ;;
        --coverage)
            COVERAGE_FLAG="--cov=src --cov-report=html --cov-report=term-missing"
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
        exit 1
    fi
}

# Function to build and run tests
run_tests() {
    local service_name="$1"
    local test_command="$2"
    
    echo -e "${BLUE}🐳 Running $TEST_TYPE tests in Docker container...${NC}"
    echo -e "${YELLOW}Service: $service_name${NC}"
    echo -e "${YELLOW}Command: $test_command${NC}"
    echo ""
    
    # Start required services first
    if [[ "$TEST_TYPE" != "unit" ]]; then
        echo -e "${BLUE}🔧 Starting required services...${NC}"
        docker-compose up -d redis vault qdrant
        
        # Wait for services to be healthy
        echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
        sleep 10
    fi
    
    # Run the test container
    docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm $BUILD_FLAG $service_name $test_command
    
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}✅ Tests completed successfully!${NC}"
    else
        echo -e "${RED}❌ Tests failed with exit code $exit_code${NC}"
    fi
    
    return $exit_code
}

# Main execution
main() {
    check_docker
    
    case $TEST_TYPE in
        unit)
            run_tests "fastapi-unit-tests" "python -m pytest tests/unit/ $VERBOSE_FLAG $COVERAGE_FLAG"
            ;;
        integration)
            run_tests "fastapi-integration-tests" "python -m pytest tests/integration/ $VERBOSE_FLAG $COVERAGE_FLAG -m \"not slow\""
            ;;
        component)
            run_tests "fastapi-component-tests" "python -m pytest tests/component/ $VERBOSE_FLAG $COVERAGE_FLAG"
            ;;
        all)
            echo -e "${BLUE}🧪 Running all test suites...${NC}"
            
            echo -e "${YELLOW}1/3 Running unit tests...${NC}"
            run_tests "fastapi-unit-tests" "python -m pytest tests/unit/ $VERBOSE_FLAG"
            unit_result=$?
            
            echo -e "${YELLOW}2/3 Running integration tests...${NC}"
            run_tests "fastapi-integration-tests" "python -m pytest tests/integration/ $VERBOSE_FLAG -m \"not slow\""
            integration_result=$?
            
            echo -e "${YELLOW}3/3 Running component tests...${NC}"
            run_tests "fastapi-component-tests" "python -m pytest tests/component/ $VERBOSE_FLAG"
            component_result=$?
            
            # Summary
            echo -e "${BLUE}📊 Test Results Summary:${NC}"
            if [[ $unit_result -eq 0 ]]; then
                echo -e "   Unit tests: ${GREEN}✅ PASSED${NC}"
            else
                echo -e "   Unit tests: ${RED}❌ FAILED${NC}"
            fi
            
            if [[ $integration_result -eq 0 ]]; then
                echo -e "   Integration tests: ${GREEN}✅ PASSED${NC}"
            else
                echo -e "   Integration tests: ${RED}❌ FAILED${NC}"
            fi
            
            if [[ $component_result -eq 0 ]]; then
                echo -e "   Component tests: ${GREEN}✅ PASSED${NC}"
            else
                echo -e "   Component tests: ${RED}❌ FAILED${NC}"
            fi
            
            # Overall result
            if [[ $unit_result -eq 0 && $integration_result -eq 0 && $component_result -eq 0 ]]; then
                echo -e "${GREEN}🎉 All tests passed!${NC}"
                exit 0
            else
                echo -e "${RED}💥 Some tests failed!${NC}"
                exit 1
            fi
            ;;
        shell)
            echo -e "${BLUE}🐚 Opening shell in test container...${NC}"
            docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm $BUILD_FLAG fastapi-test bash
            ;;
    esac
}

# Run main function
main
