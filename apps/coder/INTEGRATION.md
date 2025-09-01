# Refact.ai Integration with Zoi Ecosystem

This document describes how Refact.ai is integrated with the Zoi ecosystem services for seamless AI-powered coding assistance.

## 🏗️ Integration Architecture

```mermaid
graph TB
    subgraph "Zoi Core Services"
        PG[PostgreSQL<br/>Database]
        RD[Redis<br/>Cache]
        LLM[LiteLLM<br/>Gateway]
        QD[Qdrant<br/>Vector DB]
    end
    
    subgraph "Refact Services"
        RS[Refact Server<br/>:7400]
        RA[Refact Agent<br/>:7401]
        RG[Refact GUI<br/>:7402]
        RD_DOC[Refact Docs<br/>:7403]
    end
    
    subgraph "External Clients"
        IDE[IDE Plugins<br/>VS Code, JetBrains]
        WEB[Web Browser<br/>Chat Interface]
    end
    
    RS --> PG
    RS --> RD
    RS --> LLM
    RA --> RS
    RA --> PG
    RA --> RD
    RA --> QD
    RG --> RS
    RG --> RA
    IDE --> RA
    WEB --> RG
```

## 🔗 Service Integrations

### PostgreSQL Database Integration
- **Purpose**: Persistent storage for user data, chat sessions, code completions, and embeddings
- **Database**: `refact` (auto-created)
- **Connection**: `postgresql://postgres:litellm_password123@postgres:5432/refact`
- **Tables**:
  - `users` - User accounts and API keys
  - `models` - Available AI models configuration
  - `chat_sessions` - Chat history and context
  - `code_completions` - Code completion analytics
  - `code_embeddings` - Code embeddings for similarity search

### Redis Cache Integration
- **Purpose**: Session management, caching, and real-time data
- **Connection**: `redis://redis:6379`
- **Usage**:
  - Code completion caching
  - Session state management
  - Real-time chat message queuing
  - Model response caching

### LiteLLM Gateway Integration
- **Purpose**: Unified AI model access and routing
- **Endpoint**: `http://litellm:4000`
- **API Key**: `sk-wqn0xwq_vha4MVM2yzw`
- **Features**:
  - Automatic model selection via `zoi-auto`
  - Local model access (Ollama)
  - Cloud model access (OpenAI, Anthropic)
  - Request logging and monitoring
  - Cost tracking and budgeting

### Qdrant Vector Database Integration
- **Purpose**: Code similarity search and RAG (Retrieval-Augmented Generation)
- **Endpoint**: `http://qdrant:6333`
- **Collection**: `refact_code_embeddings`
- **Features**:
  - Code semantic search
  - Context-aware completions
  - Similar code discovery
  - Documentation search

## 🚀 Service Configuration

### Refact Server (Port 7400)
```yaml
Environment Variables:
  - REFACT_DATABASE_HOST=postgres
  - REFACT_DATABASE_NAME=refact
  - LITELLM_BASE_URL=http://litellm:4000
  - REDIS_HOST=redis
  - REFACT_ADMIN_TOKEN=refact-admin-token-zoi-2024-secure

Features:
  - Model management and fine-tuning
  - User authentication and authorization
  - Chat session management
  - Code completion analytics
  - Integration with external APIs
```

### Refact Agent (Port 7401)
```yaml
Environment Variables:
  - REFACT_SERVER_URL=http://refact-server:8008
  - OPENAI_API_BASE=http://litellm:4000/v1
  - DATABASE_URL=postgresql://postgres:litellm_password123@postgres:5432/refact
  - REDIS_URL=redis://redis:6379

Features:
  - LSP server for IDE integration
  - Real-time code completion
  - AST parsing and indexing
  - Tool integrations (Git, Docker, etc.)
  - Context-aware chat
```

### Refact GUI (Port 7402)
```yaml
Environment Variables:
  - NEXT_PUBLIC_API_URL=http://refact-server:8008
  - NEXT_PUBLIC_AGENT_URL=http://refact-agent:8001
  - NEXT_PUBLIC_LITELLM_URL=http://litellm:4000

Features:
  - Interactive chat interface
  - Code highlighting and editing
  - File management
  - Real-time collaboration
  - Model selection and configuration
```

## 🔧 Configuration Files

### Agent Configuration (`config/bring-your-own-key.yaml`)
```yaml
litellm:
  chat_endpoint: "http://litellm:4000/v1/chat/completions"
  api_key: "sk-wqn0xwq_vha4MVM2yzw"
  running_models:
    - zoi-auto
    - qwen2.5-coder:7b-instruct
    - gpt-4o
    - claude-3-5-sonnet-20241022

database:
  type: "postgresql"
  url: "postgresql://postgres:litellm_password123@postgres:5432/refact"

vector_db:
  type: "qdrant"
  url: "http://qdrant:6333"
  collection_name: "refact_code_embeddings"
```

## 🌐 Network Configuration

### Internal Communication
- All services communicate over the `zoi-network` Docker network
- Services use internal hostnames (postgres, redis, litellm, qdrant)
- No external network access required for core functionality

### External Access
- **Refact Server**: `http://localhost:7400` or `http://refact.zoi.local`
- **Refact Agent**: `http://localhost:7401` or `http://refact-agent.zoi.local`
- **Refact Chat**: `http://localhost:7402` or `http://refact-chat.zoi.local`
- **Documentation**: `http://localhost:7403` or `http://refact-docs.zoi.local`

### Traefik Integration
```yaml
Labels:
  - "traefik.enable=true"
  - "traefik.http.routers.refact-server.rule=Host(`refact.zoi.local`)"
  - "traefik.http.routers.refact-server.entrypoints=web"
```

## 🔐 Security Configuration

### Authentication
- **Admin Token**: `refact-admin-token-zoi-2024-secure`
- **Database**: PostgreSQL with password authentication
- **API Keys**: LiteLLM master key for model access
- **CORS**: Configured for local development domains

### Network Security
- Services isolated in Docker network
- No direct external database access
- API endpoints protected with authentication
- Rate limiting enabled

## 📊 Monitoring and Health Checks

### Health Endpoints
- **Refact Server**: `GET /health`
- **Refact Agent**: `GET /health`
- **Refact GUI**: `GET /health`
- **Documentation**: `GET /health`

### Monitoring Scripts
- `scripts/health-check.sh` - Comprehensive health monitoring
- `scripts/setup-integrations.sh` - Integration verification
- Docker Compose health checks for all services

### Logging
- Centralized logging via Docker Compose
- JSON structured logs for better parsing
- Log levels configurable via environment variables
- Error tracking and alerting

## 🚀 Deployment Process

### 1. Prerequisites
```bash
# Ensure core Zoi services are running
docker compose up -d postgres redis litellm qdrant

# Verify network exists
docker network create zoi-network
```

### 2. Build and Deploy
```bash
# Build Refact services
docker compose build

# Start Refact services
docker compose up -d

# Verify integration
./scripts/setup-integrations.sh
```

### 3. Health Verification
```bash
# Run health check
./scripts/health-check.sh

# Continuous monitoring
./scripts/health-check.sh continuous
```

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker compose logs refact-server

# Check dependencies
docker compose ps postgres redis litellm

# Restart service
docker compose restart refact-server
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
docker compose exec postgres psql -U postgres -d refact -c "SELECT 1;"

# Check database exists
docker compose exec postgres psql -U postgres -l | grep refact
```

#### LiteLLM Integration Issues
```bash
# Test LiteLLM health
curl http://localhost:7010/health

# Test models endpoint
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
     http://localhost:7010/v1/models
```

### Performance Optimization

#### Resource Allocation
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ system memory
- **GPU**: 8GB+ VRAM for local models
- **Storage**: SSD recommended for database and models

#### Caching Configuration
- Redis cache TTL: 3600 seconds
- Code completion cache: Enabled
- Model response cache: Enabled
- Vector embedding cache: Enabled

## 📚 Additional Resources

- [Refact.ai Documentation](http://localhost:7403)
- [LiteLLM Integration Guide](../core/README.md)
- [PostgreSQL Configuration](../../config/postgres/README.md)
- [Zoi Ecosystem Overview](../../README.md)
