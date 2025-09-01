#!/bin/bash

# Refact Health Check Script
# Monitors the health of all Refact services and their integrations

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

# Function to check service health
check_service_health() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    if curl -f -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null | grep -q "$expected_status"; then
        print_success "$service_name is healthy"
        return 0
    else
        print_fail "$service_name is not responding"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    local db_name=$1
    local host=$2
    local port=$3
    local user=$4
    local password=$5
    
    if PGPASSWORD="$password" psql -h "$host" -p "$port" -U "$user" -d "$db_name" -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "PostgreSQL ($db_name) is accessible"
        return 0
    else
        print_fail "PostgreSQL ($db_name) is not accessible"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    local host=$1
    local port=$2
    
    if redis-cli -h "$host" -p "$port" ping 2>/dev/null | grep -q "PONG"; then
        print_success "Redis is accessible"
        return 0
    else
        print_fail "Redis is not accessible"
        return 1
    fi
}

# Function to get service status
get_service_status() {
    local service_name=$1
    
    if docker compose ps "$service_name" 2>/dev/null | grep -q "Up"; then
        print_success "$service_name container is running"
        return 0
    else
        print_fail "$service_name container is not running"
        return 1
    fi
}

# Function to check resource usage
check_resource_usage() {
    print_header "📊 Resource Usage"
    
    # Check Docker stats
    echo "Container Resource Usage:"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Unable to get container status"
    
    echo ""
    echo "System Resources:"
    echo "Memory Usage: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
    echo "Disk Usage: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
    
    # Check GPU usage if available
    if command -v nvidia-smi &> /dev/null; then
        echo ""
        echo "GPU Usage:"
        nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits 2>/dev/null || echo "GPU information not available"
    fi
}

# Function to check logs for errors
check_logs_for_errors() {
    local service_name=$1
    local lines=${2:-50}
    
    print_status "Checking $service_name logs for errors..."
    
    local error_count=$(docker compose logs --tail="$lines" "$service_name" 2>/dev/null | grep -i "error\|exception\|failed\|fatal" | wc -l)
    
    if [ "$error_count" -eq 0 ]; then
        print_success "$service_name logs show no recent errors"
    else
        print_warning "$service_name logs show $error_count recent errors"
        echo "Recent errors:"
        docker compose logs --tail="$lines" "$service_name" 2>/dev/null | grep -i "error\|exception\|failed\|fatal" | tail -5
    fi
}

# Main health check function
main_health_check() {
    print_header "🏥 Refact Health Check"
    echo "======================"
    echo "Timestamp: $(date)"
    echo ""
    
    local overall_health=0
    
    # Check container status
    print_header "🐳 Container Status"
    get_service_status "refact-server" || overall_health=1
    get_service_status "refact-agent" || overall_health=1
    get_service_status "refact-gui" || overall_health=1
    get_service_status "refact-docs" || overall_health=1
    
    echo ""
    
    # Check service health endpoints
    print_header "🌐 Service Health Endpoints"
    check_service_health "Refact Server" "http://localhost:7400/health" || overall_health=1
    check_service_health "Refact Agent" "http://localhost:7401/health" || overall_health=1
    check_service_health "Refact GUI" "http://localhost:7402/health" || overall_health=1
    check_service_health "Refact Docs" "http://localhost:7403/health" || overall_health=1
    
    echo ""
    
    # Check external dependencies
    print_header "🔗 External Dependencies"
    check_database "refact" "localhost" "7063" "postgres" "litellm_password123" || overall_health=1
    check_redis "localhost" "7064" || overall_health=1
    check_service_health "LiteLLM" "http://localhost:7010/health" || overall_health=1
    check_service_health "Qdrant" "http://localhost:7060/health" || overall_health=1
    
    echo ""
    
    # Check API functionality
    print_header "🔧 API Functionality"
    
    # Test LiteLLM models endpoint
    if curl -f -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
        "http://localhost:7010/v1/models" > /dev/null 2>&1; then
        print_success "LiteLLM models API is accessible"
    else
        print_fail "LiteLLM models API is not accessible"
        overall_health=1
    fi
    
    # Test Refact Agent capabilities
    if curl -f -s "http://localhost:7401/v1/caps" > /dev/null 2>&1; then
        print_success "Refact Agent capabilities API is accessible"
    else
        print_fail "Refact Agent capabilities API is not accessible"
        overall_health=1
    fi
    
    echo ""
    
    # Check logs for errors
    print_header "📋 Recent Logs Check"
    check_logs_for_errors "refact-server"
    check_logs_for_errors "refact-agent"
    check_logs_for_errors "refact-gui"
    
    echo ""
    
    # Resource usage
    check_resource_usage
    
    echo ""
    
    # Overall health summary
    print_header "📋 Health Summary"
    if [ $overall_health -eq 0 ]; then
        print_success "All Refact services are healthy! 🎉"
        echo ""
        echo "🌐 Access URLs:"
        echo "• Refact Server:  http://localhost:7400"
        echo "• Refact Agent:   http://localhost:7401"
        echo "• Refact Chat:    http://localhost:7402"
        echo "• Documentation:  http://localhost:7403"
    else
        print_fail "Some Refact services have issues. Check the details above."
        echo ""
        echo "🔧 Troubleshooting:"
        echo "• Check service logs: docker compose logs <service-name>"
        echo "• Restart services: docker compose restart <service-name>"
        echo "• Full restart: docker compose down && docker compose up -d"
    fi
    
    return $overall_health
}

# Function to run continuous monitoring
continuous_monitoring() {
    local interval=${1:-60}
    
    print_header "🔄 Starting Continuous Monitoring (every ${interval}s)"
    echo "Press Ctrl+C to stop"
    echo ""
    
    while true; do
        main_health_check
        echo ""
        echo "Next check in ${interval} seconds..."
        sleep "$interval"
        clear
    done
}

# Parse command line arguments
case "${1:-}" in
    "continuous"|"-c"|"--continuous")
        continuous_monitoring "${2:-60}"
        ;;
    "help"|"-h"|"--help")
        echo "Refact Health Check Script"
        echo ""
        echo "Usage:"
        echo "  $0                    Run single health check"
        echo "  $0 continuous [N]     Run continuous monitoring every N seconds (default: 60)"
        echo "  $0 help              Show this help message"
        ;;
    *)
        main_health_check
        exit $?
        ;;
esac
