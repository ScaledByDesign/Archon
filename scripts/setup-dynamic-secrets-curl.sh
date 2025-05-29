#!/bin/bash

# Setup Dynamic Secret Generation for Vault using curl
# This script configures database secret engines and rotation policies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VAULT_ADDR=${VAULT_ADDR:-"http://localhost:8200"}
VAULT_TOKEN=${VAULT_ROOT_TOKEN:-"vault-root-token-change-me-in-production"}

echo -e "${BLUE}=== Setting up Dynamic Secret Generation ===${NC}"

# Function to check if Vault is accessible
check_vault() {
    echo -e "${YELLOW}Checking Vault accessibility...${NC}"
    if ! curl -s "${VAULT_ADDR}/v1/sys/health" > /dev/null; then
        echo -e "${RED}Error: Vault is not accessible at ${VAULT_ADDR}${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Vault is accessible${NC}"
}

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

# Function to enable database secret engine
enable_database_engine() {
    echo -e "${YELLOW}Enabling database secret engine...${NC}"
    
    # Check if database engine is already enabled
    local engines=$(vault_api GET "sys/mounts")
    if echo "$engines" | grep -q '"database/"'; then
        echo -e "${GREEN}✓ Database secret engine already enabled${NC}"
    else
        local data='{"type":"database"}'
        vault_api POST "sys/mounts/database" "$data"
        echo -e "${GREEN}✓ Database secret engine enabled${NC}"
    fi
}

# Function to configure MongoDB connection
configure_mongodb() {
    echo -e "${YELLOW}Configuring MongoDB dynamic secrets...${NC}"
    
    # MongoDB episodic connection configuration
    local mongodb_episodic_config='{
        "plugin_name": "mongodb-database-plugin",
        "allowed_roles": ["mongodb-episodic-role"],
        "connection_url": "mongodb://{{username}}:{{password}}@mongo-episodic:27017/admin",
        "username": "root",
        "password": "change-me-mongo-pass"
    }'
    
    vault_api POST "database/config/mongodb-episodic" "$mongodb_episodic_config"
    
    # MongoDB procedural connection configuration
    local mongodb_procedural_config='{
        "plugin_name": "mongodb-database-plugin",
        "allowed_roles": ["mongodb-procedural-role"],
        "connection_url": "mongodb://{{username}}:{{password}}@mongo-procedural:27017/admin",
        "username": "root",
        "password": "change-me-mongo-pass"
    }'
    
    vault_api POST "database/config/mongodb-procedural" "$mongodb_procedural_config"
    
    # Create MongoDB episodic role with rotation
    local mongodb_episodic_role='{
        "db_name": "mongodb-episodic",
        "creation_statements": ["{\"db\":\"admin\",\"roles\":[{\"role\":\"readWrite\",\"db\":\"episodic_memory\"}]}"],
        "default_ttl": "1h",
        "max_ttl": "24h"
    }'
    
    vault_api POST "database/roles/mongodb-episodic-role" "$mongodb_episodic_role"
    
    # Create MongoDB procedural role with rotation
    local mongodb_procedural_role='{
        "db_name": "mongodb-procedural",
        "creation_statements": ["{\"db\":\"admin\",\"roles\":[{\"role\":\"readWrite\",\"db\":\"procedural_memory\"}]}"],
        "default_ttl": "1h",
        "max_ttl": "24h"
    }'
    
    vault_api POST "database/roles/mongodb-procedural-role" "$mongodb_procedural_role"
    
    echo -e "${GREEN}✓ MongoDB dynamic secrets configured${NC}"
}

# Function to configure PostgreSQL connection (for Authentik)
configure_postgresql() {
    echo -e "${YELLOW}Configuring PostgreSQL dynamic secrets...${NC}"
    
    # PostgreSQL connection configuration
    local postgresql_config='{
        "plugin_name": "postgresql-database-plugin",
        "allowed_roles": ["postgresql-authentik-role"],
        "connection_url": "postgresql://{{username}}:{{password}}@authentik-db:5432/authentik?sslmode=disable",
        "username": "authentik",
        "password": "change-me-authentik-db-pass"
    }'
    
    vault_api POST "database/config/postgresql-authentik" "$postgresql_config"
    
    # Create PostgreSQL role with rotation
    local postgresql_role='{
        "db_name": "postgresql-authentik",
        "creation_statements": ["CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '\''{{password}}'\'' VALID UNTIL '\''{{expiration}}'\''; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";"],
        "default_ttl": "2h",
        "max_ttl": "48h"
    }'
    
    vault_api POST "database/roles/postgresql-authentik-role" "$postgresql_role"
    
    echo -e "${GREEN}✓ PostgreSQL dynamic secrets configured${NC}"
}

# Function to setup API key rotation
setup_api_key_rotation() {
    echo -e "${YELLOW}Setting up API key rotation templates...${NC}"
    
    # Check if KV v2 secret engine for API keys exists
    local engines=$(vault_api GET "sys/mounts")
    if ! echo "$engines" | grep -q '"api-keys/"'; then
        local kv_config='{"type":"kv-v2"}'
        vault_api POST "sys/mounts/api-keys" "$kv_config"
    fi
    
    # Create API key rotation policy
    local policy_data='{
        "policy": "path \"api-keys/data/services/*\" {\n  capabilities = [\"create\", \"read\", \"update\", \"delete\"]\n}\n\npath \"api-keys/metadata/services/*\" {\n  capabilities = [\"list\", \"read\", \"delete\"]\n}\n\npath \"api-keys/data/current/*\" {\n  capabilities = [\"read\"]\n}"
    }'
    
    vault_api POST "sys/policies/acl/api-key-rotation" "$policy_data"
    
    echo -e "${GREEN}✓ API key rotation templates configured${NC}"
}

# Function to create rotation schedules
create_rotation_schedules() {
    echo -e "${YELLOW}Creating rotation schedules...${NC}"
    
    # Create rotation configuration
    local rotation_config='{
        "data": {
            "database_credentials": {
                "mongodb": {
                    "rotation_interval": "720h",
                    "max_ttl": "8760h",
                    "auto_rotate": true
                },
                "postgresql": {
                    "rotation_interval": "1440h",
                    "max_ttl": "8760h", 
                    "auto_rotate": true
                }
            },
            "api_keys": {
                "service_keys": {
                    "rotation_interval": "2160h",
                    "max_ttl": "8760h",
                    "auto_rotate": true
                }
            },
            "tokens": {
                "app_tokens": {
                    "rotation_interval": "168h",
                    "max_ttl": "720h",
                    "auto_rotate": true
                }
            }
        }
    }'
    
    # Store rotation configuration in Vault
    vault_api POST "secret/data/config/rotation" "$rotation_config"
    
    echo -e "${GREEN}✓ Rotation schedules created${NC}"
}

# Function to setup monitoring and alerting
setup_monitoring() {
    echo -e "${YELLOW}Setting up rotation monitoring...${NC}"
    
    # Create monitoring policy
    local monitoring_policy='{
        "policy": "path \"secret/data/rotation/status/*\" {\n  capabilities = [\"read\", \"list\"]\n}\n\npath \"secret/data/rotation/logs/*\" {\n  capabilities = [\"create\", \"read\", \"update\"]\n}\n\npath \"sys/audit\" {\n  capabilities = [\"read\", \"list\"]\n}"
    }'
    
    vault_api POST "sys/policies/acl/rotation-monitoring" "$monitoring_policy"
    
    # Initialize rotation status tracking
    local status_data="{\"data\":{\"last_check\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}}"
    vault_api POST "secret/data/rotation/status/last_check" "$status_data"
    
    echo -e "${GREEN}✓ Rotation monitoring configured${NC}"
}

# Function to test dynamic secret generation
test_dynamic_secrets() {
    echo -e "${YELLOW}Testing dynamic secret generation...${NC}"
    
    # Test MongoDB credential generation
    echo -e "${BLUE}Testing MongoDB episodic credentials...${NC}"
    local mongodb_episodic_test=$(vault_api GET "database/creds/mongodb-episodic-role" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$mongodb_episodic_test" ]; then
        echo -e "${GREEN}✓ MongoDB episodic credentials generated successfully${NC}"
    else
        echo -e "${YELLOW}⚠ MongoDB episodic credentials test failed (database may not be ready)${NC}"
    fi
    
    echo -e "${BLUE}Testing MongoDB procedural credentials...${NC}"
    local mongodb_procedural_test=$(vault_api GET "database/creds/mongodb-procedural-role" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$mongodb_procedural_test" ]; then
        echo -e "${GREEN}✓ MongoDB procedural credentials generated successfully${NC}"
    else
        echo -e "${YELLOW}⚠ MongoDB procedural credentials test failed (database may not be ready)${NC}"
    fi
    
    # Test PostgreSQL credential generation
    echo -e "${BLUE}Testing PostgreSQL credentials...${NC}"
    local postgresql_test=$(vault_api GET "database/creds/postgresql-authentik-role" 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$postgresql_test" ]; then
        echo -e "${GREEN}✓ PostgreSQL credentials generated successfully${NC}"
    else
        echo -e "${YELLOW}⚠ PostgreSQL credentials test failed (database may not be ready)${NC}"
    fi
}

# Function to create rotation automation script
create_rotation_script() {
    echo -e "${YELLOW}Creating rotation automation script...${NC}"
    
    cat > /Users/nova/Sites/zoi/scripts/rotate-secrets-curl.sh << 'EOF'
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
EOF
    
    chmod +x /Users/nova/Sites/zoi/scripts/rotate-secrets-curl.sh
    echo -e "${GREEN}✓ Rotation automation script created${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Starting dynamic secret setup...${NC}"
    
    check_vault
    enable_database_engine
    configure_mongodb
    configure_postgresql
    setup_api_key_rotation
    create_rotation_schedules
    setup_monitoring
    create_rotation_script
    test_dynamic_secrets
    
    echo -e "${GREEN}=== Dynamic Secret Generation Setup Complete ===${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "1. Run './scripts/rotate-secrets-curl.sh' to test rotation"
    echo -e "2. Set up cron job for automated rotation"
    echo -e "3. Monitor rotation logs in Vault at secret/rotation/logs/"
    echo -e "4. Configure alerting for failed rotations"
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
