#!/bin/bash

# Setup automated secret rotation cron jobs
# This script configures cron jobs for regular secret rotation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="/Users/nova/Sites/zoi"
ROTATION_SCRIPT="${PROJECT_ROOT}/scripts/rotate-secrets-curl.sh"
LOG_DIR="${PROJECT_ROOT}/logs/rotation"

echo -e "${BLUE}=== Setting up Automated Secret Rotation ===${NC}"

# Create log directory
create_log_directory() {
    echo -e "${YELLOW}Creating rotation log directory...${NC}"
    mkdir -p "$LOG_DIR"
    echo -e "${GREEN}✓ Log directory created at ${LOG_DIR}${NC}"
}

# Create rotation wrapper script with logging
create_rotation_wrapper() {
    echo -e "${YELLOW}Creating rotation wrapper script...${NC}"
    
    cat > "${PROJECT_ROOT}/scripts/rotate-secrets-with-logging.sh" << EOF
#!/bin/bash

# Wrapper script for secret rotation with comprehensive logging
# This script runs the rotation and captures all output

set -e

PROJECT_ROOT="${PROJECT_ROOT}"
LOG_DIR="${LOG_DIR}"
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
LOG_FILE="\${LOG_DIR}/rotation_\${TIMESTAMP}.log"

# Ensure log directory exists
mkdir -p "\$LOG_DIR"

# Function to log with timestamp
log_with_timestamp() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" | tee -a "\$LOG_FILE"
}

# Main rotation execution
main() {
    log_with_timestamp "Starting automated secret rotation"
    log_with_timestamp "Log file: \$LOG_FILE"
    
    # Change to project directory
    cd "\$PROJECT_ROOT"
    
    # Run rotation script and capture output
    if ./scripts/rotate-secrets-curl.sh >> "\$LOG_FILE" 2>&1; then
        log_with_timestamp "Secret rotation completed successfully"
        exit 0
    else
        log_with_timestamp "Secret rotation failed with exit code \$?"
        exit 1
    fi
}

# Run main function
main "\$@"
EOF
    
    chmod +x "${PROJECT_ROOT}/scripts/rotate-secrets-with-logging.sh"
    echo -e "${GREEN}✓ Rotation wrapper script created${NC}"
}

# Setup cron jobs for different rotation intervals
setup_cron_jobs() {
    echo -e "${YELLOW}Setting up cron jobs for secret rotation...${NC}"
    
    # Create temporary cron file
    local temp_cron="/tmp/vault_rotation_cron"
    
    # Get existing cron jobs (excluding vault rotation ones)
    crontab -l 2>/dev/null | grep -v "vault-rotation" > "$temp_cron" || true
    
    # Add rotation cron jobs with different schedules
    cat >> "$temp_cron" << EOF

# Vault Secret Rotation Jobs
# Daily rotation check (every day at 2:00 AM)
0 2 * * * ${PROJECT_ROOT}/scripts/rotate-secrets-with-logging.sh # vault-rotation-daily

# Weekly rotation verification (every Sunday at 3:00 AM)
0 3 * * 0 ${PROJECT_ROOT}/scripts/rotate-secrets-with-logging.sh # vault-rotation-weekly

# Monthly rotation audit (first day of month at 4:00 AM)
0 4 1 * * ${PROJECT_ROOT}/scripts/rotate-secrets-with-logging.sh # vault-rotation-monthly

EOF
    
    # Install the new cron jobs
    crontab "$temp_cron"
    rm "$temp_cron"
    
    echo -e "${GREEN}✓ Cron jobs installed successfully${NC}"
}

# Create monitoring script for rotation health
create_monitoring_script() {
    echo -e "${YELLOW}Creating rotation monitoring script...${NC}"
    
    cat > "${PROJECT_ROOT}/scripts/monitor-rotation-health.sh" << 'EOF'
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
EOF
    
    chmod +x "${PROJECT_ROOT}/scripts/monitor-rotation-health.sh"
    echo -e "${GREEN}✓ Monitoring script created${NC}"
}

# Create log cleanup script
create_log_cleanup() {
    echo -e "${YELLOW}Creating log cleanup script...${NC}"
    
    cat > "${PROJECT_ROOT}/scripts/cleanup-rotation-logs.sh" << EOF
#!/bin/bash

# Cleanup old rotation logs to prevent disk space issues
# Keeps logs for 30 days by default

LOG_DIR="${LOG_DIR}"
RETENTION_DAYS=\${1:-30}

echo "Cleaning up rotation logs older than \$RETENTION_DAYS days..."

# Remove old log files
find "\$LOG_DIR" -name "rotation_*.log" -mtime +\$RETENTION_DAYS -delete 2>/dev/null || true

echo "Log cleanup completed"
EOF
    
    chmod +x "${PROJECT_ROOT}/scripts/cleanup-rotation-logs.sh"
    echo -e "${GREEN}✓ Log cleanup script created${NC}"
}

# Display current cron jobs
show_cron_jobs() {
    echo -e "${YELLOW}Current cron jobs:${NC}"
    crontab -l | grep -A 10 -B 2 "vault-rotation" || echo "No vault rotation cron jobs found"
}

# Main execution
main() {
    echo -e "${BLUE}Starting automated rotation setup...${NC}"
    
    create_log_directory
    create_rotation_wrapper
    create_monitoring_script
    create_log_cleanup
    setup_cron_jobs
    
    echo -e "${GREEN}=== Automated Secret Rotation Setup Complete ===${NC}"
    echo -e "${YELLOW}Summary:${NC}"
    echo -e "• Daily rotation: Every day at 2:00 AM"
    echo -e "• Weekly verification: Every Sunday at 3:00 AM"
    echo -e "• Monthly audit: First day of month at 4:00 AM"
    echo -e "• Logs stored in: ${LOG_DIR}"
    echo -e "• Monitoring: ./scripts/monitor-rotation-health.sh"
    echo -e "• Log cleanup: ./scripts/cleanup-rotation-logs.sh"
    
    show_cron_jobs
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
