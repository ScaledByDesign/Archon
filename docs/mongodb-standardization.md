# MongoDB Configuration Standardization

## Overview
This document outlines the comprehensive standardization of MongoDB configurations across all services in the Zoi project to resolve authentication and connectivity issues through consolidation to a single MongoDB instance with multiple databases.

## Architecture Evolution

### Previous Architecture Issues
- Multiple separate MongoDB containers (mongo-episodic, mongo-procedural)
- Complex service dependencies and networking
- Inconsistent authentication across services
- Resource overhead with multiple MongoDB instances

### Current Consolidated Architecture
- **Single MongoDB instance** (`mongo:7`) with multiple databases
- **Database isolation** through separate databases within one instance
- **Unified authentication** using consistent credentials
- **Centralized initialization** with `init-multiple-databases.js` script

## Current Database Structure

The consolidated MongoDB instance contains the following databases:

### 1. **rag_system** (Primary Application Database)
Collections:
- `documents` - Document storage and metadata
- `chunks` - Document chunks with embeddings
- `conversations` - Chat conversation history
- `users` - User management and preferences

### 2. **authentik** (Authentication Service)
Collections:
- `sessions` - User session management
- `users` - Authentication user records

### 3. **n8n** (Workflow Automation)
Collections:
- `workflows` - Workflow definitions
- `executions` - Workflow execution history

### 4. **litellm** (LLM Proxy Service)
Collections:
- `models` - Model configurations
- `usage_logs` - API usage tracking

## Current Configuration

### MongoDB Service (docker-compose.core.yml)
```yaml
mongo:
  image: mongo:7
  container_name: mongo
  environment:
    MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER:-admin}
    MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASS:-change-me-mongo-pass}
  volumes:
    - ./config/mongodb/init-multiple-databases.js:/docker-entrypoint-initdb.d/init-multiple-databases.js:ro
    - mongo_data:/data/db
  networks:
    - zoi_network
  healthcheck:
    test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### FastAPI Service Environment
```yaml
fastapi-1:
  env_file:
    - .env
    - ./config/fastapi/.env
  environment:
    MONGODB_HOST: mongo
    MONGODB_PORT: 27017
    MONGODB_DATABASE: rag_system
```

### Worker Service Environment
```yaml
worker:
  env_file:
    - .env
    - ./config/fastapi/.env
  environment:
    MONGODB_HOST: mongo
    MONGODB_PORT: 27017
    MONGODB_DATABASE: rag_system
```

## Environment Variables Standardization

### Core .env Configuration
```shell
# MongoDB Credentials
MONGO_USER=admin
MONGO_PASS=change-me-mongo-pass

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=change-me-redis-pass
REDIS_DB=0
```

### Service-Specific Configuration (config/fastapi/.env)
```shell
# MongoDB Connection
MONGODB_HOST=mongo
MONGODB_PORT=27017
MONGODB_USERNAME=admin
MONGODB_PASSWORD=change-me-mongo-pass
MONGODB_DATABASE=rag_system

# Redis Connection
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=change-me-redis-pass
REDIS_DB=0
```

## Benefits of Consolidated Architecture

### 1. **Simplified Service Management**
- Single MongoDB container to manage
- Reduced complexity in Docker Compose configurations
- Easier backup and maintenance procedures

### 2. **Consistent Authentication**
- Unified credentials across all database access
- Eliminated authentication mismatches
- Centralized credential management

### 3. **Resource Efficiency**
- Reduced memory and CPU overhead
- Single MongoDB process instead of multiple
- Shared connection pooling and caching

### 4. **Database Isolation**
- Logical separation through database names
- Clear service boundaries maintained
- Easier to manage permissions and access control

## Application Configuration

### FastAPI Settings (src/config/settings.py)
The application uses Pydantic settings to construct MongoDB URLs:

```python
class DatabaseSettings(BaseSettings):
    # MongoDB configuration
    mongodb_url: Optional[str] = None
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_username: str = "admin"
    mongodb_password: str = "password"
    mongodb_database: str = "rag_system"
    
    @property
    def mongo_url(self) -> str:
        if self.mongodb_url:
            return self.mongodb_url
        return f"mongodb://{self.mongodb_username}:{self.mongodb_password}@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"
```

## Multi-Database Support Implementation

For services requiring access to multiple databases:

```python
# Different database connections within same MongoDB instance
episodic_db = mongodb_client["rag_system"] 
procedural_db = mongodb_client["rag_system"]  # Can be separate if needed
auth_db = mongodb_client["authentik"]
workflow_db = mongodb_client["n8n"]
```

## Testing Verification

Current status after consolidation:
- ✅ Single MongoDB container starts successfully
- ✅ Multiple databases initialized correctly
- ✅ FastAPI and Worker services connect successfully
- ✅ Environment variables loaded consistently
- ✅ Authentication works across all services
- ✅ Service health checks pass
- ✅ Database collections created with proper indexes

## Files Modified

1. `docker-compose.core.yml` - Consolidated MongoDB service configuration
2. `config/mongodb/init-multiple-databases.js` - Database initialization script
3. `.env` - Standardized environment variables
4. `config/fastapi/.env` - Service-specific configurations
5. Worker service configuration - Aligned with FastAPI standards

## Outstanding Considerations

1. **Multi-Database FastAPI Usage**: Verify if application logic requires separate episodic/procedural databases
2. **Connection Pooling**: Monitor connection usage with consolidated instance
3. **Backup Strategy**: Implement database-specific backup procedures
4. **Performance Monitoring**: Track performance with multiple databases in single instance
5. **Scaling Strategy**: Plan for horizontal scaling if needed

## Next Steps

1. ✅ Verify Worker service MongoDB authentication
2. ✅ Test document upload and processing workflows
3. ✅ Monitor all service logs for connection issues
4. ⏳ Implement application-level multi-database support if required
5. ⏳ Performance testing with consolidated architecture
6. ⏳ Production deployment verification
