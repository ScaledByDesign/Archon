"""
FastAPI dependencies for the RAG System API
Provides shared dependencies for authentication, database connections, etc.
"""

import logging
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.zoi_secrets.vault_client import get_secret_manager, VaultClient, SecretManager
from src.vector_store.vector_store import QdrantVectorStore
from src.document_pipeline.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Global instances (initialized in main.py)
_secret_manager: Optional[SecretManager] = None
_vector_store: Optional[QdrantVectorStore] = None
_document_processor: Optional[DocumentProcessor] = None


def set_global_secret_manager(secret_manager: SecretManager):
    """Set the global secret manager instance"""
    global _secret_manager
    _secret_manager = secret_manager


def set_global_vector_store(vector_store: QdrantVectorStore):
    """Set the global vector store instance"""
    global _vector_store
    _vector_store = vector_store


def set_global_document_processor(document_processor: DocumentProcessor):
    """Set the global document processor instance"""
    global _document_processor
    _document_processor = document_processor


def get_secret_manager() -> SecretManager:
    """Dependency to get secret manager"""
    if not _secret_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Secret manager not available"
        )
    return _secret_manager


def get_vector_store() -> QdrantVectorStore:
    """Dependency to get vector store"""
    if not _vector_store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not available"
        )
    return _vector_store


def get_document_processor() -> DocumentProcessor:
    """Dependency to get document processor"""
    if not _document_processor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document processor not available"
        )
    return _document_processor


async def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    secrets: SecretManager = Depends(get_secret_manager)
):
    """
    Dependency to get authenticated user from JWT token
    This is a simplified version - in production, integrate with Authentik
    """
    try:
        import jwt
        
        # Get JWT configuration
        jwt_config = secrets.vault_client.get_secret_dict('app/jwt')
        
        # Decode token
        payload = jwt.decode(
            credentials.credentials,
            jwt_config['secret_key'],
            algorithms=[jwt_config.get('algorithm', 'HS256')]
        )
        
        return {
            'user_id': payload.get('user_id'),
            'username': payload.get('sub'),
            'roles': payload.get('roles', []),
            'permissions': payload.get('permissions', [])
        }
        
    except jwt.PyJWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    secrets: SecretManager = Depends(get_secret_manager)
):
    """
    Optional authentication dependency - returns user if token is provided and valid
    """
    if not credentials:
        return None
        
    try:
        import jwt
        
        jwt_config = secrets.vault_client.get_secret_dict('app/jwt')
        
        payload = jwt.decode(
            credentials.credentials,
            jwt_config['secret_key'],
            algorithms=[jwt_config.get('algorithm', 'HS256')]
        )
        
        return {
            'user_id': payload.get('user_id'),
            'username': payload.get('sub'),
            'roles': payload.get('roles', []),
            'permissions': payload.get('permissions', [])
        }
        
    except jwt.PyJWTError:
        return None
    except Exception as e:
        logger.error(f"Optional authentication error: {e}")
        return None


def require_permission(permission: str):
    """
    Dependency factory to require specific permission
    """
    def permission_checker(user: dict = Depends(get_authenticated_user)):
        if permission not in user.get('permissions', []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return user
    
    return permission_checker


def require_role(role: str):
    """
    Dependency factory to require specific role
    """
    def role_checker(user: dict = Depends(get_authenticated_user)):
        if role not in user.get('roles', []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return user
    
    return role_checker
