"""
FastAPI Backend for Production RAG System
Integrates with HashiCorp Vault, Qdrant, and other services
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.secrets.vault_client import SecretManager, VaultConfig, VaultClient
from src.vector_store.vector_store import QdrantVectorStore
from src.api.dependencies import set_global_secret_manager, set_global_vector_store, get_secret_manager, get_vector_store
from src.api.routes import auth, search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for shared resources
secret_manager: Optional[SecretManager] = None
vector_store: Optional[QdrantVectorStore] = None
app_config: Dict = {}


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    components: Dict[str, str] = Field(..., description="Component status")
    timestamp: str = Field(..., description="Check timestamp")


async def initialize_secrets():
    """Initialize secret manager and load application configuration"""
    global secret_manager, app_config
    
    try:
        logger.info("Initializing secret manager...")
        
        # Check if we're running in development mode
        vault_addr = os.getenv('VAULT_ADDR', 'http://localhost:8200')
        
        if vault_addr and not vault_addr.startswith('http://localhost'):
            # Production: Use AppRole authentication
            config = VaultConfig(
                url=vault_addr,
                role_id=os.getenv('VAULT_ROLE_ID'),
                secret_id=os.getenv('VAULT_SECRET_ID'),
                verify_ssl=os.getenv('VAULT_VERIFY_SSL', 'true').lower() == 'true'
            )
            vault_client = VaultClient(config)
        else:
            # Development: Use root token
            vault_client = VaultClient()
        
        secret_manager = SecretManager(vault_client)
        set_global_secret_manager(secret_manager)
        
        # Load application configuration from Vault
        app_config = {
            'database_url': secret_manager.get_database_url(),
            'redis_url': secret_manager.get_redis_url(),
            'mongodb_config': secret_manager.get_mongodb_credentials(),
            'qdrant_config': secret_manager.get_qdrant_credentials(),
            'llm_config': secret_manager.get_llm_credentials(),
        }
        
        logger.info("Secret manager initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize secret manager: {e}")
        return False


async def initialize_vector_store():
    """Initialize Qdrant vector store connection"""
    global vector_store
    
    try:
        logger.info("Initializing vector store...")
        
        if not secret_manager:
            raise RuntimeError("Secret manager not initialized")
        
        qdrant_config = secret_manager.get_qdrant_credentials()
        
        vector_store = QdrantVectorStore(
            url=qdrant_config['url'],
            api_key=qdrant_config.get('api_key'),
            timeout=int(qdrant_config.get('timeout', 30))
        )
        
        # Test connection
        await vector_store.health_check()
        set_global_vector_store(vector_store)
        
        logger.info("Vector store initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting RAG System API...")
    
    # Initialize services
    secrets_ok = await initialize_secrets()
    if not secrets_ok:
        logger.error("Failed to initialize secrets - continuing with limited functionality")
    
    vector_ok = await initialize_vector_store()
    if not vector_ok:
        logger.error("Failed to initialize vector store - continuing with limited functionality")
    
    logger.info("RAG System API started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down RAG System API...")
    if vector_store:
        try:
            await vector_store.close()
        except Exception as e:
            logger.error(f"Error closing vector store: {e}")


# Create FastAPI application
app = FastAPI(
    title="Production RAG System API",
    description="Secure, scalable RAG system with vector search and LLM integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,*.localhost").split(",")
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(search.router, prefix="/api")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Production RAG System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "api": {
            "auth": "/api/auth",
            "search": "/api/search"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    import time
    from datetime import datetime
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    components = {}
    
    # Check secret manager
    try:
        if secret_manager:
            # Test secret retrieval
            test_config = secret_manager.get_database_url()
            components["secrets"] = "healthy" if test_config else "degraded"
        else:
            components["secrets"] = "unavailable"
    except Exception as e:
        logger.error(f"Secret manager health check failed: {e}")
        components["secrets"] = "unhealthy"
    
    # Check vector store
    try:
        if vector_store:
            health_status = await vector_store.health_check()
            components["vector_store"] = "healthy" if health_status else "unhealthy"
        else:
            components["vector_store"] = "unavailable"
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        components["vector_store"] = "unhealthy"
    
    # Overall status
    if all(status in ["healthy"] for status in components.values()):
        overall_status = "healthy"
    elif any(status in ["healthy", "degraded"] for status in components.values()):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        components=components,
        timestamp=timestamp
    )


@app.get("/api/config", response_model=Dict[str, str])
async def get_configuration(secrets: SecretManager = Depends(get_secret_manager)):
    """Get application configuration (sensitive data masked)"""
    try:
        config = {
            "database_host": secrets.vault_client.get_secret('app/database', 'host'),
            "redis_host": secrets.vault_client.get_secret('app/redis', 'host'),
            "qdrant_url": secrets.vault_client.get_secret('app/qdrant', 'url'),
            "environment": secrets.vault_client.get_secret('env/development', 'environment', 'development'),
        }
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve configuration"
        )


@app.get("/api/collections", response_model=List[str])
async def list_collections(vector_store: QdrantVectorStore = Depends(get_vector_store)):
    """List available vector collections"""
    try:
        collections = await vector_store.list_collections()
        return [collection.name for collection in collections]
        
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collections"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
