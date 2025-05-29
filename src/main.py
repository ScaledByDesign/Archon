"""
FastAPI Backend for Production RAG System
Integrates with HashiCorp Vault, Qdrant, and other services
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from pydantic import BaseModel, Field

# Core scaffolding imports
from src.core import (
    setup_logging, get_logger,
    RequestLoggingMiddleware, SecurityHeadersMiddleware, 
    RateLimitMiddleware, ErrorHandlingMiddleware, HealthCheckMiddleware,
    initialize_databases, close_databases, get_database_manager,
    APIError, ValidationError, AuthenticationError, InternalServerError
)
from src.core.validators import HealthCheckResponse, ErrorResponse
from src.core.service_manager import service_manager
from src.config.settings import get_settings

# Observability imports
from src.observability.middleware import LangfuseMiddleware
from src.observability.langfuse_client import langfuse_tracer
from src.observability.litellm_wrapper import traced_llm

# Existing imports
from src.zoi_secrets.vault_client import get_secret_manager as create_secret_manager, VaultConfig, VaultClient, SecretManager
from src.vector_store.vector_store import QdrantVectorStore, QdrantConfig
from src.api.dependencies import set_global_secret_manager, set_global_vector_store, get_secret_manager, get_vector_store, set_global_document_processor
from src.api.routes import auth, search, oauth, document_routes
from src.document_pipeline.document_processor import DocumentProcessor
from src.auth.jwt_middleware import JWTMiddleware

# Initialize structured logging
setup_logging()
logger = get_logger(__name__)

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# Global variables for shared resources
secret_manager: Optional[SecretManager] = None
vector_store: Optional[QdrantVectorStore] = None
document_processor: Optional[DocumentProcessor] = None
app_config: Dict = {}


async def initialize_secrets():
    """Initialize secret manager and load application configuration"""
    global secret_manager, app_config
    
    try:
        logger.info("Initializing secret manager...")
        
        # Get Vault configuration from environment
        vault_config = VaultConfig.from_env()
        
        # Create Vault client (authentication happens automatically)
        vault_client = VaultClient(vault_config)
        
        # Create secret manager
        secret_manager = create_secret_manager(vault_client)
        set_global_secret_manager(secret_manager)
        
        # Load application configuration
        try:
            app_config = secret_manager.get_secret("app/config")
            logger.info("Secret manager initialized successfully with app config from Vault")
        except Exception as config_error:
            logger.warning(f"Could not load app config from Vault: {config_error}")
            app_config = None  # Use default configuration
            logger.info("Secret manager initialized successfully with default config")
        
    except Exception as e:
        logger.error(f"Failed to initialize secret manager: {e}")
        # Continue without Vault in development mode
        if os.getenv("ENVIRONMENT", "development") == "development":
            logger.warning("Running in development mode without Vault")
            secret_manager = None
        else:
            raise


async def initialize_vector_store():
    """Initialize Qdrant vector store"""
    global vector_store
    
    try:
        logger.info("Initializing vector store...")
        
        if secret_manager:
            # Get Qdrant configuration from Vault
            try:
                qdrant_config_dict = secret_manager.get_secret("qdrant/config")
                qdrant_url = qdrant_config_dict.get("url", "http://qdrant:6333")
            except Exception as e:
                logger.warning(f"Could not load Qdrant config from Vault: {e}")
                qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        else:
            # Fallback to environment variables
            qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        
        # Parse URL to extract components
        from urllib.parse import urlparse
        parsed_url = urlparse(qdrant_url)
        
        # Create Qdrant configuration
        qdrant_config = QdrantConfig(
            host=parsed_url.hostname or "qdrant",
            port=parsed_url.port or 6333,
            https=parsed_url.scheme == "https"
        )
        
        # Initialize vector store
        vector_store = QdrantVectorStore(qdrant_config)
        set_global_vector_store(vector_store)
        
        # Test connection by listing collections
        collections = vector_store.list_collections()
        logger.info(f"Vector store initialized with {len(collections)} collections")
        
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        vector_store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    # Initialize databases first
    await initialize_databases()
    
    # Initialize secrets
    await initialize_secrets()
    await initialize_vector_store()
    
    # Initialize service manager
    try:
        logger.info("Initializing service manager...")
        await service_manager.initialize()
        logger.info("Service manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize service manager: {e}")
        logger.warning("Continuing with limited functionality")
    
    # Start application
    yield
    
    # Cleanup resources
    try:
        logger.info("Shutting down application...")
        await service_manager.cleanup()
        if vector_store:
            await vector_store.close()
        await close_databases()
        logger.info("Application shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Production RAG System API",
        description="FastAPI backend for Production RAG System with comprehensive scaffolding",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add core middleware (order matters!)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(HealthCheckMiddleware)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.auth.cors_origins_list,
        allow_credentials=True,
        allow_methods=settings.auth.cors_allow_methods_list,
        allow_headers=["*"],
    )
    
    # Add trusted host middleware
    if settings.auth.trusted_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.auth.trusted_hosts_list
        )
    
    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.auth.session_secret_key,
        max_age=settings.auth.session_max_age,
        same_site="lax",
        https_only=settings.environment == "production"
    )
    
    # Add observability middleware
    app.add_middleware(
        LangfuseMiddleware,
        exclude_paths=["/health", "/metrics", "/favicon.ico"],
        include_request_body=False,  # Set to True to capture request bodies in traces
        include_response_body=False,  # Set to True to capture response bodies in traces
        include_headers=False,        # Set to True to capture headers in traces
    )
    
    # Custom exception handlers
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        """Handle custom API errors"""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.__class__.__name__,
                message=exc.detail,
                details=getattr(exc, 'details', None),
                request_id=getattr(request.state, 'request_id', None)
            ).dict()
        )
    
    @app.exception_handler(422)
    async def validation_exception_handler(request: Request, exc: HTTPException):
        """Handle validation errors"""
        logger.warning(f"Validation error: {exc}", extra={
            "request_id": getattr(request.state, 'request_id', None),
            "path": str(request.url.path),
            "method": request.method
        })
        
        error_response = ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            details=exc.errors() if hasattr(exc, 'errors') else str(exc),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return JSONResponse(
            status_code=422,
            content=json.loads(json.dumps(error_response.dict(), cls=CustomJSONEncoder))
        )
    
    @app.exception_handler(500)
    async def internal_server_error_handler(request: Request, exc: Exception):
        """Handle internal server errors"""
        logger.exception("Internal server error", extra={
            "request_id": getattr(request.state, 'request_id', None),
            "path": str(request.url.path),
            "method": request.method
        })
        
        error_response = ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return JSONResponse(
            status_code=500,
            content=json.loads(json.dumps(error_response.dict(), cls=CustomJSONEncoder))
        )
    
    # Health check endpoint
    @app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
    async def health_check():
        """Application health check"""
        try:
            components = {}
            
            # Check database connections
            try:
                db_manager = await get_database_manager()
                db_health = await db_manager.health_check()
                components.update(db_health)
            except Exception as e:
                logger.warning(f"Database health check failed: {e}")
                components["database"] = "unhealthy"
            
            # Check secret manager
            if secret_manager:
                try:
                    secret_manager.get_secret("app/config")
                    components["vault"] = "healthy"
                except Exception as e:
                    logger.warning(f"Vault health check failed: {e}")
                    components["vault"] = "unhealthy"
            else:
                components["vault"] = "not_configured"
            
            # Check vector store
            if vector_store:
                try:
                    collections = vector_store.list_collections()
                    components["qdrant"] = f"healthy ({len(collections)} collections)"
                except Exception as e:
                    logger.warning(f"Qdrant health check failed: {e}")
                    components["qdrant"] = "unhealthy"
            else:
                components["qdrant"] = "not_configured"
            
            # Determine overall status
            unhealthy_components = [k for k, v in components.items() if "unhealthy" in str(v)]
            overall_status = "unhealthy" if unhealthy_components else "healthy"
            
            return HealthCheckResponse(
                status=overall_status,
                timestamp=datetime.utcnow(),
                version="1.0.0",
                dependencies=components
            )
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise InternalServerError(detail="Health check failed")
    
    # Include API routers
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(search.router, prefix="/api/search", tags=["Search"])
    app.include_router(oauth.router, prefix="/api/oauth", tags=["OAuth"])
    app.include_router(document_routes.router, prefix="/api/documents", tags=["Documents"])
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
