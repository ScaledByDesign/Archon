"""
Live service test configuration for Production RAG System.

This configuration connects to actual Docker services instead of using mocks,
providing real-world integration testing.
"""
import asyncio
import os
import sys
import time
import httpx
import pytest
import redis.asyncio as redis
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Service Configuration - Matches docker-compose.yml
LIVE_SERVICES = {
    "authentik": {
        "url": "http://zoi.local:9443",
        "health_endpoint": "/api/v3/core/applications/",
        "timeout": 30
    },
    "fastapi": {
        "url": "http://zoi.local:8000",
        "health_endpoint": "/health",
        "timeout": 10
    },
    "vault": {
        "url": "http://zoi.local:8200",
        "health_endpoint": "/v1/sys/health",
        "timeout": 10
    },
    "qdrant": {
        "url": "http://zoi.local:6333",
        "health_endpoint": "/",
        "timeout": 10
    },
    "redis": {
        "url": "redis://zoi.local:6379",
        "password": "change-me-redis-pass",
        "timeout": 5
    },
    "mongodb": {
        "url": "mongodb://zoi.local:27017",
        "timeout": 10
    },
    "litellm": {
        "url": "http://zoi.local:4000",
        "health_endpoint": "/health",
        "timeout": 15
    },
    "rabbitmq": {
        "url": "http://zoi.local:15672",
        "health_endpoint": "/api/overview",
        "timeout": 10
    },
    "traefik": {
        "url": "http://zoi.local:8080",
        "health_endpoint": "/ping",
        "timeout": 5
    }
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def live_env_vars():
    """Live environment variables for Docker services."""
    return {
        "VAULT_ADDR": "http://zoi.local:8200",
        "VAULT_TOKEN": "vault-root-token-change-me-in-production",
        "QDRANT_URL": "http://zoi.local:6333",
        "REDIS_URL": "redis://:change-me-redis-pass@zoi.local:6379",
        "MONGODB_EPISODIC_URL": "mongodb://zoi.local:27018/episodic_memory",
        "MONGODB_PROCEDURAL_URL": "mongodb://zoi.local:27019/procedural_memory", 
        "LITELLM_API_KEY": "sk-change-me-to-random-string",
        "LITELLM_BASE_URL": "http://zoi.local:4000",
        "AUTHENTIK_BASE_URL": "http://zoi.local:9443",
        "JWT_SECRET_KEY": "your-secret-key-here",
        "SESSION_SECRET_KEY": "change-me-to-a-long-random-session-secret-key-at-least-32-chars",
        "FASTAPI_OAUTH_CLIENT_ID": "fastapi-client",
        "FASTAPI_OAUTH_CLIENT_SECRET": "temporary-secret-for-testing-oauth2-flow",
        "FASTAPI_OAUTH_REDIRECT_URI": "http://zoi.local:8000/api/auth/callback"
    }

@pytest.fixture(scope="session")
async def service_health_check():
    """Check if all required services are running and healthy."""
    async with httpx.AsyncClient() as client:
        unhealthy_services = []
        
        for service_name, config in LIVE_SERVICES.items():
            try:
                if service_name == "redis":
                    # Special handling for Redis
                    redis_client = redis.from_url(
                        config["url"],
                        password=config["password"],
                        socket_timeout=config["timeout"]
                    )
                    await redis_client.ping()
                    await redis_client.close()
                    print(f"✅ {service_name} is healthy")
                else:
                    # HTTP health check
                    url = f"{config['url']}{config['health_endpoint']}"
                    response = await client.get(
                        url,
                        timeout=config["timeout"],
                        follow_redirects=True
                    )
                    if response.status_code < 500:  # Accept redirects and auth challenges
                        print(f"✅ {service_name} is healthy (status: {response.status_code})")
                    else:
                        unhealthy_services.append(service_name)
                        print(f"❌ {service_name} is unhealthy (status: {response.status_code})")
                        
            except Exception as e:
                unhealthy_services.append(service_name)
                print(f"❌ {service_name} is unreachable: {e}")
        
        if unhealthy_services:
            pytest.skip(f"Required services are not healthy: {', '.join(unhealthy_services)}")
        
        return True

@pytest.fixture
async def live_redis_client(service_health_check):
    """Live Redis client connected to Docker service."""
    client = redis.from_url(
        "redis://:change-me-redis-pass@zoi.local:6379",
        decode_responses=True
    )
    
    # Test connection
    await client.ping()
    
    yield client
    
    # Cleanup test data
    await client.flushdb()
    await client.close()

@pytest.fixture
async def live_vault_client(service_health_check):
    """Live HashiCorp Vault client."""
    import hvac
    
    client = hvac.Client(
        url="http://zoi.local:8200",
        token="vault-root-token-change-me-in-production"
    )
    
    # Test connection
    assert client.sys.is_initialized()
    assert client.is_authenticated()
    
    yield client

@pytest.fixture
async def live_qdrant_client(service_health_check):
    """Live Qdrant vector database client."""
    from qdrant_client import QdrantClient
    
    client = QdrantClient(url="http://zoi.local:6333")
    
    # Test connection
    health = client.get_cluster_info()
    assert health is not None
    
    yield client

@pytest.fixture
async def live_fastapi_client(service_health_check):
    """Live FastAPI client for integration testing."""
    async with httpx.AsyncClient(
        base_url="http://zoi.local:8000",
        timeout=30.0
    ) as client:
        # Test connection
        response = await client.get("/health")
        assert response.status_code in [200, 401]  # May require auth
        
        yield client

@pytest.fixture
async def live_litellm_client(service_health_check):
    """Live LiteLLM client for model testing."""
    async with httpx.AsyncClient(
        base_url="http://zoi.local:4000",
        timeout=60.0,
        headers={"Authorization": "Bearer sk-change-me-to-random-string"}
    ) as client:
        # Test connection
        response = await client.get("/health")
        assert response.status_code == 200
        
        yield client

@pytest.fixture
async def live_authentik_client(service_health_check):
    """Live Authentik client for authentication testing."""
    async with httpx.AsyncClient(
        base_url="http://zoi.local:9443",
        timeout=30.0,
        follow_redirects=False  # Important for OAuth flows
    ) as client:
        yield client

@pytest.fixture
async def live_mongodb_client(service_health_check):
    """Live MongoDB client for database testing."""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    # Test both episodic and procedural databases
    episodic_client = AsyncIOMotorClient("mongodb://zoi.local:27018")
    procedural_client = AsyncIOMotorClient("mongodb://zoi.local:27019")
    
    # Test connections
    await episodic_client.admin.command('ping')
    await procedural_client.admin.command('ping')
    
    clients = {
        "episodic": episodic_client,
        "procedural": procedural_client
    }
    
    yield clients
    
    # Cleanup
    episodic_client.close()
    procedural_client.close()

@pytest.fixture
def live_jwt_token_generator():
    """Generate live JWT tokens for testing authentication."""
    import jwt
    from datetime import datetime, timedelta, timezone
    
    def generate_token(
        user_id: str = "test-user-123",
        scopes: list = None,
        expires_in: int = 3600,
        issuer: str = "http://zoi.local:9443/application/o/fastapi-client/",
        audience: str = "fastapi-client"
    ) -> str:
        if scopes is None:
            scopes = ["openid", "email", "profile", "rag:api"]
            
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "aud": audience,
            "iss": issuer,
            "iat": now.timestamp(),
            "exp": (now + timedelta(seconds=expires_in)).timestamp(),
            "scope": " ".join(scopes),
            "email": "test@example.com",
            "preferred_username": "testuser",
            "name": "Test User"
        }
        
        # Use a test secret - in production this would come from JWKS
        return jwt.encode(payload, "test-secret", algorithm="HS256")
    
    return generate_token

@pytest.fixture
async def live_oauth2_flow_tester(live_authentik_client, live_fastapi_client):
    """Test OAuth2 flow with live services."""
    async def test_oauth_flow():
        # Step 1: Initiate OAuth2 flow
        response = await live_fastapi_client.get("/api/auth/login")
        assert response.status_code == 307  # Redirect to Authentik
        
        auth_url = response.headers["location"]
        assert "zoi.local:9443" in auth_url
        assert "response_type=code" in auth_url
        assert "client_id=fastapi-client" in auth_url
        
        # Step 2: Check if redirect to Authentik is accessible
        response = await live_authentik_client.get(auth_url)
        assert response.status_code in [200, 302]  # Login page or redirect
        
        return {
            "auth_url": auth_url,
            "fastapi_redirect": response.status_code == 307,
            "authentik_accessible": response.status_code in [200, 302]
        }
    
    return test_oauth_flow

# Test markers for different service types
pytest_plugins = []

def pytest_configure(config):
    """Configure test markers."""
    config.addinivalue_line(
        "markers", "live: mark test as requiring live services"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "database: mark test as database related" 
    )
    config.addinivalue_line(
        "markers", "llm: mark test as LLM related"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )

def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on file location."""
    for item in items:
        # Auto-mark tests in live test files
        if "live" in str(item.fspath):
            item.add_marker(pytest.mark.live)
