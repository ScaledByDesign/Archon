"""
FastAPI middleware for Langfuse tracing
Automatically traces all API requests with timing and metadata
"""

import time
import logging
from typing import Callable, Dict, Any, Optional
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .langfuse_client import langfuse_tracer

logger = logging.getLogger(__name__)


class LangfuseMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for Langfuse request tracing
    Traces all API requests with timing, status codes, and endpoint information
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        exclude_paths: Optional[list[str]] = None,
        include_request_body: bool = False,
        include_response_body: bool = False,
        include_headers: bool = False,
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/favicon.ico"]
        self.include_request_body = include_request_body
        self.include_response_body = include_response_body
        self.include_headers = include_headers
        logger.info("Langfuse middleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip tracing for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Skip if Langfuse is disabled
        if not langfuse_tracer.is_enabled:
            return await call_next(request)
        
        trace_id = str(uuid4())
        request_id = str(uuid4())
        start_time = time.time()
        
        # Extract user ID from auth header or session if available
        user_id = None
        try:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This is just a placeholder - in a real app you would decode the JWT
                # and extract the user ID from the claims
                user_id = "auth_user"
        except Exception as e:
            logger.warning(f"Error extracting user ID: {e}")
        
        # Create request metadata
        metadata = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "client_host": request.client.host if request.client else None,
            "query_params": dict(request.query_params),
        }
        
        # Optionally include headers
        if self.include_headers:
            metadata["headers"] = dict(request.headers)
        
        # Optionally include request body
        if self.include_request_body:
            try:
                body = await request.body()
                if len(body) > 0:
                    try:
                        # Try to parse as JSON, fall back to string
                        metadata["body"] = await request.json()
                    except:
                        # Limit body size to avoid excessive logging
                        body_str = body.decode("utf-8", errors="replace")
                        if len(body_str) > 1000:
                            body_str = body_str[:1000] + "... [truncated]"
                        metadata["body"] = body_str
            except Exception as e:
                logger.warning(f"Error capturing request body: {e}")
        
        # Create Langfuse trace
        trace = langfuse_tracer.create_trace(
            name=f"{request.method} {request.url.path}",
            user_id=user_id,
            metadata=metadata,
            tags=["api", request.method.lower(), request.url.path]
        )
        
        # Create span for the request
        if trace:
            trace_id = trace.id
        
        # Store trace ID in request state for use in route handlers
        request.state.langfuse_trace_id = trace_id
        
        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Add response metadata
            response_metadata = {
                "status_code": status_code,
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            }
            
            # Optionally capture response body
            if self.include_response_body and hasattr(response, "body"):
                try:
                    response_body = response.body.decode("utf-8", errors="replace")
                    if len(response_body) > 1000:
                        response_body = response_body[:1000] + "... [truncated]"
                    response_metadata["body"] = response_body
                except Exception as e:
                    logger.warning(f"Error capturing response body: {e}")
            
            # Score the trace based on status code
            if trace:
                langfuse_tracer.score_trace(
                    trace_id=trace_id,
                    name="http_status",
                    value=1.0 if status_code < 400 else 0.0,
                    comment=f"HTTP {status_code}",
                    metadata=response_metadata
                )
            
            return response
        except Exception as e:
            # Log exception in Langfuse
            if trace:
                langfuse_tracer.score_trace(
                    trace_id=trace_id,
                    name="error",
                    value=0.0,
                    comment=str(e),
                    metadata={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                    }
                )
            
            # Re-raise exception for FastAPI to handle
            raise
