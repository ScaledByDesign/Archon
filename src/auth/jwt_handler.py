"""
JWT Token Handler for Authentik Integration

This module provides comprehensive JWT token validation, signing, and security
features for the Production RAG System's authentication flow.
"""

import jwt
import httpx
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class JWTSecurityConfig:
    """JWT Security Configuration"""
    
    def __init__(self):
        # Token lifetimes (in seconds)
        self.access_token_lifetime = int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', '3600'))  # 1 hour
        self.refresh_token_lifetime = int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', '86400'))  # 24 hours
        self.id_token_lifetime = int(os.getenv('JWT_ID_TOKEN_LIFETIME', '3600'))  # 1 hour
        
        # Signing algorithm
        self.algorithm = os.getenv('JWT_ALGORITHM', 'RS256')
        
        # Issuer and audience
        self.issuer = os.getenv('AUTHENTIK_ISSUER', 'https://auth.localhost/application/o/default/')
        self.audience = os.getenv('JWT_AUDIENCE', 'rag-system')
        
        # Clock skew tolerance (in seconds)
        self.clock_skew_tolerance = int(os.getenv('JWT_CLOCK_SKEW_TOLERANCE', '30'))
        
        # JWKS cache settings
        self.jwks_cache_ttl = int(os.getenv('JWKS_CACHE_TTL', '3600'))  # 1 hour
        
        # Verification options
        self.verify_signature = os.getenv('JWT_VERIFY_SIGNATURE', 'true').lower() == 'true'
        self.verify_audience = os.getenv('JWT_VERIFY_AUDIENCE', 'true').lower() == 'true'
        self.verify_issuer = os.getenv('JWT_VERIFY_ISSUER', 'true').lower() == 'true'
        self.require_exp = os.getenv('JWT_REQUIRE_EXP', 'true').lower() == 'true'
        self.require_iat = os.getenv('JWT_REQUIRE_IAT', 'true').lower() == 'true'
        self.require_nbf = os.getenv('JWT_REQUIRE_NBF', 'false').lower() == 'true'
        
        # Maximum authentication age (in seconds)
        self.max_auth_age = int(os.getenv('JWT_MAX_AUTH_AGE', '86400'))  # 24 hours
        
        logger.info(f"JWT Security Config initialized with algorithm: {self.algorithm}")
        logger.info(f"Token lifetimes - Access: {self.access_token_lifetime}s, Refresh: {self.refresh_token_lifetime}s, ID: {self.id_token_lifetime}s")
        logger.info(f"Security settings - Clock skew: {self.clock_skew_tolerance}s, Max auth age: {self.max_auth_age}s")


class JWKSManager:
    """JSON Web Key Set (JWKS) Manager for fetching and caching public keys"""
    
    def __init__(self, jwks_url: str, security_config: JWTSecurityConfig):
        self.jwks_url = jwks_url
        self.security_config = security_config
        self.http_client = httpx.AsyncClient(verify=False)  # For development
        self._jwks_cache = {}
        self._cache_timestamp = None
        
    async def get_jwks(self) -> Dict[str, Any]:
        """Fetch JWKS from Authentik, with caching"""
        now = datetime.utcnow()
        
        # Check if cache is valid
        if (self._cache_timestamp and 
            self._jwks_cache and 
            (now - self._cache_timestamp).total_seconds() < self.security_config.jwks_cache_ttl):
            logger.debug("Using cached JWKS")
            return self._jwks_cache
        
        try:
            logger.info(f"Fetching JWKS from: {self.jwks_url}")
            response = await self.http_client.get(self.jwks_url)
            response.raise_for_status()
            
            jwks = response.json()
            self._jwks_cache = jwks
            self._cache_timestamp = now
            
            logger.info(f"Successfully fetched JWKS with {len(jwks.get('keys', []))} keys")
            return jwks
            
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            if self._jwks_cache:
                logger.warning("Using stale JWKS cache due to fetch failure")
                return self._jwks_cache
            raise
    
    async def get_signing_key(self, kid: str) -> str:
        """Get signing key for a specific key ID"""
        jwks = await self.get_jwks()
        
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                if key.get('kty') == 'RSA':
                    # Convert JWK to PEM format
                    return self._jwk_to_pem(key)
                else:
                    raise ValueError(f"Unsupported key type: {key.get('kty')}")
        
        raise ValueError(f"Key with ID '{kid}' not found in JWKS")
    
    def _jwk_to_pem(self, jwk: Dict[str, Any]) -> str:
        """Convert JWK to PEM format"""
        try:
            from jwt.algorithms import RSAAlgorithm
            return RSAAlgorithm.from_jwk(json.dumps(jwk))
        except Exception as e:
            logger.error(f"Failed to convert JWK to PEM: {e}")
            raise
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()


class JWTValidator:
    """JWT Token Validator with comprehensive security checks"""
    
    def __init__(self, jwks_manager: JWKSManager, security_config: JWTSecurityConfig):
        self.jwks_manager = jwks_manager
        self.security_config = security_config
        
    async def validate_token(self, token: str, token_type: str = 'access') -> Dict[str, Any]:
        """
        Validate JWT token with comprehensive security checks
        
        Args:
            token: JWT token string
            token_type: Type of token ('access', 'id', 'refresh')
            
        Returns:
            Decoded token claims
            
        Raises:
            jwt.InvalidTokenError: If token is invalid
            jwt.ExpiredSignatureError: If token is expired
            ValueError: If token format is invalid
        """
        try:
            # Decode header to get key ID
            header = jwt.get_unverified_header(token)
            kid = header.get('kid')
            
            if not kid:
                raise ValueError("Token missing key ID (kid) in header")
            
            # Get signing key
            signing_key = await self.jwks_manager.get_signing_key(kid)
            
            # Validate token with comprehensive checks
            decoded = jwt.decode(
                token,
                signing_key,
                algorithms=[self.security_config.algorithm],
                issuer=self.security_config.issuer,
                audience=self.security_config.audience,
                leeway=self.security_config.clock_skew_tolerance,
                options={
                    "verify_signature": self.security_config.verify_signature,
                    "verify_exp": self.security_config.require_exp,
                    "verify_nbf": self.security_config.require_nbf,
                    "verify_iat": self.security_config.require_iat,
                    "verify_aud": self.security_config.verify_audience,
                    "verify_iss": self.security_config.verify_issuer,
                    "require_exp": self.security_config.require_exp,
                    "require_iat": self.security_config.require_iat,
                    "require_nbf": self.security_config.require_nbf
                }
            )
            
            # Additional security validations
            await self._validate_token_claims(decoded, token_type)
            
            logger.info(f"Successfully validated {token_type} token for user: {decoded.get('sub', 'unknown')}")
            return decoded
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise
        except jwt.InvalidAudienceError:
            logger.error("Token has invalid audience")
            raise
        except jwt.InvalidIssuerError:
            logger.error("Token has invalid issuer")
            raise
        except jwt.InvalidSignatureError:
            logger.error("Token has invalid signature")
            raise
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise jwt.InvalidTokenError(f"Token validation failed: {e}")
    
    async def _validate_token_claims(self, claims: Dict[str, Any], token_type: str):
        """Validate additional token claims based on token type"""
        
        # Validate required claims
        required_claims = ['sub', 'iat', 'exp', 'iss', 'aud']
        missing_claims = [claim for claim in required_claims if claim not in claims]
        if missing_claims:
            raise jwt.InvalidTokenError(f"Missing required claims: {missing_claims}")
        
        # Validate token type specific claims
        if token_type == 'access':
            # Access tokens should have scope
            if 'scope' not in claims:
                logger.warning("Access token missing scope claim")
        
        elif token_type == 'id':
            # ID tokens should have additional user info
            if 'email' not in claims:
                logger.warning("ID token missing email claim")
        
        # Validate custom claims
        if 'auth_time' in claims:
            auth_time = datetime.fromtimestamp(claims['auth_time'])
            max_auth_age = timedelta(seconds=self.security_config.max_auth_age)  # max auth age in seconds
            if datetime.utcnow() - auth_time > max_auth_age:
                raise jwt.InvalidTokenError("Authentication too old")
        
        logger.debug(f"Token claims validation passed for {token_type} token")


class JWTHandler:
    """Main JWT Handler for the Production RAG System"""
    
    def __init__(self, authentik_base_url: str):
        self.authentik_base_url = authentik_base_url.rstrip('/')
        self.security_config = JWTSecurityConfig()
        
        # JWKS URL
        self.jwks_url = f"{self.authentik_base_url}/application/o/default/jwks/"
        
        # Initialize JWKS manager and validator
        self.jwks_manager = JWKSManager(self.jwks_url, self.security_config)
        self.validator = JWTValidator(self.jwks_manager, self.security_config)
        
        logger.info(f"JWT Handler initialized for {self.authentik_base_url}")
    
    async def validate_access_token(self, token: str) -> Dict[str, Any]:
        """Validate access token"""
        return await self.validator.validate_token(token, 'access')
    
    async def validate_id_token(self, token: str) -> Dict[str, Any]:
        """Validate ID token"""
        return await self.validator.validate_token(token, 'id')
    
    async def validate_refresh_token(self, token: str) -> Dict[str, Any]:
        """Validate refresh token"""
        return await self.validator.validate_token(token, 'refresh')
    
    def extract_token_from_header(self, authorization_header: str) -> str:
        """Extract JWT token from Authorization header"""
        if not authorization_header:
            raise ValueError("Authorization header is required")
        
        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise ValueError("Invalid authorization header format. Expected: 'Bearer <token>'")
        
        return parts[1]
    
    def get_token_claims_unsafe(self, token: str) -> Dict[str, Any]:
        """Get token claims without validation (for debugging only)"""
        return jwt.decode(token, options={"verify_signature": False})
    
    async def close(self):
        """Close resources"""
        await self.jwks_manager.close()


# Global JWT handler instance
_jwt_handler: Optional[JWTHandler] = None


async def get_jwt_handler() -> JWTHandler:
    """Get or create JWT handler instance"""
    global _jwt_handler
    
    if _jwt_handler is None:
        authentik_url = os.getenv('AUTHENTIK_URL', 'https://localhost:9443')
        _jwt_handler = JWTHandler(authentik_url)
    
    return _jwt_handler


async def validate_jwt_token(token: str, token_type: str = 'access') -> Dict[str, Any]:
    """Convenience function to validate JWT token"""
    handler = await get_jwt_handler()
    
    if token_type == 'access':
        return await handler.validate_access_token(token)
    elif token_type == 'id':
        return await handler.validate_id_token(token)
    elif token_type == 'refresh':
        return await handler.validate_refresh_token(token)
    else:
        raise ValueError(f"Unsupported token type: {token_type}")


# JWT Security Middleware
class JWTSecurityMiddleware:
    """FastAPI middleware for JWT token validation"""
    
    def __init__(self, app, excluded_paths: Optional[List[str]] = None):
        self.app = app
        self.excluded_paths = excluded_paths or ['/health', '/docs', '/openapi.json', '/api/auth/login']
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]
            
            # Skip JWT validation for excluded paths
            if any(path.startswith(excluded) for excluded in self.excluded_paths):
                await self.app(scope, receive, send)
                return
            
            # Extract and validate JWT token
            headers = dict(scope["headers"])
            auth_header = headers.get(b"authorization", b"").decode()
            
            if auth_header:
                try:
                    handler = await get_jwt_handler()
                    token = handler.extract_token_from_header(auth_header)
                    claims = await handler.validate_access_token(token)
                    
                    # Add user info to scope
                    scope["user"] = claims
                    
                except Exception as e:
                    logger.warning(f"JWT validation failed: {e}")
                    # Continue without user info for now
                    # In production, you might want to return 401
            
        await self.app(scope, receive, send)
