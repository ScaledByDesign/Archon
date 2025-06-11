# Authentik Clean Setup Guide - 2025 Best Practices

## Overview
This guide provides a complete clean setup of Authentik with Traefik integration based on:
- Official Authentik documentation
- Community best practices (erkenes/docker-authentik, brokenscripts/authentik_traefik)
- 2025 security and configuration standards

## Prerequisites
- Docker and Docker Compose v2 installed
- Traefik v3.x already running
- DNS records configured for `auth.zoi.local` (and `auth.zoi.cc` for production)

## Step 1: Environment Variables Review

### Current Configuration Structure
Your existing configuration uses a two-file approach:
- **`.env`**: Main domain configuration and high-level settings
- **`config/authentik/authentik.env`**: Detailed Authentik-specific environment variables

### Current Values in `.env` (Domain & Core Config)
```bash
# Domain Configuration
DOMAIN=zoi.local
ACME_EMAIL=admin@${DOMAIN}

# Authentication (External URLs for other services)
AUTHENTIK_ISSUER=https://auth.${DOMAIN}/application/o/default/
AUTHENTIK_API_TOKEN=change-me-authentik-api-token-for-jwt-validation

# Authentik Core Configuration
AUTHENTIK_SECRET_KEY=authentik-secret-key-must-be-at-least-50-characters-long-for-security-purposes
AUTHENTIK_BOOTSTRAP_PASSWORD=admin123!
AUTHENTIK_BOOTSTRAP_TOKEN=authentik-bootstrap-token-32-chars
AUTHENTIK_BOOTSTRAP_EMAIL=admin@${DOMAIN}

# Authentik Host Configuration (Internal Docker Network for Forward Auth)
AUTHENTIK_HOST=http://authentik-server:9000
AUTHENTIK_URL=http://authentik-server:9000
AUTHENTIK_HOST_BROWSER=https://auth.${DOMAIN}

# Authentik Database Configuration
AUTHENTIK_POSTGRESQL__HOST=postgres
AUTHENTIK_POSTGRESQL__NAME=authentik
AUTHENTIK_POSTGRESQL__USER=authentik
AUTHENTIK_POSTGRESQL__PASSWORD=${PG_PASS}

# Database Credentials
PG_PASS=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_MULTIPLE_DATABASES=fastapi,healthchecks,authentik
```

### Current Values in `config/authentik/authentik.env`
```bash
# AUTHENTIK CORE CONFIGURATION
AUTHENTIK_SECRET_KEY=${AUTHENTIK_SECRET_KEY:-authentik-secret-key-must-be-at-least-50-characters-long-for-security-purposes}
AUTHENTIK_ERROR_REPORTING__ENABLED=${AUTHENTIK_ERROR_REPORTING__ENABLED:-false}
AUTHENTIK_DISABLE_UPDATE_CHECK=true
AUTHENTIK_DISABLE_STARTUP_ANALYTICS=true

# DATABASE CONFIGURATION
AUTHENTIK_POSTGRESQL__HOST=postgres
AUTHENTIK_POSTGRESQL__NAME=authentik
AUTHENTIK_POSTGRESQL__USER=authentik
AUTHENTIK_POSTGRESQL__PASSWORD=postgres
AUTHENTIK_POSTGRESQL__PORT=5432

# REDIS CONFIGURATION
AUTHENTIK_REDIS__HOST=redis
AUTHENTIK_REDIS__PORT=6379
AUTHENTIK_REDIS__DB=1
AUTHENTIK_REDIS__PASSWORD=${REDIS_PASSWORD:-change-me-redis-pass}

# BOOTSTRAP CONFIGURATION (CRITICAL)
AUTHENTIK_BOOTSTRAP_PASSWORD=${AUTHENTIK_BOOTSTRAP_PASSWORD:-admin123!}
AUTHENTIK_BOOTSTRAP_TOKEN=${AUTHENTIK_BOOTSTRAP_TOKEN:-authentik-bootstrap-token-32-chars}
AUTHENTIK_BOOTSTRAP_EMAIL=${AUTHENTIK_BOOTSTRAP_EMAIL:-admin@zoi.local}

# HOSTNAME CONFIGURATION (CRITICAL)
AUTHENTIK_HOST=${AUTHENTIK_HOST:-http://authentik-server:9000}
AUTHENTIK_HOST_BROWSER=${AUTHENTIK_HOST_BROWSER:-https://auth.zoi.local}
AUTHENTIK_URL=${AUTHENTIK_URL:-http://authentik-server:9000}

# LISTEN SETTINGS
AUTHENTIK_LISTEN__HTTP=${AUTHENTIK_LISTEN__HTTP:-0.0.0.0:9000}
AUTHENTIK_LISTEN__HTTPS=${AUTHENTIK_LISTEN__HTTPS:-0.0.0.0:9443}

# TRUST PROXY SETTINGS (CRITICAL)
AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS=127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,fe80::/10,::1/128
```

## Step 2: Docker Compose Configuration

### Update `docker-compose.core.yml` Authentik Services
```yaml
  authentik-server:
    image: ghcr.io/goauthentik/server:latest
    container_name: authentik-server
    restart: unless-stopped
    command: server
    environment:
      AUTHENTIK_REDIS__HOST: redis
      AUTHENTIK_REDIS__PORT: 6379
      AUTHENTIK_REDIS__DB: 1
      AUTHENTIK_REDIS__PASSWORD: ${REDIS_PASSWORD:-change-me-redis-pass}
      AUTHENTIK_POSTGRESQL__HOST: postgres
      AUTHENTIK_POSTGRESQL__USER: authentik
      AUTHENTIK_POSTGRESQL__NAME: authentik
      AUTHENTIK_POSTGRESQL__PASSWORD: ${PG_PASS:-postgres}
      AUTHENTIK_SECRET_KEY: ${AUTHENTIK_SECRET_KEY}
      AUTHENTIK_ERROR_REPORTING__ENABLED: ${AUTHENTIK_ERROR_REPORTING__ENABLED:-true}
      AUTHENTIK_DISABLE_UPDATE_CHECK: ${AUTHENTIK_DISABLE_UPDATE_CHECK:-true}
      AUTHENTIK_DISABLE_STARTUP_ANALYTICS: ${AUTHENTIK_DISABLE_STARTUP_ANALYTICS:-true}
      AUTHENTIK_HOST: http://authentik-server:9000
      AUTHENTIK_HOST_BROWSER: https://${AUTHENTIK_DOMAIN:-auth.zoi.local}
      AUTHENTIK_BOOTSTRAP_EMAIL: ${AUTHENTIK_BOOTSTRAP_EMAIL}
      AUTHENTIK_BOOTSTRAP_PASSWORD: ${AUTHENTIK_BOOTSTRAP_PASSWORD}
      AUTHENTIK_BOOTSTRAP_TOKEN: ${AUTHENTIK_BOOTSTRAP_TOKEN}
    volumes:
      - ./config/authentik/media:/media
      - ./config/authentik/custom-templates:/templates
      - ./config/authentik/blueprints:/blueprints/custom:rw
      - ./config/authentik/startup-scripts:/startup-scripts:ro
    ports:
      - "9000:9000"
      - "9444:9443"
    labels:
      - "traefik.enable=true"
      # Main Authentik router
      - "traefik.http.routers.authentik.rule=Host(`${AUTHENTIK_DOMAIN:-auth.zoi.local}`)"
      - "traefik.http.routers.authentik.entrypoints=websecure"
      - "traefik.http.routers.authentik.tls=true"
      - "traefik.http.services.authentik.loadbalancer.server.port=9000"
      # Outpost router (critical for forward auth)
      - "traefik.http.routers.authentik-outpost.rule=HostRegexp(`{subdomain:[a-z0-9-]+}.${DOMAIN:-zoi.local}`) && PathPrefix(`/outpost.goauthentik.io/`)"
      - "traefik.http.routers.authentik-outpost.entrypoints=websecure"
      - "traefik.http.routers.authentik-outpost.tls=true"
      - "traefik.http.routers.authentik-outpost.priority=15"
    entrypoint: ["sh", "/startup-scripts/entrypoint-with-blueprints.sh"]
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://zoi.local:9000/-/health/live/"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  authentik-worker:
    image: ghcr.io/goauthentik/server:latest
    container_name: authentik-worker
    restart: unless-stopped
    command: worker
    environment:
      AUTHENTIK_REDIS__HOST: redis
      AUTHENTIK_REDIS__PORT: 6379
      AUTHENTIK_REDIS__DB: 1
      AUTHENTIK_REDIS__PASSWORD: ${REDIS_PASSWORD:-change-me-redis-pass}
      AUTHENTIK_POSTGRESQL__HOST: postgres
      AUTHENTIK_POSTGRESQL__USER: authentik
      AUTHENTIK_POSTGRESQL__NAME: authentik
      AUTHENTIK_POSTGRESQL__PASSWORD: ${PG_PASS:-postgres}
      AUTHENTIK_SECRET_KEY: ${AUTHENTIK_SECRET_KEY}
      AUTHENTIK_ERROR_REPORTING__ENABLED: ${AUTHENTIK_ERROR_REPORTING__ENABLED:-true}
      AUTHENTIK_HOST: http://authentik-server:9000
      AUTHENTIK_HOST_BROWSER: https://${AUTHENTIK_DOMAIN:-auth.zoi.local}
    volumes:
      - ./config/authentik/media:/media
      - ./config/authentik/custom-templates:/templates
      - ./config/authentik/blueprints:/blueprints/custom:rw
      - /var/run/docker.sock:/var/run/docker.sock:ro  # Only if auto-provider creation needed
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "celery -A authentik.root.celery inspect ping"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
```

## Step 3: Traefik Middleware Configuration

### Update `config/traefik/dynamic/middleware.yml`
```yaml
http:
  middlewares:
    authentik-forward-auth:
      forwardAuth:
        # Use embedded outpost endpoint (NOT application endpoint)
        address: "http://auth.zoi.local/outpost.goauthentik.io/auth/traefik"
        trustForwardHeader: true
        authResponseHeaders:
          - "X-authentik-username"
          - "X-authentik-groups"
          - "X-authentik-entitlements"
          - "X-authentik-email"
          - "X-authentik-name"
          - "X-authentik-uid"
          - "X-authentik-jwt"
          - "X-authentik-meta-jwks"
          - "X-authentik-meta-outpost"
          - "X-authentik-meta-provider"
          - "X-authentik-meta-app"
          - "X-authentik-meta-version"
```

## Step 4: Blueprint Directory Structure

### Create Blueprint Directory Structure
```bash
mkdir -p config/authentik/blueprints
mkdir -p config/authentik/startup-scripts
mkdir -p config/authentik/media
mkdir -p config/authentik/custom-templates
```

### Blueprint Application Order (Critical)
The startup script must apply blueprints in dependency order:
1. `users.yaml` - Create admin group and users
2. `oauth2-flows.yaml` - Create authentication flows  
3. `oauth2-scopes.yaml` - Create OAuth2 scopes
4. `access-policies.yaml` - Create access policies
5. `00-proxy-provider.yaml` - Create proxy provider
6. `forward-auth.yaml` - Create forward auth application
7. `applications.yaml` - Create other applications
8. Application-specific blueprints (e.g., `dashy-app.yaml`)

## Step 5: Security Considerations

### Production Security Checklist
- [ ] Generate secure credentials using `openssl rand`
- [ ] Use HTTPS with proper TLS certificates (Let's Encrypt or custom)
- [ ] Configure email for notifications and password recovery
- [ ] Regular backups of PostgreSQL data and media volumes
- [ ] Keep Authentik updated to latest version
- [ ] Use environment variable fallbacks for robust configuration
- [ ] Never commit `.env` files to version control
- [ ] Remove Docker socket mount from worker if auto-provider creation not needed

### Environment Variable Validation
Create `config/authentik/validate-env.js` for runtime validation:
```javascript
const { z } = require('zod');

const envSchema = z.object({
  AUTHENTIK_SECRET_KEY: z.string().min(50),
  AUTHENTIK_BOOTSTRAP_EMAIL: z.string().email(),
  AUTHENTIK_BOOTSTRAP_PASSWORD: z.string().min(8),
  AUTHENTIK_BOOTSTRAP_TOKEN: z.string().min(32),
  PG_PASS: z.string().min(8),
  DOMAIN: z.string().min(1),
});

try {
  envSchema.parse(process.env);
  console.log('✅ Environment variables validated successfully');
} catch (error) {
  console.error('❌ Environment validation failed:', error.errors);
  process.exit(1);
}
```

## Step 6: Deployment Steps

### Clean Deployment Process
```bash
# 1. Stop existing Authentik services
docker-compose -f docker-compose.core.yml down authentik-server authentik-worker --volumes

# 2. Validate environment variables
node config/authentik/validate-env.js

# 3. Ensure PostgreSQL has authentik database
docker-compose -f docker-compose.core.yml up -d postgres
# Wait for healthy status

# 4. Start Authentik services
docker-compose -f docker-compose.core.yml up -d authentik-server authentik-worker

# 5. Wait for services to be healthy
docker-compose -f docker-compose.core.yml ps authentik-server authentik-worker

# 6. Check logs for blueprint application
docker-compose -f docker-compose.core.yml logs authentik-server
```

### Verification Steps
```bash
# Check Authentik health
curl -I http://zoi.local:9000/-/health/live/

# Check embedded outpost endpoint
curl -I http://zoi.local:9000/outpost.goauthentik.io/auth/traefik

# Check admin access
curl -I https://auth.zoi.local/

# Test forward auth with protected service
curl -k -I https://dashy.zoi.local
```

## Step 7: Authentik Configuration

### Manual Configuration via Admin UI
1. Access Authentik admin: `https://auth.zoi.local`
2. Login with bootstrap credentials
3. Create proxy provider with:
   - Mode: `forward_domain` (for multiple apps)
   - External host: `https://auth.zoi.local` (NOT zoi.local)
4. Create application linked to proxy provider
5. Verify outpost configuration shows embedded outpost

## Common Troubleshooting

### Issue: Outpost endpoint returns 404
- **Cause**: Proxy provider not configured or wrong mode
- **Solution**: Create proxy provider via admin UI with correct external_host

### Issue: Redirect loops
- **Cause**: external_host set to zoi.local or internal IP
- **Solution**: Set external_host to actual FQDN (https://auth.zoi.local)

### Issue: Blueprint application fails
- **Cause**: Wrong dependency order or missing flows
- **Solution**: Check startup script applies blueprints in correct order

### Issue: Forward auth not working
- **Cause**: Using application endpoint instead of outpost endpoint
- **Solution**: Use `/outpost.goauthentik.io/auth/traefik` endpoint

## Logging and Error Reporting Configuration

### Logging Configuration
The logging configuration is controlled by the `AUTHENTIK_LOG_LEVEL` environment variable. The available log levels are:

* `error`: Only critical errors (minimal logging)
* `warning`: Warnings and errors (recommended for production)
* `info`: Default level with operational information
* `debug`: Detailed troubleshooting information (use temporarily)
* `trace`: Most verbose (⚠️ **NEVER use in production** - exposes sensitive data)

### Error Reporting Configuration
The error reporting configuration is controlled by the `AUTHENTIK_ERROR_REPORTING__ENABLED` environment variable. When enabled, Authentik will send error reports to the configured endpoint.

### Troubleshooting Logging and Error Reporting
To troubleshoot logging and error reporting issues, you can temporarily set the log level to `debug` or `trace` to get more detailed information.

## Resources
- [Official Authentik Docker Compose Guide](https://docs.goauthentik.io/docs/install-config/install/docker-compose)
- [Authentik Traefik Integration](https://docs.goauthentik.io/docs/add-secure-apps/providers/proxy/server_traefik)
- [erkenes/docker-authentik](https://github.com/erkenes/docker-authentik)
- [brokenscripts/authentik_traefik](https://github.com/brokenscripts/authentik_traefik)
