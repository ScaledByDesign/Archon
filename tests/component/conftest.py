"""
Component test specific fixtures and configuration.
"""
import pytest
from unittest.mock import AsyncMock, Mock
import asyncio

@pytest.fixture
async def vault_config():
    """Vault configuration for component testing."""
    return {
        "url": "http://zoi.local:8200",
        "token": "test-vault-token",
        "namespace": "test",
        "verify": False
    }

@pytest.fixture
async def qdrant_config():
    """Qdrant configuration for component testing."""
    return {
        "url": "http://zoi.local:6333",
        "api_key": None,
        "timeout": 30,
        "prefer_grpc": False
    }

@pytest.fixture
async def real_vault_client(vault_config):
    """Real Vault client for component testing (mocked for safety)."""
    # In real component tests, this would create actual clients
    # For now, we'll use enhanced mocks that behave like real clients
    mock_client = AsyncMock()
    
    # Mock Vault authentication
    mock_client.is_authenticated.return_value = True
    mock_client.sys.is_initialized.return_value = True
    mock_client.sys.is_sealed.return_value = False
    
    # Mock secret operations
    mock_client.secrets.kv.v2.read_secret_version.return_value = {
        'data': {
            'data': {
                'username': 'test_user',
                'password': 'test_password',
                'api_key': 'test_api_key'
            },
            'metadata': {
                'version': 1,
                'created_time': '2024-01-01T00:00:00Z'
            }
        }
    }
    
    mock_client.secrets.kv.v2.create_or_update_secret.return_value = {
        'data': {
            'version': 1
        }
    }
    
    return mock_client

@pytest.fixture
async def real_qdrant_client(qdrant_config):
    """Real Qdrant client for component testing (mocked for safety)."""
    mock_client = AsyncMock()
    
    # Mock collection operations
    mock_client.get_collections.return_value = Mock(
        collections=[
            Mock(name="test_collection"),
            Mock(name="documents"),
            Mock(name="embeddings")
        ]
    )
    
    mock_client.collection_exists.return_value = True
    mock_client.count.return_value = Mock(count=100)
    
    # Mock search operations
    mock_client.search.return_value = [
        Mock(
            id="test_point_1",
            score=0.95,
            payload={"content": "Test content 1"}
        ),
        Mock(
            id="test_point_2", 
            score=0.89,
            payload={"content": "Test content 2"}
        )
    ]
    
    # Mock upsert operations
    mock_client.upsert.return_value = Mock(
        operation_id=123,
        status="completed"
    )
    
    return mock_client
