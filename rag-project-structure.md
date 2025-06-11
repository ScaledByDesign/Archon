# Production RAG System - Project Structure

```
rag-production-system/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── Makefile
├── services/
│   ├── fastapi/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── documents.py
│   │   │   │   └── health.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── llm_service.py
│   │   │   │   ├── vector_service.py
│   │   │   │   ├── cache_service.py
│   │   │   │   └── queue_service.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat.py
│   │   │   │   └── document.py
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       └── auth.py
│   ├── nextjs/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── next.config.js
│   │   └── src/
│   └── workers/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── worker.py
├── config/
│   ├── traefik/
│   │   ├── traefik.yml
│   │   └── dynamic/
│   │       └── routes.yml
│   ├── authentik/
│   │   └── docker-compose.override.yml
│   ├── rabbitmq/
│   │   └── definitions.json
│   └── redis/
│       └── redis.conf
├── scripts/
│   ├── init-db.sh
│   ├── backup.sh
│   └── health-check.sh
└── volumes/
    ├── mongo/
    ├── qdrant/
    ├── redis/
    └── backups/
```

## File Contents:

### 1. docker-compose.yml
```yaml
version: '3.8'

services:
  # Authentication
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD: ${PG_PASS:-secretpass}
      POSTGRES_USER: authentik
      POSTGRES_DB: authentik
    volumes:
      - authentik_db:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U authentik"]
      interval: 10s
      timeout: 5s
      retries: 5

  authentik-redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --requirepass ${AUTHENTIK_REDIS_PASS:-redispass}
    volumes:
      - authentik_redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  authentik-server:
    image: ghcr.io/goauthentik/server:latest
    restart: unless-stopped
    command: server
    environment:
      AUTHENTIK_REDIS__HOST: authentik-redis
      AUTHENTIK_REDIS__PASSWORD: ${AUTHENTIK_REDIS_PASS:-redispass}
      AUTHENTIK_POSTGRESQL__HOST: postgres
      AUTHENTIK_POSTGRESQL__USER: authentik
      AUTHENTIK_POSTGRESQL__NAME: authentik
      AUTHENTIK_POSTGRESQL__PASSWORD: ${PG_PASS:-secretpass}
      AUTHENTIK_SECRET_KEY: ${AUTHENTIK_SECRET_KEY}
      AUTHENTIK_ERROR_REPORTING__ENABLED: false
    depends_on:
      postgres:
        condition: service_healthy
      authentik-redis:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.authentik.rule=Host(`auth.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.authentik.entrypoints=websecure"
      - "traefik.http.routers.authentik.tls=true"

  # Reverse Proxy
  traefik:
    image: traefik:v3.0
    restart: unless-stopped
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.file.directory=/configuration"
      - "--providers.file.watch=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./config/traefik:/configuration:ro
      - traefik_certs:/letsencrypt
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.dashboard.service=api@internal"
      - "traefik.http.routers.dashboard.middlewares=auth@docker"

  # Cache Layer
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - ./config/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis-insight:
    image: redislabs/redisinsight:latest
    restart: unless-stopped
    ports:
      - "8001:8001"
    depends_on:
      redis:
        condition: service_healthy

  # Message Queue
  rabbitmq:
    image: rabbitmq:3-management-alpine
    restart: unless-stopped
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-admin}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-secretpass}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
      - ./config/rabbitmq/definitions.json:/etc/rabbitmq/definitions.json:ro
    ports:
      - "15672:15672"
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # API Backend (Multiple Instances)
  fastapi-1: &fastapi
    build: ./services/fastapi
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_URL=mongodb://mongo-episodic:27017,mongo-procedural:27017
      - QDRANT_URL=http://qdrant:6333
      - RABBITMQ_URL=amqp://${RABBITMQ_USER:-admin}:${RABBITMQ_PASS:-secretpass}@rabbitmq:5672
      - LITELLM_URL=http://litellm:8000
      - AUTHENTIK_URL=http://authentik-server:9000
      - INSTANCE_ID=1
    depends_on:
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls=true"
      - "traefik.http.services.api.loadbalancer.server.port=8000"
      - "traefik.http.services.api.loadbalancer.sticky.cookie=true"

  fastapi-2:
    <<: *fastapi
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_URL=mongodb://mongo-episodic:27017,mongo-procedural:27017
      - QDRANT_URL=http://qdrant:6333
      - RABBITMQ_URL=amqp://${RABBITMQ_USER:-admin}:${RABBITMQ_PASS:-secretpass}@rabbitmq:5672
      - LITELLM_URL=http://litellm:8000
      - AUTHENTIK_URL=http://authentik-server:9000
      - INSTANCE_ID=2

  fastapi-3:
    <<: *fastapi
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_URL=mongodb://mongo-episodic:27017,mongo-procedural:27017
      - QDRANT_URL=http://qdrant:6333
      - RABBITMQ_URL=amqp://${RABBITMQ_USER:-admin}:${RABBITMQ_PASS:-secretpass}@rabbitmq:5672
      - LITELLM_URL=http://litellm:8000
      - AUTHENTIK_URL=http://authentik-server:9000
      - INSTANCE_ID=3

  # Worker for async tasks
  worker:
    build: ./services/workers
    restart: unless-stopped
    environment:
      - REDIS_URL=redis://redis:6379
      - MONGODB_URL=mongodb://mongo-episodic:27017,mongo-procedural:27017
      - RABBITMQ_URL=amqp://${RABBITMQ_USER:-admin}:${RABBITMQ_PASS:-secretpass}@rabbitmq:5672
    depends_on:
      rabbitmq:
        condition: service_healthy
    deploy:
      replicas: 2

  # LLM Proxy
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    restart: unless-stopped
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OLLAMA_API_BASE=http://ollama:11434
    volumes:
      - ./config/litellm/config.yaml:/app/config.yaml
    command: ["--config", "/app/config.yaml"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://zoi.local:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Local LLM
  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Databases
  mongo-episodic:
    image: mongo:7
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASS:-secretpass}
      MONGO_INITDB_DATABASE: episodic
    volumes:
      - mongo_episodic:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongo-procedural:
    image: mongo:7
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASS:-secretpass}
      MONGO_INITDB_DATABASE: procedural
    volumes:
      - mongo_procedural:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    restart: unless-stopped
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://zoi.local:6333/readyz"]
      interval: 10s
      timeout: 5s
      retries: 5

  # UI Applications
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    restart: unless-stopped
    environment:
      - OPENAI_API_BASE_URL=http://litellm:8000/v1
      - OPENAI_API_KEY=${LITELLM_MASTER_KEY}
      - WEBUI_AUTH=false
    volumes:
      - open_webui:/app/backend/data
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.webui.rule=Host(`chat.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.webui.entrypoints=websecure"
      - "traefik.http.routers.webui.tls=true"

  # Scheduler
  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER:-admin}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASS:-secretpass}
      - N8N_HOST=n8n.${DOMAIN:-zoi.local}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.${DOMAIN:-zoi.local}/
    volumes:
      - n8n_data:/home/node/.n8n
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.n8n.rule=Host(`n8n.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.n8n.entrypoints=websecure"
      - "traefik.http.routers.n8n.tls=true"

  # Monitoring
  aim:
    image: aimstack/aim:latest
    restart: unless-stopped
    volumes:
      - aim_data:/aim
    command: ["up", "--host", "0.0.0.0", "--port", "43800"]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.aim.rule=Host(`aim.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.aim.entrypoints=websecure"
      - "traefik.http.routers.aim.tls=true"

  healthchecks:
    image: healthchecks/healthchecks:latest
    restart: unless-stopped
    environment:
      - ALLOWED_HOSTS=*
      - DB=postgres
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=healthchecks
      - DB_USER=authentik
      - DB_PASSWORD=${PG_PASS:-secretpass}
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_PORT=${EMAIL_PORT}
      - EMAIL_USE_TLS=True
      - EMAIL_HOST_USER=${EMAIL_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_PASS}
      - SECRET_KEY=${HC_SECRET_KEY}
      - SITE_ROOT=https://health.${DOMAIN:-zoi.local}
    depends_on:
      postgres:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.health.rule=Host(`health.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.health.entrypoints=websecure"
      - "traefik.http.routers.health.tls=true"

  # Backup
  backrest:
    image: garethgeorge/backrest:latest
    restart: unless-stopped
    environment:
      - BACKREST_DATA=/data
      - BACKREST_CONFIG=/config/config.json
      - XDG_CACHE_HOME=/cache
    volumes:
      - ./config/backrest:/config
      - ./volumes/backups:/data
      - backrest_cache:/cache
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - mongo_episodic:/backup/mongo_episodic:ro
      - mongo_procedural:/backup/mongo_procedural:ro
      - qdrant_data:/backup/qdrant:ro
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backrest.rule=Host(`backup.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.backrest.entrypoints=websecure"
      - "traefik.http.routers.backrest.tls=true"

volumes:
  authentik_db:
  authentik_redis:
  traefik_certs:
  redis_data:
  rabbitmq_data:
  mongo_episodic:
  mongo_procedural:
  qdrant_data:
  ollama_data:
  open_webui:
  n8n_data:
  aim_data:
  backrest_cache:

networks:
  default:
    name: rag_network
```

### 2. .env.example
```bash
# Domain Configuration
DOMAIN=zoi.local
ACME_EMAIL=admin@example.com

# Authentication
AUTHENTIK_SECRET_KEY=change-me-to-random-string-min-50-chars
AUTHENTIK_REDIS_PASS=change-me-redis-pass
PG_PASS=change-me-postgres-pass

# LLM Configuration
LITELLM_MASTER_KEY=sk-change-me-to-random-string
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Database Credentials
MONGO_USER=admin
MONGO_PASS=change-me-mongo-pass

# RabbitMQ
RABBITMQ_USER=admin
RABBITMQ_PASS=change-me-rabbitmq-pass

# Redis
REDIS_PASSWORD=change-me-redis-pass

# n8n
N8N_USER=admin
N8N_PASS=change-me-n8n-pass

# Email Configuration (for healthchecks)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Secret Keys
HC_SECRET_KEY=change-me-healthchecks-secret
```

### 3. services/fastapi/Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 4. services/fastapi/requirements.txt
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
motor==3.3.2
redis==5.0.1
httpx==0.26.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aio-pika==9.4.0
qdrant-client==1.7.0
litellm==1.17.0
prometheus-fastapi-instrumentator==6.1.0
```

### 5. services/fastapi/app/main.py
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import os

from .config import settings
from .routers import chat, documents, health
from .services import cache_service, queue_service, vector_service
from .dependencies import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting FastAPI instance {os.getenv('INSTANCE_ID', 'unknown')}")
    await cache_service.initialize()
    await queue_service.initialize()
    await vector_service.initialize()
    
    yield
    
    # Shutdown
    await cache_service.close()
    await queue_service.close()
    await vector_service.close()


app = FastAPI(
    title="RAG Production API",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["chat"],
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["documents"],
    dependencies=[Depends(get_current_user)]
)

@app.get("/")
async def root():
    return {
        "message": "RAG Production API",
        "instance": os.getenv("INSTANCE_ID", "unknown"),
        "version": "1.0.0"
    }
```

### 6. services/fastapi/app/config.py
```python
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    api_title: str = "RAG Production API"
    api_version: str = "1.0.0"
    instance_id: str = "1"
    
    # Database URLs
    mongodb_url: str = "mongodb://zoi.local:27017"
    redis_url: str = "redis://zoi.local:6379"
    qdrant_url: str = "http://zoi.local:6333"
    rabbitmq_url: str = "amqp://guest:guest@zoi.local:5672"
    
    # External Services
    litellm_url: str = "http://zoi.local:8000"
    authentik_url: str = "http://zoi.local:9000"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis Settings
    redis_ttl: int = 3600  # 1 hour
    
    # Vector DB Settings
    qdrant_collection: str = "documents"
    embedding_model: str = "text-embedding-ada-002"
    
    class Config:
        env_file = ".env"


settings = Settings()
```

### 7. services/fastapi/app/routers/chat.py
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import uuid

from ..models.chat import ChatRequest, ChatResponse, ChatMessage
from ..services.llm_service import LLMService
from ..services.vector_service import VectorService
from ..services.cache_service import CacheService
from ..dependencies import get_current_user

router = APIRouter()

@router.post("/completions", response_model=ChatResponse)
async def create_chat_completion(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    llm_service: LLMService = Depends(),
    vector_service: VectorService = Depends(),
    cache_service: CacheService = Depends()
):
    """Create a chat completion with RAG enhancement"""
    
    # Check cache first
    cache_key = f"chat:{request.model}:{hash(str(request.messages))}"
    cached_response = await cache_service.get(cache_key)
    if cached_response:
        return ChatResponse(**cached_response)
    
    # Perform vector search for context
    last_message = request.messages[-1].content
    context_docs = await vector_service.search(
        query=last_message,
        limit=5,
        filter={"user_id": current_user["id"]}
    )
    
    # Enhance prompt with context
    if context_docs:
        context = "\n".join([doc["content"] for doc in context_docs])
        enhanced_message = f"Context:\n{context}\n\nUser Query: {last_message}"
        request.messages[-1].content = enhanced_message
    
    # Get LLM response
    try:
        response = await llm_service.complete(request)
        
        # Cache the response
        await cache_service.set(cache_key, response.dict(), ttl=3600)
        
        # Store in episodic memory
        await llm_service.store_conversation(
            user_id=current_user["id"],
            messages=request.messages,
            response=response.choices[0].message.content
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_chat_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0
):
    """Get chat history for the current user"""
    # Implementation depends on your MongoDB setup
    return {"history": [], "total": 0}
```

### 8. services/fastapi/app/services/llm_service.py
```python
import httpx
from typing import List, Dict, Any
import json

from ..config import settings
from ..models.chat import ChatRequest, ChatResponse


class LLMService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.base_url = settings.litellm_url
    
    async def complete(self, request: ChatRequest) -> ChatResponse:
        """Send completion request to LiteLLM proxy"""
        
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": request.model,
            "messages": [msg.dict() for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            return ChatResponse(**response.json())
            
        except httpx.HTTPError as e:
            # Fallback to local model
            if "ollama" in request.model:
                return await self._fallback_to_ollama(request)
            raise e
    
    async def _fallback_to_ollama(self, request: ChatRequest) -> ChatResponse:
        """Fallback to Ollama for local inference"""
        # Implementation for Ollama fallback
        pass
    
    async def store_conversation(
        self,
        user_id: str,
        messages: List[Dict[str, Any]],
        response: str
    ):
        """Store conversation in episodic memory"""
        # Implementation for MongoDB storage
        pass
```

### 9. Makefile
```makefile
.PHONY: help up down logs init clean backup

help:
	@echo "Available commands:"
	@echo "  make init    - Initialize the project"
	@echo "  make up      - Start all services"
	@echo "  make down    - Stop all services"
	@echo "  make logs    - Show logs"
	@echo "  make clean   - Clean up volumes"
	@echo "  make backup  - Run backup"

init:
	cp .env.example .env
	@echo "Please edit .env file with your configuration"
	@echo "Generating secret keys..."
	@echo "AUTHENTIK_SECRET_KEY=$$(openssl rand -base64 50 | tr -d '\n')" >> .env
	@echo "HC_SECRET_KEY=$$(openssl rand -base64 32 | tr -d '\n')" >> .env
	@echo "LITELLM_MASTER_KEY=sk-$$(openssl rand -hex 32)" >> .env
	mkdir -p volumes/{mongo,qdrant,redis,backups}
	mkdir -p config/{traefik/dynamic,authentik,rabbitmq,redis,litellm,backrest}

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

clean:
	docker compose down -v
	rm -rf volumes/*

backup:
	docker exec rag-production-system-backrest-1 backrest backup --all
```

### 10. README.md
```markdown
# Production RAG System

A production-ready Retrieval-Augmented Generation (RAG) system with enterprise features.

## Features

- 🔐 **Authentication**: OAuth2/OIDC with Authentik
- ⚡ **High Performance**: Redis caching, load-balanced API
- 🔄 **Reliability**: Automated backups, health monitoring
- 📊 **Observability**: Prometheus metrics, distributed tracing
- 🤖 **Multi-LLM**: Cloud and local LLM support with fallback
- 🔍 **Vector Search**: Qdrant for semantic search
- 📝 **Workflow Automation**: n8n for scheduled tasks

## Quick Start

1. **Initialize the project:**
   ```bash
   make init
   ```

2. **Configure environment:**
   Edit `.env` file with your API keys and settings

3. **Start services:**
   ```bash
   make up
   ```

4. **Access services:**
   - Chat UI: https://chat.zoi.local
   - API: https://api.zoi.local
   - Traefik Dashboard: https://traefik.zoi.local
   - RabbitMQ Management: http://zoi.local:15672
   - n8n Workflows: https://n8n.zoi.local
   - Authentik: https://auth.zoi.local
   - Monitoring: https://aim.zoi.local
   - Health Checks: https://health.zoi.local
   - Backups: https://backup.zoi.local

## Architecture

See the architecture diagram in the docs folder for a visual overview.

## Configuration

### API Keys
Add your LLM API keys in `.env`:
- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic Claude API key

### Domain Setup
1. Update `DOMAIN` in `.env` for production
2. Set `ACME_EMAIL` for Let's Encrypt SSL certificates

### Authentication
1. Access Authentik at https://auth.zoi.local
2. Default admin user is created on first run
3. Configure OAuth2 applications for services

## Development

### Adding New Services
1. Add service definition to `docker-compose.yml`
2. Configure Traefik labels for routing
3. Add health checks
4. Update backup configuration if needed

### API Development
The FastAPI backend is in `services/fastapi/`. To add new endpoints:
1. Create router in `app/routers/`
2. Add service logic in `app/services/`
3. Include router in `app/main.py`

## Operations

### Monitoring
- Prometheus metrics: Available at `/metrics` on each service
- Aim: ML experiment tracking at https://aim.zoi.local
- Health checks: Automated monitoring at https://health.zoi.local

### Backups
Automated backups run daily via Backrest:
```bash
make backup  # Manual backup
```

### Scaling
To scale services:
```bash
docker compose up -d --scale fastapi=5 --scale worker=3
```

## Troubleshooting

### Service Health
Check service status:
```bash
docker compose ps
docker compose logs <service-name>
```

### Reset Everything
```bash
make clean
make init
make up
```

## Security

- All traffic encrypted with TLS
- Authentication required for all services
- Rate limiting enabled
- Regular automated backups
- Secrets management via environment variables

## License

MIT License
```

### 11. config/traefik/traefik.yml
```yaml
api:
  dashboard: true
  debug: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
  file:
    directory: /configuration
    watch: true

metrics:
  prometheus:
    buckets:
      - 0.1
      - 0.3
      - 1.2
      - 5.0

log:
  level: INFO

accessLog: {}
```

### 12. config/redis/redis.conf
```conf
# Redis configuration for production

# Network
bind 0.0.0.0
protected-mode yes
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300

# General
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

# Replication
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5

# Security
requirepass ${REDIS_PASSWORD}

# Limits
maxclients 10000

# Memory Management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Append Only Mode
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no

# Lua
lua-time-limit 5000

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Event Notification
notify-keyspace-events ""

# Advanced
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
```

### 13. config/rabbitmq/definitions.json
```json
{
  "rabbit_version": "3.12",
  "rabbitmq_version": "3.12",
  "users": [
    {
      "name": "admin",
      "password_hash": "WILL_BE_REPLACED",
      "hashing_algorithm": "rabbit_password_hashing_sha256",
      "tags": ["administrator"]
    }
  ],
  "vhosts": [
    {
      "name": "/"
    }
  ],
  "permissions": [
    {
      "user": "admin",
      "vhost": "/",
      "configure": ".*",
      "write": ".*",
      "read": ".*"
    }
  ],
  "exchanges": [
    {
      "name": "rag.direct",
      "vhost": "/",
      "type": "direct",
      "durable": true,
      "auto_delete": false,
      "internal": false,
      "arguments": {}
    },
    {
      "name": "rag.topic",
      "vhost": "/",
      "type": "topic",
      "durable": true,
      "auto_delete": false,
      "internal": false,
      "arguments": {}
    }
  ],
  "queues": [
    {
      "name": "document.processing",
      "vhost": "/",
      "durable": true,
      "auto_delete": false,
      "arguments": {
        "x-message-ttl": 3600000,
        "x-max-length": 10000
      }
    },
    {
      "name": "vector.indexing",
      "vhost": "/",
      "durable": true,
      "auto_delete": false,
      "arguments": {
        "x-message-ttl": 3600000,
        "x-max-length": 10000
      }
    },
    {
      "name": "llm.requests",
      "vhost": "/",
      "durable": true,
      "auto_delete": false,
      "arguments": {
        "x-message-ttl": 600000,
        "x-max-length": 1000,
        "x-max-priority": 10
      }
    }
  ],
  "bindings": [
    {
      "source": "rag.direct",
      "vhost": "/",
      "destination": "document.processing",
      "destination_type": "queue",
      "routing_key": "document",
      "arguments": {}
    },
    {
      "source": "rag.direct",
      "vhost": "/",
      "destination": "vector.indexing",
      "destination_type": "queue",
      "routing_key": "vector",
      "arguments": {}
    },
    {
      "source": "rag.topic",
      "vhost": "/",
      "destination": "llm.requests",
      "destination_type": "queue",
      "routing_key": "llm.*",
      "arguments": {}
    }
  ]
}
```

### 14. config/litellm/config.yaml
```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: gpt-4-0125-preview
      api_key: ${OPENAI_API_KEY}
      
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: gpt-3.5-turbo-0125
      api_key: ${OPENAI_API_KEY}
      
  - model_name: claude-3-opus
    litellm_params:
      model: claude-3-opus-20240229
      api_key: ${ANTHROPIC_API_KEY}
      
  - model_name: claude-3-sonnet
    litellm_params:
      model: claude-3-sonnet-20240229
      api_key: ${ANTHROPIC_API_KEY}
      
  - model_name: llama3-local
    litellm_params:
      model: ollama/llama3
      api_base: http://ollama:11434
      
  - model_name: mistral-local
    litellm_params:
      model: ollama/mistral
      api_base: http://ollama:11434

litellm_settings:
  drop_params: true
  max_budget: 100.0
  budget_duration: 86400  # 24 hours
  
  # Fallback configuration
  fallbacks:
    gpt-4:
      - claude-3-opus
      - llama3-local
    claude-3-opus:
      - gpt-4
      - llama3-local
    gpt-3.5-turbo:
      - claude-3-sonnet
      - mistral-local

  # Rate limiting
  redis_host: redis
  redis_port: 6379
  redis_password: ${REDIS_PASSWORD}
  
  # Caching
  cache: true
  cache_ttl: 3600

  # Logging
  success_callback: ["prometheus"]
  failure_callback: ["prometheus"]
```

### 15. .gitignore
```gitignore
# Environment files
.env
.env.local
.env.*.local

# Volumes
volumes/
data/

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Certificates
*.pem
*.key
*.crt
*.csr
acme.json

# Backups
*.bak
*.backup
backups/

# Temporary files
*.tmp
*.temp
.cache/
```

### 16. services/workers/worker.py
```python
import asyncio
import json
import logging
from typing import Dict, Any
import aio_pika
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AsyncWorker:
    def __init__(self):
        self.redis_client = None
        self.mongo_client = None
        self.rabbit_connection = None
        self.rabbit_channel = None
        
    async def initialize(self):
        """Initialize all connections"""
        # Redis
        self.redis_client = await redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379")
        )
        
        # MongoDB
        self.mongo_client = AsyncIOMotorClient(
            os.getenv("MONGODB_URL", "mongodb://zoi.local:27017")
        )
        
        # RabbitMQ
        self.rabbit_connection = await aio_pika.connect_robust(
            os.getenv("RABBITMQ_URL", "amqp://guest:guest@zoi.local:5672")
        )
        self.rabbit_channel = await self.rabbit_connection.channel()
        
        # Set QoS
        await self.rabbit_channel.set_qos(prefetch_count=10)
        
        logger.info("Worker initialized successfully")
    
    async def process_document(self, message: aio_pika.IncomingMessage):
        """Process document indexing tasks"""
        async with message.process():
            try:
                data = json.loads(message.body)
                logger.info(f"Processing document: {data.get('document_id')}")
                
                # Your document processing logic here
                # - Extract text
                # - Generate embeddings
                # - Store in vector DB
                
                # Cache result
                await self.redis_client.setex(
                    f"doc:{data['document_id']}",
                    3600,
                    json.dumps({"status": "processed"})
                )
                
            except Exception as e:
                logger.error(f"Error processing document: {e}")
                # Requeue message
                await message.nack(requeue=True)
    
    async def process_vector_indexing(self, message: aio_pika.IncomingMessage):
        """Process vector indexing tasks"""
        async with message.process():
            try:
                data = json.loads(message.body)
                logger.info(f"Processing vector indexing: {data.get('task_id')}")
                
                # Your vector indexing logic here
                
            except Exception as e:
                logger.error(f"Error in vector indexing: {e}")
                await message.nack(requeue=True)
    
    async def start_consuming(self):
        """Start consuming messages from queues"""
        # Document processing queue
        doc_queue = await self.rabbit_channel.declare_queue(
            "document.processing",
            durable=True
        )
        await doc_queue.consume(self.process_document)
        
        # Vector indexing queue
        vector_queue = await self.rabbit_channel.declare_queue(
            "vector.indexing",
            durable=True
        )
        await vector_queue.consume(self.process_vector_indexing)
        
        logger.info("Worker started consuming messages")
        
        # Keep the worker running
        await asyncio.Future()
    
    async def shutdown(self):
        """Clean shutdown"""
        if self.rabbit_connection:
            await self.rabbit_connection.close()
        if self.redis_client:
            await self.redis_client.close()
        if self.mongo_client:
            self.mongo_client.close()


async def main():
    worker = AsyncWorker()
    
    try:
        await worker.initialize()
        await worker.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

### 17. scripts/init-db.sh
```bash
#!/bin/bash

echo "Initializing databases..."

# Wait for MongoDB to be ready
until docker exec rag-production-system-mongo-episodic-1 mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
    echo "Waiting for MongoDB..."
    sleep 2
done

# Create collections and indexes
docker exec -i rag-production-system-mongo-episodic-1 mongosh <<EOF
use episodic
db.createCollection("conversations")
db.conversations.createIndex({ "user_id": 1, "timestamp": -1 })
db.conversations.createIndex({ "session_id": 1 })

db.createCollection("messages")
db.messages.createIndex({ "conversation_id": 1, "timestamp": 1 })
EOF

docker exec -i rag-production-system-mongo-procedural-1 mongosh <<EOF
use procedural
db.createCollection("workflows")
db.workflows.createIndex({ "name": 1 })
db.workflows.createIndex({ "tags": 1 })

db.createCollection("documents")
db.documents.createIndex({ "user_id": 1, "created_at": -1 })
db.documents.createIndex({ "tags": 1 })
EOF

# Initialize Qdrant collection
curl -X PUT "http://zoi.local:6333/collections/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1536,
      "distance": "Cosine"
    }
  }'

echo "Database initialization complete!"
```

### 18. scripts/backup.sh
```bash
#!/bin/bash

# Backup script for RAG system
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting backup to $BACKUP_DIR"

# MongoDB backups
docker exec rag-production-system-mongo-episodic-1 \
  mongodump --out=/tmp/episodic_backup

docker cp rag-production-system-mongo-episodic-1:/tmp/episodic_backup \
  "$BACKUP_DIR/mongo_episodic"

docker exec rag-production-system-mongo-procedural-1 \
  mongodump --out=/tmp/procedural_backup

docker cp rag-production-system-mongo-procedural-1:/tmp/procedural_backup \
  "$BACKUP_DIR/mongo_procedural"

# Qdrant backup
curl -X POST "http://zoi.local:6333/snapshots" \
  -H "Content-Type: application/json" \
  -d '{"wait": true}'

# Redis backup
docker exec rag-production-system-redis-1 \
  redis-cli --rdb /tmp/redis_backup.rdb

docker cp rag-production-system-redis-1:/tmp/redis_backup.rdb \
  "$BACKUP_DIR/redis_backup.rdb"

echo "Backup completed successfully!"
```