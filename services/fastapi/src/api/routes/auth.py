"""
Authentication routes for the RAG System API
Handles login, token management, and user authentication
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Form
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from src.api.dependencies import get_secret_manager, get_authenticated_user

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")


class UserInfo(BaseModel):
    """User information model"""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email")
    roles: list[str] = Field(..., description="User roles")
    permissions: list[str] = Field(..., description="User permissions")


async def get_jwt_config(secrets: SecretManager) -> dict:
    """Get JWT configuration from Vault"""
    try:
        jwt_config = secrets.vault_client.get_secret_dict('app/jwt')
        return {
            'secret_key': jwt_config['secret_key'],
            'algorithm': jwt_config.get('algorithm', 'HS256'),
            'expiration': int(jwt_config.get('expiration', 3600))
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get JWT configuration: {e}"
        )


def create_access_token(data: dict, secret_key: str, algorithm: str, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    secrets: SecretManager = Depends(get_secret_manager)
):
    """Verify JWT token and return user info"""
    try:
        jwt_config = await get_jwt_config(secrets)
        
        payload = jwt.decode(
            credentials.credentials,
            jwt_config['secret_key'],
            algorithms=[jwt_config['algorithm']]
        )
        
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    secrets: SecretManager = Depends(get_secret_manager)
):
    """
    Login endpoint - integrates with Authentik SSO
    For now, this is a placeholder that creates a token for demo purposes
    """
    # TODO: Integrate with Authentik SSO for actual authentication
    # This is a simplified version for demonstration
    
    # Validate credentials (placeholder)
    if request.username == "demo" and request.password == "demo":
        jwt_config = await get_jwt_config(secrets)
        
        # Create token data
        token_data = {
            "sub": request.username,
            "user_id": "demo-user-id",
            "roles": ["user"],
            "permissions": ["read", "write"]
        }
        
        expires_delta = timedelta(seconds=jwt_config['expiration'])
        access_token = create_access_token(
            data=token_data,
            secret_key=jwt_config['secret_key'],
            algorithm=jwt_config['algorithm'],
            expires_delta=expires_delta
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=jwt_config['expiration']
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user(token_data: dict = Depends(verify_token)):
    """Get current user information from token"""
    return UserInfo(
        id=token_data.get("user_id", "unknown"),
        username=token_data.get("sub", "unknown"),
        email=f"{token_data.get('sub', 'unknown')}@example.com",
        roles=token_data.get("roles", []),
        permissions=token_data.get("permissions", [])
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: dict = Depends(verify_token),
    secrets: SecretManager = Depends(get_secret_manager)
):
    """Refresh an access token"""
    jwt_config = await get_jwt_config(secrets)
    
    # Create new token with same data
    expires_delta = timedelta(seconds=jwt_config['expiration'])
    new_token = create_access_token(
        data={
            "sub": token_data["sub"],
            "user_id": token_data.get("user_id"),
            "roles": token_data.get("roles", []),
            "permissions": token_data.get("permissions", [])
        },
        secret_key=jwt_config['secret_key'],
        algorithm=jwt_config['algorithm'],
        expires_delta=expires_delta
    )
    
    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        expires_in=jwt_config['expiration']
    )


@router.post("/logout")
async def logout():
    """Logout endpoint - invalidates token on client side"""
    return {"message": "Successfully logged out"}


@router.get("/health")
async def auth_health():
    """Authentication service health check"""
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
