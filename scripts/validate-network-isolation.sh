#!/bin/bash

# Network Isolation Validation Script
# This script tests Docker network isolation and cross-network connectivity

set -e

echo "🔍 Docker Network Isolation Validation"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "ℹ️  $message"
            ;;
    esac
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_status "ERROR" "Docker is not running"
    exit 1
fi

print_status "SUCCESS" "Docker is running"

# List all networks
echo ""
echo "📋 Current Docker Networks:"
echo "=========================="
docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"

# Check if our custom networks exist
echo ""
echo "🔍 Checking Custom Networks:"
echo "============================"

networks=("zoi_frontend" "zoi_backend" "zoi_database" "zoi_auth" "zoi_monitoring" "zoi_infrastructure")

for network in "${networks[@]}"; do
    if docker network inspect "$network" >/dev/null 2>&1; then
        print_status "SUCCESS" "Network '$network' exists"
        
        # Get network details
        subnet=$(docker network inspect "$network" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
        print_status "INFO" "  Subnet: $subnet"
        
        # List containers in this network
        containers=$(docker network inspect "$network" --format '{{range $k, $v := .Containers}}{{$v.Name}} {{end}}')
        if [ -n "$containers" ]; then
            print_status "INFO" "  Connected containers: $containers"
        else
            print_status "WARNING" "  No containers connected to $network"
        fi
    else
        print_status "ERROR" "Network '$network' does not exist"
    fi
done

# Function to test connectivity between containers
test_connectivity() {
    local from_container=$1
    local to_container=$2
    local to_port=$3
    local expected_result=$4  # "success" or "fail"
    
    if docker ps --format '{{.Names}}' | grep -q "^${from_container}$" && docker ps --format '{{.Names}}' | grep -q "^${to_container}$"; then
        if docker exec "$from_container" nc -z "$to_container" "$to_port" >/dev/null 2>&1; then
            if [ "$expected_result" = "success" ]; then
                print_status "SUCCESS" "$from_container → $to_container:$to_port (Expected: accessible)"
            else
                print_status "ERROR" "$from_container → $to_container:$to_port (Expected: blocked, but accessible)"
            fi
        else
            if [ "$expected_result" = "fail" ]; then
                print_status "SUCCESS" "$from_container → $to_container:$to_port (Expected: blocked)"
            else
                print_status "ERROR" "$from_container → $to_container:$to_port (Expected: accessible, but blocked)"
            fi
        fi
    else
        print_status "WARNING" "Skipping test: $from_container → $to_container:$to_port (containers not running)"
    fi
}

# Check if containers are running
echo ""
echo "🚀 Container Status:"
echo "==================="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20

echo ""
echo "🔗 Network Connectivity Tests:"
echo "=============================="

# Test expected successful connections
echo ""
echo "Expected Successful Connections:"
echo "-------------------------------"

# FastAPI should reach databases
test_connectivity "zoi-fastapi-1" "zoi-mongo-episodic" "27017" "success"
test_connectivity "zoi-fastapi-1" "zoi-qdrant" "6333" "success"
test_connectivity "zoi-fastapi-1" "zoi-redis" "6379" "success"

# FastAPI should reach Vault
test_connectivity "zoi-fastapi-1" "zoi-vault" "8200" "success"

# Open WebUI should reach FastAPI
test_connectivity "zoi-open-webui" "zoi-fastapi-1" "8000" "success"

# Worker should reach databases
test_connectivity "zoi-worker" "zoi-mongo-episodic" "27017" "success"
test_connectivity "zoi-worker" "zoi-qdrant" "6333" "success"

# Authentik components should communicate
test_connectivity "zoi-authentik-server" "zoi-authentik-db" "5432" "success"
test_connectivity "zoi-authentik-server" "zoi-authentik-redis" "6379" "success"

echo ""
echo "Expected Blocked Connections (Network Isolation):"
echo "------------------------------------------------"

# Frontend should not directly access databases (should go through backend)
test_connectivity "zoi-open-webui" "zoi-mongo-episodic" "27017" "fail"
test_connectivity "zoi-open-webui" "zoi-qdrant" "6333" "fail"

# Monitoring should not access auth databases directly
test_connectivity "zoi-aim" "zoi-authentik-db" "5432" "fail"

echo ""
echo "🔍 Network Inspection Summary:"
echo "============================="

# Show network details for each custom network
for network in "${networks[@]}"; do
    if docker network inspect "$network" >/dev/null 2>&1; then
        echo ""
        echo "Network: $network"
        echo "----------------"
        docker network inspect "$network" --format '{{json .IPAM.Config}}' | jq -r '.[].Subnet // "No subnet configured"'
        
        # Count containers
        container_count=$(docker network inspect "$network" --format '{{len .Containers}}')
        echo "Connected containers: $container_count"
    fi
done

echo ""
echo "📊 Validation Complete!"
echo "======================"

# Summary
total_networks=${#networks[@]}
existing_networks=0

for network in "${networks[@]}"; do
    if docker network inspect "$network" >/dev/null 2>&1; then
        ((existing_networks++))
    fi
done

print_status "INFO" "Custom networks: $existing_networks/$total_networks configured"

if [ $existing_networks -eq $total_networks ]; then
    print_status "SUCCESS" "All custom networks are properly configured"
else
    print_status "WARNING" "Some custom networks are missing"
fi

echo ""
echo "💡 Next Steps:"
echo "============="
echo "1. Run 'docker-compose up -d' to start services with new network configuration"
echo "2. Monitor logs for any connectivity issues"
echo "3. Test application functionality to ensure services can communicate properly"
echo "4. Use 'docker network inspect <network_name>' for detailed network information"
