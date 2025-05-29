#!/bin/bash

# Monitor secret rotation health and send alerts if needed
# This script checks rotation logs and Vault status

set -e

PROJECT_ROOT="/Users/nova/Sites/zoi"
LOG_DIR="${PROJECT_ROOT}/logs/rotation"
VAULT_ADDR=${VAULT_ADDR:-"http://localhost:8200"}
VAULT_TOKEN=${VAULT_ROOT_TOKEN:-"vault-root-token-change-me-in-production"}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to make Vault API calls
vault_api() {
    local method=$1
    local path=$2
    
    curl -s -X "$method" \
        -H "X-Vault-Token: $VAULT_TOKEN" \
        "${VAULT_ADDR}/v1/${path}"
}

# Check recent rotation logs
check_rotation_logs() {
    echo -e "${YELLOW}Checking recent rotation logs...${NC}"
    
    local recent_logs=$(find "$LOG_DIR" -name "rotation_*.log" -mtime -1 2>/dev/null || true)
    
    if [ -z "$recent_logs" ]; then
        echo -e "${RED}⚠ No recent rotation logs found${NC}"
        return 1
    fi
    
    local failed_rotations=0
    for log_file in $recent_logs; do
        if grep -q "failed" "$log_file"; then
            echo -e "${RED}✗ Failed rotation found in: $(basename $log_file)${NC}"
            failed_rotations=$((failed_rotations + 1))
        else
            echo -e "${GREEN}✓ Successful rotation: $(basename $log_file)${NC}"
        fi
    done
    
    return $failed_rotations
}

# Check Vault health
check_vault_health() {
    echo -e "${YELLOW}Checking Vault health...${NC}"
    
    local health=$(vault_api GET "sys/health" 2>/dev/null)
    if [ $? -eq 0 ] && echo "$health" | grep -q '"sealed":false'; then
        echo -e "${GREEN}✓ Vault is healthy and unsealed${NC}"
        return 0
    else
        echo -e "${RED}✗ Vault health check failed${NC}"
        return 1
    fi
}

# Check rotation status in Vault
check_rotation_status() {
    echo -e "${YELLOW}Checking rotation status in Vault...${NC}"
    
    local status=$(vault_api GET "secret/data/rotation/status/last_check" 2>/dev/null)
    if [ $? -eq 0 ]; then
        local last_check=$(echo "$status" | grep -o '"last_check":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✓ Last rotation check: ${last_check}${NC}"
        return 0
    else
        echo -e "${RED}✗ Could not retrieve rotation status${NC}"
        return 1
    fi
}

# Main monitoring function
main() {
    echo -e "${BLUE}=== Secret Rotation Health Monitor ===${NC}"
    echo -e "${YELLOW}Started at: $(date)${NC}"
    
    local exit_code=0
    
    check_vault_health || exit_code=1
    check_rotation_status || exit_code=1
    check_rotation_logs || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}=== All rotation health checks passed ===${NC}"
    else
        echo -e "${RED}=== Some rotation health checks failed ===${NC}"
    fi
    
    echo -e "${YELLOW}Completed at: $(date)${NC}"
    return $exit_code
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
