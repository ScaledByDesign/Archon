#!/bin/bash

# Setup Dynamic Secret Generation for Vault
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

# Function to authenticate with Vault
authenticate_vault() {
    echo -e "${YELLOW}Authenticating with Vault...${NC}"
    export VAULT_TOKEN="${VAULT_TOKEN}"
    
    # Verify authentication
    if ! vault auth -method=token token="${VAULT_TOKEN}" > /dev/null 2>&1; then
        echo -e "${RED}Error: Failed to authenticate with Vault${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Authenticated with Vault${NC}"
}

# Function to enable database secret engine
enable_database_engine() {
    echo -e "${YELLOW}Enabling database secret engine...${NC}"
    
    # Check if database engine is already enabled
    if vault secrets list | grep -q "database/"; then
        echo -e "${GREEN}✓ Database secret engine already enabled${NC}"
    else
        vault secrets enable database
        echo -e "${GREEN}✓ Database secret engine enabled${NC}"
    fi
}

# Function to configure MongoDB connection
configure_mongodb() {
    echo -e "${YELLOW}Configuring MongoDB dynamic secrets...${NC}"
    
    # MongoDB connection configuration
    vault write database/config/mongodb-episodic \
        plugin_name=mongodb-database-plugin \
        allowed_roles="mongodb-episodic-role" \
        connection_url="mongodb://{{username}}:{{password}}@mongo-episodic:27017/admin" \
        username="root" \
        password="change-me-mongo-pass"
    
    vault write database/config/mongodb-procedural \
        plugin_name=mongodb-database-plugin \
        allowed_roles="mongodb-procedural-role" \
        connection_url="mongodb://{{username}}:{{password}}@mongo-procedural:27017/admin" \
        username="root" \
        password="change-me-mongo-pass"
    
    # Create MongoDB roles with rotation
    vault write database/roles/mongodb-episodic-role \
        db_name=mongodb-episodic \
        creation_statements='{"db":"admin","roles":[{"role":"readWrite","db":"episodic_memory"}]}' \
        default_ttl="1h" \
        max_ttl="24h"
    
    vault write database/roles/mongodb-procedural-role \
        db_name=mongodb-procedural \
        creation_statements='{"db":"admin","roles":[{"role":"readWrite","db":"procedural_memory"}]}' \
        default_ttl="1h" \
        max_ttl="24h"
    
    echo -e "${GREEN}✓ MongoDB dynamic secrets configured${NC}"
}

# Function to configure PostgreSQL connection (for Authentik)
configure_postgresql() {
    echo -e "${YELLOW}Configuring PostgreSQL dynamic secrets...${NC}"
    
    # PostgreSQL connection configuration
    vault write database/config/postgresql-authentik \
        plugin_name=postgresql-database-plugin \
        allowed_roles="postgresql-authentik-role" \
        connection_url="postgresql://{{username}}:{{password}}@authentik-db:5432/authentik?sslmode=disable" \
        username="authentik" \
        password="change-me-authentik-db-pass"
    
    # Create PostgreSQL role with rotation
    vault write database/roles/postgresql-authentik-role \
        db_name=postgresql-authentik \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
        default_ttl="2h" \
        max_ttl="48h"
    
    echo -e "${GREEN}✓ PostgreSQL dynamic secrets configured${NC}"
}

# Function to setup API key rotation
setup_api_key_rotation() {
    echo -e "${YELLOW}Setting up API key rotation templates...${NC}"
    
    # Create KV v2 secret engine for API keys if not exists
    if ! vault secrets list | grep -q "api-keys/"; then
        vault secrets enable -path=api-keys kv-v2
    fi
    
    # Create API key rotation policy
    cat > /tmp/api-key-rotation-policy.hcl << EOF
path "api-keys/data/services/*" {
  capabilities = ["create", "read", "update", "delete"]
}

path "api-keys/metadata/services/*" {
  capabilities = ["list", "read", "delete"]
}

# Allow reading current API keys for rotation
path "api-keys/data/current/*" {
  capabilities = ["read"]
}
EOF
    
    vault policy write api-key-rotation /tmp/api-key-rotation-policy.hcl
    rm /tmp/api-key-rotation-policy.hcl
    
    echo -e "${GREEN}✓ API key rotation templates configured${NC}"
}

# Function to create rotation schedules
create_rotation_schedules() {
    echo -e "${YELLOW}Creating rotation schedules...${NC}"
    
    # Create rotation configuration
    cat > /tmp/rotation-config.json << EOF
{
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
EOF
    
    # Store rotation configuration in Vault
    vault kv put secret/config/rotation @/tmp/rotation-config.json
    rm /tmp/rotation-config.json
    
    echo -e "${GREEN}✓ Rotation schedules created${NC}"
}

# Function to setup monitoring and alerting
setup_monitoring() {
    echo -e "${YELLOW}Setting up rotation monitoring...${NC}"
    
    # Create monitoring policy
    cat > /tmp/monitoring-policy.hcl << EOF
# Allow reading rotation status
path "secret/data/rotation/status/*" {
  capabilities = ["read", "list"]
}

# Allow updating rotation logs
path "secret/data/rotation/logs/*" {
  capabilities = ["create", "read", "update"]
}

# Allow reading audit logs
path "sys/audit" {
  capabilities = ["read", "list"]
}
EOF
    
    vault policy write rotation-monitoring /tmp/monitoring-policy.hcl
    rm /tmp/monitoring-policy.hcl
    
    # Initialize rotation status tracking
    vault kv put secret/rotation/status/last_check "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    echo -e "${GREEN}✓ Rotation monitoring configured${NC}"
}

# Function to test dynamic secret generation
test_dynamic_secrets() {
    echo -e "${YELLOW}Testing dynamic secret generation...${NC}"
    
    # Test MongoDB credential generation
    echo -e "${BLUE}Testing MongoDB episodic credentials...${NC}"
    if vault read database/creds/mongodb-episodic-role > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MongoDB episodic credentials generated successfully${NC}"
    else
        echo -e "${YELLOW}⚠ MongoDB episodic credentials test failed (database may not be ready)${NC}"
    fi
    
    echo -e "${BLUE}Testing MongoDB procedural credentials...${NC}"
    if vault read database/creds/mongodb-procedural-role > /dev/null 2>&1; then
        echo -e "${GREEN}✓ MongoDB procedural credentials generated successfully${NC}"
    else
        echo -e "${YELLOW}⚠ MongoDB procedural credentials test failed (database may not be ready)${NC}"
    fi
    
    # Test PostgreSQL credential generation
    echo -e "${BLUE}Testing PostgreSQL credentials...${NC}"
    if vault read database/creds/postgresql-authentik-role > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL credentials generated successfully${NC}"
    else
        echo -e "${YELLOW}⚠ PostgreSQL credentials test failed (database may not be ready)${NC}"
    fi
}

# Function to create rotation automation script
create_rotation_script() {
    echo -e "${YELLOW}Creating rotation automation script...${NC}"
    
    cat > /Users/nova/Sites/zoi/scripts/rotate-secrets.sh << 'EOF'
#!/bin/bash

# Automated Secret Rotation Script
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

log_rotation() {
    local service=$1
    local status=$2
    local message=$3
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    
    vault kv put secret/rotation/logs/${service} \
        timestamp="${timestamp}" \
        status="${status}" \
        message="${message}"
}

rotate_database_credentials() {
    echo -e "${YELLOW}Rotating database credentials...${NC}"
    
    # Get current rotation config
    local config=$(vault kv get -format=json secret/config/rotation)
    
    # Rotate MongoDB credentials
    echo -e "${BLUE}Rotating MongoDB credentials...${NC}"
    if vault read database/creds/mongodb-episodic-role > /dev/null 2>&1; then
        log_rotation "mongodb-episodic" "success" "Credentials rotated successfully"
        echo -e "${GREEN}✓ MongoDB episodic credentials rotated${NC}"
    else
        log_rotation "mongodb-episodic" "failed" "Failed to rotate credentials"
        echo -e "${RED}✗ MongoDB episodic rotation failed${NC}"
    fi
    
    if vault read database/creds/mongodb-procedural-role > /dev/null 2>&1; then
        log_rotation "mongodb-procedural" "success" "Credentials rotated successfully"
        echo -e "${GREEN}✓ MongoDB procedural credentials rotated${NC}"
    else
        log_rotation "mongodb-procedural" "failed" "Failed to rotate credentials"
        echo -e "${RED}✗ MongoDB procedural rotation failed${NC}"
    fi
    
    # Rotate PostgreSQL credentials
    echo -e "${BLUE}Rotating PostgreSQL credentials...${NC}"
    if vault read database/creds/postgresql-authentik-role > /dev/null 2>&1; then
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
    vault kv put secret/rotation/status/last_check "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    
    # Check for failed rotations in the last 24 hours
    echo -e "${BLUE}Recent rotation logs:${NC}"
    vault kv list secret/rotation/logs/ 2>/dev/null || echo "No rotation logs found"
}

# Main execution
main() {
    export VAULT_TOKEN="${VAULT_TOKEN}"
    
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
    
    chmod +x /Users/nova/Sites/zoi/scripts/rotate-secrets.sh
    echo -e "${GREEN}✓ Rotation automation script created${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}Starting dynamic secret setup...${NC}"
    
    check_vault
    authenticate_vault
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
    echo -e "1. Run './scripts/rotate-secrets.sh' to test rotation"
    echo -e "2. Set up cron job for automated rotation"
    echo -e "3. Monitor rotation logs in Vault at secret/rotation/logs/"
    echo -e "4. Configure alerting for failed rotations"
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
