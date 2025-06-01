#!/bin/bash
set -e

echo "Starting SuperCoder server..."

# Wait for database to be ready
until pg_isready -h "$AI_DEVELOPER_DB_HOST" -p 5432 -U "$AI_DEVELOPER_DB_USER" 2>/dev/null; do
  echo "Waiting for database..."
  sleep 2
done

echo "Database is ready"

# Check if AI_DEVELOPER_GITNESS_TOKEN is set
if [ -z "$AI_DEVELOPER_GITNESS_TOKEN" ]; then
  echo "AI_DEVELOPER_GITNESS_TOKEN is not set, attempting to obtain it..."

  # Wait until Gitness is up
  echo "Waiting for Gitness to be available..."
  while true; do
    curl -s ${AI_DEVELOPER_GITNESS_URL:-http://supercoder-gitness:3000}/ > /dev/null
    if [ $? -eq 0 ]; then
      break
    fi
    echo "Gitness not ready, retrying..."
    sleep 2
  done

  echo "Gitness is up"

  # Generate login data
  data=$(jq -n --arg login_identifier "$AI_DEVELOPER_GITNESS_USER" --arg password "$AI_DEVELOPER_GITNESS_PASSWORD" '{login_identifier: $login_identifier, password: $password}')

  # Attempt to login and get the login token
  response=$(curl -s -X POST \
    ${AI_DEVELOPER_GITNESS_URL:-http://supercoder-gitness:3000}/api/v1/login \
    -H "Content-Type: application/json" \
    -d "$data")

  # Extract access token from the response
  access_token=$(echo "$response" | jq -r '.access_token')
  
  if [ "$access_token" = "null" ] || [ -z "$access_token" ]; then
    echo "Failed to obtain access token from Gitness"
    echo "Response: $response"
    exit 1
  fi

  export AI_DEVELOPER_GITNESS_TOKEN=$access_token
  echo "Access token obtained and exported"
else
  echo "AI_DEVELOPER_GITNESS_TOKEN is already set"
fi

echo "Starting SuperCoder Go server..."

# Start the main application
exec go run server.go
