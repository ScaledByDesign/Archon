#!/bin/bash

# Automated Secret Rotation Script using curl
# This script handles automatic rotation of dynamic secrets

set -e

VAULT_ADDR=${VAULT_ADDR:-"http://localhost:8200"}
VAULT_TOKEN=${VAULT_ROOT_TOKEN:-"vault-root-token-change-me-in-production"}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to make authenticated Vault API calls
vault_api() {
    local method=$1
    local path=$2
    local data=$3
    
    if [ -n "$data" ]; then
        curl -s -X "$method" \
            -H "X-Vault-Token: $VAULT_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${VAULT_ADDR}/v1/${path}"
    else
        curl -s -X "$method" \
            -H "X-Vault-Token: $VAULT_TOKEN" \
            "${VAULT_ADDR}/v1/${path}"
    fi
}

log_rotation() {
    local service=$1
    local status=$2
    local message=$3
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    local log_data="{\"data\":{\"timestamp\":\"${timestamp}\",\"status\":\"${status}\",\"message\":\"${message}\"}}"
    vault_api POST "secret/data/rotation/logs/${service}" "$log_data"
}

rotate_database_credentials() {
    echo -e "${YELLOW}Rotating database credentials...${NC}"
    
    # Rotate MongoDB credentials
    echo -e "${BLUE}Rotating MongoDB credentials...${NC}"
    local mongodb_episodic_creds=$(vault_api GET "database/creds/mongodb-episodic-role" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$mongodb_episodic_creds" ]; then
        log_rotation "mongodb-episodic" "success" "Credentials rotated successfully"
        echo -e "${GREEN}✓ MongoDB episodic credentials rotated${NC}"
    else
        log_rotation "mongodb-episodic" "failed" "Failed to rotate credentials"
        echo -e "${RED}✗ MongoDB episodic rotation failed${NC}"
    fi
    
    local mongodb_procedural_creds=$(vault_api GET "database/creds/mongodb-procedural-role" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$mongodb_procedural_creds" ]; then
        log_rotation "mongodb-procedural" "success" "Credentials rotated successfully"
        echo -e "${GREEN}✓ MongoDB procedural credentials rotated${NC}"
    else
        log_rotation "mongodb-procedural" "failed" "Failed to rotate credentials"
        echo -e "${RED}✗ MongoDB procedural rotation failed${NC}"
    fi
    
    # Rotate PostgreSQL credentials
    echo -e "${BLUE}Rotating PostgreSQL credentials...${NC}"
    local postgresql_creds=$(vault_api GET "database/creds/postgresql-authentik-role" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$postgresql_creds" ]; then
        log_rotation "postgresql-authentik" "success" "Credentials rotated successfully"
        echo -e "${GREEN}✓ PostgreSQL credentials rotated${NC}"
    else
        log_rotation "postgresql-authentik" "failed" "Failed to rotate credentials"
        echo -e "${RED}✗ PostgreSQL rotation failed${NC}"
    fi
}

check_rotation_status() {
    echo -e "${YELLOW}Checking rotation status...${NC}"
    
    # Update last check timestamp
    local status_data="{\"data\":{\"last_check\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
    vault_api POST "secret/data/rotation/status/last_check" "$status_data"
    
    # Check for recent rotation logs
    echo -e "${BLUE}Recent rotation status:${NC}"
    local logs=$(vault_api GET "secret/metadata/rotation/logs" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$logs" ]; then
        echo "Rotation logs available in Vault"
    else
        echo "No rotation logs found"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}=== Automated Secret Rotation ===${NC}"
    echo -e "${YELLOW}Started at: $(date)${NC}"
    
    check_rotation_status
    rotate_database_credentials
    
    echo -e "${GREEN}=== Rotation Complete ===${NC}"
    echo -e "${YELLOW}Completed at: $(date)${NC}"
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
