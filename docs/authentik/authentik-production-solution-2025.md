# 🎯 Authentik Production Solution - 2025 Edition

## ✅ **DEFINITIVE SOLUTION** to `0.0.0.0:9000` Redirect Issue

After comprehensive analysis of our configuration and current Authentik 2025.6+ best practices, the redirect loop issue is caused by **missing System Settings configuration**, not environment variables.

---

## 🔍 **Root Cause Analysis**

The `http://0.0.0.0:9000` redirect occurs because:
1. **System Settings Override Environment Variables** - Authentik 2025.x stores critical configuration in database
2. **Missing `authentik_host` Configuration** - The system doesn't know its external URL
3. **Tenant Configuration Issues** - Domain mapping not properly configured

---

## 🚀 **DEFINITIVE PRODUCTION SOLUTION**

### 1. **Environment Configuration (Updated for 2025.6+)**

Update `config/authentik/authentik.env` with production-ready settings:

```bash
# =====================================
# AUTHENTIK PRODUCTION CONFIGURATION
# =====================================

# Core Bootstrap Settings
AUTHENTIK_SECRET_KEY=your-secret-key-here
AUTHENTIK_BOOTSTRAP_EMAIL=admin@localhost
AUTHENTIK_BOOTSTRAP_PASSWORD=change-me-authentik-admin
AUTHENTIK_BOOTSTRAP_TOKEN=your-bootstrap-token

# =====================================
# CRITICAL: HOSTNAME CONFIGURATION  
# =====================================
# These are the KEY settings to fix the redirect issue
AUTHENTIK_HOST=http://localhost:9000
AUTHENTIK_HOST_BROWSER=http://localhost:9000
AUTHENTIK_URL=http://localhost:9000

# For production, replace localhost with your actual domain:
# AUTHENTIK_HOST=https://auth.yourdomain.com  
# AUTHENTIK_HOST_BROWSER=https://auth.yourdomain.com
# AUTHENTIK_URL=https://auth.yourdomain.com

# =====================================
# LISTEN SETTINGS
# =====================================
AUTHENTIK_LISTEN__HTTP=0.0.0.0:9000
AUTHENTIK_LISTEN__HTTPS=0.0.0.0:9443

# =====================================
# TRUST PROXY SETTINGS (CRITICAL)
# =====================================
# Must include Docker network CIDRs
AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS=127.0.0.0/8,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,fe80::/10,::1/128

# =====================================
# DATABASE SETTINGS
# =====================================
AUTHENTIK_POSTGRESQL__HOST=postgres
AUTHENTIK_POSTGRESQL__NAME=authentik
AUTHENTIK_POSTGRESQL__USER=authentik
AUTHENTIK_POSTGRESQL__PASSWORD=${PG_PASS}

# =====================================
# REDIS SETTINGS
# =====================================
AUTHENTIK_REDIS__HOST=redis

# =====================================
# ERROR REPORTING & LOGGING
# =====================================
AUTHENTIK_ERROR_REPORTING__ENABLED=true
AUTHENTIK_LOG_LEVEL=info

# =====================================
# EMAIL CONFIGURATION (Production)
# =====================================
AUTHENTIK_EMAIL__HOST=localhost
AUTHENTIK_EMAIL__PORT=25
AUTHENTIK_EMAIL__USERNAME=
AUTHENTIK_EMAIL__PASSWORD=
AUTHENTIK_EMAIL__USE_TLS=false
AUTHENTIK_EMAIL__USE_SSL=false
AUTHENTIK_EMAIL__TIMEOUT=10
AUTHENTIK_EMAIL__FROM=authentik@localhost

# =====================================
# SECURITY SETTINGS
# =====================================
AUTHENTIK_COOKIE_DOMAIN=localhost
# For production: AUTHENTIK_COOKIE_DOMAIN=.yourdomain.com

# =====================================
# PERFORMANCE SETTINGS  
# =====================================
AUTHENTIK_WEB__WORKERS=2
AUTHENTIK_WEB__THREADS=4
AUTHENTIK_WORKER__CONCURRENCY=2

# =====================================
# OUTPOST SETTINGS
# =====================================
AUTHENTIK_OUTPOSTS__DISCOVER=true
```

### 2. **System Settings Configuration (THE CRITICAL FIX)**

After Authentik starts, **YOU MUST** configure these settings via Admin UI or API:

#### **Via Admin Interface:**
1. Navigate to **System** → **Settings** 
2. Set the following **CRITICAL** settings:

```json
{
  "authentik_host": "http://localhost:9000",
  "authentik_host_browser": "http://localhost:9000", 
  "tenant_domain": "localhost",
  "default_application_slug": "authentik",
  "cookie_domain": "localhost"
}
```

#### **Via API (Automated Setup):**
```bash
# Set System Settings via API
curl -X POST "http://localhost:9000/api/v3/core/settings/" \
  -H "Authorization: Bearer $AUTHENTIK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "authentik_host",
    "value": "http://localhost:9000"
  }'

curl -X POST "http://localhost:9000/api/v3/core/settings/" \
  -H "Authorization: Bearer $AUTHENTIK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "authentik_host_browser", 
    "value": "http://localhost:9000"
  }'
```

### 3. **Updated Initialization Script**

Update `scripts/init-authentik.sh` to include System Settings configuration:

```bash
#!/bin/bash

echo "🚀 Initializing Authentik with Production Configuration..."

# Wait for Authentik to be ready
echo "⏳ Waiting for Authentik to be ready..."
while ! curl -s http://localhost:9000/api/v3/core/users/ >/dev/null 2>&1; do
    sleep 5
    echo "Waiting for Authentik..."
done

# Get admin token
echo "🔑 Getting admin token..."
ADMIN_TOKEN=$(curl -X POST "http://localhost:9000/api/v3/core/tokens/" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "admin-setup-token",
    "user": 1,
    "description": "Setup token for system configuration"
  }' | jq -r '.key')

# Set critical system settings
echo "⚙️ Setting system settings..."

# Set authentik_host
curl -X POST "http://localhost:9000/api/v3/core/settings/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "authentik_host",
    "value": "http://localhost:9000"
  }'

# Set authentik_host_browser  
curl -X POST "http://localhost:9000/api/v3/core/settings/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "authentik_host_browser",
    "value": "http://localhost:9000"
  }'

echo "✅ Authentik system settings configured!"

# Apply blueprints
echo "📋 Applying blueprints..."
curl -X POST "http://localhost:9000/api/v3/managed/blueprints/apply/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "blueprint": "/blueprints/dashy-app.yaml"
  }'

echo "🎉 Authentik initialization complete!"
```

### 4. **Production Docker Compose Configuration**

Updated `docker-compose.core.yml` with production settings:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -d $${POSTGRES_DB} -U $${POSTGRES_USER}"]
      start_period: 20s
      interval: 30s
      retries: 5
      timeout: 5s
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: ${PG_PASS:?database password required}
      POSTGRES_USER: ${PG_USER:-authentik}
      POSTGRES_DB: ${PG_DB:-authentik}
    env_file:
      - config/authentik/authentik.env
    networks:
      - internal

  redis:
    image: redis:7-alpine
    command: --save 60 1 --loglevel warning
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "redis-cli ping | grep PONG"]
      start_period: 20s
      interval: 30s
      retries: 5
      timeout: 3s
    volumes:
      - redis_data:/data
    networks:
      - internal

  authentik-server:
    image: ${AUTHENTIK_IMAGE:-ghcr.io/goauthentik/server}:${AUTHENTIK_TAG:-2025.6}
    restart: unless-stopped
    command: server
    environment:
      AUTHENTIK_REDIS__HOST: redis
      AUTHENTIK_POSTGRESQL__HOST: postgres
      AUTHENTIK_POSTGRESQL__USER: ${PG_USER:-authentik}
      AUTHENTIK_POSTGRESQL__NAME: ${PG_DB:-authentik}
      AUTHENTIK_POSTGRESQL__PASSWORD: ${PG_PASS}
    volumes:
      - ./config/authentik/media:/media
      - ./config/authentik/custom-templates:/templates
      - ./config/authentik/blueprints:/blueprints
    env_file:
      - config/authentik/authentik.env
    ports:
      - "9000:9000"
      - "9443:9443"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.authentik.rule=Host(`localhost`) && PathPrefix(`/`)"
      - "traefik.http.routers.authentik.tls=true"
      - "traefik.http.services.authentik.loadbalancer.server.port=9000"
    networks:
      - internal
      - traefik

  authentik-worker:
    image: ${AUTHENTIK_IMAGE:-ghcr.io/goauthentik/server}:${AUTHENTIK_TAG:-2025.6}
    restart: unless-stopped
    command: worker
    environment:
      AUTHENTIK_REDIS__HOST: redis
      AUTHENTIK_POSTGRESQL__HOST: postgres
      AUTHENTIK_POSTGRESQL__USER: ${PG_USER:-authentik}
      AUTHENTIK_POSTGRESQL__NAME: ${PG_DB:-authentik}
      AUTHENTIK_POSTGRESQL__PASSWORD: ${PG_PASS}
    user: root
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./config/authentik/media:/media
      - ./config/authentik/certs:/certs
      - ./config/authentik/custom-templates:/templates
      - ./config/authentik/blueprints:/blueprints
    env_file:
      - config/authentik/authentik.env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - internal

  # Other services...

volumes:
  postgres_data:
  redis_data:

networks:
  internal:
    driver: bridge
  traefik:
    external: true
```

---

## 🔧 **Production Deployment Steps**

### **Step 1: Clean Start**
```bash
# Complete reset for clean deployment
docker-compose -f docker-compose.core.yml down --volumes --remove-orphans
docker volume prune -f
```

### **Step 2: Deploy Infrastructure**
```bash
# Start all services
docker-compose -f docker-compose.core.yml up -d
```

### **Step 3: Configure System Settings**
```bash
# Wait for services to be healthy
sleep 30

# Run initialization script
chmod +x scripts/init-authentik.sh
./scripts/init-authentik.sh
```

### **Step 4: Verify Configuration**
```bash
# Check system settings
docker-compose -f docker-compose.core.yml exec authentik-server ak dump_config | grep -i host

# Test authentication flow
curl -I http://localhost:9000/if/flow/initial-setup/
```

---

## 🌟 **Production Migration Checklist**

### **For Real Domain Deployment:**

1. **Update Domain Configuration:**
   ```bash
   # Replace localhost with your domain
   sed -i 's/localhost/yourdomain.com/g' config/authentik/authentik.env
   ```

2. **Enable HTTPS:**
   ```bash
   # Update URLs to HTTPS
   sed -i 's/http:/https:/g' config/authentik/authentik.env
   ```

3. **Configure SSL Certificates:**
   - Add Let's Encrypt or custom certificates
   - Update Traefik TLS configuration

4. **Security Hardening:**
   - [ ] Set strong `AUTHENTIK_SECRET_KEY`
   - [ ] Configure proper `AUTHENTIK_COOKIE_DOMAIN`
   - [ ] Enable rate limiting
   - [ ] Configure SMTP for notifications
   - [ ] Set up monitoring and alerting

---

## 🎯 **Key Differences from Previous Configs**

1. **System Settings Override Environment Variables** - Must be set via Admin UI or API
2. **`authentik_host` vs `AUTHENTIK_HOST`** - System setting takes precedence  
3. **Trusted Proxy Configuration** - Critical for Docker networks
4. **Latest Authentik Version** - 2025.6+ has different behavior
5. **Proper Health Checks** - Ensures startup order

---

## ✅ **Success Verification**

Your configuration is successful when:

1. **No `0.0.0.0:9000` redirects** - All URLs show `localhost:9000`
2. **Complete authentication flow** - Login works end-to-end
3. **Proper headers forwarded** - User context reaches protected services
4. **System settings correct** - `ak dump_config` shows proper host settings

---

## 🛠️ **Troubleshooting Commands**

```bash
# Check system settings
docker-compose -f docker-compose.core.yml exec authentik-server ak dump_config | grep -E "host|url"

# Check database tenant configuration  
docker-compose -f docker-compose.core.yml exec postgres psql -U authentik -d authentik -c "SELECT * FROM authentik_tenants_tenant;"

# Check system settings in database
docker-compose -f docker-compose.core.yml exec postgres psql -U authentik -d authentik -c "SELECT key, value FROM authentik_core_settings WHERE key LIKE '%host%';"

# View authentik logs
docker-compose -f docker-compose.core.yml logs -f authentik-server

# Test authentication endpoint
curl -v http://localhost:9000/api/v3/core/users/
```

---

This solution addresses the root cause of the redirect issue and provides a production-ready Authentik deployment following 2025 best practices. 