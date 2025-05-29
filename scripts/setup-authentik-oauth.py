#!/usr/bin/env python3
"""
Setup OAuth2 applications in Authentik using proper API authentication
Based on Authentik documentation and FastAPI OAuth2 patterns
"""
import requests
import json
import os
import sys
import secrets
import base64
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

def authenticate_with_credentials(base_url, username, password):
    """Authenticate using username/password to get session token"""
    session = requests.Session()
    session.verify = False
    
    # Step 1: Get the login page to extract CSRF token
    login_page_url = urljoin(base_url, '/if/flow/default-authentication-flow/')
    response = session.get(login_page_url)
    
    if response.status_code != 200:
        print(f"❌ Could not access login page: {response.status_code}")
        return None
    
    # Extract CSRF token from the response
    import re
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
    if not csrf_match:
        print("❌ Could not extract CSRF token from login page")
        return None
    
    csrf_token = csrf_match.group(1)
    
    # Step 2: Perform login
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'uid_field': username,
        'password': password
    }
    
    login_response = session.post(
        login_page_url,
        data=login_data,
        allow_redirects=False
    )
    
    # Check if login was successful (should redirect)
    if login_response.status_code not in [302, 200]:
        print(f"❌ Login failed: {login_response.status_code}")
        return None
    
    # Step 3: Create an API token
    # First, get the admin interface
    admin_response = session.get(urljoin(base_url, '/if/admin/'))
    if admin_response.status_code != 200:
        print("❌ Could not access admin interface after login")
        return None
    
    # Extract CSRF token for API token creation
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', admin_response.text)
    if not csrf_match:
        print("❌ Could not extract CSRF token from admin page")
        return None
    
    csrf_token = csrf_match.group(1)
    
    # Create API token via admin interface
    token_data = {
        'csrfmiddlewaretoken': csrf_token,
        'identifier': 'oauth-setup-token',
        'description': 'Token for OAuth2 application setup',
        'expires': '',  # No expiration
        'expiring': False
    }
    
    token_response = session.post(
        urljoin(base_url, '/api/v3/core/tokens/'),
        json={
            'identifier': 'oauth-setup-token',
            'description': 'Token for OAuth2 application setup',
            'expiring': False
        },
        headers={
            'X-CSRFToken': csrf_token,
            'Content-Type': 'application/json'
        }
    )
    
    if token_response.status_code in [200, 201]:
        token_data = token_response.json()
        return token_data.get('key')
    
    print(f"❌ Could not create API token: {token_response.status_code}")
    print(f"Response: {token_response.text}")
    return None

def create_oauth2_provider(session, base_url, provider_config):
    """Create OAuth2 provider using Authentik API"""
    print(f"🔧 Creating OAuth2 provider: {provider_config['name']}")
    
    # Generate client secret
    client_secret = secrets.token_urlsafe(32)
    
    provider_data = {
        "name": provider_config['name'],
        "authorization_flow": "default-provider-authorization-explicit-consent",
        "client_type": "confidential",
        "client_id": provider_config['client_id'],
        "client_secret": client_secret,
        "redirect_uris": provider_config['redirect_uri'],
        "sub_mode": "hashed_user_id",
        "include_claims_in_id_token": True,
        "issuer_mode": "per_provider"
    }
    
    response = session.post(
        urljoin(base_url, '/api/v3/providers/oauth2/'),
        json=provider_data
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create provider: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    provider = response.json()
    print(f"✅ Provider created: {provider['name']}")
    return provider

def create_application(session, base_url, app_config, provider_pk):
    """Create application using Authentik API"""
    print(f"🔧 Creating application: {app_config['name']}")
    
    app_data = {
        "name": app_config['name'],
        "slug": app_config['slug'],
        "provider": provider_pk,
        "policy_engine_mode": "any",
        "meta_launch_url": app_config.get('launch_url', ''),
        "meta_description": app_config.get('description', ''),
        "meta_icon": app_config.get('icon', '')
    }
    
    response = session.post(
        urljoin(base_url, '/api/v3/core/applications/'),
        json=app_data
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create application: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    application = response.json()
    print(f"✅ Application created: {application['name']}")
    return application

def update_env_file(client_secrets):
    """Update .env file with generated client secrets"""
    print("🔧 Updating .env file with client secrets...")
    
    # Read current .env file
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Update client secret lines
    updated_lines = []
    for line in lines:
        if line.startswith('FASTAPI_OAUTH_CLIENT_SECRET=') and 'fastapi' in client_secrets:
            updated_lines.append(f"FASTAPI_OAUTH_CLIENT_SECRET={client_secrets['fastapi']}\n")
        elif line.startswith('WEBUI_OAUTH_CLIENT_SECRET=') and 'webui' in client_secrets:
            updated_lines.append(f"WEBUI_OAUTH_CLIENT_SECRET={client_secrets['webui']}\n")
        elif line.startswith('N8N_OAUTH_CLIENT_SECRET=') and 'n8n' in client_secrets:
            updated_lines.append(f"N8N_OAUTH_CLIENT_SECRET={client_secrets['n8n']}\n")
        else:
            updated_lines.append(line)
    
    # Write updated .env file
    with open('.env', 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ .env file updated successfully")

def main():
    print("🚀 Setting up OAuth2 applications in Authentik...")
    
    # Load environment
    load_env()
    
    base_url = os.getenv('AUTHENTIK_BASE_URL', 'https://localhost:9443')
    username = os.getenv('AUTHENTIK_BOOTSTRAP_EMAIL', 'admin@localhost')
    password = os.getenv('AUTHENTIK_BOOTSTRAP_PASSWORD', 'change-me-authentik-admin')
    
    # Check if Authentik is accessible
    try:
        response = requests.get(base_url, verify=False, timeout=10)
        if response.status_code not in [200, 302]:
            print(f"❌ Authentik is not accessible at {base_url}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to Authentik: {e}")
        sys.exit(1)
    
    print("✅ Authentik is accessible")
    
    # Authenticate and get API token
    api_token = authenticate_with_credentials(base_url, username, password)
    if not api_token:
        print("❌ Could not authenticate with Authentik")
        sys.exit(1)
    
    print("✅ Authentication successful")
    
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
        print(f"❌ API authentication failed: {test_response.status_code}")
        sys.exit(1)
    
    print("✅ API access confirmed")
    
    # Define applications to create
    applications = [
        {
            'name': 'FastAPI RAG System',
            'slug': 'fastapi-rag',
            'client_id': os.getenv('FASTAPI_OAUTH_CLIENT_ID', 'fastapi-client'),
            'redirect_uri': os.getenv('FASTAPI_OAUTH_REDIRECT_URI', 'http://localhost:8000/api/auth/callback'),
            'launch_url': 'http://localhost:8000',
            'description': 'FastAPI-based RAG system with OAuth2 authentication',
            'key': 'fastapi'
        },
        {
            'name': 'Open WebUI',
            'slug': 'open-webui',
            'client_id': os.getenv('WEBUI_OAUTH_CLIENT_ID', 'webui-client'),
            'redirect_uri': 'http://localhost:3000/auth/callback',
            'launch_url': 'http://localhost:3000',
            'description': 'Open WebUI chat interface',
            'key': 'webui'
        },
        {
            'name': 'n8n Workflow',
            'slug': 'n8n-workflow',
            'client_id': os.getenv('N8N_OAUTH_CLIENT_ID', 'n8n-client'),
            'redirect_uri': 'http://localhost:5678/rest/oauth2-credential/callback',
            'launch_url': 'http://localhost:5678',
            'description': 'n8n workflow automation platform',
            'key': 'n8n'
        }
    ]
    
    # Create applications and collect client secrets
    created_apps = []
    client_secrets = {}
    
    for app_config in applications:
        # Create OAuth2 provider
        provider = create_oauth2_provider(session, base_url, app_config)
        if not provider:
            continue
        
        # Create application
        application = create_application(session, base_url, app_config, provider['pk'])
        if not application:
            continue
        
        created_apps.append({
            'application': application,
            'provider': provider,
            'config': app_config
        })
        
        client_secrets[app_config['key']] = provider['client_secret']
    
    # Update .env file with client secrets
    if client_secrets:
        update_env_file(client_secrets)
    
    # Print summary
    print("\n📋 OAuth2 Applications Summary:")
    print("=" * 60)
    for app in created_apps:
        print(f"Application: {app['application']['name']}")
        print(f"Slug: {app['application']['slug']}")
        print(f"Client ID: {app['provider']['client_id']}")
        print(f"Client Secret: {app['provider']['client_secret']}")
        print(f"Redirect URI: {app['provider']['redirect_uris']}")
        print(f"Launch URL: {app['application']['meta_launch_url']}")
        print("-" * 40)
    
    print(f"\n✅ Successfully created {len(created_apps)} OAuth2 applications")
    print("🔄 Restart your FastAPI service to use the new client secrets")

if __name__ == '__main__':
    main()
