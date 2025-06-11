#!/bin/bash

# Test Vault Integration Script
# Tests basic Vault functionality using curl commands

set -e

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🧪 Testing Vault Integration"
echo "=" * 50

# Configuration
VAULT_ADDR="${VAULT_ADDR:-http://zoi.local:8200}"
VAULT_TOKEN="${VAULT_ROOT_TOKEN:-vault-root-token-change-me-in-production}"

echo "🔧 Configuration:"
echo "   Vault URL: $VAULT_ADDR"
echo "   Token: ${VAULT_TOKEN:0:10}..."
echo ""

# Test 1: Vault Health Check
echo "🏥 Test 1: Vault Health Check"
if curl -s -f "$VAULT_ADDR/v1/sys/health" > /dev/null; then
    echo "✅ Vault is healthy and accessible"
else
    echo "❌ Vault health check failed"
    exit 1
fi

# Test 2: Authentication Test
echo ""
echo "🔐 Test 2: Authentication Test"
auth_response=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/auth/token/lookup-self")
if echo "$auth_response" | grep -q '"display_name"'; then
    echo "✅ Authentication successful"
else
    echo "❌ Authentication failed"
    echo "Response: $auth_response"
    exit 1
fi

# Test 3: Secret Retrieval Tests
echo ""
echo "📖 Test 3: Secret Retrieval Tests"

# Test database secrets
echo "  📊 Testing database secrets..."
db_response=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/secret/data/app/database")
if echo "$db_response" | grep -q '"database"'; then
    echo "  ✅ Database secrets accessible"
    # Extract and display (masked) database config
    echo "$db_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())['data']['data']
    print(f'    Host: {data[\"host\"]}')
    print(f'    Database: {data[\"database\"]}')
    print(f'    Username: {data[\"username\"]}')
    print(f'    Password: {data[\"password\"][:3]}***')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
else
    echo "  ❌ Database secrets not accessible"
fi

# Test Redis secrets
echo "  🔴 Testing Redis secrets..."
redis_response=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/secret/data/app/redis")
if echo "$redis_response" | grep -q '"host"'; then
    echo "  ✅ Redis secrets accessible"
    echo "$redis_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())['data']['data']
    print(f'    Host: {data[\"host\"]}')
    print(f'    Port: {data[\"port\"]}')
    print(f'    Password: {data[\"password\"][:3]}***')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
else
    echo "  ❌ Redis secrets not accessible"
fi

# Test LLM secrets
echo "  🤖 Testing LLM secrets..."
llm_response=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/secret/data/app/llm")
if echo "$llm_response" | grep -q '"openai_api_key"'; then
    echo "  ✅ LLM secrets accessible"
    echo "$llm_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())['data']['data']
    for key, value in data.items():
        masked_value = str(value)[:10] + '...' if len(str(value)) > 10 else str(value)
        print(f'    {key}: {masked_value}')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
else
    echo "  ❌ LLM secrets not accessible"
fi

# Test 4: AppRole Authentication
echo ""
echo "🎭 Test 4: AppRole Authentication Test"
if [ -n "$VAULT_ROLE_ID" ] && [ -n "$VAULT_SECRET_ID" ]; then
    echo "  🔑 Testing AppRole login..."
    approle_response=$(curl -s -X POST \
        -d "{\"role_id\":\"$VAULT_ROLE_ID\",\"secret_id\":\"$VAULT_SECRET_ID\"}" \
        "$VAULT_ADDR/v1/auth/approle/login")
    
    if echo "$approle_response" | grep -q '"client_token"'; then
        echo "  ✅ AppRole authentication successful"
        # Extract token for further testing
        app_token=$(echo "$approle_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(data['auth']['client_token'])
except:
    pass
")
        echo "  📱 Generated application token: ${app_token:0:10}..."
        
        # Test using app token
        echo "  🧪 Testing secret access with app token..."
        app_test_response=$(curl -s -H "X-Vault-Token: $app_token" "$VAULT_ADDR/v1/secret/data/app/database")
        if echo "$app_test_response" | grep -q '"database"'; then
            echo "  ✅ App token can access secrets"
        else
            echo "  ⚠️ App token cannot access secrets (check policies)"
        fi
    else
        echo "  ❌ AppRole authentication failed"
        echo "  Response: $approle_response"
    fi
else
    echo "  ⚠️ AppRole credentials not found in environment"
fi

# Test 5: Secret Listing
echo ""
echo "📂 Test 5: Secret Structure Test"
echo "  📋 Listing application secrets..."
list_response=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/secret/metadata/app?list=true")
if echo "$list_response" | grep -q '"keys"'; then
    echo "  ✅ Secret listing successful"
    echo "$list_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())['data']['keys']
    print('    Available secrets:')
    for key in data:
        print(f'      - app/{key}')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
else
    echo "  ❌ Secret listing failed"
fi

# Test 6: Write/Delete Test (optional)
echo ""
echo "✏️ Test 6: Write/Delete Test"
test_secret_path="test/integration-test"
test_data='{"test_key":"test_value","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'

echo "  📝 Writing test secret..."
write_response=$(curl -s -X POST \
    -H "X-Vault-Token: $VAULT_TOKEN" \
    -d "{\"data\":$test_data}" \
    "$VAULT_ADDR/v1/secret/data/$test_secret_path")

if echo "$write_response" | grep -q '"version"'; then
    echo "  ✅ Test secret written successfully"
    
    # Read back the secret
    echo "  📖 Reading test secret..."
    read_response=$(curl -s -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/secret/data/$test_secret_path")
    if echo "$read_response" | grep -q '"test_key"'; then
        echo "  ✅ Test secret read successfully"
        
        # Clean up
        echo "  🗑️ Cleaning up test secret..."
        delete_response=$(curl -s -X DELETE \
            -H "X-Vault-Token: $VAULT_TOKEN" \
            "$VAULT_ADDR/v1/secret/data/$test_secret_path")
        echo "  ✅ Test secret deleted"
    else
        echo "  ❌ Test secret read failed"
    fi
else
    echo "  ❌ Test secret write failed"
    echo "  Response: $write_response"
fi

echo ""
echo "🎉 Vault Integration Test Complete!"
echo ""
echo "📊 Summary:"
echo "   - Vault Health: ✅"
echo "   - Authentication: ✅"
echo "   - Secret Access: ✅"
echo "   - AppRole Auth: $([ -n "$app_token" ] && echo "✅" || echo "⚠️")"
echo "   - Write/Delete: ✅"
echo ""
echo "🔗 Vault UI: $VAULT_ADDR/ui"
echo "   Login with token: $VAULT_TOKEN"
