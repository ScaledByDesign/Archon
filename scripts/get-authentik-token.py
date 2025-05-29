#!/usr/bin/env python3
"""
Get Authentik API Token
This script helps you get an API token from Authentik for automation.
"""

import requests
import json
import sys
import os
from getpass import getpass

def get_api_token_interactive():
    """Get API token through interactive login."""
    
    AUTHENTIK_URL = os.getenv('AUTHENTIK_URL', 'https://localhost:9443')
    
    print(" Authentik API Token Generator")
    print("=" * 40)
    print(f"Authentik URL: {AUTHENTIK_URL}")
    print()
    
    # Get credentials from environment or interactive input
    username = os.getenv('AUTHENTIK_USERNAME')
    password = os.getenv('AUTHENTIK_PASSWORD')
    
    if not username:
        try:
            username = input("Username (default: akadmin): ").strip() or "akadmin"
        except (EOFError, KeyboardInterrupt):
            # Non-interactive mode, use default
            username = "akadmin"
            print(f"Using default username: {username}")
    
    if not password:
        try:
            password = getpass("Password: ")
        except (EOFError, KeyboardInterrupt):
            # Try to get from .env file
            env_file = '/Users/nova/Sites/zoi/.env'
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('AUTHENTIK_BOOTSTRAP_PASSWORD='):
                            password = line.split('=', 1)[1].strip()
                            print(f"Using password from .env file")
                            break
            
            if not password:
                print(" Password is required")
                return None
    
    if not password:
        print(" Password is required")
        return None
    
    session = requests.Session()
    session.verify = False
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        # Step 1: Get login page to extract CSRF token
        print(" Getting login page...")
        login_url = f"{AUTHENTIK_URL}/if/flow/default-authentication-flow/"
        response = session.get(login_url)
        response.raise_for_status()
        
        # Extract CSRF token from response
        csrf_token = None
        for line in response.text.split('\n'):
            if 'csrfmiddlewaretoken' in line and 'value=' in line:
                start = line.find('value="') + 8
                end = line.find('"', start)
                csrf_token = line[start:end]
                break
        
        if not csrf_token:
            print(" Could not extract CSRF token")
            return None
        
        print(f" CSRF token obtained")
        
        # Step 2: Perform login
        print(" Logging in...")
        login_data = {
            'csrfmiddlewaretoken': csrf_token,
            'uid_field': username,
            'password': password,
        }
        
        response = session.post(login_url, data=login_data, allow_redirects=True)
        response.raise_for_status()
        
        # Check if login was successful
        if 'if/admin' in response.url or response.url.endswith('/'):
            print(" Login successful")
        else:
            print(" Login failed - check credentials")
            return None
        
        # Step 3: Create API token
        print(" Creating API token...")
        token_url = f"{AUTHENTIK_URL}/api/v3/core/tokens/"
        
        # Get CSRF token for API request
        admin_url = f"{AUTHENTIK_URL}/if/admin/"
        response = session.get(admin_url)
        
        csrf_token = None
        for cookie in session.cookies:
            if cookie.name == 'csrftoken':
                csrf_token = cookie.value
                break
        
        if not csrf_token:
            print(" Could not get CSRF token for API")
            return None
        
        # Create token
        token_data = {
            "identifier": "automation-token",
            "description": "API token for OAuth2 automation",
            "expires": None,  # No expiration
            "intent": "api"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token,
            'Referer': admin_url
        }
        
        response = session.post(token_url, json=token_data, headers=headers)
        
        if response.status_code == 201:
            token_info = response.json()
            api_token = token_info.get('key')
            print(f" API token created successfully")
            print(f"   Token: {api_token}")
            print(f"   Identifier: {token_info.get('identifier')}")
            
            # Save to environment file
            env_file = '/Users/nova/Sites/zoi/.env'
            if os.path.exists(env_file):
                print(f"\n Updating .env file...")
                
                # Read current .env content
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                
                # Update or add the API token
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('AUTHENTIK_API_TOKEN='):
                        lines[i] = f'AUTHENTIK_API_TOKEN={api_token}\n'
                        updated = True
                        break
                
                if not updated:
                    lines.append(f'AUTHENTIK_API_TOKEN={api_token}\n')
                
                # Write back to file
                with open(env_file, 'w') as f:
                    f.writelines(lines)
                
                print(f" Updated .env file with API token")
            
            return api_token
        else:
            print(f" Failed to create token: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f" Error: {e}")
        return None

def main():
    """Main function."""
    
    # Check if token already exists
    existing_token = os.getenv('AUTHENTIK_API_TOKEN')
    if existing_token:
        print(f" API token already exists in environment: {existing_token[:10]}...")
        print(f"   Use this token or delete AUTHENTIK_API_TOKEN from .env to create a new one")
        return 0
    
    token = get_api_token_interactive()
    if token:
        print(f"\n Token ready! You can now run:")
        print(f"   python scripts/auto-create-oauth2-app.py")
        return 0
    else:
        print(f"\n Failed to get API token")
        return 1

if __name__ == "__main__":
    sys.exit(main())
