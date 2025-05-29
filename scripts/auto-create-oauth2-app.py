#!/usr/bin/env python3
"""
Automated OAuth2 Application Creator for Authentik
This script automatically creates OAuth2 providers and applications in Authentik using the REST API.
"""

import requests
import json
import sys
import os
import time
from urllib.parse import urljoin
from typing import Dict, Any, Optional

class AuthentikAPIClient:
    """Client for interacting with Authentik REST API."""
    
    def __init__(self, base_url: str, api_token: str, verify_ssl: bool = False):
        """Initialize the API client."""
        self.base_url = base_url.rstrip('/')
        self.api_url = urljoin(self.base_url, '/api/v3/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.session.verify = verify_ssl
        
        # Suppress SSL warnings for development
        if not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request and return the response."""
        url = urljoin(self.api_url, endpoint.lstrip('/'))
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {}
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"   Response content: {e.response.text}")
            raise
    
    def get_flows(self) -> Dict[str, Any]:
        """Get all available flows."""
        return self._make_request('GET', '/flows/instances/')
    
    def get_certificates(self) -> Dict[str, Any]:
        """Get all available certificates/keys."""
        return self._make_request('GET', '/crypto/certificatekeypairs/')
    
    def get_applications(self) -> Dict[str, Any]:
        """Get all applications."""
        return self._make_request('GET', '/core/applications/')
    
    def get_oauth2_providers(self) -> Dict[str, Any]:
        """Get all OAuth2 providers."""
        return self._make_request('GET', '/providers/oauth2/')
    
    def create_application(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new application."""
        return self._make_request('POST', '/core/applications/', app_data)
    
    def create_oauth2_provider(self, provider_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new OAuth2 provider."""
        return self._make_request('POST', '/providers/oauth2/', provider_data)
    
    def update_application(self, app_id: str, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing application."""
        return self._make_request('PATCH', f'/core/applications/{app_id}/', app_data)

class OAuth2AppCreator:
    """High-level OAuth2 application creator."""
    
    def __init__(self, api_client: AuthentikAPIClient):
        self.client = api_client
        self.default_auth_flow = None
        self.default_signing_key = None
    
    def _get_default_auth_flow(self) -> str:
        """Get the default authentication flow."""
        if self.default_auth_flow:
            return self.default_auth_flow
        
        print("🔍 Finding default authentication flow...")
        flows = self.client.get_flows()
        
        # Look for default authentication flow
        for flow in flows.get('results', []):
            if flow.get('slug') == 'default-authentication-flow':
                self.default_auth_flow = flow['pk']
                print(f"✅ Found default auth flow: {flow['name']} ({flow['pk']})")
                return self.default_auth_flow
        
        # Fallback to first authentication flow
        for flow in flows.get('results', []):
            if flow.get('designation') == 'authentication':
                self.default_auth_flow = flow['pk']
                print(f"✅ Using auth flow: {flow['name']} ({flow['pk']})")
                return self.default_auth_flow
        
        raise Exception("No authentication flow found")
    
    def _get_default_signing_key(self) -> str:
        """Get the default signing key."""
        if self.default_signing_key:
            return self.default_signing_key
        
        print("🔍 Finding default signing key...")
        certificates = self.client.get_certificates()
        
        # Look for authentik self-signed key
        for cert in certificates.get('results', []):
            if 'authentik' in cert.get('name', '').lower() and 'self-signed' in cert.get('name', '').lower():
                self.default_signing_key = cert['pk']
                print(f"✅ Found signing key: {cert['name']} ({cert['pk']})")
                return self.default_signing_key
        
        # Fallback to first available key
        if certificates.get('results'):
            cert = certificates['results'][0]
            self.default_signing_key = cert['pk']
            print(f"✅ Using signing key: {cert['name']} ({cert['pk']})")
            return self.default_signing_key
        
        raise Exception("No signing key found")
    
    def check_existing_app(self, app_name: str, client_id: str) -> Optional[Dict[str, Any]]:
        """Check if an application already exists."""
        print(f"🔍 Checking for existing application: {app_name}")
        
        apps = self.client.get_applications()
        for app in apps.get('results', []):
            if app.get('name') == app_name or app.get('slug') == app_name.lower().replace(' ', '-'):
                print(f"⚠️  Application already exists: {app['name']} ({app['pk']})")
                return app
        
        # Check OAuth2 providers for client_id
        providers = self.client.get_oauth2_providers()
        for provider in providers.get('results', []):
            if provider.get('client_id') == client_id:
                print(f"⚠️  OAuth2 provider with client_id '{client_id}' already exists")
                return provider
        
        return None
    
    def create_oauth2_application(self, 
                                app_name: str,
                                client_id: str,
                                redirect_uris: list,
                                scopes: list = None,
                                client_secret: str = None,
                                description: str = None) -> Dict[str, Any]:
        """Create a complete OAuth2 application with provider."""
        
        if scopes is None:
            scopes = ["openid", "email", "profile", "offline_access"]
        
        if description is None:
            description = f"OAuth2 application for {app_name}"
        
        # Check if application already exists
        existing = self.check_existing_app(app_name, client_id)
        if existing:
            print(f"✅ Using existing application/provider")
            return existing
        
        print(f"🚀 Creating OAuth2 application: {app_name}")
        
        # Get required resources
        auth_flow = self._get_default_auth_flow()
        signing_key = self._get_default_signing_key()
        
        # Step 1: Create the application (without provider initially)
        print("📝 Creating application...")
        app_slug = app_name.lower().replace(' ', '-').replace('_', '-')
        app_data = {
            "name": app_name,
            "slug": app_slug,
            "provider": None,  # Will be set after creating provider
            "policy_engine_mode": "all",
            "meta_launch_url": "",
            "meta_description": description,
            "meta_publisher": "",
            "meta_icon": None
        }
        
        app_response = self.client.create_application(app_data)
        app_id = app_response['pk']
        print(f"✅ Application created: {app_name} ({app_id})")
        
        # Step 2: Create the OAuth2 provider
        print("🔐 Creating OAuth2 provider...")
        provider_data = {
            "name": f"{app_name} OAuth2 Provider",
            "authorization_flow": auth_flow,
            "client_id": client_id,
            "redirect_uris": redirect_uris,
            "signing_key": signing_key,
            "client_type": "confidential",
            "include_claims_in_id_token": True,
            "issuer_mode": "per_provider",
            "sub_mode": "hashed_user_id",
            "access_code_validity": "minutes=1",
            "access_token_validity": "minutes=5",
            "refresh_token_validity": "days=30",
            "property_mappings": [],
            "jwks_sources": []
        }
        
        # Add client secret if provided
        if client_secret:
            provider_data["client_secret"] = client_secret
        
        provider_response = self.client.create_oauth2_provider(provider_data)
        provider_id = provider_response['pk']
        actual_client_secret = provider_response.get('client_secret', 'Generated by Authentik')
        print(f"✅ OAuth2 provider created: {provider_id}")
        
        # Step 3: Update the application with the provider
        print("🔗 Linking application to provider...")
        update_data = {"provider": provider_id}
        self.client.update_application(app_id, update_data)
        print(f"✅ Application linked to provider")
        
        # Return complete information
        result = {
            "application": app_response,
            "provider": provider_response,
            "client_id": client_id,
            "client_secret": actual_client_secret,
            "redirect_uris": redirect_uris,
            "scopes": scopes
        }
        
        print(f"\n🎉 OAuth2 application created successfully!")
        print(f"   Application ID: {app_id}")
        print(f"   Provider ID: {provider_id}")
        print(f"   Client ID: {client_id}")
        print(f"   Client Secret: {actual_client_secret}")
        print(f"   Redirect URIs: {', '.join(redirect_uris)}")
        
        return result

def main():
    """Main function to create OAuth2 application."""
    
    # Configuration
    AUTHENTIK_URL = os.getenv('AUTHENTIK_URL', 'https://localhost:9443')
    API_TOKEN = os.getenv('AUTHENTIK_API_TOKEN')
    
    # OAuth2 Application Configuration
    APP_NAME = os.getenv('OAUTH_APP_NAME', 'FastAPI Client')
    CLIENT_ID = os.getenv('OAUTH_CLIENT_ID', 'fastapi-client')
    CLIENT_SECRET = os.getenv('OAUTH_CLIENT_SECRET')  # Optional, will be generated if not provided
    REDIRECT_URIS = os.getenv('OAUTH_REDIRECT_URIS', 'http://localhost:8000/api/auth/callback').split(',')
    SCOPES = os.getenv('OAUTH_SCOPES', 'openid,email,profile,rag:api').split(',')
    
    if not API_TOKEN:
        print("❌ AUTHENTIK_API_TOKEN environment variable is required")
        print("   You can get an API token from: https://localhost:9443/if/admin/#/core/tokens")
        return 1
    
    print("🚀 Authentik OAuth2 Application Creator")
    print("=" * 50)
    print(f"Authentik URL: {AUTHENTIK_URL}")
    print(f"Application Name: {APP_NAME}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Redirect URIs: {', '.join(REDIRECT_URIS)}")
    print(f"Scopes: {', '.join(SCOPES)}")
    print()
    
    try:
        # Initialize API client
        print("🔑 Initializing Authentik API client...")
        client = AuthentikAPIClient(AUTHENTIK_URL, API_TOKEN, verify_ssl=False)
        
        # Test API connection
        print("🔍 Testing API connection...")
        flows = client.get_flows()
        print(f"✅ Connected to Authentik API ({len(flows.get('results', []))} flows found)")
        
        # Create OAuth2 application
        creator = OAuth2AppCreator(client)
        result = creator.create_oauth2_application(
            app_name=APP_NAME,
            client_id=CLIENT_ID,
            redirect_uris=REDIRECT_URIS,
            scopes=SCOPES,
            client_secret=CLIENT_SECRET,
            description=f"OAuth2 application for {APP_NAME} - Created automatically via API"
        )
        
        # Save client secret to .env file
        env_file = '/Users/nova/Sites/zoi/.env'
        if os.path.exists(env_file):
            print(f"\n📝 Updating .env file with client secret...")
            
            # Read current .env content
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            # Update or add the client secret
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('FASTAPI_OAUTH_CLIENT_SECRET='):
                    lines[i] = f'FASTAPI_OAUTH_CLIENT_SECRET={result["client_secret"]}\n'
                    updated = True
                    break
            
            if not updated:
                lines.append(f'FASTAPI_OAUTH_CLIENT_SECRET={result["client_secret"]}\n')
            
            # Write back to file
            with open(env_file, 'w') as f:
                f.writelines(lines)
            
            print(f"✅ Updated .env file with client secret")
        
        print(f"\n🎯 Next Steps:")
        print(f"   1. Restart FastAPI service: docker-compose restart fastapi-1")
        print(f"   2. Test OAuth2 flow: http://localhost:8000/api/auth/login")
        print(f"   3. Check application in Authentik: {AUTHENTIK_URL}/if/admin/#/core/applications")
        
        return 0
        
    except Exception as e:
        print(f"❌ Failed to create OAuth2 application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
