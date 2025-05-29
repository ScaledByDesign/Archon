# Testing Guide - Production RAG System

## Overview
This document provides comprehensive information about testing in the Production RAG System, including test organization, execution, and maintenance after the recent FastAPI code structure merging.

## Test Organization

### Directory Structure
```
tests/
├── __init__.py                 # Main test package
├── conftest.py                # Shared fixtures and configuration
├── unit/                      # Unit tests for individual components
│   ├── __init__.py
│   ├── conftest.py           # Unit test specific fixtures
│   └── test_jwt_handler.py   # JWT authentication unit tests
├── integration/               # Integration tests for component interactions
│   ├── __init__.py
│   ├── conftest.py           # Integration test specific fixtures
│   ├── test_document_pipeline.py        # Document processing pipeline
│   ├── test_litellm_connection.py       # LiteLLM connectivity tests
│   ├── test_litellm_integration_final.py # Complete LiteLLM integration
│   ├── test_model_router.py             # Model routing functionality
│   ├── test_model_router_docker.py      # Docker-based model routing
│   ├── test_router_direct.py            # Direct router testing
│   └── test_simple_router.py            # Basic router functionality
├── component/                 # Component tests for external services
│   ├── __init__.py
│   ├── conftest.py           # Component test specific fixtures
│   ├── test_vault.py         # HashiCorp Vault integration
│   └── test_qdrant.py        # Qdrant vector database integration
└── scripts/                   # Script-based tests and utilities
    ├── __init__.py
    ├── test-fastapi-integration.sh      # FastAPI service integration
    ├── test-jwt-security.py             # JWT security flow testing
    ├── test-litellm-client.py           # LiteLLM client functionality
    ├── test-litellm-integration-complete.py # Complete LiteLLM tests
    ├── test-litellm-local.py            # Local LLM testing (Ollama)
    ├── test-litellm-simple.py           # Basic LiteLLM functionality
    ├── test-oauth-setup.sh              # OAuth2 setup and configuration
    ├── test-oauth2-flow.py              # OAuth2 authentication flow
    └── test-vault-integration.sh        # Vault integration testing
```

## Test Categories

### 1. Unit Tests (`/tests/unit/`)
**Purpose**: Test individual functions, classes, and modules in isolation.

**Current Tests**:
- `test_jwt_handler.py` - JWT token creation, validation, and security

**Characteristics**:
- Fast execution (< 1 second per test)
- No external dependencies
- Mock all external services
- High code coverage focus

**Running Unit Tests**:
```bash
# Run all unit tests
make test-unit

# Or directly with pytest
pytest tests/unit/ -v
```

### 2. Integration Tests (`/tests/integration/`)
**Purpose**: Test interactions between components and data flow through the system.

**Current Tests**:
- Document processing pipeline end-to-end
- LiteLLM integration with multiple providers
- Model routing and selection logic
- API routing and middleware

**Characteristics**:
- Moderate execution time (1-30 seconds per test)
- May use mock services or lightweight test doubles
- Focus on component interaction
- Test business logic flows

**Running Integration Tests**:
```bash
# Run all integration tests
make test-integration

# Skip slow tests
pytest tests/integration/ -v -m "not slow"
```

### 3. Component Tests (`/tests/component/`)
**Purpose**: Test integration with external services and infrastructure components.

**Current Tests**:
- HashiCorp Vault secret management
- Qdrant vector database operations

**Characteristics**:
- Slower execution (5-60 seconds per test)
- May require external services (mocked for safety)
- Test real service contracts
- Focus on error handling and edge cases

**Running Component Tests**:
```bash
# Run all component tests
make test-component

# Or directly with pytest
pytest tests/component/ -v
```

### 4. Script Tests (`/tests/scripts/`)
**Purpose**: Test deployment scripts, integration utilities, and system-level functionality.

**Current Tests**:
- OAuth2 setup automation
- Vault integration scripts
- LiteLLM client utilities
- FastAPI service integration

**Characteristics**:
- Variable execution time
- May require Docker services
- Test deployment and configuration
- Shell and Python script testing

**Running Script Tests**:
```bash
# Run all script tests
make test-scripts

# Run specific script
python tests/scripts/test-oauth2-flow.py
```

## Testing Framework

### Primary Framework: pytest
- **Version**: 7.4.3
- **Async Support**: pytest-asyncio==0.21.1
- **Mocking**: pytest-mock==3.12.0

### Configuration
**pytest.ini** - Main pytest configuration with:
- Test discovery patterns
- Coverage settings
- Async mode configuration
- Custom markers for test categorization

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.component` - Component tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.requires_docker` - Tests requiring Docker services
- `@pytest.mark.requires_vault` - Tests requiring HashiCorp Vault
- `@pytest.mark.requires_qdrant` - Tests requiring Qdrant
- `@pytest.mark.requires_llm` - Tests requiring LLM services

## Fixtures and Test Utilities

### Global Fixtures (`tests/conftest.py`)
- `mock_env_vars` - Standard environment variables for testing
- `mock_vault_client` - HashiCorp Vault client mock
- `mock_qdrant_client` - Qdrant vector store client mock
- `mock_redis_client` - Redis client mock
- `mock_mongodb_client` - MongoDB client mock
- `sample_jwt_payload` - JWT token payload for testing
- `sample_document` - Document data for testing
- `sample_vector_embedding` - Vector embedding data

### Unit Test Fixtures (`tests/unit/conftest.py`)
- `mock_fastapi_app` - FastAPI application mock
- `mock_jwt_handler` - JWT handler with token operations
- `mock_oauth_client` - OAuth client mock

### Integration Test Fixtures (`tests/integration/conftest.py`)
- `docker_services` - Mock Docker service configuration
- `litellm_client` - LiteLLM client for integration testing
- `document_processor` - Document processing pipeline mock
- `vector_store` - Vector store operations mock

### Component Test Fixtures (`tests/component/conftest.py`)
- `vault_config` - Vault configuration for component testing
- `qdrant_config` - Qdrant configuration for component testing
- `real_vault_client` - Enhanced Vault client mock
- `real_qdrant_client` - Enhanced Qdrant client mock

## Running Tests

### Quick Start
```bash
# Install dependencies
make install-test-deps

# Run basic unit tests
make test

# Run all tests
make test-all

# Run with coverage
make test-coverage
```

### Makefile Commands
```bash
make test              # Run unit tests only
make test-unit         # Run unit tests
make test-integration  # Run integration tests
make test-component    # Run component tests
make test-scripts      # Run script-based tests
make test-all          # Run all Python tests
make test-coverage     # Run with coverage report
make test-slow         # Run slow tests
make test-docker       # Run Docker-dependent tests
make test-file FILE=path/to/test.py    # Run specific file
make test-pattern PATTERN=test_name    # Run tests matching pattern
make lint-tests        # Lint test code
make format-tests      # Format test code
make clean-test        # Clean test artifacts
make validate-tests    # Validate test setup
```

### Manual pytest Commands
```bash
# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v --tb=short
pytest tests/component/ -v

# Run with markers
pytest -m "unit" -v
pytest -m "integration and not slow" -v
pytest -m "requires_docker" -v

# Run specific test
pytest tests/unit/test_jwt_handler.py::test_create_token -v

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run tests matching pattern
pytest -k "jwt" -v
pytest -k "vault or qdrant" -v
```

## Test Environment Setup

### Environment Variables
Tests automatically set up mock environment variables through the `setup_test_env` fixture:
- Database connection strings
- API keys (mocked)
- JWT secrets
- Service URLs

### Dependencies
All test dependencies are included in `requirements.txt`:
```text
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
```

### Import Path Setup
Tests automatically configure Python import paths to access the `src/` directory through `conftest.py` fixtures.

## Test Data and Mocking

### Mock Strategy
- **Unit Tests**: Mock all external dependencies
- **Integration Tests**: Use lightweight test doubles
- **Component Tests**: Enhanced mocks that behave like real services
- **Script Tests**: May use real services in test environment

### Test Data
- Sample JWT payloads for authentication testing
- Mock document data for pipeline testing
- Vector embeddings for search testing
- Configuration data for service testing

## Coverage and Quality

### Coverage Targets
- **Unit Tests**: > 90% line coverage
- **Integration Tests**: > 80% feature coverage
- **Component Tests**: > 95% service interaction coverage

### Quality Checks
- Code formatting with `black`
- Linting with `flake8`
- Type checking with `mypy`
- Security scanning for test credentials

## Post-Merge Testing Status

### ✅ Verified After FastAPI Merging
- All test files successfully moved to organized structure
- Import paths updated for new directory structure
- Pytest configuration created and validated
- Makefile commands functional
- Fixture system established

### 🔄 Updates Made
- Moved tests from root level to categorized directories
- Fixed import paths in component tests
- Created comprehensive fixture system
- Added test markers for categorization
- Established proper test configuration

### 🎯 Next Steps
1. Run test validation to ensure all tests pass
2. Update any remaining import issues
3. Add missing test markers to existing tests
4. Implement coverage tracking
5. Create CI/CD integration for automated testing

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure `src/` is in Python path (handled by conftest.py)
2. **Missing Dependencies**: Run `make install-test-deps`
3. **Docker Service Tests**: Ensure Docker services are running
4. **Environment Variables**: Check mock environment setup in conftest.py

### Debug Commands
```bash
# Validate test setup
make validate-tests

# Show test structure
make show-tests

# Run single test with debug output
pytest tests/unit/test_jwt_handler.py::test_create_token -v -s

# Check import paths
python -c "import sys; print('\\n'.join(sys.path))"
```

## Contributing to Tests

### Adding New Tests
1. Choose appropriate category (unit/integration/component/scripts)
2. Follow naming convention: `test_*.py`
3. Use appropriate fixtures from conftest.py
4. Add proper test markers
5. Update this documentation

### Test Writing Guidelines
- Write clear, descriptive test names
- Use appropriate fixtures instead of manual setup
- Mock external dependencies appropriately
- Add docstrings for complex test logic
- Follow existing code style and patterns

This testing guide ensures comprehensive coverage of the Production RAG System while maintaining organization and efficiency after the recent FastAPI code structure merging.
