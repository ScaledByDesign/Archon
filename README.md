# ZOI Platform

A complete AI-powered platform with authentication, API services, and dashboard management.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- 16GB+ RAM recommended
- Ports 80, 443, and various service ports available

### Automated Setup

1. Clone the repository and navigate to the project directory
2. Copy `.env.example` to `.env` and adjust if needed
3. Run the initialization script:

```bash
# Start all services
docker-compose -f docker-compose.core.yml up -d
docker-compose up -d

# Initialize platform with authentication
./scripts/init-all.sh
```

This will:
- Start all Docker services
- Initialize databases
- Configure Authentik forward authentication
- Set up Traefik routing with SSL

### Manual Setup (if needed)

If you prefer to set up components individually:

```bash
# Initialize only Authentik forward auth
./scripts/init-authentik.sh

# Or configure manually via Authentik admin:
# 1. Access http://zoi.local:9000/if/admin/
# 2. Login: admin@zoi.local / admin123!
# 3. Create Proxy Provider (Forward auth mode)
# 4. Create Application with slug: traefik-forward-auth
```

## 🔐 Authentication

All services are protected by Authentik forward authentication:

- **Login**: admin@zoi.local / admin123!
- **Auth Portal**: http://auth.zoi.local
- **Single Sign-On**: Automatic across all services

## 🌐 Available Services

### Via Traefik (HTTPS with authentication):
- **Dashy Dashboard**: https://dashy.zoi.local
- **Authentik**: http://auth.zoi.local  
- **FastAPI**: https://api.zoi.local
- **LiteLLM Proxy**: https://llm.zoi.local
- **Traefik Dashboard**: https://traefik.zoi.local

### Direct Access (Development):
- **Dashy**: http://zoi.local:4001
- **Authentik**: http://zoi.local:9000
- **FastAPI**: http://zoi.local:8000
- **LiteLLM**: http://zoi.local:4000
- **Traefik**: http://zoi.local:8081

## 📁 Project Structure

```
zoi/
├── config/              # Service configurations
│   ├── authentik/       # Auth blueprints & settings
│   ├── traefik/         # Reverse proxy config
│   └── ...
├── scripts/             # Automation scripts
│   ├── init-all.sh      # Complete platform init
│   └── init-authentik.sh # Auth setup only
├── docker-compose.yml   # Main services
├── docker-compose.core.yml # Core infrastructure
└── .env                 # Environment configuration
```

## 🔧 Configuration

### Environment Variables
Key settings in `.env`:
- `DOMAIN`: Base domain (default: zoi.local)
- `AUTHENTIK_BOOTSTRAP_PASSWORD`: Admin password
- `AUTHENTIK_BOOTSTRAP_EMAIL`: Admin email

### Traefik Routing
All services automatically get:
- SSL certificates (Let's Encrypt in production)
- Subdomain routing (service.domain)
- Forward authentication via Authentik

### Adding New Services

1. Add service to docker-compose.yml
2. Add Traefik labels:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.myservice.rule=Host(`myservice.${DOMAIN:-zoi.local}`)"
  - "traefik.http.routers.myservice.entrypoints=websecure"
  - "traefik.http.routers.myservice.middlewares=authentik-forward-auth@file"
  - "traefik.http.services.myservice.loadbalancer.server.port=8080"
```

## 🐛 Troubleshooting

### Authentication Issues
- **Redirect shows internal hostname**: This is cosmetic; the browser handles it correctly
- **Can't login**: Check Authentik logs: `docker logs authentik-server`
- **Services not accessible**: Verify Traefik routing: http://zoi.local:8081

### Common Commands
```bash
# View logs
docker-compose logs -f [service-name]

# Restart services
docker-compose -f docker-compose.core.yml restart traefik dashy

# Re-run initialization
./scripts/init-authentik.sh

# Check service health
docker ps
```

## 🔒 Security Notes

- Change default passwords in production
- Configure proper SSL certificates for non-zoi.local domains
- Review Authentik security policies
- Enable 2FA for admin accounts

## 📚 Additional Documentation

- [Authentik Docs](https://docs.goauthentik.io/)
- [Traefik Docs](https://doc.traefik.io/traefik/)
- [Project Architecture](./docs/architecture.md)
