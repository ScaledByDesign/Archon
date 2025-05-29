#!/bin/bash

# Auto-scaling script for FastAPI instances
# This script monitors CPU and memory usage and scales instances accordingly

set -euo pipefail

# Configuration
MIN_INSTANCES=3
MAX_INSTANCES=10
CPU_THRESHOLD_UP=80
CPU_THRESHOLD_DOWN=30
MEMORY_THRESHOLD_UP=80
MEMORY_THRESHOLD_DOWN=30
SCALE_UP_COOLDOWN=300  # 5 minutes
SCALE_DOWN_COOLDOWN=600  # 10 minutes
METRICS_WINDOW=60  # 1 minute

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if docker-compose is available
check_dependencies() {
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        error "docker is not installed or not in PATH"
        exit 1
    fi
}

# Get current number of running FastAPI instances
get_current_instances() {
    docker-compose ps --services --filter "status=running" | grep -E "fastapi-[0-9]+" | wc -l
}

# Get average CPU usage for FastAPI instances
get_avg_cpu_usage() {
    local total_cpu=0
    local count=0
    
    for service in $(docker-compose ps --services --filter "status=running" | grep -E "fastapi-[0-9]+"); do
        local container_id=$(docker-compose ps -q "$service")
        if [ -n "$container_id" ]; then
            local cpu_usage=$(docker stats --no-stream --format "{{.CPUPerc}}" "$container_id" | sed 's/%//')
            total_cpu=$(echo "$total_cpu + $cpu_usage" | bc -l)
            count=$((count + 1))
        fi
    done
    
    if [ "$count" -gt 0 ]; then
        echo "scale=2; $total_cpu / $count" | bc -l
    else
        echo "0"
    fi
}

# Get average memory usage for FastAPI instances
get_avg_memory_usage() {
    local total_memory=0
    local count=0
    
    for service in $(docker-compose ps --services --filter "status=running" | grep -E "fastapi-[0-9]+"); do
        local container_id=$(docker-compose ps -q "$service")
        if [ -n "$container_id" ]; then
            local memory_usage=$(docker stats --no-stream --format "{{.MemPerc}}" "$container_id" | sed 's/%//')
            total_memory=$(echo "$total_memory + $memory_usage" | bc -l)
            count=$((count + 1))
        fi
    done
    
    if [ "$count" -gt 0 ]; then
        echo "scale=2; $total_memory / $count" | bc -l
    else
        echo "0"
    fi
}

# Check if enough time has passed since last scaling operation
check_cooldown() {
    local operation=$1
    local cooldown_file="/tmp/fastapi_scale_${operation}_last"
    local cooldown_period
    
    if [ "$operation" = "up" ]; then
        cooldown_period=$SCALE_UP_COOLDOWN
    else
        cooldown_period=$SCALE_DOWN_COOLDOWN
    fi
    
    if [ -f "$cooldown_file" ]; then
        local last_scale=$(cat "$cooldown_file")
        local current_time=$(date +%s)
        local time_diff=$((current_time - last_scale))
        
        if [ "$time_diff" -lt "$cooldown_period" ]; then
            local remaining=$((cooldown_period - time_diff))
            warning "Cooldown period active. $remaining seconds remaining for $operation scaling."
            return 1
        fi
    fi
    
    return 0
}

# Record scaling operation timestamp
record_scaling() {
    local operation=$1
    local cooldown_file="/tmp/fastapi_scale_${operation}_last"
    date +%s > "$cooldown_file"
}

# Scale up FastAPI instances
scale_up() {
    local current_instances=$1
    local new_instances=$((current_instances + 1))
    
    if [ "$new_instances" -gt "$MAX_INSTANCES" ]; then
        warning "Cannot scale up. Maximum instances ($MAX_INSTANCES) reached."
        return 1
    fi
    
    if ! check_cooldown "up"; then
        return 1
    fi
    
    log "Scaling up from $current_instances to $new_instances instances"
    
    # Create new FastAPI service configuration
    local new_service="fastapi-$new_instances"
    
    # Scale using docker-compose
    if docker-compose up -d --scale "fastapi-1=$new_instances"; then
        success "Successfully scaled up to $new_instances instances"
        record_scaling "up"
        
        # Wait for new instance to be healthy
        sleep 30
        check_instance_health "$new_service"
    else
        error "Failed to scale up instances"
        return 1
    fi
}

# Scale down FastAPI instances
scale_down() {
    local current_instances=$1
    local new_instances=$((current_instances - 1))
    
    if [ "$new_instances" -lt "$MIN_INSTANCES" ]; then
        warning "Cannot scale down. Minimum instances ($MIN_INSTANCES) required."
        return 1
    fi
    
    if ! check_cooldown "down"; then
        return 1
    fi
    
    log "Scaling down from $current_instances to $new_instances instances"
    
    # Scale using docker-compose
    if docker-compose up -d --scale "fastapi-1=$new_instances"; then
        success "Successfully scaled down to $new_instances instances"
        record_scaling "down"
    else
        error "Failed to scale down instances"
        return 1
    fi
}

# Check health of a specific instance
check_instance_health() {
    local service=$1
    local container_id=$(docker-compose ps -q "$service")
    
    if [ -n "$container_id" ]; then
        local health_check=$(docker exec "$container_id" curl -f -s http://localhost:8000/health || echo "unhealthy")
        if [[ "$health_check" == *"healthy"* ]]; then
            success "Instance $service is healthy"
            return 0
        else
            error "Instance $service is unhealthy"
            return 1
        fi
    else
        error "Instance $service not found"
        return 1
    fi
}

# Main monitoring loop
monitor_and_scale() {
    log "Starting auto-scaling monitor..."
    log "Configuration:"
    log "  Min instances: $MIN_INSTANCES"
    log "  Max instances: $MAX_INSTANCES"
    log "  CPU thresholds: ${CPU_THRESHOLD_DOWN}% - ${CPU_THRESHOLD_UP}%"
    log "  Memory thresholds: ${MEMORY_THRESHOLD_DOWN}% - ${MEMORY_THRESHOLD_UP}%"
    log "  Scale up cooldown: ${SCALE_UP_COOLDOWN}s"
    log "  Scale down cooldown: ${SCALE_DOWN_COOLDOWN}s"
    
    while true; do
        local current_instances=$(get_current_instances)
        local avg_cpu=$(get_avg_cpu_usage)
        local avg_memory=$(get_avg_memory_usage)
        
        log "Current metrics: Instances=$current_instances, CPU=${avg_cpu}%, Memory=${avg_memory}%"
        
        # Check if scaling up is needed
        if (( $(echo "$avg_cpu > $CPU_THRESHOLD_UP" | bc -l) )) || (( $(echo "$avg_memory > $MEMORY_THRESHOLD_UP" | bc -l) )); then
            warning "High resource usage detected. CPU: ${avg_cpu}%, Memory: ${avg_memory}%"
            scale_up "$current_instances"
        # Check if scaling down is possible
        elif (( $(echo "$avg_cpu < $CPU_THRESHOLD_DOWN" | bc -l) )) && (( $(echo "$avg_memory < $MEMORY_THRESHOLD_DOWN" | bc -l) )); then
            log "Low resource usage detected. CPU: ${avg_cpu}%, Memory: ${avg_memory}%"
            scale_down "$current_instances"
        else
            log "Resource usage within normal range"
        fi
        
        sleep "$METRICS_WINDOW"
    done
}

# Handle script termination
cleanup() {
    log "Shutting down auto-scaling monitor..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_dependencies
    
    case "${1:-monitor}" in
        "monitor")
            monitor_and_scale
            ;;
        "scale-up")
            local current_instances=$(get_current_instances)
            scale_up "$current_instances"
            ;;
        "scale-down")
            local current_instances=$(get_current_instances)
            scale_down "$current_instances"
            ;;
        "status")
            local current_instances=$(get_current_instances)
            local avg_cpu=$(get_avg_cpu_usage)
            local avg_memory=$(get_avg_memory_usage)
            
            echo "FastAPI Auto-scaling Status:"
            echo "  Current instances: $current_instances"
            echo "  Average CPU usage: ${avg_cpu}%"
            echo "  Average memory usage: ${avg_memory}%"
            echo "  Min instances: $MIN_INSTANCES"
            echo "  Max instances: $MAX_INSTANCES"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  monitor     Start continuous monitoring and auto-scaling (default)"
            echo "  scale-up    Manually scale up by one instance"
            echo "  scale-down  Manually scale down by one instance"
            echo "  status      Show current scaling status"
            echo "  help        Show this help message"
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"
