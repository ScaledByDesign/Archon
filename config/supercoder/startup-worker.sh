#!/bin/bash
set -e

echo "Starting SuperCoder worker..."

# Wait for database to be ready
until pg_isready -h "$AI_DEVELOPER_DB_HOST" -p 5432 -U "$AI_DEVELOPER_DB_USER" 2>/dev/null; do
  echo "Waiting for database..."
  sleep 2
done

echo "Database is ready, starting worker..."

# Start the worker
exec go run worker.go
