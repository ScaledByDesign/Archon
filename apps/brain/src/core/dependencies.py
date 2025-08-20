"""
FastAPI dependencies for the core module
Provides dependency injection for common services and utilities
"""

from typing import Optional, Dict, Any, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from src.core.database import DatabaseManager, get_database_manager
from src.core.security import verify_session_token
from src.core.exceptions import AuthenticationError, AuthorizationError
from src.config.settings import get_settings


logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user from JWT token or session
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        
    Returns:
        User information if authenticated, None otherwise
        
    Raises:
        AuthenticationError: If token is invalid
    """
    # Try to get user from JWT token first
    if credentials:
        try:
            # This would integrate with your JWT handler
            # For now, we'll use a placeholder
            from src.auth.jwt_handler import verify_jwt_token
            user_info = await verify_jwt_token(credentials.credentials)
            if user_info:
                return user_info
        except Exception as e:
            logger.warning(f"JWT token verification failed: {e}")
    
    # Try to get user from session
    session_token = request.cookies.get("session_token")
    if session_token:
        try:
            settings = get_settings()
            user_info = verify_session_token(session_token, settings.session_secret_key)
            if user_info:
                return user_info
        except Exception as e:
            logger.warning(f"Session token verification failed: {e}")
    
    return None


async def require_authentication(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require user to be authenticated
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        User information
        
    Raises:
        AuthenticationError: If user is not authenticated
    """
    if not current_user:
        raise AuthenticationError(
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user


async def require_admin(
    current_user: Dict[str, Any] = Depends(require_authentication)
) -> Dict[str, Any]:
    """
    Require user to have admin privileges
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
        
    Raises:
        AuthorizationError: If user is not an admin
    """
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and "administrator" not in user_roles:
        raise AuthorizationError(
            detail="Administrator privileges required"
        )
    return current_user


def require_scope(required_scope: str):
    """
    Create a dependency that requires a specific scope
    
    Args:
        required_scope: The scope that is required
        
    Returns:
        Dependency function
    """
    async def scope_dependency(
        current_user: Dict[str, Any] = Depends(require_authentication)
    ) -> Dict[str, Any]:
        user_scopes = current_user.get("scopes", [])
        if required_scope not in user_scopes:
            raise AuthorizationError(
                detail=f"Scope '{required_scope}' required"
            )
        return current_user
    
    return scope_dependency


async def get_request_id(request: Request) -> str:
    """
    Get request ID from request state
    
    Args:
        request: FastAPI request object
        
    Returns:
        Request ID string
    """
    return getattr(request.state, 'request_id', 'unknown')


async def get_user_id(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Optional[str]:
    """
    Get user ID from current user
    
    Args:
        current_user: Current user information
        
    Returns:
        User ID if available, None otherwise
    """
    if current_user:
        return current_user.get("user_id") or current_user.get("sub")
    return None


async def get_logger_with_context(
    request_id: str = Depends(get_request_id),
    user_id: Optional[str] = Depends(get_user_id)
) -> logging.Logger:
    """
    Get logger with request context
    
    Args:
        request_id: Request ID
        user_id: User ID if available
        
    Returns:
        Logger with context
    """
    logger_instance = logging.getLogger("api")
    
    # Add context to logger
    extra = {
        "request_id": request_id,
        "user_id": user_id
    }
    
    return logging.LoggerAdapter(logger_instance, extra)


async def get_database_helper(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> DatabaseManager:
    """
    Get database manager dependency
    
    Args:
        db_manager: Database manager instance
        
    Returns:
        Database manager
    """
    return db_manager


async def validate_api_key(
    request: Request,
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> Optional[Dict[str, Any]]:
    """
    Validate API key from request headers
    
    Args:
        request: FastAPI request object
        db_manager: Database manager
        
    Returns:
        API key information if valid, None otherwise
    """
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    try:
        # Check API key in Redis cache first
        redis_client = db_manager.redis
        api_key_data = await redis_client.get(f"api_key:{api_key}")
        
        if api_key_data:
            import json
            return json.loads(api_key_data)
        
        # If not in cache, check database
        # This would query your API key storage
        # For now, return None
        return None
        
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        return None


def require_api_key():
    """
    Create a dependency that requires a valid API key
    
    Returns:
        Dependency function
    """
    async def api_key_dependency(
        api_key_data: Optional[Dict[str, Any]] = Depends(validate_api_key)
    ) -> Dict[str, Any]:
        if not api_key_data:
            raise AuthenticationError(
                detail="Valid API key required",
                headers={"WWW-Authenticate": "ApiKey"}
            )
        return api_key_data
    
    return api_key_dependency


async def get_rate_limit_key(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> str:
    """
    Get rate limit key for the request
    
    Args:
        request: FastAPI request object
        current_user: Current user if authenticated
        
    Returns:
        Rate limit key
    """
    if current_user:
        user_id = current_user.get("user_id") or current_user.get("sub")
        return f"user:{user_id}"
    
    # Fall back to IP address
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    
    return f"ip:{client_ip}"


async def check_rate_limit(
    rate_limit_key: str = Depends(get_rate_limit_key),
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> bool:
    """
    Check if request is within rate limits
    
    Args:
        rate_limit_key: Rate limit key
        db_manager: Database manager
        
    Returns:
        True if within limits, False otherwise
    """
    try:
        import time
        from src.core.exceptions import RateLimitError
        
        redis_client = db_manager.redis
        current_time = int(time.time())
        window_key = f"rate_limit:{rate_limit_key}:{current_time // 60}"
        
        # Get current count
        current_count = await redis_client.get(window_key)
        current_count = int(current_count) if current_count else 0
        
        # Check limit (60 requests per minute by default)
        rate_limit = 60
        if current_count >= rate_limit:
            raise RateLimitError(
                detail="Rate limit exceeded",
                retry_after=60
            )
        
        # Increment counter
        await redis_client.incr(window_key)
        await redis_client.expire(window_key, 120)  # Keep for 2 minutes
        
        return True
        
    except RateLimitError:
        raise
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        return True  # Allow request if rate limit check fails


# Common dependency combinations
CurrentUser = Annotated[Dict[str, Any], Depends(require_authentication)]
AdminUser = Annotated[Dict[str, Any], Depends(require_admin)]
DatabaseDep = Annotated[DatabaseManager, Depends(get_database_manager)]
LoggerDep = Annotated[logging.LoggerAdapter, Depends(get_logger_with_context)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
