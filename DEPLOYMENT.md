# Zoi Production Deployment Guide

## Prerequisites

1. **Server Requirements:**
   - Ubuntu 20.04+ or CentOS 8+ server
   - 8GB RAM minimum (16GB+ recommended)
   - 50GB+ storage space
   - Docker and Docker Compose installed

2. **Domain Setup:**
   - Point your DNS records for `zoi.cc` and subdomains to your server IP
   - Required DNS A records:
     - `zoi.cc` → Server IP
     - `*.zoi.cc` → Server IP (wildcard for subdomains)

3. **Firewall Configuration:**
   ```bash
   sudo ufw allow 80/tcp   # HTTP (redirects to HTTPS)
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw allow 22/tcp   # SSH
   ```

## Deployment Steps

### 1. Clone and Configure

```bash
# Clone repository
git clone <your-repo-url> zoi
cd zoi

# Create production environment file
cp .env.example .env
```

### 2. Update Environment Variables

Edit `.env` file with production values:

```bash
# Domain is already set to zoi.cc
DOMAIN=zoi.cc
ACME_EMAIL=admin@zoi.cc  # Change to your email

# Generate strong secrets (minimum 50 characters)
AUTHENTIK_SECRET_KEY=your-super-long-random-secret-key-min-50-chars
AUTHENTIK_REDIS_PASS=your-strong-redis-password
PG_PASS=your-strong-postgres-password

# Database credentials
MONGO_USER=admin
MONGO_PASS=your-strong-mongo-password

# RabbitMQ
RABBITMQ_USER=admin
RABBITMQ_PASS=your-strong-rabbitmq-password

# Redis
REDIS_PASSWORD=your-strong-redis-password

# LLM API Keys
LITELLM_MASTER_KEY=sk-your-random-litellm-key
OPENAI_API_KEY=sk-your-actual-openai-key
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key

# n8n credentials
N8N_USER=admin
N8N_PASS=your-strong-n8n-password
```

### 3. Deploy Services

```bash
# Start all services in detached mode
docker-compose up -d

# Monitor startup logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### 4. Verify Deployment

Your services will be available at:

- **Chat Interface:** https://chat.zoi.cc
- **Admin Dashboard:** https://auth.zoi.cc
- **System Dashboard:** https://dashy.zoi.cc
- **API Endpoint:** https://api.zoi.cc
- **Health Monitoring:** https://health.zoi.cc
- **Workflow Automation:** https://n8n.zoi.cc
- **Backup Management:** https://backup.zoi.cc

### 5. SSL Certificate Verification

Traefik will automatically:
- Redirect HTTP to HTTPS
- Request Let's Encrypt certificates for all domains
- Handle certificate renewal

Monitor certificate status:
```bash
docker-compose logs traefik | grep -i cert
```

## Post-Deployment

### Initial Setup
1. Access https://auth.zoi.cc to configure Authentik authentication
2. Visit https://chat.zoi.cc to access the Open WebUI interface
3. Configure your LLM models via the API endpoints

### Monitoring
- View service status at https://dashy.zoi.cc
- Check logs: `docker-compose logs <service-name>`
- Monitor resource usage: `docker stats`

### Backup
- Database backups are handled by Backrest at https://backup.zoi.cc
- Configuration files are in the `config/` directory

## Troubleshooting

### SSL Issues
```bash
# Check Traefik logs
docker-compose logs traefik

# Restart Traefik if needed
docker-compose restart traefik
```

### Service Not Starting
```bash
# Check specific service logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>
```

### Domain Resolution
Verify DNS propagation:
```bash
nslookup zoi.cc
nslookup chat.zoi.cc
```

## Security Notes

- All passwords and API keys should be unique and strong
- Regularly update Docker images: `docker-compose pull && docker-compose up -d`
- Monitor access logs via Traefik and individual services
- Consider setting up firewall rules to restrict access to specific ports
