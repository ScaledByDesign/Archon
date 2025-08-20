"""
Authentication routes for OAuth2 flow with Authentik
"""

from fastapi import APIRouter, Request, Response, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional, Dict, Any
import secrets
import logging
from urllib.parse import urlencode, parse_qs, urlparse

from ...auth.oauth_client import OAuth2Manager
from ...auth.dependencies import (
    get_current_user_optional, 
    get_current_user, 
    get_oauth_manager,
    check_auth_rate_limit,
    SecurityHeaders
)
from ...auth.jwt_handler import get_jwt_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.get("/health")
async def health_check():
    """Health check for authentication service"""
    return {"status": "healthy", "service": "authentication"}


@router.get("/status")
async def auth_status(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get current authentication status"""
    oauth_manager = OAuth2Manager()
    
    return {
        "authenticated": current_user is not None,
        "user": current_user,
        "oauth_configured": oauth_manager.client is not None
    }


@router.get("/login")
async def login(
    request: Request, 
    response: Response,
    redirect_url: Optional[str] = Query(None),
    oauth_manager: OAuth2Manager = Depends(get_oauth_manager),
    _rate_limit: bool = Depends(check_auth_rate_limit)
):
    """Initiate OAuth2 login flow"""
    try:
        if not oauth_manager.client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth2 not configured"
            )
        
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)
        
        # Store state and redirect URL in session
        request.session["oauth_state"] = state
        if redirect_url:
            request.session["redirect_after_auth"] = redirect_url
        
        # Get authorization URL
        auth_url = oauth_manager.get_authorization_url(state)
        
        # Add security headers
        for header, value in SecurityHeaders.get_security_headers().items():
            response.headers[header] = value
        
        logger.info(f"Redirecting to OAuth2 authorization: {auth_url}")
        return RedirectResponse(url=auth_url, status_code=307)
        
    except Exception as e:
        logger.error(f"Login initiation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/callback")
async def oauth_callback(
    request: Request,
    response: Response,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    oauth_manager: OAuth2Manager = Depends(get_oauth_manager),
    _rate_limit: bool = Depends(check_auth_rate_limit)
):
    """Handle OAuth2 callback from Authentik"""
    try:
        # Check for OAuth2 errors
        if error:
            logger.error(f"OAuth2 callback error: {error}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth2 error: {error}"
            )
        
        # Validate required parameters
        if not code or not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing authorization code or state parameter"
            )
        
        # Validate state parameter
        stored_state = request.session.get("oauth_state")
        if not stored_state or stored_state != state:
            logger.error("OAuth2 state mismatch - possible CSRF attack")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # Exchange authorization code for tokens
        tokens = await oauth_manager.handle_callback(code)
        
        # Validate and extract user information from tokens
        access_token = tokens.get("access_token")
        id_token = tokens.get("id_token")
        refresh_token = tokens.get("refresh_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No access token received"
            )
        
        # Get user information using the new JWT handler
        jwt_handler = await get_jwt_handler()
        
        # Validate access token and get user info
        user_claims = await jwt_handler.validate_access_token(access_token)
        
        # Validate ID token if present
        id_claims = None
        if id_token:
            try:
                id_claims = await jwt_handler.validate_id_token(id_token)
            except Exception as e:
                logger.warning(f"ID token validation failed: {e}")
        
        # Store tokens and user info in session
        request.session["access_token"] = access_token
        request.session["refresh_token"] = refresh_token
        request.session["user_info"] = {
            "sub": user_claims.get("sub"),
            "email": user_claims.get("email"),
            "name": user_claims.get("name"),
            "preferred_username": user_claims.get("preferred_username"),
            "groups": user_claims.get("groups", []),
            "scope": user_claims.get("scope", "").split(),
            "auth_time": user_claims.get("auth_time"),
            "session_state": user_claims.get("session_state")
        }
        
        # Clean up OAuth state
        request.session.pop("oauth_state", None)
        
        # Get redirect URL
        redirect_after_auth = request.session.pop("redirect_after_auth", "/")
        
        # Add security headers
        for header, value in SecurityHeaders.get_security_headers().items():
            response.headers[header] = value
        
        logger.info(f"OAuth2 callback successful for user: {user_claims.get('sub')}")
        
        # Return success response with user info
        return JSONResponse(
            content={
                "success": True,
                "user": request.session["user_info"],
                "redirect_url": redirect_after_auth,
                "token_info": {
                    "expires_in": tokens.get("expires_in"),
                    "token_type": tokens.get("token_type", "Bearer"),
                    "scope": tokens.get("scope")
                }
            },
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth2 callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return {
        "user": current_user,
        "authenticated": True
    }


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Logout current user"""
    try:
        # Clear session data
        request.session.clear()
        
        # Add security headers
        for header, value in SecurityHeaders.get_security_headers().items():
            response.headers[header] = value
        
        logger.info(f"User logged out: {current_user.get('sub') if current_user else 'unknown'}")
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.post("/refresh")
async def refresh_token(
    request: Request,
    oauth_manager: OAuth2Manager = Depends(get_oauth_manager),
    _rate_limit: bool = Depends(check_auth_rate_limit)
):
    """Refresh access token using refresh token"""
    try:
        refresh_token = request.session.get("refresh_token")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token available"
            )
        
        # Refresh the token
        new_tokens = await oauth_manager.refresh_token(refresh_token)
        
        # Validate new access token
        jwt_handler = await get_jwt_handler()
        new_access_token = new_tokens.get("access_token")
        
        if not new_access_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No access token in refresh response"
            )
        
        # Validate new token and update user info
        user_claims = await jwt_handler.validate_access_token(new_access_token)
        
        # Update session with new tokens
        request.session["access_token"] = new_access_token
        if new_tokens.get("refresh_token"):
            request.session["refresh_token"] = new_tokens["refresh_token"]
        
        # Update user info
        request.session["user_info"] = {
            "sub": user_claims.get("sub"),
            "email": user_claims.get("email"),
            "name": user_claims.get("name"),
            "preferred_username": user_claims.get("preferred_username"),
            "groups": user_claims.get("groups", []),
            "scope": user_claims.get("scope", "").split(),
            "auth_time": user_claims.get("auth_time"),
            "session_state": user_claims.get("session_state")
        }
        
        logger.info(f"Token refreshed for user: {user_claims.get('sub')}")
        
        return {
            "success": True,
            "token_info": {
                "expires_in": new_tokens.get("expires_in"),
                "token_type": new_tokens.get("token_type", "Bearer"),
                "scope": new_tokens.get("scope")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.get("/validate")
async def validate_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Validate current access token"""
    return {
        "valid": True,
        "user": current_user,
        "message": "Token is valid"
    }
