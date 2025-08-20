"""
FastAPI Dependencies for JWT Authentication

This module provides FastAPI dependencies for JWT token validation and user authentication.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional, List
import logging
from .jwt_handler import get_jwt_handler, JWTHandler
from .oauth_client import OAuth2Manager

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


async def get_oauth_manager() -> OAuth2Manager:
    """Dependency to get OAuth2 manager"""
    return OAuth2Manager()


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token (optional - returns None if no token or invalid)
    
    This dependency doesn't raise exceptions, making it suitable for endpoints
    that work with both authenticated and unauthenticated users.
    """
    if not credentials:
        return None
    
    try:
        # Validate access token
        claims = await jwt_handler.validate_access_token(credentials.credentials)
        
        # Return user information
        return {
            'sub': claims.get('sub'),
            'email': claims.get('email'),
            'name': claims.get('name'),
            'preferred_username': claims.get('preferred_username'),
            'groups': claims.get('groups', []),
            'scope': claims.get('scope', '').split(),
            'auth_time': claims.get('auth_time'),
            'session_state': claims.get('session_state'),
            'raw_claims': claims
        }
        
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> Dict[str, Any]:
    """
    Get current user from JWT token (required)
    
    This dependency raises HTTP 401 if no valid token is provided.
    """
    if not credentials:
        raise AuthenticationError("Authorization header required")
    
    try:
        # Validate access token
        claims = await jwt_handler.validate_access_token(credentials.credentials)
        
        # Return user information
        return {
            'sub': claims.get('sub'),
            'email': claims.get('email'),
            'name': claims.get('name'),
            'preferred_username': claims.get('preferred_username'),
            'groups': claims.get('groups', []),
            'scope': claims.get('scope', '').split(),
            'auth_time': claims.get('auth_time'),
            'session_state': claims.get('session_state'),
            'raw_claims': claims
        }
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise AuthenticationError(f"Invalid token: {str(e)}")


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user and verify admin privileges
    
    This dependency requires the user to be authenticated and have admin privileges.
    """
    # Check if user has admin group or scope
    groups = current_user.get('groups', [])
    scopes = current_user.get('scope', [])
    
    is_admin = (
        'authentik Admins' in groups or
        'admin' in groups or
        'rag:admin' in scopes or
        'admin' in scopes
    )
    
    if not is_admin:
        logger.warning(f"User {current_user.get('sub')} attempted admin access without privileges")
        raise AuthorizationError("Admin privileges required")
    
    return current_user


def require_scopes(*required_scopes: str):
    """
    Create a dependency that requires specific OAuth2 scopes
    
    Usage:
        @app.get("/api/protected")
        async def protected_endpoint(user: dict = Depends(require_scopes("rag:api", "read"))):
            return {"message": "Access granted"}
    """
    async def check_scopes(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_scopes = set(current_user.get('scope', []))
        required_scopes_set = set(required_scopes)
        
        if not required_scopes_set.issubset(user_scopes):
            missing_scopes = required_scopes_set - user_scopes
            logger.warning(
                f"User {current_user.get('sub')} missing required scopes: {missing_scopes}"
            )
            raise AuthorizationError(
                f"Required scopes missing: {', '.join(missing_scopes)}"
            )
        
        return current_user
    
    return check_scopes


def require_groups(*required_groups: str):
    """
    Create a dependency that requires specific user groups
    
    Usage:
        @app.get("/api/admin")
        async def admin_endpoint(user: dict = Depends(require_groups("authentik Admins"))):
            return {"message": "Admin access granted"}
    """
    async def check_groups(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_groups = set(current_user.get('groups', []))
        required_groups_set = set(required_groups)
        
        if not required_groups_set.intersection(user_groups):
            logger.warning(
                f"User {current_user.get('sub')} not in required groups: {required_groups}"
            )
            raise AuthorizationError(
                f"Required group membership: {', '.join(required_groups)}"
            )
        
        return current_user
    
    return check_groups


async def validate_session_token(
    request: Request,
    jwt_handler: JWTHandler = Depends(get_jwt_handler)
) -> Optional[Dict[str, Any]]:
    """
    Validate session token from cookies or session storage
    
    This is useful for web-based authentication flows.
    """
    # Try to get token from session cookie
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None
    
    try:
        claims = await jwt_handler.validate_access_token(session_token)
        return {
            'sub': claims.get('sub'),
            'email': claims.get('email'),
            'name': claims.get('name'),
            'preferred_username': claims.get('preferred_username'),
            'groups': claims.get('groups', []),
            'scope': claims.get('scope', '').split(),
            'raw_claims': claims
        }
    except Exception as e:
        logger.warning(f"Session token validation failed: {e}")
        return None


class SecurityHeaders:
    """Security headers for JWT-protected endpoints"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }


# Rate limiting for authentication endpoints
class AuthRateLimit:
    """Rate limiting for authentication-related endpoints"""
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self._attempts = {}  # In production, use Redis or similar
    
    async def check_rate_limit(self, identifier: str) -> bool:
        """Check if rate limit is exceeded for given identifier"""
        # Simple in-memory rate limiting (use Redis in production)
        import time
        now = time.time()
        window_start = now - (self.window_minutes * 60)
        
        if identifier not in self._attempts:
            self._attempts[identifier] = []
        
        # Clean old attempts
        self._attempts[identifier] = [
            attempt for attempt in self._attempts[identifier]
            if attempt > window_start
        ]
        
        # Check if limit exceeded
        if len(self._attempts[identifier]) >= self.max_attempts:
            return False
        
        # Record this attempt
        self._attempts[identifier].append(now)
        return True


# Global rate limiter instance
auth_rate_limiter = AuthRateLimit()


async def check_auth_rate_limit(request: Request) -> bool:
    """Dependency to check authentication rate limiting"""
    client_ip = request.client.host if request.client else "unknown"
    
    if not await auth_rate_limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later."
        )
    
    return True
