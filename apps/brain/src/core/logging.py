"""
Logging configuration and utilities for the FastAPI backend
Provides structured logging with JSON formatting for production
"""

import logging
import logging.config
import sys
from typing import Any, Dict, Optional
from datetime import datetime
import json
import traceback

from src.config.settings import get_settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created",
                "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "getMessage", "exc_info",
                "exc_text", "stack_info"
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class ContextFilter(logging.Filter):
    """Add contextual information to log records"""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record"""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Set up logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting
        context: Additional context to include in all log messages
    """
    settings = get_settings()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter
    if json_format or settings.environment.value == "production":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt=settings.log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    
    # Add context filter if provided
    if context:
        context_filter = ContextFilter(context)
        console_handler.addFilter(context_filter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_third_party_loggers(level)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "level": level,
            "json_format": json_format,
            "environment": settings.environment.value
        }
    )


def configure_third_party_loggers(level: str) -> None:
    """Configure logging levels for third-party libraries"""
    
    # Reduce noise from third-party libraries
    third_party_loggers = {
        "uvicorn": "INFO",
        "uvicorn.access": "WARNING",
        "uvicorn.error": "INFO",
        "fastapi": "INFO",
        "httpx": "WARNING",
        "httpcore": "WARNING",
        "qdrant_client": "WARNING",
        "motor": "WARNING",
        "pymongo": "WARNING",
        "redis": "WARNING",
        "hvac": "WARNING",
        "urllib3": "WARNING",
        "requests": "WARNING",
        "aiohttp": "WARNING",
    }
    
    for logger_name, logger_level in third_party_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, logger_level))


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger with optional context
    
    Args:
        name: Logger name (usually __name__)
        context: Additional context to include in log messages
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if context:
        # Create a custom adapter that adds context to all log messages
        class ContextAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                # Merge context with any extra kwargs
                extra = kwargs.get('extra', {})
                extra.update(self.extra)
                kwargs['extra'] = extra
                return msg, kwargs
        
        return ContextAdapter(logger, context)
    
    return logger


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> None:
    """
    Log HTTP request information
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: User ID if authenticated
        request_id: Unique request ID
    """
    logger = get_logger("api.requests")
    
    log_data = {
        "http_method": method,
        "http_path": path,
        "http_status_code": status_code,
        "duration_ms": duration_ms,
        "user_id": user_id,
        "request_id": request_id,
    }
    
    if status_code >= 500:
        logger.error("HTTP request failed", extra=log_data)
    elif status_code >= 400:
        logger.warning("HTTP request error", extra=log_data)
    else:
        logger.info("HTTP request completed", extra=log_data)


def log_database_operation(
    operation: str,
    table: str,
    duration_ms: float,
    success: bool = True,
    error: Optional[str] = None,
    affected_rows: Optional[int] = None
) -> None:
    """
    Log database operation information
    
    Args:
        operation: Database operation (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration_ms: Operation duration in milliseconds
        success: Whether the operation succeeded
        error: Error message if operation failed
        affected_rows: Number of affected rows
    """
    logger = get_logger("database")
    
    log_data = {
        "db_operation": operation,
        "db_table": table,
        "duration_ms": duration_ms,
        "success": success,
        "affected_rows": affected_rows,
    }
    
    if success:
        logger.info("Database operation completed", extra=log_data)
    else:
        log_data["error"] = error
        logger.error("Database operation failed", extra=log_data)


def log_external_api_call(
    service: str,
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: float,
    success: bool = True,
    error: Optional[str] = None
) -> None:
    """
    Log external API call information
    
    Args:
        service: Service name (e.g., "openai", "vault", "qdrant")
        endpoint: API endpoint
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        success: Whether the call succeeded
        error: Error message if call failed
    """
    logger = get_logger("external_api")
    
    log_data = {
        "service": service,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "success": success,
    }
    
    if success:
        logger.info("External API call completed", extra=log_data)
    else:
        log_data["error"] = error
        logger.error("External API call failed", extra=log_data)
