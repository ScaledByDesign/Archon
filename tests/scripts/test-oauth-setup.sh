#!/bin/bash

# Test OAuth2 Setup Script
# Tests the OAuth2 integration between FastAPI and Authentik

set -e

echo "🧪 Testing OAuth2 Setup..."

# Load environment variables
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ .env file not found"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test functions
test_authentik_accessibility() {
    echo -e "${BLUE}🔍 Testing Authentik accessibility...${NC}"
    
    if curl -k -s --connect-timeout 10 https://zoi.local:9443/application/o/default/.well-known/openid_configuration > /dev/null; then
        echo -e "${GREEN}✅ Authentik is accessible${NC}"
        return 0
    else
        echo -e "${RED}❌ Authentik is not accessible${NC}"
        return 1
    fi
}

test_fastapi_health() {
    echo -e "${BLUE}🔍 Testing FastAPI health...${NC}"
    
    if curl -s --connect-timeout 10 http://zoi.local:8000/health > /dev/null; then
        echo -e "${GREEN}✅ FastAPI is accessible${NC}"
        return 0
    else
        echo -e "${RED}❌ FastAPI is not accessible${NC}"
        return 1
    fi
}

test_oauth_endpoints() {
    echo -e "${BLUE}🔍 Testing OAuth2 endpoints...${NC}"
    
    # Test auth health endpoint
    if curl -s --connect-timeout 10 http://zoi.local:8000/api/auth/health | grep -q "oauth_authentication"; then
        echo -e "${GREEN}✅ OAuth2 auth health endpoint working${NC}"
    else
        echo -e "${RED}❌ OAuth2 auth health endpoint failed${NC}"
        return 1
    fi
    
    # Test auth status endpoint
    if curl -s --connect-timeout 10 http://zoi.local:8000/api/auth/status | grep -q "authenticated"; then
        echo -e "${GREEN}✅ OAuth2 auth status endpoint working${NC}"
    else
        echo -e "${RED}❌ OAuth2 auth status endpoint failed${NC}"
        return 1
    fi
    
    return 0
}

test_oauth_configuration() {
    echo -e "${BLUE}🔍 Testing OAuth2 configuration...${NC}"
    
    # Check if OAuth2 client credentials are configured
    if [ -z "$FASTAPI_OAUTH_CLIENT_SECRET" ] || [ "$FASTAPI_OAUTH_CLIENT_SECRET" = "to-be-generated" ]; then
        echo -e "${YELLOW}⚠️  OAuth2 client secret not configured${NC}"
        echo -e "${YELLOW}   Please configure FASTAPI_OAUTH_CLIENT_SECRET in .env${NC}"
        return 1
    else
        echo -e "${GREEN}✅ OAuth2 client secret configured${NC}"
    fi
    
    # Check OAuth2 configuration endpoint
    response=$(curl -s http://zoi.local:8000/api/auth/status)
    if echo "$response" | grep -q '"oauth_configured": true'; then
        echo -e "${GREEN}✅ OAuth2 client properly configured${NC}"
    else
        echo -e "${YELLOW}⚠️  OAuth2 client not fully configured${NC}"
        echo -e "${YELLOW}   Response: $response${NC}"
    fi
    
    return 0
}

test_oauth_flow() {
    echo -e "${BLUE}🔍 Testing OAuth2 authorization flow...${NC}"
    
    # Test login endpoint (should redirect to Authentik)
    login_response=$(curl -s -w "%{http_code}" -o /dev/null http://zoi.local:8000/api/auth/login)
    
    if [ "$login_response" = "307" ] || [ "$login_response" = "302" ]; then
        echo -e "${GREEN}✅ OAuth2 login redirect working${NC}"
    else
        echo -e "${RED}❌ OAuth2 login redirect failed (HTTP $login_response)${NC}"
        return 1
    fi
    
    return 0
}

show_oauth_urls() {
    echo -e "${BLUE}🔗 OAuth2 URLs:${NC}"
    echo "  • Authorization: https://zoi.local:9443/application/o/authorize/"
    echo "  • Token: https://zoi.local:9443/application/o/token/"
    echo "  • User Info: https://zoi.local:9443/application/o/userinfo/"
    echo "  • JWKS: https://zoi.local:9443/application/o/default/jwks/"
    echo ""
    echo -e "${BLUE}🔗 FastAPI OAuth2 Endpoints:${NC}"
    echo "  • Login: http://zoi.local:8000/api/auth/login"
    echo "  • Callback: http://zoi.local:8000/api/auth/callback"
    echo "  • Status: http://zoi.local:8000/api/auth/status"
    echo "  • User Info: http://zoi.local:8000/api/auth/me"
    echo "  • Logout: http://zoi.local:8000/api/auth/logout"
}

# Main test execution
main() {
    echo "🚀 Starting OAuth2 setup tests..."
    echo ""
    
    # Track test results
    tests_passed=0
    tests_failed=0
    
    # Run tests
    if test_authentik_accessibility; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    if test_fastapi_health; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    if test_oauth_endpoints; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    if test_oauth_configuration; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    if test_oauth_flow; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    echo ""
    show_oauth_urls
    echo ""
    
    # Summary
    echo -e "${BLUE}📊 Test Summary:${NC}"
    echo -e "  ${GREEN}✅ Passed: $tests_passed${NC}"
    echo -e "  ${RED}❌ Failed: $tests_failed${NC}"
    
    if [ $tests_failed -eq 0 ]; then
        echo ""
        echo -e "${GREEN}🎉 All OAuth2 tests passed!${NC}"
        echo -e "${GREEN}   OAuth2 integration is ready for testing${NC}"
        echo ""
        echo -e "${YELLOW}📝 Next Steps:${NC}"
        echo "   1. Configure OAuth2 applications in Authentik admin UI"
        echo "   2. Update client secrets in .env file"
        echo "   3. Test full OAuth2 flow by visiting:"
        echo "      http://zoi.local:8000/api/auth/login"
        return 0
    else
        echo ""
        echo -e "${RED}❌ Some OAuth2 tests failed${NC}"
        echo -e "${RED}   Please check the configuration and try again${NC}"
        return 1
    fi
}

# Run main function
main "$@"
