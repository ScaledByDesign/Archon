# Quick Start Guide - Zoi FastAPI Services

## Prerequisites
- Docker and Docker Compose installed
- All code fixes are already applied ✅

## Start All Services

### Option 1: Use the convenience script
```bash
./scripts/start-dev-services.sh
```

### Option 2: Manual startup
```bash
# Start core services
docker-compose up -d postgres redis rabbitmq vault

# Start database services  
docker-compose up -d mongo-episodic mongo-procedural

# Start vector database
docker-compose up -d qdrant

# Start FastAPI services
docker-compose up -d fastapi-1 fastapi-2 fastapi-3
```

## Verify Health
```bash
# Check all services
curl http://localhost:8000/health | jq .
curl http://localhost:8010/health | jq .
curl http://localhost:8020/health | jq .
```

## Service Endpoints
- **FastAPI-1**: http://localhost:8000 (docs: /docs)
- **FastAPI-2**: http://localhost:8010 (docs: /docs)  
- **FastAPI-3**: http://localhost:8020 (docs: /docs)
- **Vault**: http://localhost:8200
- **RabbitMQ Management**: http://localhost:15672
- **Qdrant**: http://localhost:6333

## Expected Health Status
All services should report "healthy" status:
- ✅ MongoDB (episodic & procedural): healthy
- ✅ Redis: healthy
- ✅ PostgreSQL: healthy  
- ✅ Qdrant: healthy
- ⚠️ Vault: not_configured (expected in dev mode)

## Code Fixes Applied
1. Renamed `secrets` module to `zoi_secrets` (avoids Python conflicts)
2. Fixed Vault async authentication initialization
3. Updated health response model for nested dependency structures

All code fixes are permanent and will persist across builds! 🎉
