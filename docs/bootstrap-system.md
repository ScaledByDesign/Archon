# Zoi Bootstrap System

## Overview

The Zoi bootstrap system provides automated initialization and configuration for the entire stack, making it easy to get from zero to a fully working system with a single command.

## Quick Start

### Complete Bootstrap (Recommended for new deployments)
```bash
make bootstrap
```

This single command will:
1. ✅ Set up local DNS entries in `/etc/hosts`
2. ✅ Start services in dependency order
3. ✅ Apply all Authentik blueprints automatically
4. ✅ Configure n8n with sample workflows
5. ✅ Perform health checks on all services
6. ✅ Provide access URLs and credentials

### Development Mode
```bash
make dev-start
```

Starts the system with additional development tools and bootstrap features.

## Available Commands

| Command | Description |
|---------|-------------|
| `make bootstrap` | Complete first-time system setup |
| `make start` | Start all services (standard) |
| `make dev-start` | Start with development tools |
| `make stop` | Stop all services |
| `make restart` | Restart all services |
| `make status` | Show service status |
| `make logs` | Show service logs |
| `make health` | Check all service health |
| `make test-endpoints` | Test service endpoints |
| `make n8n-bootstrap` | Bootstrap n8n workflows |
| `make auth-reset` | Reset and reapply Authentik config |
| `make clean` | Clean up everything |

## Bootstrap Features

### 1. Automatic DNS Setup
Automatically adds required entries to `/etc/hosts`:
- `auth.zoi.local` - Authentik authentication
- `traefik.zoi.local` - Traefik dashboard  
- `dashy.zoi.local` - Dashboard
- `llm.zoi.local` - LiteLLM proxy
- `n8n.zoi.local` - n8n workflows

### 2. Service Dependency Management
Services start in proper order:
1. Infrastructure (Traefik, PostgreSQL, Redis)
2. Authentication (Authentik)
3. Applications (LiteLLM, n8n, Dashy)

### 3. Authentik Blueprint Auto-Application
Automatically applies all blueprints:
- User groups and policies
- Forward auth providers
- OAuth2 configurations
- Outpost assignments

### 4. n8n Workflow Templates
Creates sample workflows:
- **Sample Webhook**: Basic webhook responder
- **Health Check**: System monitoring workflow
- **Authentik Integration**: User sync template

### 5. Environment Configuration
Pre-configures optimal settings:
- Security settings for local development
- Performance optimizations
- Integration configurations

## Directory Structure

```
scripts/
├── bootstrap-init.sh       # Main bootstrap script
├── authentik-bootstrap.sh  # Authentik configuration
├── n8n-bootstrap.sh       # n8n workflow setup
└── postgres-bootstrap.sql # Database initialization

config/
├── n8n/
│   ├── workflows/         # Sample workflows
│   ├── templates/         # Workflow templates
│   └── credentials/       # Credential templates
├── authentik/
│   └── blueprints/        # Auto-applied blueprints
└── traefik/
    └── dynamic/           # Middleware configuration
```

## Bootstrap Process Details

### Phase 1: Infrastructure Setup
1. **DNS Configuration**: Adds local domain entries
2. **Directory Creation**: Creates required config directories
3. **Core Services**: Starts Traefik, PostgreSQL, Redis

### Phase 2: Authentication Setup  
1. **Authentik Start**: Launches authentication service
2. **Blueprint Application**: Applies all configuration blueprints
3. **Provider Setup**: Configures forward auth and OAuth2

### Phase 3: Application Deployment
1. **Service Start**: Launches LiteLLM, n8n, Dashy
2. **Configuration**: Applies service-specific settings
3. **Health Checks**: Verifies all services are operational

### Phase 4: Verification
1. **Endpoint Testing**: Tests all service URLs
2. **Authentication Testing**: Verifies auth flows
3. **API Testing**: Tests direct access endpoints

## Service Endpoints After Bootstrap

| Service | Frontend URL | API/Direct Access |
|---------|--------------|------------------|
| **Authentik** | http://auth.zoi.local | Admin: admin/password123 |
| **Traefik** | http://traefik.zoi.local | Dashboard |
| **Dashy** | http://dashy.zoi.local | SSO Protected |
| **LiteLLM** | http://llm.zoi.local | `/v1/*` Direct Access |
| **n8n** | http://n8n.zoi.local | `/webhook/*`, `/api/*` Direct |

## Security Considerations

### Development vs Production

**Development Mode** (Local):
- HTTP endpoints for simplicity
- Relaxed security settings
- Development tools included
- Sample data and workflows

**Production Mode**:
- Use `make prod-start` instead
- Configure HTTPS certificates
- Change default passwords
- Remove development tools

### Default Credentials
🔐 **Change these immediately after bootstrap:**
- Authentik admin: `admin` / `password123`
- Database: Uses environment variables
- LiteLLM: Master key authentication

## Troubleshooting

### Bootstrap Fails
```bash
# Check logs
make logs

# Clean and retry
make clean
make bootstrap
```

### Service Not Responding
```bash
# Check individual service
docker compose ps SERVICE_NAME
docker compose logs SERVICE_NAME

# Restart specific service
docker compose restart SERVICE_NAME
```

### DNS Issues
```bash
# Verify hosts file
cat /etc/hosts | grep zoi.local

# Re-run DNS setup
sudo scripts/bootstrap-init.sh
```

### Authentication Issues
```bash
# Reset Authentik configuration
make auth-reset

# Check Authentik logs
docker compose logs authentik-server
```

## Customization

### Adding Services
1. Add service to `docker-compose.yml`
2. Create bootstrap script in `scripts/`
3. Add to `scripts/bootstrap-init.sh`
4. Update Makefile commands

### Custom Workflows
1. Export workflows from n8n
2. Place in `config/n8n/workflows/`
3. Add to `scripts/n8n-bootstrap.sh`

### Custom Blueprints
1. Create blueprint YAML
2. Place in `config/authentik/blueprints/`
3. Add to bootstrap script

## Benefits

✅ **Zero-Configuration Start**: Single command deployment  
✅ **Consistent Environment**: Reproducible across systems  
✅ **Development Ready**: Includes tools and samples  
✅ **Production Capable**: Scalable configuration  
✅ **Self-Documenting**: Clear process and structure  
✅ **Error Recovery**: Easy cleanup and restart  

## Next Steps After Bootstrap

1. **Change Default Passwords**
2. **Configure LLM Models** in LiteLLM
3. **Create Custom Workflows** in n8n  
4. **Customize Dashboard** in Dashy
5. **Set Up Monitoring** and alerting
6. **Configure Backups** for persistent data

---

The bootstrap system transforms a complex multi-service deployment into a simple, reliable, one-command experience! 🚀
