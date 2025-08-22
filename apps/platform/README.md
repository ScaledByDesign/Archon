# 🏗️ Zoi Platform (Core Infrastructure)

A comprehensive platform infrastructure stack providing authentication, databases, reverse proxy, and monitoring services for the Zoi ecosystem.

## 🏛️ Architecture

### Core Infrastructure Services
- **PostgreSQL** → Multi-database PostgreSQL server for application persistence
- **Redis** → High-performance caching and session management
- **MongoDB** → Document database for flexible data storage
- **Traefik** → Reverse proxy and load balancer with automatic service discovery

### Authentication & Security
- **Authentik** → Enterprise-grade identity provider and SSO
- **Authentik Worker** → Background task processing for authentication workflows

### Monitoring & Management
- **Dashy** → Centralized dashboard for service management and monitoring

## 🌐 Service Endpoints

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| **PostgreSQL** | localhost:7200 | 7200 | Database server |
| **Redis** | localhost:7201 | 7201 | Cache server |
| **MongoDB** | localhost:7202 | 7202 | Document database |
| **Dashy** | http://localhost:7207 | 7207 | Management dashboard |
| **Authentik** | http://localhost:7208 | 7208 | Authentication server |
| **Authentik HTTPS** | https://localhost:7209 | 7209 | Secure auth server |
| **Traefik HTTP** | http://localhost:80 | 80 | Web traffic |
| **Traefik HTTPS** | https://localhost:443 | 443 | Secure web traffic |
| **Traefik Dashboard** | http://localhost:8080 | 8080 | Proxy management |
| **Traefik API** | http://localhost:8081 | 8081 | Proxy API |

## 🚀 Quick Start

### 1. Environment Setup
```powershell
# Copy environment template (if available)
cp .env.example .env

# Edit environment variables
notepad .env
```

### 2. Start the Platform
```powershell
# Start all services
docker compose up -d

# Check service status
docker compose ps
```

### 3. Verify Services
```powershell
# Check database connectivity
docker exec -it postgres psql -U postgres -c "\l"

# Check Redis
docker exec -it redis redis-cli ping

# Check MongoDB
docker exec -it mongo mongosh --eval "db.adminCommand('ping')"

# Check Traefik
curl http://localhost:8080/api/rawdata
```

## 🗄️ Database Configuration

### PostgreSQL Multi-Database Setup
The PostgreSQL service automatically creates multiple databases:
- `fastapi` - FastAPI applications
- `healthchecks` - Health monitoring
- `authentik` - Authentication data
- `litellm` - LiteLLM proxy data
- `n8n` - Workflow automation
- `langflow` - AI workflow builder
- `langfuse` - LLM observability

### Default Credentials
```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secretpass

# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=change-me-mongo-pass

# Redis
REDIS_PASSWORD=change-me-redis-pass
```

## 🔐 Authentication with Authentik

### Features
- **Single Sign-On (SSO)** across all platform services
- **OAuth2/OIDC** provider for external integrations
- **LDAP** support for enterprise directories
- **Multi-factor Authentication (MFA)**
- **User and group management**
- **Application proxy** with forward authentication

### Initial Setup
1. **Access Authentik**: http://localhost:7208
2. **Default Admin**: Created during first startup
3. **Configure Applications**: Add your services to Authentik
4. **Setup Forward Auth**: Configure Traefik middleware

### Traefik Integration
Services can use Authentik forward authentication:
```yaml
labels:
  - "traefik.http.routers.myapp.middlewares=authentik-forward-auth@file"
```

## 🌐 Traefik Reverse Proxy

### Features
- **Automatic Service Discovery** via Docker labels
- **SSL/TLS Termination** with Let's Encrypt support
- **Load Balancing** and health checks
- **Middleware Support** for authentication, rate limiting, etc.
- **Real-time Configuration** updates

### Service Registration
Add these labels to your services:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myapp.rule=Host(`myapp.zoi.local`)"
  - "traefik.http.routers.myapp.entrypoints=web"
  - "traefik.http.services.myapp.loadbalancer.server.port=8080"
```

## 📊 Monitoring with Dashy

### Features
- **Service Status Monitoring** with health checks
- **Quick Access Links** to all platform services
- **Customizable Dashboard** with widgets and themes
- **Authentication Integration** with Authentik

### Configuration
Dashboard configuration is stored in:
- `./config/dashy/conf.yml` - Main dashboard configuration
- `dashy_data` volume - Icons and user data

## 🔧 Configuration Files

### Directory Structure
```
apps/platform/
├── config/
│   ├── authentik/
│   │   ├── authentik.env
│   │   ├── blueprints/
│   │   └── startup-scripts/
│   ├── dashy/
│   │   └── conf.yml
│   ├── postgres/
│   │   └── init-multiple-databases.sh
│   ├── redis/
│   │   └── redis.conf
│   └── traefik/
│       ├── traefik.yml
│       └── dynamic/
├── docker-compose.yml
└── README.md
```

### Key Configuration Files
- **`authentik.env`** - Authentik environment variables
- **`traefik.yml`** - Traefik static configuration
- **`redis.conf`** - Redis server configuration
- **`dashy/conf.yml`** - Dashboard layout and services

## 🔍 Troubleshooting

### Health Checks
```powershell
# Check all service health
docker compose ps

# View service logs
docker compose logs [service-name]

# Check specific service health
docker exec [container-name] [health-command]
```

### Common Issues

**Database Connection Issues**:
```powershell
# Check PostgreSQL
docker exec -it postgres pg_isready -U postgres

# Check MongoDB
docker exec -it mongo mongosh --eval "db.adminCommand('ping')"

# Check Redis
docker exec -it redis redis-cli ping
```

**Authentik Not Loading**:
```powershell
# Check Authentik logs
docker compose logs authentik-server

# Verify database connection
docker compose logs authentik-worker

# Check post-deployment script
docker compose logs authentik-post-deploy
```

**Traefik Routing Issues**:
```powershell
# Check Traefik configuration
curl http://localhost:8081/api/rawdata

# View Traefik logs
docker compose logs traefik

# Verify service labels
docker inspect [service-container]
```

## 📈 Performance & Scaling

### Resource Requirements

| Service | CPU | RAM | Storage | Notes |
|---------|-----|-----|---------|-------|
| PostgreSQL | 1-2 cores | 2-4GB | 10-50GB | Scales with data |
| Redis | 1 core | 1-2GB | 1-5GB | Memory-based |
| MongoDB | 1-2 cores | 2-4GB | 10-100GB | Document storage |
| Authentik | 1 core | 1GB | 2GB | + Worker process |
| Traefik | 1 core | 512MB | 1GB | Lightweight proxy |
| Dashy | 0.5 core | 256MB | 1GB | Static dashboard |

### Optimization Tips

1. **Database Tuning**: Adjust PostgreSQL `shared_buffers` and `work_mem`
2. **Redis Memory**: Configure `maxmemory` and eviction policies
3. **Traefik Caching**: Enable response caching for static content
4. **Authentik Performance**: Use Redis for session storage
5. **MongoDB Indexing**: Create appropriate indexes for queries

## 🔗 Integration with Other Zoi Services

### LLM Stack Integration
- **Database**: Provides PostgreSQL for LiteLLM, LangFlow
- **Authentication**: SSO for AI service dashboards
- **Proxy**: Routes traffic to AI services

### Monitoring Stack Integration
- **Metrics**: Exposes metrics for Prometheus collection
- **Logs**: Centralized logging through Docker
- **Health**: Health check endpoints for monitoring

## 🎯 Next Steps

1. **🔐 Configure Authentication**: Set up Authentik applications and users
2. **🌐 Add Services**: Register your applications with Traefik
3. **📊 Customize Dashboard**: Configure Dashy for your services
4. **🔍 Setup Monitoring**: Integrate with monitoring stack
5. **🚀 Scale Services**: Adjust resources based on usage

---

**🏗️ Your core platform infrastructure is ready to support the entire Zoi ecosystem!**
