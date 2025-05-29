#!/usr/bin/env python3
"""
Setup OAuth2 applications in Authentik via API
"""
import requests
import json
import os
import sys
from urllib.parse import urljoin
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_env():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
    except FileNotFoundError:
        print("❌ .env file not found")
        sys.exit(1)
    return env_vars

def get_api_token():
    """Get API token by authenticating with username/password"""
    base_url = os.getenv('AUTHENTIK_BASE_URL', 'https://localhost:9443')
    username = os.getenv('AUTHENTIK_BOOTSTRAP_EMAIL', 'admin@localhost')
    password = os.getenv('AUTHENTIK_BOOTSTRAP_PASSWORD', 'change-me-authentik-admin')
    
    # Try to get token via API
    token_url = urljoin(base_url, '/api/v3/core/tokens/')
    
    # First, try to create a token using basic auth or session
    session = requests.Session()
    session.verify = False
    
    # Get CSRF token from login page
    login_page_url = urljoin(base_url, '/if/admin/')
    response = session.get(login_page_url)
    
    if response.status_code != 200:
        print(f"❌ Could not access Authentik at {base_url}")
        return None
    
    # For now, let's try using the admin credentials to create a temporary token
    # This is a simplified approach - in production, use proper API authentication
    print("⚠️  Manual token creation required")
    print(f"Please visit {base_url}/if/admin/ and:")
    print("1. Login with username:", username)
    print("2. Go to Directory -> Tokens")
    print("3. Create a new token with 'authentik Core: Can view Application' permission")
    print("4. Copy the token and set it as AUTHENTIK_API_TOKEN in .env")
    
    # Check if token is already set
    api_token = os.getenv('AUTHENTIK_API_TOKEN')
    if api_token:
        return api_token
    
    return None

def create_oauth_application(session, base_url, app_config):
    """Create an OAuth2 application"""
    print(f"🔧 Creating application: {app_config['name']}")
    
    # Create provider first
    provider_data = {
        "name": f"{app_config['name']}-provider",
        "authorization_flow": "default-authorization-flow",
        "client_type": "confidential",
        "client_id": app_config['client_id'],
        "redirect_uris": app_config['redirect_uri'],
        "sub_mode": "hashed_user_id"
    }
    
    provider_response = session.post(
        urljoin(base_url, '/api/v3/providers/oauth2/'),
        json=provider_data
    )
    
    if provider_response.status_code not in [200, 201]:
        print(f"❌ Failed to create provider: {provider_response.text}")
        return None
    
    provider = provider_response.json()
    print(f"✅ Provider created: {provider['name']}")
    
    # Create application
    app_data = {
        "name": app_config['name'],
        "slug": app_config['slug'],
        "provider": provider['pk']
    }
    
    app_response = session.post(
        urljoin(base_url, '/api/v3/core/applications/'),
        json=app_data
    )
    
    if app_response.status_code not in [200, 201]:
        print(f"❌ Failed to create application: {app_response.text}")
        return None
    
    application = app_response.json()
    print(f"✅ Application created: {application['name']}")
    
    # Return the provider info with client secret
    return {
        'application': application,
        'provider': provider,
        'client_id': provider['client_id'],
        'client_secret': provider['client_secret']
    }

def main():
    print("🚀 Setting up OAuth2 applications in Authentik...")
    
    # Load environment
    load_env()
    
    base_url = os.getenv('AUTHENTIK_BASE_URL', 'https://localhost:9443')
    api_token = get_api_token()
    
    if not api_token:
        print("❌ Could not get API token. Please set AUTHENTIK_API_TOKEN in .env")
        return
    
    # Setup session with API token
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    })
    
    # Test API access
    test_response = session.get(urljoin(base_url, '/api/v3/core/applications/'))
    if test_response.status_code != 200:
        print(f"❌ API authentication failed: {test_response.text}")
        return
    
    print("✅ API authentication successful")
    
    # Define applications to create
    applications = [
        {
            'name': 'FastAPI RAG System',
            'slug': 'fastapi-rag',
            'client_id': os.getenv('FASTAPI_OAUTH_CLIENT_ID', 'fastapi-client'),
            'redirect_uri': os.getenv('FASTAPI_OAUTH_REDIRECT_URI', 'http://localhost:8000/api/auth/callback')
        },
        {
            'name': 'Open WebUI',
            'slug': 'open-webui',
            'client_id': os.getenv('WEBUI_OAUTH_CLIENT_ID', 'webui-client'),
            'redirect_uri': 'http://localhost:3000/auth/callback'
        },
        {
            'name': 'n8n Workflow',
            'slug': 'n8n-workflow',
            'client_id': os.getenv('N8N_OAUTH_CLIENT_ID', 'n8n-client'),
            'redirect_uri': 'http://localhost:5678/rest/oauth2-credential/callback'
        }
    ]
    
    # Create applications
    created_apps = []
    for app_config in applications:
        result = create_oauth_application(session, base_url, app_config)
        if result:
            created_apps.append(result)
    
    # Print summary
    print("\n📋 OAuth2 Applications Summary:")
    print("=" * 50)
    for app in created_apps:
        print(f"Application: {app['application']['name']}")
        print(f"Client ID: {app['client_id']}")
        print(f"Client Secret: {app['client_secret']}")
        print("-" * 30)
    
    print("\n🔧 Update your .env file with these client secrets:")
    for app in created_apps:
        if 'fastapi' in app['application']['slug']:
            print(f"FASTAPI_OAUTH_CLIENT_SECRET={app['client_secret']}")
        elif 'webui' in app['application']['slug']:
            print(f"WEBUI_OAUTH_CLIENT_SECRET={app['client_secret']}")
        elif 'n8n' in app['application']['slug']:
            print(f"N8N_OAUTH_CLIENT_SECRET={app['client_secret']}")

if __name__ == '__main__':
    main()
