"""
Custom exception classes for the FastAPI backend
Provides structured error handling and HTTP status codes
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException as FastAPIHTTPException, status


class BaseAPIException(FastAPIHTTPException):
    """Base exception class for API errors"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.context = context or {}


# Alias for backward compatibility
APIError = BaseAPIException


class ValidationError(BaseAPIException):
    """Raised when request validation fails"""
    
    def __init__(
        self,
        detail: str = "Validation error",
        field_errors: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers,
            error_code="VALIDATION_ERROR",
            context={"field_errors": field_errors or {}}
        )


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails"""
    
    def __init__(
        self,
        detail: str = "Authentication failed",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"},
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(BaseAPIException):
    """Raised when authorization fails"""
    
    def __init__(
        self,
        detail: str = "Insufficient permissions",
        required_permissions: Optional[list] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers,
            error_code="AUTHORIZATION_ERROR",
            context={"required_permissions": required_permissions or []}
        )


class NotFoundError(BaseAPIException):
    """Raised when a resource is not found"""
    
    def __init__(
        self,
        detail: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers,
            error_code="NOT_FOUND_ERROR",
            context={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )


class ConflictError(BaseAPIException):
    """Raised when a resource conflict occurs"""
    
    def __init__(
        self,
        detail: str = "Resource conflict",
        conflicting_resource: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers,
            error_code="CONFLICT_ERROR",
            context={"conflicting_resource": conflicting_resource}
        )


class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded"""
    
    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        retry_headers = headers or {}
        if retry_after:
            retry_headers["Retry-After"] = str(retry_after)
            
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=retry_headers,
            error_code="RATE_LIMIT_ERROR",
            context={"retry_after": retry_after}
        )


class ServiceUnavailableError(BaseAPIException):
    """Raised when a service is temporarily unavailable"""
    
    def __init__(
        self,
        detail: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
        retry_after: Optional[int] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        retry_headers = headers or {}
        if retry_after:
            retry_headers["Retry-After"] = str(retry_after)
            
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            headers=retry_headers,
            error_code="SERVICE_UNAVAILABLE_ERROR",
            context={
                "service_name": service_name,
                "retry_after": retry_after
            }
        )


class DatabaseError(BaseAPIException):
    """Raised when database operations fail"""
    
    def __init__(
        self,
        detail: str = "Database operation failed",
        operation: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers,
            error_code="DATABASE_ERROR",
            context={"operation": operation}
        )


class ConnectionError(BaseAPIException):
    """Raised when connection to external service fails"""
    
    def __init__(
        self,
        detail: str = "Connection failed",
        service: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            headers=headers,
            error_code="CONNECTION_ERROR",
            context={"service": service}
        )


class InternalServerError(BaseAPIException):
    """Raised for internal server errors"""
    
    def __init__(
        self,
        detail: str = "Internal server error",
        error_id: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers,
            error_code="INTERNAL_SERVER_ERROR",
            context={"error_id": error_id}
        )


class BadRequestError(BaseAPIException):
    """Raised for bad request errors"""
    
    def __init__(
        self,
        detail: str = "Bad request",
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers,
            error_code="BAD_REQUEST_ERROR"
        )


class VectorStoreError(BaseAPIException):
    """Raised when vector store operations fail"""
    
    def __init__(
        self,
        detail: str = "Vector store operation failed",
        operation: Optional[str] = None,
        collection: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            headers=headers,
            error_code="VECTOR_STORE_ERROR",
            context={
                "operation": operation,
                "collection": collection
            }
        )
