"""
Shared test fixtures and configuration for Production RAG System tests.

Supports both mock testing (default) and live service testing.
Set LIVE_TESTING=true to use live Docker services.
"""
import asyncio
import os
import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock
from typing import AsyncGenerator, Generator

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Determine testing mode
LIVE_TESTING = os.getenv("LIVE_TESTING", "false").lower() == "true"

if LIVE_TESTING:
    # Import live service fixtures
    from .conftest_live import *
    print(" LIVE TESTING MODE: Using real Docker services")
else:
    print(" MOCK TESTING MODE: Using mocked services")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def testing_mode():
    """Indicate current testing mode."""
    return "live" if LIVE_TESTING else "mock"

# Mock fixtures (used when LIVE_TESTING=false)
@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    if LIVE_TESTING:
        pytest.skip("Using live services - mock env vars not needed")
        
    return {
        "VAULT_ADDR": "http://zoi.local:8200",
        "VAULT_TOKEN": "test-token",
        "QDRANT_URL": "http://zoi.local:6333",
        "REDIS_URL": "redis://zoi.local:6379",
        "MONGODB_URL": "mongodb://zoi.local:27017",
        "LITELLM_API_KEY": "test-api-key",
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "JWT_SECRET_KEY": "test-jwt-secret-key-for-testing-only",
        "SESSION_SECRET_KEY": "test-session-secret-key-for-testing-only"
    }

@pytest.fixture
async def mock_vault_client():
    """Mock HashiCorp Vault client."""
    if LIVE_TESTING:
        pytest.skip("Using live vault client")
        
    mock_client = AsyncMock()
    mock_client.is_authenticated.return_value = True
    mock_client.sys.is_initialized.return_value = True
    mock_client.sys.is_sealed.return_value = False
    mock_client.secrets.kv.v2.read_secret_version.return_value = {
        'data': {
            'data': {
                'username': 'test_user',
                'password': 'test_pass'
            }
        }
    }
    yield mock_client

@pytest.fixture
async def mock_redis_client():
    """Mock Redis client."""
    if LIVE_TESTING:
        pytest.skip("Using live redis client")
        
    mock_client = AsyncMock()
    mock_client.ping.return_value = "PONG"
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = 0
    yield mock_client

@pytest.fixture
async def mock_qdrant_client():
    """Mock Qdrant vector database client."""
    if LIVE_TESTING:
        pytest.skip("Using live qdrant client")
        
    mock_client = Mock()
    mock_client.get_collections.return_value = Mock()
    mock_client.create_collection.return_value = True
    mock_client.upsert.return_value = True
    mock_client.search.return_value = []
    yield mock_client

@pytest.fixture
async def mock_jwt_handler():
    """Mock JWT handler for authentication tests."""
    if LIVE_TESTING:
        pytest.skip("Using live JWT handler")
        
    mock_handler = AsyncMock()
    mock_handler.validate_access_token.return_value = {
        "sub": "test-user-123",
        "aud": "test-audience",
        "iss": "test-issuer",
        "exp": 9999999999,
        "iat": 1234567890,
        "scope": "openid email profile rag:api"
    }
    mock_handler.create_access_token.return_value = "mock-jwt-token"
    yield mock_handler

# Test configuration
def pytest_configure(config):
    """Configure test markers and options."""
    config.addinivalue_line(
        "markers", "mock: mark test as using mock services"
    )
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
    """Auto-mark and filter tests based on mode and markers."""
    for item in items:
        # Skip live tests in mock mode
        if not LIVE_TESTING and item.get_closest_marker("live"):
            item.add_marker(pytest.mark.skip(reason="Live testing disabled"))
        
        # Skip mock tests in live mode  
        if LIVE_TESTING and item.get_closest_marker("mock"):
            item.add_marker(pytest.mark.skip(reason="Mock testing disabled in live mode"))
        
        # Auto-mark based on file location
        if "live" in str(item.fspath):
            item.add_marker(pytest.mark.live)
        elif "mock" in str(item.fspath):
            item.add_marker(pytest.mark.mock)

@pytest.fixture(scope="session", autouse=True)
def testing_setup():
    """Setup testing environment."""
    mode = "LIVE" if LIVE_TESTING else "MOCK"
    print(f"\n{'='*50}")
    print(f" Production RAG System Test Suite")
    print(f" Testing Mode: {mode}")
    print(f"{'='*50}")
    
    if LIVE_TESTING:
        print(" Testing against live Docker services")
        print("  Ensure all services are running: docker-compose up -d")
    else:
        print(" Testing with mocked services")
        print(" Set LIVE_TESTING=true for integration testing")
    
    print(f"{'='*50}\n")

@pytest.fixture
def sample_jwt_payload():
    """Sample JWT payload for testing."""
    return {
        "sub": "test_user_id",
        "email": "test@example.com",
        "name": "Test User",
        "roles": ["user"],
        "permissions": ["read", "write"],
        "exp": 9999999999,  # Far future expiration
        "iat": 1640995200,  # Fixed issued at time
        "iss": "http://auth.zoi.local",
        "aud": "fastapi-client"
    }

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "id": "test_doc_id",
        "title": "Test Document",
        "content": "This is a test document for testing purposes.",
        "metadata": {
            "author": "Test Author",
            "created_at": "2024-01-01T00:00:00Z",
            "tags": ["test", "sample"]
        }
    }

@pytest.fixture
def sample_vector_embedding():
    """Sample vector embedding for testing."""
    return [0.1, 0.2, 0.3, 0.4, 0.5] * 256  # 1280 dimensions

@pytest.fixture(autouse=True)
def setup_test_env(mock_env_vars, monkeypatch):
    """Automatically set up test environment variables."""
    for key, value in mock_env_vars.items():
        monkeypatch.setenv(key, value)
