# Docker Network Isolation Documentation

## Overview

This document describes the network isolation architecture implemented for the Production RAG System. The system uses Docker custom networks to segment services into logical groups, improving security, manageability, and performance.

## Network Architecture

### Network Segmentation Strategy

The application is divided into 6 isolated networks, each serving a specific purpose:

```
┌─────────────────────────────────────────────────────────────┐
│                    NETWORK ISOLATION                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  FRONTEND   │  │   BACKEND   │  │  DATABASE   │         │
│  │ 172.20.0.0  │  │ 172.21.0.0  │  │ 172.22.0.0  │         │
│  │    /24      │  │    /24      │  │    /24      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │    AUTH     │  │ MONITORING  │  │INFRASTRUCTURE│         │
│  │ 172.23.0.0  │  │ 172.24.0.0  │  │ 172.25.0.0  │         │
│  │    /24      │  │    /24      │  │    /24      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Network Definitions

### 1. Frontend Network (`zoi_frontend`)
- **Subnet**: `172.20.0.0/24`
- **Purpose**: User-facing services and web interfaces
- **Services**:
  - `open-webui`: Main chat interface
  - `n8n`: Workflow automation UI
  - `traefik`: Reverse proxy (frontend access)

### 2. Backend Network (`zoi_backend`)
- **Subnet**: `172.21.0.0/24`
- **Purpose**: Application logic and API services
- **Services**:
  - `fastapi-1`, `fastapi-2`, `fastapi-3`: API servers
  - `worker`, `worker-2`: Background task processors
  - `litellm`: LLM proxy service
  - `ollama`: Local LLM service
  - `rabbitmq`: Message queue
  - `traefik`: Reverse proxy (backend routing)

### 3. Database Network (`zoi_database`)
- **Subnet**: `172.22.0.0/24`
- **Purpose**: Data storage and persistence
- **Services**:
  - `mongo-episodic`: Episodic memory database
  - `mongo-procedural`: Procedural memory database
  - `qdrant`: Vector database
  - `redis`: Cache and session storage
  - `redis-insight`: Redis management UI

### 4. Auth Network (`zoi_auth`)
- **Subnet**: `172.23.0.0/24`
- **Purpose**: Authentication and authorization
- **Services**:
  - `authentik-server`: SSO server
  - `authentik-worker`: Auth background tasks
  - `authentik-db`: Auth database (PostgreSQL)
  - `authentik-redis`: Auth cache

### 5. Monitoring Network (`zoi_monitoring`)
- **Subnet**: `172.24.0.0/24`
- **Purpose**: System monitoring and observability
- **Services**:
  - `aim`: ML experiment tracking
  - `healthchecks`: Service health monitoring

### 6. Infrastructure Network (`zoi_infrastructure`)
- **Subnet**: `172.25.0.0/24`
- **Purpose**: Core infrastructure services
- **Services**:
  - `vault`: Secret management
  - `backrest`: Backup service
  - `traefik`: Reverse proxy (infrastructure access)

## Cross-Network Communication

### Multi-Network Services

Some services are connected to multiple networks to enable controlled cross-network communication:

#### Traefik (Reverse Proxy)
- **Networks**: `frontend`, `backend`, `infrastructure`
- **Purpose**: Routes traffic between networks while maintaining isolation
- **Access**: Can reach services in frontend, backend, and infrastructure networks

#### FastAPI Services
- **Networks**: `frontend`, `backend`, `database`, `infrastructure`
- **Purpose**: Serves as the main API gateway
- **Access**: Can reach databases, vault, and serve frontend requests

#### Authentik Server
- **Networks**: `frontend`, `backend`, `auth`
- **Purpose**: Provides SSO for both frontend and backend services
- **Access**: Can authenticate users from frontend and authorize backend API calls

## Security Benefits

### 1. Network Segmentation
- **Isolation**: Services can only communicate within their designated networks
- **Least Privilege**: Services only have access to resources they need
- **Attack Surface Reduction**: Compromised services have limited lateral movement

### 2. Controlled Access Points
- **Traefik Gateway**: Single point of entry for external traffic
- **API Gateway**: FastAPI services control access to backend resources
- **Auth Gateway**: Authentik controls authentication across all services

### 3. Database Protection
- **Isolated Database Network**: Databases are not directly accessible from frontend
- **API-Only Access**: All database access goes through FastAPI services
- **Credential Management**: Database credentials stored securely in Vault

## Network Validation

### Connectivity Testing

Use the provided validation script to test network isolation:

```bash
./scripts/validate-network-isolation.sh
```

### Manual Testing

Test connectivity between services:

```bash
# Test FastAPI to Qdrant (should work)
docker exec zoi-fastapi-1-1 python -c "import socket; s = socket.socket(); s.settimeout(3); result = s.connect_ex(('zoi-qdrant-1', 6333)); s.close(); print('✅ Connected' if result == 0 else '❌ Failed')"

# Test Authentik to its database (should work)
docker exec zoi-authentik-server-1 python -c "import socket; s = socket.socket(); s.settimeout(3); result = s.connect_ex(('zoi-authentik-db-1', 5432)); s.close(); print('✅ Connected' if result == 0 else '❌ Failed')"
```

### Expected Connectivity Matrix

| From Service | To Service | Expected | Reason |
|--------------|------------|----------|---------|
| FastAPI | Qdrant | ✅ Allow | API needs database access |
| FastAPI | Vault | ✅ Allow | API needs secrets |
| FastAPI | Mongo | ✅ Allow | API needs database access |
| Open WebUI | FastAPI | ✅ Allow | Frontend needs API |
| Open WebUI | Qdrant | ❌ Block | Frontend should use API |
| Open WebUI | Mongo | ❌ Block | Frontend should use API |
| Authentik | Auth DB | ✅ Allow | Auth needs its database |
| Authentik | Qdrant | ❌ Block | Auth doesn't need vector DB |

## Configuration Files

### Docker Compose Networks Section

```yaml
networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24

  backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/24

  database:
    driver: bridge
    ipam:
      config:
        - subnet: 172.22.0.0/24

  auth:
    driver: bridge
    ipam:
      config:
        - subnet: 172.23.0.0/24

  monitoring:
    driver: bridge
    ipam:
      config:
        - subnet: 172.24.0.0/24

  infrastructure:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/24
```

### Service Network Assignment Example

```yaml
services:
  fastapi-1:
    networks:
      - frontend
      - backend
      - database
      - infrastructure

  qdrant:
    networks:
      - database

  authentik-server:
    networks:
      - frontend
      - backend
      - auth
```

## Monitoring and Troubleshooting

### Network Inspection Commands

```bash
# List all networks
docker network ls

# Inspect specific network
docker network inspect zoi_frontend

# See which containers are on a network
docker network inspect zoi_backend --format '{{range $k, $v := .Containers}}{{$v.Name}} {{end}}'

# Check container network configuration
docker inspect zoi-fastapi-1-1 --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}: {{$v.IPAddress}} {{end}}'
```

### Common Issues and Solutions

#### 1. Service Cannot Connect to Database
- **Symptom**: Connection timeouts or "host not found" errors
- **Solution**: Verify both services are on the same network or have a bridge service
- **Check**: `docker network inspect zoi_database`

#### 2. Frontend Cannot Reach API
- **Symptom**: API calls fail from web interface
- **Solution**: Ensure Traefik is properly routing and both services are on frontend network
- **Check**: Traefik dashboard at `http://localhost:8080`

#### 3. Authentication Issues
- **Symptom**: SSO redirects fail or authentication timeouts
- **Solution**: Verify Authentik server is on both frontend and backend networks
- **Check**: `docker logs zoi-authentik-server-1`

## Best Practices

### 1. Network Design
- Keep networks as isolated as possible
- Only add services to multiple networks when necessary
- Use descriptive network names
- Document all cross-network communications

### 2. Security
- Regularly audit network configurations
- Monitor cross-network traffic
- Use Vault for all sensitive credentials
- Implement proper authentication at network boundaries

### 3. Maintenance
- Test network isolation after configuration changes
- Update documentation when adding new services
- Monitor network performance and connectivity
- Use health checks to verify service connectivity

## Future Enhancements

### 1. Network Policies
- Implement Kubernetes-style network policies
- Add firewall rules for additional security
- Create network monitoring dashboards

### 2. Service Mesh
- Consider implementing Istio or Linkerd for advanced traffic management
- Add mTLS between services
- Implement distributed tracing across networks

### 3. Monitoring
- Add network-level monitoring
- Implement alerting for connectivity issues
- Create network topology visualization

---

*Last updated: 2025-05-27*
*Version: 1.0*
