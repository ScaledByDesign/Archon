#!/usr/bin/env python3
"""
Simplified OAuth2 Application Creator for Authentik
This script creates OAuth2 applications using a manually provided API token.
"""

import requests
import json
import sys
import os
from typing import Dict, Any, Optional

def create_oauth2_app_simple():
    """Create OAuth2 application with minimal setup."""
    
    print(" Simple OAuth2 Application Creator")
    print("=" * 50)
    
    # Configuration
    AUTHENTIK_URL = "https://localhost:9443"
    API_TOKEN = os.getenv('AUTHENTIK_API_TOKEN')
    
    if not API_TOKEN:
        print(" AUTHENTIK_API_TOKEN environment variable is required")
        print("   Please create an API token manually:")
        print("   1. Go to https://localhost:9443/if/admin/#/core/tokens")
        print("   2. Create a new token with 'API' intent")
        print("   3. Add it to .env: AUTHENTIK_API_TOKEN=your_token_here")
        return False
    
    print(f" Using API token: {API_TOKEN[:10]}...")
    
    # Setup session
    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    })
    session.verify = False
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        # Test API connection
        print(" Testing API connection...")
        response = session.get(f"{AUTHENTIK_URL}/api/v3/flows/instances/")
        response.raise_for_status()
        flows = response.json()
        print(f" Connected to Authentik API ({len(flows.get('results', []))} flows found)")
        
        # Get default authentication flow
        print(" Finding authentication flow...")
        auth_flow = None
        invalidation_flow = None
        for flow in flows.get('results', []):
            if flow.get('designation') == 'authentication':
                auth_flow = flow['pk']
                print(f" Using auth flow: {flow['name']} ({flow['pk']})")
            elif flow.get('designation') == 'invalidation':
                invalidation_flow = flow['pk']
                print(f" Using invalidation flow: {flow['name']} ({flow['pk']})")
        
        if not auth_flow:
            print(" No authentication flow found")
            return False
        
        if not invalidation_flow:
            # Use the same flow for invalidation if no specific invalidation flow exists
            invalidation_flow = auth_flow
            print(f"  Using auth flow for invalidation as well")
        
        # Get signing key
        print(" Finding signing key...")
        response = session.get(f"{AUTHENTIK_URL}/api/v3/crypto/certificatekeypairs/")
        response.raise_for_status()
        certificates = response.json()
        
        signing_key = None
        for cert in certificates.get('results', []):
            if 'authentik' in cert.get('name', '').lower():
                signing_key = cert['pk']
                print(f" Using signing key: {cert['name']} ({cert['pk']})")
                break
        
        if not signing_key and certificates.get('results'):
            cert = certificates['results'][0]
            signing_key = cert['pk']
            print(f" Using first available key: {cert['name']} ({cert['pk']})")
        
        if not signing_key:
            print(" No signing key found")
            return False
        
        # Create OAuth2 provider
        print(" Creating OAuth2 provider...")
        provider_data = {
            "name": "FastAPI Client OAuth2 Provider",
            "authorization_flow": auth_flow,
            "invalidation_flow": invalidation_flow,
            "client_id": "fastapi-client",
            "redirect_uris": [
                {
                    "url": "http://localhost:8000/api/auth/callback",
                    "matching_mode": "strict"
                }
            ],
            "signing_key": signing_key,
            "client_type": "confidential",
            "include_claims_in_id_token": True,
            "issuer_mode": "per_provider",
            "sub_mode": "hashed_user_id",
            "access_code_validity": "minutes=1",
            "access_token_validity": "minutes=5",
            "refresh_token_validity": "days=30"
        }
        
        response = session.post(f"{AUTHENTIK_URL}/api/v3/providers/oauth2/", json=provider_data)
        
        if response.status_code == 201:
            provider = response.json()
            provider_id = provider["pk"]
            client_secret = provider["client_secret"]
            
            print(f" OAuth2 provider created successfully!")
            print(f"   Provider ID: {provider_id}")
            print(f"   Client ID: {provider['client_id']}")
            print(f"   Client Secret: {client_secret}")
            
            # Create or link application
            print(" Creating application...")
            app_data = {
                "name": "FastAPI OAuth2 App",
                "slug": "fastapi-oauth2-app",
                "provider": provider_id,
                "meta_launch_url": "http://localhost:8000",
                "meta_description": "FastAPI application with OAuth2 authentication"
            }
            
            app_response = session.post(f"{AUTHENTIK_URL}/api/v3/core/applications/", json=app_data)
            
            if app_response.status_code == 201:
                app = app_response.json()
                print(f" Application created successfully!")
                print(f"   Application ID: {app['pk']}")
                print(f"   Name: {app['name']}")
                print(f"   Launch URL: {app['meta_launch_url']}")
            else:
                print(f" Failed to create application: {app_response.status_code}")
                print(f"   Details: {app_response.text}")
            
            # Update .env file
            print(" Updating .env file...")
            try:
                env_file = ".env"
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('FASTAPI_OAUTH_CLIENT_SECRET='):
                        lines[i] = f'FASTAPI_OAUTH_CLIENT_SECRET={client_secret}\n'
                        updated = True
                        break
                
                if updated:
                    with open(env_file, 'w') as f:
                        f.writelines(lines)
                    print(" Updated .env file with client secret")
                else:
                    print(" FASTAPI_OAUTH_CLIENT_SECRET not found in .env file")
                    print(f"   Please add: FASTAPI_OAUTH_CLIENT_SECRET={client_secret}")
                    
            except Exception as e:
                print(f" Error updating .env file: {e}")
                print(f"   Please manually add: FASTAPI_OAUTH_CLIENT_SECRET={client_secret}")
            
            print(f"\n OAuth2 Setup Complete!")
            print(f"   Client ID: fastapi-client")
            print(f"   Client Secret: {client_secret}")
            print(f"   Redirect URI: http://localhost:8000/api/auth/callback")
            print(f"   Provider: FastAPI Client OAuth2 Provider")
            print(f"   Application: FastAPI OAuth2 App")
            print(f"\n Ready to test OAuth2 flow!")
            print(f"   Test URL: http://localhost:8000/api/auth/login")
            
        else:
            print(f" Failed to create OAuth2 provider")
            print(f"   Status: {response.status_code}")
            error_details = response.json() if response.content else "No details available"
            print(f"   Details: {error_details}")
            return False
        
    except Exception as e:
        print(f" Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"   Details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   Response: {e.response.text}")
        return False

def main():
    """Main function."""
    success = create_oauth2_app_simple()
    
    if success:
        print(f"\n Next steps:")
        print(f"   1. Restart FastAPI: docker-compose restart fastapi-1")
        print(f"   2. Test OAuth2: python scripts/test-oauth2-flow.py")
        print(f"   3. Open browser: http://localhost:8000/api/auth/login")
        return 0
    else:
        print(f"\n Failed to create OAuth2 application")
        return 1

if __name__ == "__main__":
    sys.exit(main())
