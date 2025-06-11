"""
OAuth2 client implementation for Authentik integration.
"""

import os
import logging
import httpx
import jwt
from typing import Dict, Any, Optional
from urllib.parse import urlencode, parse_qs, urlparse
from .jwt_handler import JWTHandler, validate_jwt_token

logger = logging.getLogger(__name__)


class AuthentikOAuth2Client:
    """OAuth2 client for Authentik integration."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authentik_base_url: str,
        redirect_uri: str,
        scopes: Optional[list] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authentik_base_url = authentik_base_url.rstrip('/')
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ['openid', 'email', 'profile']
        
        # OAuth2 endpoints
        self.authorize_url = f"{self.authentik_base_url}/application/o/authorize/"
        self.token_url = f"{self.authentik_base_url}/application/o/token/"
        self.userinfo_url = f"{self.authentik_base_url}/application/o/userinfo/"
        self.jwks_url = f"{self.authentik_base_url}/application/o/default/jwks/"
        
        # HTTP client with SSL verification disabled for development
        self.http_client = httpx.AsyncClient(verify=False)
        
        # Initialize JWT handler
        self.jwt_handler = JWTHandler(self.authentik_base_url)
        
        logger.info(f"Initialized OAuth2 client for {self.authentik_base_url}")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate authorization URL for OAuth2 flow."""
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
        }
        
        if state:
            params['state'] = state
            
        auth_url = f"{self.authorize_url}?{urlencode(params)}"
        logger.debug(f"Generated authorization URL: {auth_url}")
        return auth_url
    
    async def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        try:
            data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': self.redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
            
            response = await self.http_client.post(
                self.token_url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                raise Exception(f"Token exchange failed: {response.status_code}")
            
            tokens = response.json()
            logger.info("Successfully exchanged authorization code for tokens")
            return tokens
            
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            raise
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        try:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            }
            
            response = await self.http_client.post(
                self.token_url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                raise Exception(f"Token refresh failed: {response.status_code}")
            
            tokens = response.json()
            logger.info("Successfully refreshed access token")
            return tokens
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            raise
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token."""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = await self.http_client.get(
                self.userinfo_url,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"User info request failed: {response.status_code} - {response.text}")
                raise Exception(f"User info request failed: {response.status_code}")
            
            user_info = response.json()
            logger.info(f"Retrieved user info for user: {user_info.get('sub', 'unknown')}")
            return user_info
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise
    
    async def validate_token(self, token: str, token_type: str = 'access') -> Dict[str, Any]:
        """Validate JWT token using proper JWT handler with signature verification."""
        try:
            # Use the comprehensive JWT handler for validation
            claims = await validate_jwt_token(token, token_type)
            
            logger.info(f"Token validated for user: {claims.get('sub', 'unknown')}")
            return claims
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise
    
    async def validate_access_token(self, token: str) -> Dict[str, Any]:
        """Validate access token specifically."""
        return await self.validate_token(token, 'access')
    
    async def validate_id_token(self, token: str) -> Dict[str, Any]:
        """Validate ID token specifically."""
        return await self.validate_token(token, 'id')
    
    async def get_user_from_token(self, access_token: str) -> Dict[str, Any]:
        """Get user information from validated access token."""
        try:
            # First validate the token
            claims = await self.validate_access_token(access_token)
            
            # Extract user info from token claims
            user_info = {
                'sub': claims.get('sub'),
                'email': claims.get('email'),
                'name': claims.get('name'),
                'preferred_username': claims.get('preferred_username'),
                'groups': claims.get('groups', []),
                'scope': claims.get('scope', '').split(),
                'auth_time': claims.get('auth_time'),
                'session_state': claims.get('session_state')
            }
            
            # Optionally fetch additional user info from userinfo endpoint
            # This provides more detailed user information
            try:
                additional_info = await self.get_user_info(access_token)
                user_info.update(additional_info)
            except Exception as e:
                logger.warning(f"Could not fetch additional user info: {e}")
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error getting user from token: {e}")
            raise
    
    async def close(self):
        """Close HTTP client and JWT handler."""
        await self.http_client.aclose()
        await self.jwt_handler.close()


class OAuth2Manager:
    """Manager for OAuth2 operations."""
    
    def __init__(self):
        self.client: Optional[AuthentikOAuth2Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OAuth2 client from environment variables."""
        try:
            client_id = os.getenv('FASTAPI_OAUTH_CLIENT_ID', 'fastapi-client')
            client_secret = os.getenv('FASTAPI_OAUTH_CLIENT_SECRET')
            authentik_url = os.getenv('AUTHENTIK_URL', 'https://zoi.local:9443')
            redirect_uri = os.getenv('FASTAPI_OAUTH_REDIRECT_URI', 'http://zoi.local:8000/auth/callback')
            
            if not client_secret:
                logger.warning("OAuth2 client secret not configured")
                return
            
            self.client = AuthentikOAuth2Client(
                client_id=client_id,
                client_secret=client_secret,
                authentik_base_url=authentik_url,
                redirect_uri=redirect_uri,
                scopes=['openid', 'email', 'profile', 'rag:api']
            )
            
            logger.info("OAuth2 manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OAuth2 client: {e}")
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get authorization URL for OAuth2 flow."""
        if not self.client:
            raise Exception("OAuth2 client not initialized")
        return self.client.get_authorization_url(state)
    
    async def handle_callback(self, authorization_code: str) -> Dict[str, Any]:
        """Handle OAuth2 callback and return user info."""
        if not self.client:
            raise Exception("OAuth2 client not initialized")
        
        # Exchange code for tokens
        tokens = await self.client.exchange_code_for_tokens(authorization_code)
        
        # Get user info
        user_info = await self.client.get_user_info(tokens['access_token'])
        
        return {
            'tokens': tokens,
            'user': user_info
        }
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate access token."""
        if not self.client:
            raise Exception("OAuth2 client not initialized")
        return await self.client.validate_access_token(token)
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token."""
        if not self.client:
            raise Exception("OAuth2 client not initialized")
        return await self.client.refresh_access_token(refresh_token)
    
    def is_configured(self) -> bool:
        """Check if OAuth2 is properly configured."""
        return self.client is not None
    
    async def close(self):
        """Close OAuth2 client."""
        if self.client:
            await self.client.close()


# Global OAuth2 manager instance
oauth2_manager = OAuth2Manager()
