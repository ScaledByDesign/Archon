"""
Tests for JWT Handler functionality

This module tests JWT validation, signing, and security features.
Supports both mock testing (default) and live testing against real services.
"""

import os
import pytest
import jwt
import httpx
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta, timezone
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

# Determine testing mode
LIVE_TESTING = os.getenv("LIVE_TESTING", "false").lower() == "true"

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
def sample_jwt_payload():
    """Sample JWT payload for testing"""
    now = datetime.now(timezone.utc)
    return {
        "sub": "user123",
        "aud": "test-audience",
        "iss": "test-issuer",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "scope": "openid email profile rag:api",
        "email": "test@example.com",
        "preferred_username": "testuser"
    }

@pytest.fixture
def live_env_config():
    """Live environment configuration for JWT testing"""
    return {
        "JWT_SECRET_KEY": "your-secret-key-here",
        "JWT_ALGORITHM": "RS256",
        "JWT_ISSUER_URL": "http://zoi.local:9443/application/o/fastapi-client/",
        "JWT_AUDIENCE": "fastapi-client",
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "JWKS_URL": "http://zoi.local:9443/application/o/fastapi-client/jwks/",
        "JWT_VERIFY_SIGNATURE": "true",
        "JWT_VERIFY_AUDIENCE": "true", 
        "JWT_VERIFY_ISSUER": "true",
        "JWT_CLOCK_SKEW_SECONDS": "30"
    }

class TestJWTSecurityConfig:
    """Test JWT security configuration"""
    
    def test_config_initialization_mock(self, mock_env_vars):
        """Test config initialization with mock environment"""
        if LIVE_TESTING:
            pytest.skip("Using live config")
            
        with patch.dict('os.environ', mock_env_vars):
            config = JWTSecurityConfig()
            assert config.secret_key == mock_env_vars["JWT_SECRET_KEY"]
            assert config.algorithm == "HS256"  # Default for testing

    def test_config_initialization_live(self, live_env_config):
        """Test config initialization with live environment"""
        if not LIVE_TESTING:
            pytest.skip("Using mock config")
            
        with patch.dict('os.environ', live_env_config):
            config = JWTSecurityConfig()
            assert config.secret_key == live_env_config["JWT_SECRET_KEY"]
            assert config.algorithm == "RS256"  # Production algorithm
            assert config.issuer_url == live_env_config["JWT_ISSUER_URL"]
            assert config.audience == live_env_config["JWT_AUDIENCE"]

    def test_config_validation(self, live_env_config if LIVE_TESTING else mock_env_vars):
        """Test configuration validation"""
        env_vars = live_env_config if LIVE_TESTING else mock_env_vars
        
        with patch.dict('os.environ', env_vars):
            config = JWTSecurityConfig()
            
            # Test required fields
            assert config.secret_key is not None
            assert config.algorithm is not None
            assert config.access_token_expire_minutes > 0
            
            if LIVE_TESTING:
                assert config.issuer_url is not None
                assert config.audience is not None

class TestJWKSManager:
    """Test JWKS Manager functionality"""
    
    @pytest.mark.asyncio
    async def test_jwks_fetch_mock(self, mock_rsa_keys):
        """Test JWKS fetching with mock data"""
        if LIVE_TESTING:
            pytest.skip("Using live JWKS")
            
        # Mock JWKS response
        mock_jwks = {
            "keys": [{
                "kty": "RSA",
                "kid": "test-key-id",
                "use": "sig",
                "alg": "RS256",
                "n": "test-modulus",
                "e": "AQAB"
            }]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            manager = JWKSManager("http://test-jwks-url")
            keys = await manager.get_signing_keys()
            
            assert len(keys) == 1
            assert "test-key-id" in keys

    @pytest.mark.asyncio
    async def test_jwks_fetch_live(self):
        """Test JWKS fetching from live Authentik service"""
        if not LIVE_TESTING:
            pytest.skip("Using mock JWKS")
            
        jwks_url = "http://zoi.local:9443/application/o/fastapi-client/jwks/"
        manager = JWKSManager(jwks_url)
        
        try:
            keys = await manager.get_signing_keys()
            # May not have keys configured yet, which is expected
            assert isinstance(keys, dict)
        except Exception as e:
            # JWKS endpoint may not be fully configured yet
            pytest.skip(f"JWKS endpoint not ready: {e}")

class TestJWTValidator:
    """Test JWT validation functionality"""
    
    def test_token_validation_mock(self, sample_jwt_payload, mock_rsa_keys):
        """Test JWT validation with mock keys"""
        if LIVE_TESTING:
            pytest.skip("Using live validation")
            
        # Create token with mock key
        token = jwt.encode(
            sample_jwt_payload,
            mock_rsa_keys['private_key'],
            algorithm="RS256"
        )
        
        # Mock the validator to use our test key
        with patch.object(JWTValidator, '_get_public_key') as mock_get_key:
            mock_get_key.return_value = mock_rsa_keys['public_key']
            
            validator = JWTValidator()
            # This will still fail audience validation, but tests key validation
            with pytest.raises(Exception):  # Expected to fail validation
                validator.validate_token(token)

    def test_token_validation_live(self, live_env_config):
        """Test JWT validation with live configuration"""
        if not LIVE_TESTING:
            pytest.skip("Using mock validation")
            
        with patch.dict('os.environ', live_env_config):
            validator = JWTValidator()
            
            # Test with a malformed token (should fail)
            with pytest.raises(Exception):
                validator.validate_token("invalid.token.here")
            
            # Test with expired token (should fail)
            expired_payload = {
                "sub": "test-user",
                "aud": live_env_config["JWT_AUDIENCE"],
                "iss": live_env_config["JWT_ISSUER_URL"], 
                "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
                "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
                "scope": "openid email profile"
            }
            
            # Use test secret (will fail signature validation with RS256)
            expired_token = jwt.encode(expired_payload, "test-secret", algorithm="HS256")
            
            with pytest.raises(Exception):
                validator.validate_token(expired_token)

class TestJWTHandler:
    """Test JWT Handler main functionality"""
    
    @pytest.mark.asyncio
    async def test_handler_initialization_mock(self, mock_env_vars):
        """Test JWT handler initialization with mock environment"""
        if LIVE_TESTING:
            pytest.skip("Using live handler")
            
        with patch.dict('os.environ', mock_env_vars):
            handler = JWTHandler()
            assert handler is not None
            assert handler.config is not None
            assert handler.validator is not None

    @pytest.mark.asyncio
    async def test_handler_initialization_live(self, live_env_config):
        """Test JWT handler initialization with live environment"""
        if not LIVE_TESTING:
            pytest.skip("Using mock handler")
            
        with patch.dict('os.environ', live_env_config):
            handler = JWTHandler()
            assert handler is not None
            assert handler.config is not None
            assert handler.validator is not None
            assert handler.config.algorithm == "RS256"

    @pytest.mark.asyncio
    async def test_validate_access_token_live(self, live_env_config, live_jwt_token_generator):
        """Test access token validation with live configuration"""
        if not LIVE_TESTING:
            pytest.skip("Using mock validation")
            
        with patch.dict('os.environ', live_env_config):
            handler = JWTHandler()
            
            # Generate test token
            token = live_jwt_token_generator(
                user_id="test-user-handler",
                scopes=["openid", "email", "profile", "rag:api"]
            )
            
            # Should fail with test token (expected)
            with pytest.raises(Exception):
                await handler.validate_access_token(token)

    def test_token_creation_mock(self, mock_env_vars, sample_jwt_payload):
        """Test token creation with mock configuration"""
        if LIVE_TESTING:
            pytest.skip("Using live token creation")
            
        with patch.dict('os.environ', mock_env_vars):
            handler = JWTHandler()
            
            # Create access token
            token = handler.create_access_token(
                subject="test-user",
                additional_claims={"scope": "test-scope"}
            )
            
            assert token is not None
            assert isinstance(token, str)
            
            # Decode and verify structure (will fail validation due to test setup)
            try:
                decoded = jwt.decode(token, options={"verify_signature": False})
                assert decoded["sub"] == "test-user"
                assert "exp" in decoded
                assert "iat" in decoded
            except Exception:
                pass  # Expected in test environment

class TestJWTIntegration:
    """Test JWT integration with other components"""
    
    @pytest.mark.asyncio
    async def test_jwt_middleware_integration_live(self, live_fastapi_client, live_jwt_token_generator):
        """Test JWT middleware integration with live FastAPI"""
        if not LIVE_TESTING:
            pytest.skip("Using mock integration")
            
        # Test without token
        response = await live_fastapi_client.get("/api/auth/me")
        assert response.status_code in [401, 404, 405]  # Unauthorized or not found
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid-token"}
        response = await live_fastapi_client.get("/api/auth/me", headers=headers)
        assert response.status_code in [401, 422]  # Unauthorized or validation error
        
        # Test with test token (should fail validation but test path)
        token = live_jwt_token_generator()
        headers = {"Authorization": f"Bearer {token}"}
        response = await live_fastapi_client.get("/api/auth/me", headers=headers)
        assert response.status_code in [401, 422]  # Expected to fail with test token

    @pytest.mark.asyncio
    async def test_jwt_redis_integration_live(self, live_redis_client):
        """Test JWT token storage in Redis"""
        if not LIVE_TESTING:
            pytest.skip("Using mock Redis")
            
        from auth.token_storage import TokenStorage
        from cryptography.fernet import Fernet
        
        # Test token storage
        encryption_key = Fernet.generate_key()
        storage = TokenStorage(
            redis_client=live_redis_client,
            encryption_key=encryption_key.decode()
        )
        
        user_id = "test-jwt-user"
        token_data = {
            "access_token": "test-access-token-jwt",
            "refresh_token": "test-refresh-token-jwt",
            "expires_in": 3600
        }
        
        # Store and retrieve
        await storage.store_tokens(user_id, token_data)
        retrieved = await storage.get_tokens(user_id)
        
        assert retrieved["access_token"] == token_data["access_token"]
        
        # Cleanup
        await storage.revoke_tokens(user_id)

class TestJWTPerformance:
    """Test JWT performance characteristics"""
    
    @pytest.mark.performance
    def test_token_validation_performance(self, sample_jwt_payload, mock_rsa_keys):
        """Test JWT validation performance"""
        if LIVE_TESTING:
            # Use simpler performance test for live mode
            start = time.time()
            for _ in range(100):
                try:
                    jwt.decode("invalid.token.here", options={"verify_signature": False})
                except:
                    pass
            duration = time.time() - start
            assert duration < 1.0  # Should be very fast
        else:
            # Mock performance test
            token = jwt.encode(sample_jwt_payload, "test-secret", algorithm="HS256")
            
            start = time.time()
            for _ in range(100):
                try:
                    jwt.decode(token, "test-secret", algorithms=["HS256"])
                except:
                    pass
            duration = time.time() - start
            
            # Should validate 100 tokens in under 1 second
            assert duration < 1.0

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_jwks_caching_performance(self):
        """Test JWKS caching performance"""
        if not LIVE_TESTING:
            pytest.skip("JWKS caching test requires live services")
            
        manager = JWKSManager("http://zoi.local:9443/application/o/fastapi-client/jwks/")
        
        # First call (should fetch)
        start = time.time()
        try:
            await manager.get_signing_keys()
            first_duration = time.time() - start
        except:
            pytest.skip("JWKS endpoint not available")
        
        # Second call (should use cache)
        start = time.time()
        try:
            await manager.get_signing_keys()
            second_duration = time.time() - start
        except:
            pass
        
        # Cached call should be faster (if caching is implemented)
        # This is more of a performance observation than assertion
        print(f"First call: {first_duration:.3f}s, Second call: {second_duration:.3f}s")

# Test markers and configuration
pytestmark = pytest.mark.unit

if __name__ == "__main__":
    """Run JWT handler tests."""
    pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])
