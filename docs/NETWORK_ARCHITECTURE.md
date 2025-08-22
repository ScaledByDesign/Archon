# 🌐 Zoi Ecosystem Network Architecture

## Overview

The Zoi ecosystem has been simplified to use a unified network architecture that enables seamless communication between all services while maintaining security and performance.

## 🏗️ Network Design

### **Single Shared Network: `zoi-network`**

All services across the ecosystem communicate through a single Docker bridge network called `zoi-network`. This design provides:

- **Simplified Configuration**: No complex network routing or external dependencies
- **Direct Service Communication**: Services can reach each other by container name
- **Consistent Naming**: All services use the same network namespace
- **Easy Troubleshooting**: Single network to monitor and debug

### **Network Topology**

```
┌─────────────────────────────────────────────────────────────────┐
│                        zoi-network                              │
│                     (Bridge Network)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ LLM Stack   │  │ Platform    │  │ Tools Stack │             │
│  │             │  │ Stack       │  │             │             │
│  │ • LiteLLM   │  │ • Traefik   │  │ • n8n       │             │
│  │ • vLLM      │  │ • Authentik │  │ • OpenWebUI │             │
│  │ • Ollama    │  │ • PostgreSQL│  │ • LobeChat  │             │
│  │ • PostgreSQL│  │ • Redis     │  │             │             │
│  │ • Redis     │  │ • MongoDB   │  │             │             │
│  │ • Qdrant    │  │ • Dashy     │  │             │             │
│  │ • LangFlow  │  │             │  │             │             │
│  │ • Neo4j     │  └─────────────┘  └─────────────┘             │
│  └─────────────┘                                               │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐                              │
│  │ Archon MCP  │  │ Monitoring  │                              │
│  │             │  │ Stack       │                              │
│  │ • Server    │  │ • Prometheus│                              │
│  │ • MCP       │  │ • Grafana   │                              │
│  │ • Agents    │  │ • Exporters │                              │
│  │ • UI        │  │ • AlertMgr  │                              │
│  └─────────────┘  └─────────────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Service Communication Matrix

### **Database Connections**

| Service | Database | Connection String |
|---------|----------|-------------------|
| **LiteLLM** | PostgreSQL | `postgresql://litellm:litellm_password123@postgres:5432/litellm` |
| **LangFlow** | PostgreSQL | `postgresql://postgres:litellm_password123@postgres:5432/langflow` |
| **n8n** | PostgreSQL | `postgresql://postgres:litellm_password123@postgres:5432/n8n` |
| **OpenWebUI** | PostgreSQL | `postgresql://postgres:litellm_password123@postgres:5432/openwebui` |
| **LobeChat** | PostgreSQL | `postgresql://postgres:litellm_password123@postgres:5432/lobechat` |
| **Authentik** | PostgreSQL | Platform PostgreSQL (separate instance) |

### **AI Service Connections**

| Service | Target | Connection |
|---------|--------|------------|
| **Tools → LiteLLM** | AI Gateway | `http://litellm:4000/v1` |
| **LiteLLM → vLLM** | Inference | `http://vllm:8000/v1` |
| **LiteLLM → Ollama** | Local Models | `http://ollama:11434` |
| **Services → Qdrant** | Vector DB | `http://qdrant:6333` |
| **Services → Neo4j** | Graph DB | `http://neo4j:7474` |

### **Monitoring Connections**

| Exporter | Target | Connection |
|----------|--------|------------|
| **Redis Exporter** | Redis | `redis://redis:6379` |
| **Postgres Exporter** | PostgreSQL | `postgresql://litellm:litellm_password123@postgres:5432/litellm` |
| **Prometheus** | All Exporters | Direct container names |

## 🚀 Startup Sequence

### **Recommended Order**

1. **LLM Stack** (Foundation)
   ```bash
   cd apps/llm-local
   docker compose up -d
   ```

2. **Platform Stack** (Infrastructure)
   ```bash
   cd apps/platform
   docker compose up -d
   ```

3. **Tools Stack** (Applications)
   ```bash
   cd apps/tools
   docker compose up -d
   ```

4. **Archon MCP** (Knowledge Management)
   ```bash
   cd apps/archon-mcp
   docker compose up -d
   ```

5. **Monitoring Stack** (Observability)
   ```bash
   cd apps/monitor
   docker compose up -d
   ```

## 🔧 Network Configuration

### **Network Creation**

The `zoi-network` is created by the LLM stack and used as an external network by all other stacks:

```yaml
# In llm-local/docker-compose.yml
networks:
  zoi-network:
    name: zoi-network
    driver: bridge

# In other stacks
networks:
  zoi-network:
    name: zoi-network
    external: true
```

### **Service Discovery**

Services can reach each other using container names:
- `postgres` - PostgreSQL database
- `redis` - Redis cache
- `litellm` - LiteLLM proxy
- `traefik` - Reverse proxy
- `authentik-server` - Authentication
- `prometheus` - Metrics collection
- `grafana` - Dashboards

## 🔍 Troubleshooting

### **Network Connectivity**

```bash
# Check if network exists
docker network ls | grep zoi-network

# Inspect network
docker network inspect zoi-network

# Test connectivity between services
docker exec -it <container> ping <target-container>
```

### **Service Resolution**

```bash
# Check if service is reachable
docker exec -it <container> nslookup <target-service>

# Test HTTP connectivity
docker exec -it <container> curl http://<target-service>:<port>/health
```

### **Common Issues**

1. **Network Not Found**: Start LLM stack first to create the network
2. **Service Unreachable**: Ensure both services are on zoi-network
3. **DNS Resolution**: Use container names, not localhost or IPs
4. **Port Conflicts**: Check for port collisions on host machine

## 📊 Benefits

### **Simplified Architecture**
- ✅ Single network to manage
- ✅ No complex routing rules
- ✅ Consistent service discovery
- ✅ Easy to understand and debug

### **Performance**
- ✅ Direct container-to-container communication
- ✅ No network translation overhead
- ✅ Optimized for Docker bridge networking
- ✅ Reduced latency between services

### **Security**
- ✅ Isolated from host network by default
- ✅ Services only accessible within ecosystem
- ✅ Traefik handles external access
- ✅ No unnecessary external dependencies

### **Maintainability**
- ✅ Easy to add new services
- ✅ Simple configuration changes
- ✅ Clear service dependencies
- ✅ Consistent across all stacks

## 🎯 Migration Notes

### **What Changed**
- Removed complex multi-network setup
- Eliminated external network dependencies
- Simplified connection strings
- Removed host.docker.internal references
- Unified all services on single network

### **Breaking Changes**
- Services must be restarted in correct order
- Database connections use container names
- External access only through Traefik
- Monitoring connects directly to services

---

**🌐 Your Zoi ecosystem now has a clean, simple, and efficient network architecture!**
