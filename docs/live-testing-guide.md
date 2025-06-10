# Live Testing Guide

This guide explains how to run tests against live services instead of mock data, enabling real-world integration testing for the Production RAG System.

## Overview

The live testing system allows you to validate functionality against actual Docker services, providing more accurate testing of real-world scenarios including:

- **JWT authentication** with Authentik
- **Database operations** with MongoDB and Redis
- **Vector operations** with Qdrant
- **LLM interactions** with LiteLLM
- **Service health** and performance validation

## Quick Start

### 1. Start Services

```bash
# Start all required services
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
./scripts/run-live-tests.sh --help
```

### 2. Run Live Tests

```bash
# Run all live tests
./scripts/run-live-tests.sh

# Run specific test categories
./scripts/run-live-tests.sh auth
./scripts/run-live-tests.sh database
./scripts/run-live-tests.sh integration

# Run with environment flag
LIVE_TESTING=true pytest tests/integration/ -v -m live
```

## Configuration

### Environment Variables

The live testing system uses these environment variables:

```bash
# Core Testing
LIVE_TESTING=true                    # Enable live testing mode
PYTHONPATH=/path/to/project/src      # Python module path

# Authentication (Authentik)
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=RS256
JWT_ISSUER_URL=http://localhost:9443/application/o/fastapi-client/
JWT_AUDIENCE=fastapi-client
JWKS_URL=http://localhost:9443/application/o/fastapi-client/jwks/

# Service URLs
VAULT_ADDR=http://localhost:8200
QDRANT_URL=http://localhost:6333
REDIS_URL=redis://localhost:6379
MONGODB_URL=mongodb://localhost:27017
LITELLM_API_KEY=test-key

# Security
SESSION_SECRET_KEY=your-session-secret
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Docker Services

Required services from `docker-compose.yml`:

- **authentik-server** (9443) - Authentication service
- **postgres** (PostgreSQL) - Authentik database  
- **authentik-redis** (6379) - Authentik Redis cache
- **fastapi-1** (8000) - Main FastAPI application
- **redis** (6379) - Application Redis cache
- **vault** (8200) - Secret management
- **qdrant** (6333) - Vector database
- **mongo-episodic** (27017) - MongoDB episodic memory
- **mongo-procedural** (27018) - MongoDB procedural memory
- **litellm** (4000) - LLM proxy service

## Test Structure

### Test Categories

Tests are organized by category and marked with pytest markers:

```python
@pytest.mark.live
@pytest.mark.auth
async def test_jwt_validation():
    """Test JWT validation with live Authentik"""
    pass

@pytest.mark.live  
@pytest.mark.database
async def test_mongodb_operations():
    """Test MongoDB operations with live database"""
    pass

@pytest.mark.live
@pytest.mark.integration
async def test_full_workflow():
    """Test complete workflow with all services"""
    pass
```

### Test Files

- `tests/conftest.py` - Main test configuration
- `tests/conftest_live.py` - Live service fixtures
- `tests/integration/test_live_authentication.py` - Authentication tests
- `tests/unit/test_jwt_handler.py` - JWT handler tests (dual mode)

### Fixtures

Live testing fixtures are automatically available when `LIVE_TESTING=true`:

```python
# Available fixtures for live testing
live_fastapi_client    # HTTP client for FastAPI
live_redis_client      # Redis connection
live_mongodb_client    # MongoDB connection  
live_qdrant_client     # Qdrant vector client
live_vault_client      # Vault secrets client
live_jwt_token_generator  # Generate test JWT tokens
```

## Running Tests

### Using the Test Script

The `scripts/run-live-tests.sh` script provides a comprehensive testing solution:

```bash
# Full test suite with service health checks
./scripts/run-live-tests.sh

# Authentication tests only
./scripts/run-live-tests.sh auth

# Database integration tests
./scripts/run-live-tests.sh database

# LLM integration tests  
./scripts/run-live-tests.sh llm

# Performance benchmarks
./scripts/run-live-tests.sh performance
```

### Using pytest Directly

For more control, use pytest with markers:

```bash
# Set environment and run live tests
export LIVE_TESTING=true
export PYTHONPATH=$(pwd)/src

# Run all live tests
pytest tests/ -v -m live

# Run specific test categories
pytest tests/ -v -m "live and auth"
pytest tests/ -v -m "live and database"
pytest tests/ -v -m "live and integration"

# Run with coverage
pytest tests/ -v -m live --cov=src --cov-report=html

# Run performance tests
pytest tests/ -v -m "live and performance" --benchmark-only
```

### Test Filtering

Use pytest expressions to filter tests:

```bash
# Run tests matching pattern
pytest tests/ -v -k "test_jwt" -m live

# Run tests excluding certain patterns
pytest tests/ -v -m live --ignore=tests/unit/

# Run integration tests only
pytest tests/integration/ -v -m live
```

## Service Health Monitoring

### Health Check Endpoints

Live tests verify service health before running:

```bash
# FastAPI application
curl http://localhost:8000/health

# Authentik authentication  
curl http://localhost:9443

# Vault secrets
curl http://localhost:8200/v1/sys/health

# Qdrant vector database
curl http://localhost:6333

# LiteLLM proxy
curl http://localhost:4000/health
```

### Manual Health Verification

```bash
# Check Redis connectivity
docker-compose exec redis redis-cli -a "change-me-redis-pass" ping

# Check MongoDB connectivity  
docker-compose exec mongo-episodic mongosh --eval "db.runCommand('ping')"

# Check service status
docker-compose ps
```

## Debugging Live Tests

### View Service Logs

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f fastapi-1
docker-compose logs -f authentik-server
docker-compose logs -f redis
```

### Common Issues and Solutions

**Services not starting:**
```bash
# Check Docker resources
docker system df
docker system prune

# Restart services
docker-compose down
docker-compose up -d
```

**Authentication failures:**
```bash
# Check Authentik configuration
docker-compose logs authentik-server | grep ERROR

# Verify JWT configuration
curl -s http://localhost:9443/application/o/fastapi-client/jwks/ | jq
```

**Database connection issues:**
```bash
# Check MongoDB status
docker-compose exec mongo-episodic mongosh --eval "db.runCommand('ismaster')"

# Check Redis connectivity
docker-compose exec redis redis-cli -a "change-me-redis-pass" info
```

**Network connectivity:**
```bash
# Test service connectivity from container
docker-compose exec fastapi-1 curl http://redis:6379
docker-compose exec fastapi-1 curl http://mongo-episodic:27017
```

## Performance Testing

### Benchmark Configuration

Performance tests use pytest-benchmark:

```bash
# Run performance tests only
pytest tests/ -v -m "live and performance" --benchmark-only

# Save benchmark results
pytest tests/ -v -m "live and performance" --benchmark-json=benchmarks.json

# Compare benchmarks
pytest-benchmark compare benchmarks.json
```

### Performance Metrics

Tests measure:
- **JWT validation speed** (tokens/second)
- **Database operation latency** (ms per operation)
- **Vector search performance** (queries/second)
- **Memory usage** during operations
- **Service startup times**

## Test Data Management

### Data Isolation

Live tests use isolated test data:

```python
# Each test uses unique identifiers
user_id = f"test-user-{uuid.uuid4()}"
session_id = f"test-session-{int(time.time())}"

# Cleanup after tests
@pytest.fixture(scope="function", autouse=True)
async def cleanup_test_data():
    yield
    # Cleanup logic here
```

### Data Persistence

By default, test data is cleaned up after each test. To persist data for debugging:

```bash
# Skip cleanup (for debugging)
SKIP_CLEANUP=true pytest tests/ -v -m live

# Manual cleanup
./scripts/cleanup-test-data.sh
```

## Continuous Integration

### CI Configuration

For CI/CD pipelines:

```yaml
# .github/workflows/live-tests.yml
name: Live Integration Tests

on: [push, pull_request]

jobs:
  live-tests:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Compose
        run: |
          docker-compose up -d
          sleep 30
      
      - name: Run live tests
        run: |
          export LIVE_TESTING=true
          ./scripts/run-live-tests.sh
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results-*.xml
```

### Test Reporting

Generate comprehensive test reports:

```bash
# HTML coverage report
pytest tests/ -v -m live --cov=src --cov-report=html

# JUnit XML for CI
pytest tests/ -v -m live --junit-xml=test-results.xml

# Combined report
./scripts/run-live-tests.sh > test-report.txt 2>&1
```

## Best Practices

### Test Design

1. **Use proper test isolation** - Each test should be independent
2. **Include cleanup** - Always clean up test data
3. **Handle service unavailability** - Skip tests gracefully if services are down
4. **Use realistic data** - Test with data similar to production
5. **Monitor performance** - Include performance assertions

### Service Management

1. **Health checks first** - Always verify service health before testing
2. **Graceful degradation** - Handle partial service failures
3. **Resource management** - Monitor Docker resource usage
4. **Log collection** - Preserve logs for debugging

### Development Workflow

1. **Start with mock tests** - Ensure logic works before live testing
2. **Run live tests locally** - Validate before CI/CD
3. **Monitor test execution** - Watch for performance regressions
4. **Regular maintenance** - Keep test data clean and services updated

## Troubleshooting

### Common Error Messages

**"Service not ready"**: Wait for services to fully start (30+ seconds)
**"Authentication failed"**: Check Authentik configuration and JWT settings
**"Connection refused"**: Verify service ports and Docker networking
**"Permission denied"**: Check file permissions on test scripts

### Debug Commands

```bash
# Check all service health
curl -f http://localhost:8000/health
curl -f http://localhost:9443
curl -f http://localhost:8200/v1/sys/health

# Test service connectivity
docker-compose exec fastapi-1 nc -zv redis 6379
docker-compose exec fastapi-1 nc -zv mongo-episodic 27017

# View service configurations
docker-compose config

# Check resource usage
docker stats
```

For additional support, check the service logs and ensure all environment variables are properly configured.
