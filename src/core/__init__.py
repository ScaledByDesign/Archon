"""
Core utilities and shared components for the FastAPI backend
"""

from .exceptions import *
from .logging import *
from .middleware import *
from .security import *
from .database import *

__all__ = [
    # Exceptions
    "APIError",
    "ValidationError", 
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "InternalServerError",
    "DatabaseError",
    "ConnectionError",
    "ConfigurationError",
    
    # Logging
    "JSONFormatter",
    "setup_logging",
    "get_logger",
    "log_request",
    "log_error",
    "log_security_event",
    
    # Middleware
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware", 
    "RateLimitMiddleware",
    "ErrorHandlingMiddleware",
    "HealthCheckMiddleware",
    
    # Security
    "hash_password",
    "verify_password",
    "generate_secure_token",
    "generate_api_key",
    "generate_password",
    "create_signature",
    "verify_signature",
    "derive_key",
    "constant_time_compare",
    "sanitize_filename",
    "validate_email",
    "validate_password_strength",
    "generate_csrf_token",
    "create_session_token",
    "verify_session_token",
    
    # Database
    "DatabaseManager",
    "Base",
    "db_manager",
    "get_database_manager",
    "get_mongo_client",
    "get_redis_client", 
    "get_postgres_session",
    "MongoHelper",
    "RedisHelper",
    "initialize_databases",
    "close_databases",
]
