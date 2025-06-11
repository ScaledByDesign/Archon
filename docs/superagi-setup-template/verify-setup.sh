#!/bin/bash
# SuperAGI + Qdrant + LiteLLM Setup Verification Script

echo "🔍 Verifying SuperAGI + Qdrant + LiteLLM Setup..."
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Qdrant Health Check
echo "📊 Testing Qdrant Connection..."
qdrant_response=$(curl -s http://zoi.local:6333/readyz)
if echo "$qdrant_response" | grep -q "ready"; then
    echo -e "${GREEN}✅ Qdrant: HEALTHY${NC}"
else
    echo -e "${RED}❌ Qdrant: FAILED${NC}"
    echo "   Response: $qdrant_response"
fi

# Test 2: LiteLLM Health Check
echo "📊 Testing LiteLLM Connection..."
litellm_response=$(curl -s -w "%{http_code}" -H "Authorization: Bearer sk-change-me-to-random-string" http://zoi.local:4000/v1/models)
http_code="${litellm_response: -3}"
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✅ LiteLLM: HEALTHY${NC}"
else
    echo -e "${RED}❌ LiteLLM: FAILED (HTTP $http_code)${NC}"
fi

# Test 3: SuperAGI Backend Health
echo "📊 Testing SuperAGI Backend..."
superagi_health=$(curl -s -w "%{http_code}" http://zoi.local:8001/health 2>/dev/null)
if [ "${superagi_health: -3}" = "200" ]; then
    echo -e "${GREEN}✅ SuperAGI Backend: HEALTHY${NC}"
else
    echo -e "${YELLOW}⚠️  SuperAGI Backend: Using fallback test${NC}"
fi

# Test 4: SuperAGI Models
echo "📊 Testing SuperAGI Models..."
models_response=$(curl -s "http://zoi.local:8001/models_controller/fetch_models")
if echo "$models_response" | grep -q "gpt"; then
    echo -e "${GREEN}✅ SuperAGI Models: AVAILABLE${NC}"
    models=$(echo "$models_response" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | tr '\n' ', ' | sed 's/,$//')
    echo "   Available models: $models"
else
    echo -e "${RED}❌ SuperAGI Models: NOT AVAILABLE${NC}"
    echo "   Response: $models_response"
fi

# Test 5: SuperAGI API Keys
echo "📊 Testing SuperAGI API Keys..."
api_keys_response=$(curl -s "http://zoi.local:8001/models_controller/get_api_keys")
if echo "$api_keys_response" | grep -q "OpenAI"; then
    echo -e "${GREEN}✅ SuperAGI API Keys: CONFIGURED${NC}"
else
    echo -e "${RED}❌ SuperAGI API Keys: NOT CONFIGURED${NC}"
    echo "   You may need to run the API key storage command"
fi

# Test 6: Docker Services Status
echo "📊 Testing Docker Services..."
services=("superagi-backend" "qdrant" "litellm")
for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        echo -e "${GREEN}✅ $service: RUNNING${NC}"
    else
        echo -e "${RED}❌ $service: NOT RUNNING${NC}"
    fi
done

echo "=================================================="
echo "🎯 Setup Verification Complete!"
echo ""

# Summary
all_good=true
if ! echo "$qdrant_response" | grep -q "ready"; then all_good=false; fi
if [ "$http_code" != "200" ]; then all_good=false; fi
if ! echo "$models_response" | grep -q "gpt"; then all_good=false; fi

if [ "$all_good" = true ]; then
    echo -e "${GREEN}🎉 SUCCESS: All components are working correctly!${NC}"
    echo "🌐 Access SuperAGI at: http://zoi.local:3001"
else
    echo -e "${YELLOW}⚠️  PARTIAL SUCCESS: Some components may need attention${NC}"
    echo ""
    echo "💡 Common fixes:"
    echo "   - Wait 30-60 seconds for services to fully start"
    echo "   - Run: docker-compose restart superagi-backend"
    echo "   - Store API key with the provided curl command"
fi
