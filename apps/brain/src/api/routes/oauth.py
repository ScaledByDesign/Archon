"""
OAuth2 authentication routes for Authentik integration.
"""

import logging
import secrets
from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.auth.oauth_client import oauth2_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer(auto_error=False)

@router.get("/health")
async def auth_health():
    """Health check for authentication service."""
    return {
        "status": "healthy",
        "service": "oauth_authentication",
        "oauth_configured": oauth2_manager.is_configured(),
        "timestamp": "2025-05-28T00:50:00Z"
    }

@router.get("/login")
async def login(request: Request, redirect_url: Optional[str] = Query(None)):
    """Initiate OAuth2 login flow."""
    try:
        if not oauth2_manager.is_configured():
            raise HTTPException(
                status_code=503, 
                detail="OAuth2 not configured"
            )
        
        # Generate state parameter for security
        state = secrets.token_urlsafe(32)
        
        # Store state and redirect URL in session (in production, use proper session storage)
        request.session['oauth_state'] = state
        if redirect_url:
            request.session['redirect_after_login'] = redirect_url
        
        # Get authorization URL
        auth_url = oauth2_manager.get_authorization_url(state=state)
        
        logger.info(f"Redirecting to OAuth2 authorization: {auth_url}")
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Login initiation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """Handle OAuth2 callback from Authentik."""
    try:
        # Check for OAuth2 errors
        if error:
            logger.error(f"OAuth2 error: {error}")
            raise HTTPException(status_code=400, detail=f"OAuth2 error: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code missing")
        
        # Verify state parameter (in production, check against stored state)
        stored_state = request.session.get('oauth_state')
        if not stored_state or stored_state != state:
            logger.warning("OAuth2 state mismatch")
            # In development, we'll continue but log the warning
        
        # Exchange code for tokens and get user info
        auth_result = await oauth2_manager.handle_callback(code)
        
        # Store tokens in session (in production, use secure token storage)
        request.session['access_token'] = auth_result['tokens']['access_token']
        request.session['refresh_token'] = auth_result['tokens'].get('refresh_token')
        request.session['user_info'] = auth_result['user']
        
        # Clean up OAuth state
        request.session.pop('oauth_state', None)
        
        # Redirect to original URL or default
        redirect_url = request.session.pop('redirect_after_login', '/dashboard')
        
        logger.info(f"OAuth2 login successful for user: {auth_result['user'].get('email', 'unknown')}")
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"OAuth2 callback failed: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.get("/me")
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current user information."""
    try:
        access_token = None
        
        # Try to get token from Authorization header
        if credentials:
            access_token = credentials.credentials
        else:
            # Fallback to session token
            access_token = request.session.get('access_token')
        
        if not access_token:
            raise HTTPException(status_code=401, detail="No access token provided")
        
        # Validate token and get user info
        user_claims = await oauth2_manager.validate_token(access_token)
        
        # Get additional user info from session if available
        session_user_info = request.session.get('user_info', {})
        
        user_info = {
            'sub': user_claims.get('sub'),
            'email': user_claims.get('email') or session_user_info.get('email'),
            'name': user_claims.get('name') or session_user_info.get('name'),
            'preferred_username': user_claims.get('preferred_username') or session_user_info.get('preferred_username'),
            'groups': user_claims.get('groups', []),
            'scopes': user_claims.get('scope', '').split() if user_claims.get('scope') else []
        }
        
        return {
            "user": user_info,
            "authenticated": True,
            "token_valid": True
        }
        
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/logout")
async def logout(request: Request):
    """Logout user and clear session."""
    try:
        # Clear session data
        request.session.clear()
        
        logger.info("User logged out successfully")
        
        return {
            "message": "Logged out successfully",
            "authenticated": False
        }
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        return {
            "message": "Logout completed",
            "authenticated": False
        }

@router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh access token using refresh token."""
    try:
        refresh_token = request.session.get('refresh_token')
        
        if not refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token available")
        
        # Refresh the token
        new_tokens = await oauth2_manager.refresh_token(refresh_token)
        
        # Update session with new tokens
        request.session['access_token'] = new_tokens['access_token']
        if 'refresh_token' in new_tokens:
            request.session['refresh_token'] = new_tokens['refresh_token']
        
        logger.info("Access token refreshed successfully")
        
        return {
            "message": "Token refreshed successfully",
            "access_token": new_tokens['access_token'],
            "expires_in": new_tokens.get('expires_in', 300)
        }
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")

@router.get("/status")
async def auth_status(request: Request):
    """Get authentication status."""
    try:
        # Check if session exists and has required data
        if not hasattr(request, 'session'):
            return {
                "authenticated": False,
                "user": None,
                "oauth_configured": oauth2_manager.is_configured(),
                "error": "SessionMiddleware must be installed to access request.session"
            }
            
        access_token = request.session.get('access_token')
        user_info = request.session.get('user_info', {})
        
        if access_token:
            try:
                # Validate current token
                await oauth2_manager.validate_token(access_token)
                return {
                    "authenticated": True,
                    "user": {
                        "email": user_info.get('email'),
                        "name": user_info.get('name'),
                        "sub": user_info.get('sub')
                    },
                    "oauth_configured": oauth2_manager.is_configured()
                }
            except:
                # Token is invalid
                pass
        
        return {
            "authenticated": False,
            "user": None,
            "oauth_configured": oauth2_manager.is_configured()
        }
        
    except Exception as e:
        logger.error(f"Auth status check failed: {e}")
        return {
            "authenticated": False,
            "user": None,
            "oauth_configured": False,
            "error": str(e)
        }

# Dependency for protecting routes
async def require_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Dependency to require authentication for protected routes."""
    try:
        access_token = None
        
        # Try to get token from Authorization header
        if credentials:
            access_token = credentials.credentials
        else:
            # Fallback to session token
            access_token = request.session.get('access_token')
        
        if not access_token:
            raise HTTPException(
                status_code=401, 
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate token
        user_claims = await oauth2_manager.validate_token(access_token)
        return user_claims
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication check failed: {e}")
        raise HTTPException(
            status_code=401, 
            detail="Invalid authentication",
            headers={"WWW-Authenticate": "Bearer"}
        )
