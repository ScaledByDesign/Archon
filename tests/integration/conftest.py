"""
Integration test specific fixtures and configuration.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any

@pytest.fixture(scope="session")
async def docker_services():
    """Mock docker services for integration testing."""
    # This would normally start real Docker services for integration tests
    # For now, we'll use mocks to avoid requiring Docker for tests
    return {
        "redis": {"host": "zoi.local", "port": 6379},
        "qdrant": {"host": "zoi.local", "port": 6333},
        "mongodb": {"host": "zoi.local", "port": 27017},
        "vault": {"host": "zoi.local", "port": 8200}
    }

@pytest.fixture
async def litellm_client():
    """Mock LiteLLM client for integration testing."""
    mock_client = AsyncMock()
    mock_client.chat_completion.return_value = {
        "choices": [{
            "message": {
                "content": "This is a test response from the mock LLM."
            }
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        }
    }
    mock_client.embedding.return_value = {
        "data": [{
            "embedding": [0.1] * 1536
        }]
    }
    return mock_client

@pytest.fixture
async def document_processor():
    """Mock document processor for integration testing."""
    mock_processor = AsyncMock()
    mock_processor.process_document.return_value = {
        "id": "test_doc_id",
        "chunks": [
            {
                "content": "Test chunk content",
                "embedding": [0.1] * 1536,
                "metadata": {"chunk_id": 0}
            }
        ]
    }
    return mock_processor

@pytest.fixture
async def vector_store():
    """Mock vector store for integration testing."""
    mock_store = AsyncMock()
    mock_store.search.return_value = [
        {
            "id": "test_result_id",
            "score": 0.95,
            "payload": {
                "content": "Test search result",
                "metadata": {"source": "test_doc"}
            }
        }
    ]
    mock_store.upsert.return_value = True
    return mock_store
