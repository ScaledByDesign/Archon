#!/usr/bin/env python3
"""
Simple OAuth2 Application Creation Script for Authentik
This script creates OAuth2 providers and applications directly using Django ORM
"""

# OAuth2 Providers and Applications Creation
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping
from authentik.core.models import Application
from authentik.flows.models import Flow
import secrets
import string

def generate_client_secret(length=32):
    """Generate a secure random client secret"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_oauth_app(name, client_id, redirect_uris, description=""):
    """Create OAuth2 provider and application"""
    
    # Get the authorization flow
    try:
        auth_flow = Flow.objects.get(slug="default-provider-authorization-explicit-consent")
    except Flow.DoesNotExist:
        auth_flow = Flow.objects.get(slug="default-provider-authorization-implicit-consent")
    
    # Create OAuth2 Provider
    provider, created = OAuth2Provider.objects.get_or_create(
        name=f"{name} OAuth2 Provider",
        defaults={
            'client_id': client_id,
            'client_secret': generate_client_secret(),
            'authorization_flow': auth_flow,
            'redirect_uris': redirect_uris,
            'access_code_validity': 'minutes=1',
            'access_token_validity': 'minutes=5',
            'refresh_token_validity': 'days=30',
            'include_claims_in_id_token': True,
            'issuer_mode': 'per_provider',
        }
    )
    
    if created:
        print(f"✅ Created OAuth2 provider for {name}")
        print(f"   Client ID: {provider.client_id}")
        print(f"   Client Secret: {provider.client_secret}")
    else:
        print(f"ℹ️  OAuth2 provider for {name} already exists")
        print(f"   Client ID: {provider.client_id}")
        print(f"   Client Secret: {provider.client_secret}")
    
    # Create Application
    app, app_created = Application.objects.get_or_create(
        name=name,
        defaults={
            'slug': name.lower().replace(' ', '-'),
            'provider': provider,
            'meta_description': description,
            'open_in_new_tab': False,
        }
    )
    
    if app_created:
        print(f"✅ Created application: {name}")
    else:
        print(f"ℹ️  Application {name} already exists")
    
    return provider, app

def main():
    """Main execution function"""
    print("🚀 Creating OAuth2 applications for Production RAG System...")
    print()
    
    # Create FastAPI Backend Application
    print("📱 Creating FastAPI Backend application...")
    fastapi_provider, fastapi_app = create_oauth_app(
        name="FastAPI Backend",
        client_id="fastapi-client", 
        redirect_uris="https://api.localhost/auth/callback\nhttps://localhost:8000/auth/callback",
        description="RAG System API Backend"
    )
    print()
    
    # Create Chat Interface Application  
    print("📱 Creating Chat Interface application...")
    webui_provider, webui_app = create_oauth_app(
        name="Chat Interface",
        client_id="webui-client",
        redirect_uris="https://chat.localhost/auth/callback\nhttps://localhost:3000/auth/callback", 
        description="RAG System Chat Interface"
    )
    print()
    
    # Create n8n Workflow Application
    print("📱 Creating Workflow Automation application...")
    n8n_provider, n8n_app = create_oauth_app(
        name="Workflow Automation", 
        client_id="n8n-client",
        redirect_uris="https://n8n.localhost/rest/oauth2-credential/callback\nhttps://localhost:5678/rest/oauth2-credential/callback",
        description="RAG System Workflow Automation"
    )
    print()
    
    print("🎉 OAuth2 application creation completed!")
    print()
    print("📄 Client Secrets Summary:")
    print("=" * 50)
    print(f"FASTAPI_OAUTH_CLIENT_SECRET={fastapi_provider.client_secret}")
    print(f"WEBUI_OAUTH_CLIENT_SECRET={webui_provider.client_secret}")
    print(f"N8N_OAUTH_CLIENT_SECRET={n8n_provider.client_secret}")
    print()
    print("🔍 Verify the setup in Authentik admin:")
    print("  - Applications: https://localhost:9443/if/admin/#/core/applications")
    print("  - Providers: https://localhost:9443/if/admin/#/core/providers")

if __name__ == "__main__":
    main()
