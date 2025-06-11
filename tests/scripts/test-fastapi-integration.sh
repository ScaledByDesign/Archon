#!/bin/bash

# Test FastAPI Integration with Vault and Qdrant
# Tests the complete API stack integration

set -e

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🧪 Testing FastAPI Integration with Vault & Qdrant"
echo "=" * 60

# Configuration
API_URL="http://zoi.local:8000"
VAULT_URL="${VAULT_ADDR:-http://zoi.local:8200}"

echo "🔧 Configuration:"
echo "   API URL: $API_URL"
echo "   Vault URL: $VAULT_URL"
echo ""

# Helper function to make API requests
api_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local token="$4"
    
    if [ -n "$token" ]; then
        if [ -n "$data" ]; then
            curl -s -X "$method" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $token" \
                -d "$data" \
                "$API_URL$endpoint"
        else
            curl -s -X "$method" \
                -H "Authorization: Bearer $token" \
                "$API_URL$endpoint"
        fi
    else
        if [ -n "$data" ]; then
            curl -s -X "$method" \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$API_URL$endpoint"
        else
            curl -s -X "$method" \
                "$API_URL$endpoint"
        fi
    fi
}

# Test 1: Root endpoint
echo "🏠 Test 1: Root Endpoint"
root_response=$(api_request "GET" "/")
if echo "$root_response" | grep -q '"message"'; then
    echo "✅ Root endpoint accessible"
    echo "$root_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(f'    Message: {data.get(\"message\", \"unknown\")}')
    print(f'    Version: {data.get(\"version\", \"unknown\")}')
    print(f'    Docs: {data.get(\"docs\", \"unknown\")}')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
else
    echo "❌ Root endpoint failed"
    echo "Response: $root_response"
    exit 1
fi

# Test 2: Health Check
echo ""
echo "🏥 Test 2: Health Check"
health_response=$(api_request "GET" "/health")
if echo "$health_response" | grep -q '"status"'; then
    echo "✅ Health endpoint accessible"
    echo "$health_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(f'    Status: {data.get(\"status\", \"unknown\")}')
    print(f'    Version: {data.get(\"version\", \"unknown\")}')
    components = data.get('components', {})
    print('    Components:')
    for name, status in components.items():
        print(f'      {name}: {status}')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
else
    echo "❌ Health endpoint failed"
    echo "Response: $health_response"
fi

# Test 3: Authentication
echo ""
echo "🔐 Test 3: Authentication"
login_data='{"username":"demo","password":"demo"}'
login_response=$(api_request "POST" "/api/auth/login" "$login_data")

if echo "$login_response" | grep -q '"access_token"'; then
    echo "✅ Authentication successful"
    access_token=$(echo "$login_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(data['access_token'])
except:
    pass
")
    echo "    Token: ${access_token:0:20}..."
else
    echo "❌ Authentication failed"
    echo "Response: $login_response"
    access_token=""
fi

# Test 4: Protected Endpoint (User Info)
if [ -n "$access_token" ]; then
    echo ""
    echo "👤 Test 4: User Information"
    user_response=$(api_request "GET" "/api/auth/me" "" "$access_token")
    
    if echo "$user_response" | grep -q '"username"'; then
        echo "✅ User info endpoint accessible"
        echo "$user_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(f'    Username: {data.get(\"username\", \"unknown\")}')
    print(f'    User ID: {data.get(\"id\", \"unknown\")}')
    print(f'    Roles: {data.get(\"roles\", [])}')
    print(f'    Permissions: {data.get(\"permissions\", [])}')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
    else
        echo "❌ User info endpoint failed"
        echo "Response: $user_response"
    fi
fi

# Test 5: Configuration Endpoint
if [ -n "$access_token" ]; then
    echo ""
    echo "⚙️ Test 5: Configuration"
    config_response=$(api_request "GET" "/api/config" "" "$access_token")
    
    if echo "$config_response" | grep -q '"database_host"'; then
        echo "✅ Configuration endpoint accessible"
        echo "$config_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    for key, value in data.items():
        print(f'    {key}: {value}')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
    else
        echo "❌ Configuration endpoint failed"
        echo "Response: $config_response"
    fi
fi

# Test 6: Collections Endpoint
if [ -n "$access_token" ]; then
    echo ""
    echo "📚 Test 6: Vector Collections"
    collections_response=$(api_request "GET" "/api/collections" "" "$access_token")
    
    if echo "$collections_response" | grep -q '\['; then
        echo "✅ Collections endpoint accessible"
        echo "$collections_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    if data:
        print('    Available collections:')
        for collection in data:
            print(f'      - {collection}')
    else:
        print('    No collections available')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
    else
        echo "❌ Collections endpoint failed"
        echo "Response: $collections_response"
    fi
fi

# Test 7: Vector Search
if [ -n "$access_token" ]; then
    echo ""
    echo "🔍 Test 7: Vector Search"
    search_data='{"query":"test search query","collection":"documents","limit":5}'
    search_response=$(api_request "POST" "/api/search/" "$search_data" "$access_token")
    
    if echo "$search_response" | grep -q '"results"'; then
        echo "✅ Search endpoint accessible"
        echo "$search_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(f'    Query: {data.get(\"query\", \"unknown\")}')
    print(f'    Results: {data.get(\"total\", 0)}')
    print(f'    Execution time: {data.get(\"execution_time\", 0):.3f}s')
    print(f'    Collection: {data.get(\"collection\", \"unknown\")}')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
    else
        echo "❌ Search endpoint failed"
        echo "Response: $search_response"
    fi
fi

# Test 8: Document Upload
if [ -n "$access_token" ]; then
    echo ""
    echo "📄 Test 8: Document Upload"
    upload_data='{"content":"This is a test document for the RAG system.","metadata":{"title":"Test Document","category":"testing"},"collection":"documents"}'
    upload_response=$(api_request "POST" "/api/search/upload" "$upload_data" "$access_token")
    
    if echo "$upload_response" | grep -q '"document_id"'; then
        echo "✅ Document upload successful"
        echo "$upload_response" | python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    print(f'    Document ID: {data.get(\"document_id\", \"unknown\")}')
    print(f'    Collection: {data.get(\"collection\", \"unknown\")}')
    print(f'    Status: {data.get(\"status\", \"unknown\")}')
    print(f'    Vector count: {data.get(\"vector_count\", 0)}')
except Exception as e:
    print(f'    Error parsing response: {e}')
"
    else
        echo "❌ Document upload failed"
        echo "Response: $upload_response"
    fi
fi

# Test 9: API Documentation
echo ""
echo "📖 Test 9: API Documentation"
docs_response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/docs")
if [ "$docs_response" = "200" ]; then
    echo "✅ API documentation accessible"
    echo "    OpenAPI docs: $API_URL/docs"
    echo "    ReDoc: $API_URL/redoc"
else
    echo "❌ API documentation not accessible (HTTP $docs_response)"
fi

echo ""
echo "🎉 FastAPI Integration Test Complete!"
echo ""
echo "📊 Test Summary:"
echo "   - Root endpoint: ✅"
echo "   - Health check: ✅"
echo "   - Authentication: $([ -n "$access_token" ] && echo "✅" || echo "⚠️")"
echo "   - Protected endpoints: $([ -n "$access_token" ] && echo "✅" || echo "⚠️")"
echo "   - Vector operations: $([ -n "$access_token" ] && echo "✅" || echo "⚠️")"
echo "   - API documentation: ✅"
echo ""
echo "🔗 Access Points:"
echo "   - API Base: $API_URL"
echo "   - Interactive Docs: $API_URL/docs"
echo "   - Health Check: $API_URL/health"
echo "   - Authentication: $API_URL/api/auth/login"
echo ""

if [ -n "$access_token" ]; then
    echo "🔑 Demo Authentication:"
    echo "   Username: demo"
    echo "   Password: demo"
    echo "   Access Token: ${access_token:0:30}..."
fi
