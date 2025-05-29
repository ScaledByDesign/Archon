"""
Tests for JWT Handler functionality

This module tests JWT validation, signing, and security features.
"""

import pytest
import jwt
import httpx
import json
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.auth.jwt_handler import (
    JWTSecurityConfig,
    JWKSManager,
    JWTValidator,
    JWTHandler,
    validate_jwt_token,
    get_jwt_handler
)


@pytest.fixture
def mock_rsa_keys():
    """Generate mock RSA key pair for testing"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    public_key = private_key.public_key()
    
    # Serialize keys
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return {
        'private_key': private_key,
        'public_key': public_key,
        'private_pem': private_pem,
        'public_pem': public_pem
   }


@pytest.fixture
def mock_jwks_response(mock_rsa_keys):
    """Mock JWKS response from Authentik"""
    public_key = mock_rsa_keys['public_key']
    
    # Get public key numbers for JWK
    public_numbers = public_key.public_numbers()
    
    # Convert to base64url encoded values
    import base64
    
    def int_to_base64url(value):
        # Convert integer to bytes, then to base64url
        byte_length = (value.bit_length() + 7) // 8
        value_bytes = value.to_bytes(byte_length, 'big')
        return base64.urlsafe_b64encode(value_bytes).decode('ascii').rstrip('=')
    
    n = int_to_base64url(public_numbers.n)
    e = int_to_base64url(public_numbers.e)
    
    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "kid": "test-key-id",
                "alg": "RS256",
                "n": n,
                "e": e
            }
        ]
    }


@pytest.fixture
def jwt_config():
    """Create JWT security configuration for testing"""
    return JWTSecurityConfig()


@pytest.fixture
def valid_jwt_token():
    """Create a valid JWT token for testing"""
    # Create a test private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Create payload with current time
    now = datetime.utcnow()
    payload = {
        "iss": "https://auth.localhost/application/o/default/",
        "aud": "fastapi-client",
        "sub": "test-user-id",
        "email": "test@example.com",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "auth_time": int(now.timestamp()),
        "azp": "fastapi-client",
        "scope": "openid email profile rag:api"
    }
    
    # Create JWT token
    token = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key-id"}
    )
    
    return token


class TestJWTSecurityConfig:
    """Test JWT security configuration"""
    
    def test_default_config(self):
        """Test default JWT security configuration"""
        config = JWTSecurityConfig()
        
        assert config.access_token_lifetime == 300  # 5 minutes default
        assert config.refresh_token_lifetime == 1800  # 30 minutes default
        assert config.id_token_lifetime == 600  # 10 minutes default
        assert config.algorithm == "RS256"
        assert config.issuer == "https://auth.localhost/application/o/default/"
        assert config.audience == "fastapi-client"
        assert config.clock_skew_tolerance == 30
    
    def test_custom_config(self):
        """Test custom configuration values"""
        # Set environment variables for custom config
        import os
        original_values = {}
        test_env = {
            'JWT_ACCESS_TOKEN_LIFETIME': '7200',
            'JWT_REFRESH_TOKEN_LIFETIME': '172800',
            'JWT_ID_TOKEN_LIFETIME': '1800',
            'JWT_ALGORITHM': 'RS256',
            'AUTHENTIK_ISSUER': 'https://custom.auth.com/o/default/',
            'JWT_AUDIENCE': 'custom-client',
            'JWT_CLOCK_SKEW_TOLERANCE': '120'
        }
        
        # Save original values and set test values
        for key, value in test_env.items():
            original_values[key] = os.getenv(key)
            os.environ[key] = value
        
        try:
            config = JWTSecurityConfig()
            
            assert config.access_token_lifetime == 7200
            assert config.refresh_token_lifetime == 172800
            assert config.id_token_lifetime == 1800
            assert config.algorithm == "RS256"
            assert config.issuer == "https://custom.auth.com/o/default/"
            assert config.audience == "custom-client"
            assert config.clock_skew_tolerance == 120
        finally:
            # Restore original values
            for key, original_value in original_values.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


class TestJWKSManager:
    """Test JWKS manager functionality"""
    
    @pytest.mark.asyncio
    async def test_fetch_jwks_success(self, mock_jwks_response):
        """Test successful JWKS fetching"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            config = JWTSecurityConfig()
            manager = JWKSManager("https://auth.localhost/application/o/default/jwks/", config)
            
            jwks = await manager.get_jwks()
            
            assert "keys" in jwks
            assert len(jwks["keys"]) == 1
            assert jwks["keys"][0]["kid"] == "test-key-id"
    
    @pytest.mark.asyncio
    async def test_fetch_jwks_http_error(self):
        """Test JWKS fetching with HTTP error"""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock HTTP error
            mock_get.side_effect = httpx.HTTPError("Connection failed")
            
            config = JWTSecurityConfig()
            manager = JWKSManager("https://auth.localhost/application/o/default/jwks/", config)
            
            with pytest.raises(Exception):
                await manager.get_jwks()
    
    @pytest.mark.asyncio
    async def test_get_signing_key_success(self, mock_jwks_response):
        """Test successful signing key retrieval"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            config = JWTSecurityConfig()
            manager = JWKSManager("https://auth.localhost/application/o/default/jwks/", config)
            key = await manager.get_signing_key("test-key-id")
            
            assert key is not None
    
    @pytest.mark.asyncio
    async def test_get_signing_key_not_found(self, mock_jwks_response):
        """Test signing key retrieval with key not found"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            config = JWTSecurityConfig()
            manager = JWKSManager("https://auth.localhost/application/o/default/jwks/", config)
            
            with pytest.raises(ValueError, match="Key with ID 'non-existent-key' not found in JWKS"):
                await manager.get_signing_key("non-existent-key")


class TestJWTValidator:
    """Test JWT validator functionality"""
    
    @pytest.mark.asyncio
    async def test_validate_valid_token(self, valid_jwt_token, mock_jwks_response, jwt_config):
        """Test validation of a valid JWT token"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Use the same fixed timestamp as the token
            now = datetime.utcnow()
            with patch('time.time', return_value=now.timestamp()):
                jwks_manager = JWKSManager("https://auth.localhost/application/o/default/jwks/", jwt_config)
                validator = JWTValidator(jwks_manager, jwt_config)
                claims = await validator.validate_token(valid_jwt_token)
                
                assert claims["sub"] == "test-user-id"
                assert claims["email"] == "test@example.com"
                assert claims["iss"] == jwt_config.issuer
                assert claims["aud"] == jwt_config.audience

    @pytest.mark.asyncio
    async def test_validate_expired_token(self, mock_rsa_keys, mock_jwks_response, jwt_config):
        """Test validation with expired token"""
        private_key = mock_rsa_keys['private_key']
        
        # Use a fixed timestamp for consistency
        now = datetime.utcnow()
        
        # Create expired token
        payload = {
            "iss": jwt_config.issuer,
            "aud": jwt_config.audience,
            "sub": "test-user-123",
            "iat": int((now - timedelta(hours=2)).timestamp()),  # 2 hours ago
            "exp": int((now - timedelta(hours=1)).timestamp())   # 1 hour ago (expired)
        }
        
        expired_token = jwt.encode(
            payload,
            private_key,
            algorithm=jwt_config.algorithm,
            headers={"kid": "test-key-id"}
        )
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Mock current time to be after token expiry
            with patch('time.time', return_value=now.timestamp()):
                jwks_manager = JWKSManager("https://auth.localhost/application/o/default/jwks/", jwt_config)
                validator = JWTValidator(jwks_manager, jwt_config)
                
                with pytest.raises(jwt.ExpiredSignatureError, match="Signature has expired"):
                    await validator.validate_token(expired_token)

    @pytest.mark.asyncio
    async def test_validate_invalid_issuer(self, mock_rsa_keys, mock_jwks_response, jwt_config):
        """Test validation with invalid issuer"""
        private_key = mock_rsa_keys['private_key']
        
        # Use a fixed timestamp for consistency
        now = datetime.utcnow()
        
        # Create token with wrong issuer
        payload = {
            "iss": "https://wrong.issuer",  # Wrong issuer
            "aud": jwt_config.audience,
            "sub": "test-user-123",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),  # 1 hour from now
        }
        
        invalid_token = jwt.encode(
            payload,
            private_key,
            algorithm=jwt_config.algorithm,
            headers={"kid": "test-key-id"}
        )
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Mock current time to match token iat
            with patch('time.time', return_value=now.timestamp()):
                jwks_manager = JWKSManager("https://auth.localhost/application/o/default/jwks/", jwt_config)
                validator = JWTValidator(jwks_manager, jwt_config)
                
                with pytest.raises(jwt.InvalidIssuerError, match="Invalid issuer"):
                    await validator.validate_token(invalid_token)


class TestJWTHandler:
    """Test JWT handler functionality"""
    
    @pytest.mark.asyncio
    async def test_validate_access_token(self, valid_jwt_token, mock_jwks_response):
        """Test access token validation"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            handler = JWTHandler("https://auth.localhost")
            claims = await handler.validate_access_token(valid_jwt_token)
            
            assert claims["sub"] == "test-user-id"
            assert claims["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_validate_id_token(self, valid_jwt_token, mock_jwks_response):
        """Test ID token validation"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            handler = JWTHandler("https://auth.localhost")
            claims = await handler.validate_id_token(valid_jwt_token)
            
            assert claims["sub"] == "test-user-id"
            assert claims["email"] == "test@example.com"


class TestJWTUtilityFunctions:
    """Test JWT utility functions"""
    
    @pytest.mark.asyncio
    async def test_validate_jwt_token_function(self, valid_jwt_token, mock_jwks_response):
        """Test the validate_jwt_token utility function"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch.dict('os.environ', {'AUTHENTIK_URL': 'https://auth.localhost'}):
                claims = await validate_jwt_token(valid_jwt_token, 'access')
                
                assert claims["sub"] == "test-user-id"
                assert claims["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_jwt_handler_function(self):
        """Test the get_jwt_handler dependency function"""
        with patch.dict('os.environ', {'AUTHENTIK_URL': 'https://auth.localhost'}):
            handler = await get_jwt_handler()
            
            assert isinstance(handler, JWTHandler)
            assert handler.authentik_base_url == "https://auth.localhost"


class TestJWTIntegration:
    """Integration tests for JWT handling"""
    
    @pytest.mark.asyncio
    async def test_full_token_validation_flow(self, valid_jwt_token, mock_jwks_response):
        """Test complete token validation flow"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Test with environment variables
            with patch.dict('os.environ', {
                'AUTHENTIK_URL': 'https://auth.localhost',
                'JWT_ALGORITHM': 'RS256',
                'AUTHENTIK_ISSUER': 'https://auth.localhost/application/o/default/',
                'JWT_AUDIENCE': 'rag-system'
            }):
                # Create handler
                handler = JWTHandler("https://auth.localhost")
                
                # Validate token
                claims = await handler.validate_access_token(valid_jwt_token)
                
                # Verify claims
                assert claims["sub"] == "test-user-id"
                assert claims["email"] == "test@example.com"
                assert claims["azp"] == "fastapi-client"
                assert "openid" in claims["scope"]
                assert "email" in claims["scope"]
                assert "profile" in claims["scope"]
                assert "rag:api" in claims["scope"]
    
    @pytest.mark.asyncio
    async def test_token_caching_behavior(self, valid_jwt_token, mock_jwks_response):
        """Test that JWKS are cached properly"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            handler = JWTHandler("https://auth.localhost")
            
            # First validation should fetch JWKS
            claims1 = await handler.validate_access_token(valid_jwt_token)
            
            # Second validation should use cached JWKS
            claims2 = await handler.validate_access_token(valid_jwt_token)
            
            # Should only call the JWKS endpoint once due to caching
            assert mock_get.call_count == 1
            assert claims1["sub"] == claims2["sub"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
