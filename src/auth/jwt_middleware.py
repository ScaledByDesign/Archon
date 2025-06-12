"""
JWT Middleware for FastAPI

This module provides JWT authentication middleware for the Production RAG System,
integrating with Authentik SSO and providing comprehensive token validation.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from .jwt_handler import JWTHandler

logger = logging.getLogger(__name__)

# Initialize JWT handler
AUTHENTIK_BASE_URL = os.getenv('AUTHENTIK_BASE_URL', 'http://auth.zoi.local')
jwt_handler = JWTHandler(AUTHENTIK_BASE_URL)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


class JWTMiddleware:
    """JWT Authentication Middleware"""
    
    def __init__(self, required_scopes: Optional[List[str]] = None):
        self.required_scopes = required_scopes or []
    
    async def __call__(self, 
                      request: Request,
                      credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
                      ) -> Dict[str, Any]:
        """
        Validate JWT token and return user claims
        
        Args:
            request: FastAPI request object
            credentials: HTTP Bearer credentials
            
        Returns:
            Dict containing user claims and token info
            
        Raises:
            HTTPException: If authentication fails
        """
        
        # Check for token in Authorization header
        if not credentials:
            # Check for token in cookies as fallback
            token = request.cookies.get('access_token')
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authentication token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        else:
            token = credentials.credentials
        
        try:
            # Validate the access token
            claims = await jwt_handler.validate_access_token(token)
            
            # Check required scopes
            if self.required_scopes:
                token_scopes = claims.get('scope', '').split()
                if not any(scope in token_scopes for scope in self.required_scopes):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions. Required scopes: {self.required_scopes}",
                    )
            
            # Add request context
            user_info = {
                'user_id': claims.get('sub'),
                'username': claims.get('preferred_username'),
                'email': claims.get('email'),
                'scopes': claims.get('scope', '').split(),
                'groups': claims.get('groups', []),
                'session_id': claims.get('sid'),
                'auth_time': claims.get('auth_time'),
                'token_type': 'access',
                'claims': claims
            }
            
            logger.info(f"Authenticated user: {user_info['username']} ({user_info['user_id']})")
            return user_info
            
        except Exception as e:
            logger.error(f"JWT validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )


class OptionalJWTMiddleware:
    """Optional JWT Authentication Middleware (doesn't require authentication)"""
    
    async def __call__(self, 
                      request: Request,
                      credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
                      ) -> Optional[Dict[str, Any]]:
        """
        Optionally validate JWT token if present
        
        Returns:
            Dict containing user claims if token is valid, None otherwise
        """
        
        # Check for token
        token = None
        if credentials:
            token = credentials.credentials
        else:
            token = request.cookies.get('access_token')
        
        if not token:
            return None
        
        try:
            claims = await jwt_handler.validate_access_token(token)
            
            user_info = {
                'user_id': claims.get('sub'),
                'username': claims.get('preferred_username'),
                'email': claims.get('email'),
                'scopes': claims.get('scope', '').split(),
                'groups': claims.get('groups', []),
                'session_id': claims.get('sid'),
                'auth_time': claims.get('auth_time'),
                'token_type': 'access',
                'claims': claims
            }
            
            logger.debug(f"Optional authentication successful for: {user_info['username']}")
            return user_info
            
        except Exception as e:
            logger.warning(f"Optional JWT validation failed: {e}")
            return None


# Convenience dependency functions
async def require_auth(user: Dict[str, Any] = Depends(JWTMiddleware())) -> Dict[str, Any]:
    """Require authentication for endpoint"""
    return user


async def require_scopes(*scopes: str):
    """Require specific scopes for endpoint"""
    def dependency(user: Dict[str, Any] = Depends(JWTMiddleware(required_scopes=list(scopes)))) -> Dict[str, Any]:
        return user
    return dependency


async def optional_auth(user: Optional[Dict[str, Any]] = Depends(OptionalJWTMiddleware())) -> Optional[Dict[str, Any]]:
    """Optional authentication for endpoint"""
    return user


# Scope-specific dependencies
async def require_admin(user: Dict[str, Any] = Depends(JWTMiddleware(required_scopes=['admin']))) -> Dict[str, Any]:
    """Require admin scope"""
    return user


async def require_api_access(user: Dict[str, Any] = Depends(JWTMiddleware(required_scopes=['rag:api']))) -> Dict[str, Any]:
    """Require API access scope"""
    return user


async def require_search_access(user: Dict[str, Any] = Depends(JWTMiddleware(required_scopes=['rag:search']))) -> Dict[str, Any]:
    """Require search access scope"""
    return user


async def require_write_access(user: Dict[str, Any] = Depends(JWTMiddleware(required_scopes=['rag:write']))) -> Dict[str, Any]:
    """Require write access scope"""
    return user


class TokenInfo:
    """Token information utility class"""
    
    @staticmethod
    def extract_user_id(user: Dict[str, Any]) -> str:
        """Extract user ID from user info"""
        return user.get('user_id', '')
    
    @staticmethod
    def extract_username(user: Dict[str, Any]) -> str:
        """Extract username from user info"""
        return user.get('username', '')
    
    @staticmethod
    def extract_email(user: Dict[str, Any]) -> str:
        """Extract email from user info"""
        return user.get('email', '')
    
    @staticmethod
    def has_scope(user: Dict[str, Any], scope: str) -> bool:
        """Check if user has specific scope"""
        return scope in user.get('scopes', [])
    
    @staticmethod
    def has_group(user: Dict[str, Any], group: str) -> bool:
        """Check if user is in specific group"""
        return group in user.get('groups', [])
    
    @staticmethod
    def is_admin(user: Dict[str, Any]) -> bool:
        """Check if user has admin privileges"""
        return TokenInfo.has_scope(user, 'admin') or TokenInfo.has_group(user, 'admins')


# Health check for JWT system
async def jwt_health_check() -> Dict[str, Any]:
    """Health check for JWT authentication system"""
    try:
        # Test JWKS endpoint connectivity
        jwks = await jwt_handler.jwks_manager.get_jwks()
        key_count = len(jwks.get('keys', []))
        
        return {
            'status': 'healthy',
            'jwks_url': jwt_handler.jwks_url,
            'key_count': key_count,
            'algorithm': jwt_handler.security_config.algorithm,
            'issuer': jwt_handler.security_config.issuer,
            'audience': jwt_handler.security_config.audience
        }
    except Exception as e:
        logger.error(f"JWT health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'jwks_url': jwt_handler.jwks_url
        }


# Cleanup function
async def cleanup_jwt_handler():
    """Cleanup JWT handler resources"""
    try:
        await jwt_handler.jwks_manager.close()
        logger.info("JWT handler cleanup completed")
    except Exception as e:
        logger.error(f"JWT handler cleanup failed: {e}")
