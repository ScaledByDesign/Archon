#!/bin/bash

# Wrapper script for secret rotation with comprehensive logging
# This script runs the rotation and captures all output

set -e

PROJECT_ROOT="/Users/nova/Sites/zoi"
LOG_DIR="/Users/nova/Sites/zoi/logs/rotation"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/rotation_${TIMESTAMP}.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Main rotation execution
main() {
    log_with_timestamp "Starting automated secret rotation"
    log_with_timestamp "Log file: $LOG_FILE"
    
    # Change to project directory
    cd "$PROJECT_ROOT"
    
    # Run rotation script and capture output
    if ./scripts/rotate-secrets-curl.sh >> "$LOG_FILE" 2>&1; then
        log_with_timestamp "Secret rotation completed successfully"
        exit 0
    else
        log_with_timestamp "Secret rotation failed with exit code $?"
        exit 1
    fi
}

# Run main function
main "$@"
