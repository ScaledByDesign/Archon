"""
Custom middleware for the FastAPI backend
Provides request/response processing, logging, and monitoring
"""

import time
import uuid
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException
import logging

from src.core.logging import log_request
from src.core.exceptions import RateLimitError, InternalServerError


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""
    
    def __init__(self, app, logger: Optional[logging.Logger] = None):
        super().__init__(app)
        self.logger = logger or logging.getLogger("api.requests")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log information"""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Extract user information if available
        user_id = getattr(request.state, 'user_id', None)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request
            log_request(
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=user_id,
                request_id=request_id
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine status code
            status_code = getattr(e, 'status_code', 500)
            
            # Log error
            self.logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "user_id": user_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            
            # Re-raise the exception
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware for adding security headers to responses"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            ),
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.request_counts = {}  # In production, use Redis
        self.logger = logging.getLogger("api.ratelimit")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits before processing request"""
        # Get client identifier (IP address or user ID)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if self._is_rate_limited(client_id):
            self.logger.warning(
                "Rate limit exceeded",
                extra={
                    "client_id": client_id,
                    "path": str(request.url.path),
                    "method": request.method
                }
            )
            raise RateLimitError(
                detail="Rate limit exceeded. Please try again later.",
                retry_after=60
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from request state
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        current_time = int(time.time())
        minute_key = f"{client_id}:{current_time // 60}"
        
        # Get current request count for this minute
        current_count = self.request_counts.get(minute_key, 0)
        
        # Check if rate limit exceeded
        if current_count >= self.requests_per_minute:
            return True
        
        # Increment request count
        self.request_counts[minute_key] = current_count + 1
        
        # Clean up old entries (simple cleanup, in production use Redis with TTL)
        self._cleanup_old_entries(current_time)
        
        return False
    
    def _get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        current_time = int(time.time())
        minute_key = f"{client_id}:{current_time // 60}"
        current_count = self.request_counts.get(minute_key, 0)
        return max(0, self.requests_per_minute - current_count)
    
    def _cleanup_old_entries(self, current_time: int) -> None:
        """Remove old rate limit entries"""
        current_minute = current_time // 60
        keys_to_remove = []
        
        for key in self.request_counts:
            if ":" in key:
                try:
                    minute = int(key.split(":")[-1])
                    if minute < current_minute - 1:  # Keep last 2 minutes
                        keys_to_remove.append(key)
                except (ValueError, IndexError):
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.request_counts[key]


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling uncaught exceptions"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("api.errors")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle uncaught exceptions"""
        try:
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTP exceptions (they're handled by FastAPI)
            raise
        except Exception as e:
            # Log unexpected errors
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            self.logger.exception(
                "Unhandled exception in request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": str(request.url.path),
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
            
            # Return generic error response
            raise InternalServerError(
                detail="An unexpected error occurred",
                error_id=request_id
            )


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for handling health check requests"""
    
    def __init__(self, app, health_check_path: str = "/health"):
        super().__init__(app)
        self.health_check_path = health_check_path
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle health check requests"""
        # Skip logging and other middleware for health checks
        if request.url.path == self.health_check_path:
            return await call_next(request)
        
        return await call_next(request)
