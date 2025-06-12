"""
Unit test specific fixtures and configuration.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI application for unit testing."""
    mock_app = Mock()
    mock_app.state = Mock()
    return mock_app

@pytest.fixture
def mock_jwt_handler():
    """Mock JWT handler for unit testing."""
    mock_handler = Mock()
    mock_handler.create_token.return_value = "mock_jwt_token"
    mock_handler.verify_token.return_value = {
        "sub": "test_user",
        "exp": 9999999999
    }
    mock_handler.decode_token.return_value = {
        "sub": "test_user",
        "email": "test@example.com"
    }
    return mock_handler

@pytest.fixture
def mock_oauth_client():
    """Mock OAuth client for unit testing."""
    mock_client = Mock()
    mock_client.get_authorization_url.return_value = "http://auth.example.com/authorize"
    mock_client.exchange_code.return_value = {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "id_token": "mock_id_token"
    }
    return mock_client
