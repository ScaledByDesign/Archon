"""
JWT Authentication Middleware for FastAPI

This module provides middleware for JWT token validation and security headers.
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Optional, Dict, Any, List
import logging
import time
from .jwt_handler import get_jwt_handler, JWTValidationError
from .dependencies import SecurityHeaders

logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT token validation and user context injection
    
    This middleware automatically validates JWT tokens for protected routes
    and injects user context into the request state.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        protected_paths: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None,
        add_security_headers: bool = True
    ):
        super().__init__(app)
        self.protected_paths = protected_paths or ["/api/"]
        self.excluded_paths = excluded_paths or [
            "/api/auth/login",
            "/api/auth/callback", 
            "/api/auth/health",
            "/api/auth/status",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics"
        ]
        self.add_security_headers = add_security_headers
    
    def _is_protected_path(self, path: str) -> bool:
        """Check if path requires authentication"""
        # Check excluded paths first
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return False
        
        # Check if path matches protected patterns
        for protected in self.protected_paths:
            if path.startswith(protected):
                return True
        
        return False
    
    def _extract_token_from_request(self, request: Request) -> Optional[str]:
        """Extract JWT token from request headers or cookies"""
        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1]
        
        # Try session cookie
        session_token = request.cookies.get("session_token")
        if session_token:
            return session_token
        
        # Try access token from session (for session-based auth)
        if hasattr(request, 'session'):
            access_token = request.session.get("access_token")
            if access_token:
                return access_token
        
        return None
    
    async def dispatch(self, request: Request, call_next):
        """Process request through JWT authentication"""
        start_time = time.time()
        
        # Add security headers to response
        response = await call_next(request)
        
        if self.add_security_headers:
            for header, value in SecurityHeaders.get_security_headers().items():
                response.headers[header] = value
        
        # Add timing header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class JWTValidationMiddleware(BaseHTTPMiddleware):
    """
    Strict JWT validation middleware for API routes
    
    This middleware enforces JWT validation on protected routes and
    returns 401 for invalid or missing tokens.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        protected_paths: Optional[List[str]] = None,
        excluded_paths: Optional[List[str]] = None,
        require_valid_token: bool = True
    ):
        super().__init__(app)
        self.protected_paths = protected_paths or ["/api/"]
        self.excluded_paths = excluded_paths or [
            "/api/auth/login",
            "/api/auth/callback",
            "/api/auth/health",
            "/api/auth/status",
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/metrics"
        ]
        self.require_valid_token = require_valid_token
    
    def _is_protected_path(self, path: str) -> bool:
        """Check if path requires authentication"""
        # Check excluded paths first
        for excluded in self.excluded_paths:
            if path.startswith(excluded):
                return False
        
        # Check if path matches protected patterns
        for protected in self.protected_paths:
            if path.startswith(protected):
                return True
        
        return False
    
    def _extract_token_from_request(self, request: Request) -> Optional[str]:
        """Extract JWT token from request"""
        # Try Authorization header first
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ", 1)[1]
        
        # Try session for web-based auth
        if hasattr(request, 'session'):
            access_token = request.session.get("access_token")
            if access_token:
                return access_token
        
        return None
    
    async def dispatch(self, request: Request, call_next):
        """Validate JWT token for protected routes"""
        path = request.url.path
        
        # Skip validation for non-protected paths
        if not self._is_protected_path(path):
            return await call_next(request)
        
        # Extract token
        token = self._extract_token_from_request(request)
        
        if not token and self.require_valid_token:
            logger.warning(f"No token provided for protected path: {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication required",
                    "detail": "No valid token provided",
                    "path": path
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if token:
            try:
                # Validate token
                jwt_handler = await get_jwt_handler()
                claims = await jwt_handler.validate_access_token(token)
                
                # Inject user context into request state
                request.state.user = {
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
                request.state.authenticated = True
                
                logger.debug(f"Token validated for user: {claims.get('sub')} on path: {path}")
                
            except JWTValidationError as e:
                logger.error(f"JWT validation failed for path {path}: {e}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "Invalid token",
                        "detail": str(e),
                        "path": path
                    },
                    headers={"WWW-Authenticate": "Bearer"}
                )
            except Exception as e:
                logger.error(f"Unexpected error during token validation: {e}")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "error": "Authentication error",
                        "detail": "Internal server error during authentication",
                        "path": path
                    }
                )
        else:
            # No token but path is protected and token not required
            request.state.user = None
            request.state.authenticated = False
        
        return await call_next(request)


class CORSAndSecurityMiddleware(BaseHTTPMiddleware):
    """
    CORS and Security Headers Middleware
    
    Handles CORS for OAuth2 flows and adds security headers.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: Optional[List[str]] = None,
        allowed_methods: Optional[List[str]] = None,
        allowed_headers: Optional[List[str]] = None,
        expose_headers: Optional[List[str]] = None,
        allow_credentials: bool = True,
        max_age: int = 86400
    ):
        super().__init__(app)
        self.allowed_origins = allowed_origins or [
            "http://zoi.local:3000",
            "http://zoi.local:8000", 
            "http://auth.zoi.local",
            "https://zoi.local"
        ]
        self.allowed_methods = allowed_methods or [
            "GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"
        ]
        self.allowed_headers = allowed_headers or [
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "Cache-Control",
            "X-Requested-With"
        ]
        self.expose_headers = expose_headers or [
            "X-Process-Time",
            "X-Request-ID"
        ]
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    def _is_cors_preflight(self, request: Request) -> bool:
        """Check if request is a CORS preflight request"""
        return (
            request.method == "OPTIONS" and
            "origin" in request.headers and
            "access-control-request-method" in request.headers
        )
    
    def _get_origin(self, request: Request) -> Optional[str]:
        """Get origin from request headers"""
        return request.headers.get("origin")
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed"""
        if "*" in self.allowed_origins:
            return True
        return origin in self.allowed_origins
    
    async def dispatch(self, request: Request, call_next):
        """Handle CORS and security headers"""
        origin = self._get_origin(request)
        
        # Handle CORS preflight
        if self._is_cors_preflight(request):
            if origin and self._is_origin_allowed(origin):
                response = Response()
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
                response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
                response.headers["Access-Control-Max-Age"] = str(self.max_age)
                
                if self.allow_credentials:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                
                return response
            else:
                return Response(status_code=403)
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers to response
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            if self.expose_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(self.expose_headers)
        
        # Add security headers
        security_headers = SecurityHeaders.get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware for authentication and security monitoring
    """
    
    def __init__(self, app: ASGIApp, log_body: bool = False):
        super().__init__(app)
        self.log_body = log_body
    
    async def dispatch(self, request: Request, call_next):
        """Log request details for security monitoring"""
        start_time = time.time()
        
        # Extract request info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        path = request.url.path
        
        # Check if user is authenticated
        user_id = "anonymous"
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.get('sub', 'unknown')
        
        # Log request
        logger.info(
            f"Request: {method} {path} - IP: {client_ip} - User: {user_id} - UA: {user_agent}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} - {method} {path} - "
                f"Time: {process_time:.3f}s - User: {user_id}"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {method} {path} - Time: {process_time:.3f}s - "
                f"User: {user_id} - Error: {str(e)}"
            )
            raise
