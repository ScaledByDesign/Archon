#!/bin/bash

# Cleanup old rotation logs to prevent disk space issues
# Keeps logs for 30 days by default

LOG_DIR="/Users/nova/Sites/zoi/logs/rotation"
RETENTION_DAYS=${1:-30}

echo "Cleaning up rotation logs older than $RETENTION_DAYS days..."

# Remove old log files
find "$LOG_DIR" -name "rotation_*.log" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true

echo "Log cleanup completed"
