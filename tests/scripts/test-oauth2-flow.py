#!/usr/bin/env python3
"""
Test script for OAuth2 authentication flow with Authentik.
This script tests the various OAuth2 endpoints and flows.
"""

import requests
import json
import sys
from urllib.parse import urlparse, parse_qs

# Configuration
FASTAPI_BASE_URL = "http://localhost:8000"
AUTHENTIK_BASE_URL = "https://localhost:9443"

def test_oauth2_status():
    """Test the OAuth2 configuration status."""
    print("🔍 Testing OAuth2 configuration status...")
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/api/auth/status")
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Status endpoint accessible")
        print(f"   - Authenticated: {data.get('authenticated', False)}")
        print(f"   - OAuth2 Configured: {data.get('oauth_configured', False)}")
        
        if not data.get('oauth_configured', False):
            print("❌ OAuth2 is not configured properly")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Failed to check OAuth2 status: {e}")
        return False

def test_login_redirect():
    """Test the OAuth2 login redirect."""
    print("\n🔍 Testing OAuth2 login redirect...")
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/api/auth/login", allow_redirects=False)
        
        if response.status_code == 307:
            location = response.headers.get('location', '')
            print(f"✅ Login redirect working (307)")
            print(f"   - Redirect URL: {location}")
            
            # Parse the redirect URL to check parameters
            parsed_url = urlparse(location)
            query_params = parse_qs(parsed_url.query)
            
            expected_params = ['response_type', 'client_id', 'redirect_uri', 'scope', 'state']
            for param in expected_params:
                if param in query_params:
                    print(f"   - {param}: {query_params[param][0]}")
                else:
                    print(f"   - ❌ Missing parameter: {param}")
            
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test login redirect: {e}")
        return False

def test_health_endpoints():
    """Test various health endpoints."""
    print("\n🔍 Testing health endpoints...")
    
    endpoints = [
        "/health",
        "/api/auth/health",
        "/api/search/health"
    ]
    
    all_healthy = True
    for endpoint in endpoints:
        try:
            response = requests.get(f"{FASTAPI_BASE_URL}{endpoint}")
            response.raise_for_status()
            print(f"✅ {endpoint}: Healthy")
        except Exception as e:
            print(f"❌ {endpoint}: Failed - {e}")
            all_healthy = False
    
    return all_healthy

def test_authentik_accessibility():
    """Test if Authentik is accessible."""
    print("\n🔍 Testing Authentik accessibility...")
    try:
        response = requests.get(AUTHENTIK_BASE_URL, verify=False, timeout=5)
        print(f"✅ Authentik accessible (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Authentik not accessible: {e}")
        return False

def test_session_management():
    """Test session management."""
    print("\n🔍 Testing session management...")
    try:
        session = requests.Session()
        response = session.get(f"{FASTAPI_BASE_URL}/api/auth/login", allow_redirects=False)
        
        # Check if session cookie is set
        if 'session' in session.cookies:
            print("✅ Session cookie set properly")
            return True
        else:
            print("❌ No session cookie found")
            return False
            
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        return False

def main():
    """Run all OAuth2 tests."""
    print("🚀 OAuth2 Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("OAuth2 Status", test_oauth2_status),
        ("Health Endpoints", test_health_endpoints),
        ("Authentik Accessibility", test_authentik_accessibility),
        ("Login Redirect", test_login_redirect),
        ("Session Management", test_session_management),
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! OAuth2 integration is working correctly.")
        print("\n📝 Next steps:")
        print("   1. Open http://localhost:8000/api/auth/login in your browser")
        print("   2. Complete the authentication flow")
        print("   3. Test user information retrieval")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and try again.")
        print("\n📖 Refer to docs/manual-oauth2-setup.md for setup instructions.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
