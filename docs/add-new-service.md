# Adding a New Service to Zoi: Complete Integration Guide

> **Documentation Source**: Based on successful N8N integration and established project patterns  
> **Last Updated**: 2025-06-12  
> **Context7 Research**: [Authentik Forward Auth](context7://authentik-forward-auth), [Traefik Configuration](context7://traefik-middleware)

## 📋 **Overview**

This guide provides a complete step-by-step process for integrating new services into the Zoi project infrastructure. All services must follow established patterns for configuration, authentication, networking, and deployment.

## 🏗️ **Project Architecture Standards**

### **Core Infrastructure Components**
- **Reverse Proxy**: Traefik (routing, SSL, middleware)
- **Authentication**: Authentik (SSO, OAuth2, Forward Auth)
- **Database**: PostgreSQL (shared instance with multi-DB support)
- **Cache**: Redis (shared instance)
- **Document Store**: MongoDB (shared instance)
- **Vector Store**: Qdrant (for AI/ML services)
- **Message Queue**: RabbitMQ (for async processing)

### **Network Architecture**
- `frontend_network`: Web-facing services (Traefik, UI components)
- `backend_network`: API services, application logic
- `database_network`: Database services (PostgreSQL, MongoDB, Redis)
- `auth_network`: Authentication services (Authentik)
- `infrastructure_network`: Core infrastructure services
- `monitoring_network`: Monitoring and dashboard services

---

## 🛠️ **Step-by-Step Integration Process**

### **Step 1: Project Planning & Research**

#### **1.1 Service Analysis**
```bash
# Document service requirements
- Service name and purpose
- Port requirements (internal/external)
- Database needs (PostgreSQL, MongoDB, Redis)
- Authentication requirements (SSO, API keys, OAuth2)
- External dependencies
- Volume/storage requirements
- Environment variables needed
```

#### **1.2 Context7 Research**
```bash
# Use Context7 for documentation research
task-master research --service="{service_name}"
# Example: task-master research --service="grafana"
```

### **Step 2: Directory Structure Setup**

#### **2.1 Create Configuration Directory**
```bash
mkdir -p config/{service_name}
cd config/{service_name}
```

#### **2.2 Required Configuration Files**
```bash
# Standard configuration structure
config/{service_name}/
├── {service_name}.env          # Primary environment file
├── config.yaml                 # Service-specific config (if needed)
├── docker-entrypoint.sh        # Custom startup script (if needed)
└── blueprints/                 # Authentik blueprints (if auth needed)
    └── {service_name}-oauth-integration.yaml
```

### **Step 3: Environment Configuration**

#### **3.1 Create Service Environment File**
**File**: `config/{service_name}/{service_name}.env`

```bash
# {Service Name} Configuration
# Generated: $(date)

# Database Configuration (if using PostgreSQL)
DB_TYPE=postgresdb
DB_POSTGRESDB_DATABASE={service_name}
DB_POSTGRESDB_HOST=postgres
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_USER={service_name}
DB_POSTGRESDB_PASSWORD=${PG_PASS:-secretpass}

# Service Configuration
{SERVICE_NAME}_HOST={service_name}.${DOMAIN:-zoi.local}
{SERVICE_NAME}_PORT={default_port}
{SERVICE_NAME}_PROTOCOL=http

# Authentication (if using basic auth)
{SERVICE_NAME}_USER=${'{SERVICE_NAME}_USER:-admin'}
{SERVICE_NAME}_PASSWORD=${'{SERVICE_NAME}_PASS:-change-me-{service_name}-pass'}

# Redis Configuration (if needed)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=${REDIS_PASSWORD:-change-me-redis-pass}
REDIS_URL=redis://:${REDIS_PASSWORD:-change-me-redis-pass}@redis:6379/0

# MongoDB Configuration (if needed)
MONGODB_URI=mongodb://${MONGO_USER:-admin}:${MONGO_PASS:-change-me-mongo-pass}@mongo:27017
MONGODB_HOST=mongo
MONGODB_PORT=27017
MONGODB_USERNAME=${MONGO_USER:-admin}
MONGODB_PASSWORD=${MONGO_PASS:-change-me-mongo-pass}
MONGODB_DATABASE={service_name}

# Email Configuration (if needed)
{SERVICE_NAME}_EMAIL_MODE=smtp
{SERVICE_NAME}_SMTP_HOST=smtp.gmail.com
{SERVICE_NAME}_SMTP_PORT=587
{SERVICE_NAME}_SMTP_USER=${'{SERVICE_NAME}_SMTP_USER:-your-email@gmail.com'}
{SERVICE_NAME}_SMTP_PASS=${'{SERVICE_NAME}_SMTP_PASS:-your-smtp-app-password'}
{SERVICE_NAME}_SMTP_SENDER=${'{SERVICE_NAME}_SMTP_SENDER:-{service_name}@zoi.local'}

# OAuth2 Configuration (if using Authentik integration)
{SERVICE_NAME}_OAUTH_CLIENT_ID=${'{SERVICE_NAME}_OAUTH_CLIENT_ID:-{service_name}-oauth-client'}
{SERVICE_NAME}_OAUTH_CLIENT_SECRET=${'{SERVICE_NAME}_OAUTH_CLIENT_SECRET:-change-me-{service_name}-oauth-secret'}
AUTHENTIK_ISSUER=${AUTHENTIK_ISSUER:-http://auth.zoi.local/application/o/{service_name}-oauth}

# Timezone
GENERIC_TIMEZONE=America/Chicago
TZ=America/Chicago

# Security (adjust based on service requirements)
{SERVICE_NAME}_SECURE_COOKIE=false
{SERVICE_NAME}_SECURITY_AUDIT_DAYS=7
```

#### **3.2 Update Global Environment Files**

**Add to `.env.example`:**
```bash
# {Service Name}
{SERVICE_NAME}_USER=admin
{SERVICE_NAME}_PASS=change-me-{service_name}-pass
{SERVICE_NAME}_SMTP_USER=your-email@gmail.com
{SERVICE_NAME}_SMTP_PASS=your-smtp-app-password
{SERVICE_NAME}_SMTP_SENDER={service_name}@zoi.local
{SERVICE_NAME}_OAUTH_CLIENT_ID={service_name}-oauth-client
{SERVICE_NAME}_OAUTH_CLIENT_SECRET=change-me-{service_name}-oauth-secret
```

### **Step 4: Database Integration**

#### **4.1 PostgreSQL Database Setup**
**Update `docker-compose.yml` - PostgreSQL service:**
```yaml
environment:
  POSTGRES_MULTIPLE_DATABASES: ${POSTGRES_MULTIPLE_DATABASES:-fastapi,healthchecks,authentik,litellm,n8n,{service_name}}
```

#### **4.2 Database User Creation**
The `config/postgres/init-multiple-databases.sh` script automatically creates:
- Database: `{service_name}`
- User: `{service_name}`  
- Password: `${PG_PASS}`

For custom database names, update the case statement in the init script.

### **Step 5: Docker Compose Service Configuration**

#### **5.1 Add Service Definition**
**Location**: `docker-compose.yml`

```yaml
  # {Service Description}
  {service_name}:
    image: {official_image}:{version}
    container_name: {service_name}
    restart: unless-stopped
    ports:
      - "{host_port}:{container_port}"
    env_file:
      - ./config/{service_name}/{service_name}.env
    volumes:
      - {service_name}_data:/path/to/data
      - ./config/{service_name}/config.yaml:/app/config.yaml:ro  # if needed
      - /etc/localtime:/etc/localtime:ro
    depends_on:
      postgres:
        condition: service_healthy
      redis:                    # if using Redis
        condition: service_healthy
      mongo:                    # if using MongoDB
        condition: service_healthy
      traefik:
        condition: service_healthy
      authentik-server:         # if using authentication
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "wget --quiet --tries=1 --spider http://localhost:{container_port}/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    labels:
      - "traefik.enable=true"
      
      # API/Webhook routes (if applicable) - higher priority, no authentication
      - "traefik.http.routers.{service_name}-api.rule=Host(`{service_name}.${DOMAIN:-zoi.local}`) && (PathPrefix(`/api`) || PathPrefix(`/webhook`))"
      - "traefik.http.routers.{service_name}-api.entrypoints=web"
      - "traefik.http.routers.{service_name}-api.priority=100"
      - "traefik.http.routers.{service_name}-api.service={service_name}"
      
      # Frontend/UI routes - lower priority, with authentication
      - "traefik.http.routers.{service_name}-frontend.rule=Host(`{service_name}.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.{service_name}-frontend.entrypoints=web"
      - "traefik.http.routers.{service_name}-frontend.priority=50"
      - "traefik.http.routers.{service_name}-frontend.middlewares={service_name}-frontend-auth@file"
      - "traefik.http.routers.{service_name}-frontend.service={service_name}"
      
      # Service definition
      - "traefik.http.services.{service_name}.loadbalancer.server.port={container_port}"
      
      # Authentik outpost callbacks - highest priority
      - "traefik.http.routers.{service_name}-outpost.rule=Host(`{service_name}.${DOMAIN:-zoi.local}`) && PathPrefix(`/outpost.goauthentik.io/`)"
      - "traefik.http.routers.{service_name}-outpost.entrypoints=web"
      - "traefik.http.routers.{service_name}-outpost.service=authentik"
      - "traefik.http.routers.{service_name}-outpost.priority=200"
    networks:
      - backend_network         # Always include
      - frontend_network        # Always include
      - database_network        # If using databases
      - auth_network           # If using authentication
      - monitoring_network     # If dashboard/monitoring integration
```

#### **5.2 Add Volume Definition**
**Add to `volumes` section in `docker-compose.yml`:**
```yaml
volumes:
  # ... existing volumes ...
  {service_name}_data:
```

### **Step 6: Traefik Middleware Configuration**

#### **6.1 Update Middleware Configuration**
**File**: `config/traefik/dynamic/middleware.yml`

```yaml
    # {Service Name} Frontend Authentication
    {service_name}-frontend-auth:
      chain:
        middlewares:
          - authentik-forward-auth
          # Add service-specific middlewares if needed
          # - {service_name}-headers-inject  # for API key injection
```

#### **6.2 Service-Specific Middleware (if needed)**
```yaml
    # Auto-inject API keys for authenticated users (example)
    {service_name}-headers-inject:
      headers:
        customRequestHeaders:
          Authorization: "Bearer ${'{SERVICE_NAME}_API_KEY'}"
          X-User-Context: "authenticated-via-authentik"
```

### **Step 7: Authentik Integration**

#### **7.1 Create Authentik Blueprint**
**File**: `config/authentik/blueprints/{service_name}-oauth-integration.yaml`

```yaml
# yaml-language-server: $schema=https://goauthentik.io/blueprints/schema.json
version: 1
metadata:
  name: 0X-{service_name}-oauth-integration
  labels:
    blueprints.goauthentik.io/instantiate: "true"
    blueprints.goauthentik.io/description: "Step X: {Service Name} OAuth2/OIDC and Forward Auth Integration"
context: {}
entries:
  # OAuth2/OIDC Provider (if service supports OAuth2)
  - model: authentik_providers_oauth2.oauth2provider
    state: present
    identifiers:
      name: {Service Name} OAuth2 Provider
    attrs:
      name: "{Service Name} OAuth2 Provider"
      client_type: confidential
      client_id: "{service_name}-api-client"
      client_secret: !Env [{SERVICE_NAME}_OAUTH_CLIENT_SECRET, "{service_name}-secret-change-me"]
      authorization_flow: !Find [authentik_flows.flow, [slug, "default-provider-authorization-explicit-consent"]]
      invalidation_flow: !Find [authentik_flows.flow, [slug, "default-invalidation-flow"]]
      
      # Redirect URIs
      redirect_uris:
        - "http://{service_name}.zoi.local/auth/callback"
        - "http://{service_name}.zoi.local/oauth/callback"
        - "https://{service_name}.zoi.local/auth/callback"
        - "https://{service_name}.zoi.local/oauth/callback"
      
      # JWT Configuration
      sub_mode: hashed_user_id
      include_claims_in_id_token: true
      issuer_mode: per_provider
      access_token_validity: hours=1
      refresh_token_validity: days=7
      
      # Scopes
      property_mappings:
        - !Find [authentik_providers_oauth2.scopemapping, [scope_name, openid]]
        - !Find [authentik_providers_oauth2.scopemapping, [scope_name, profile]]
        - !Find [authentik_providers_oauth2.scopemapping, [scope_name, email]]

  # Forward Auth Provider for UI access
  - model: authentik_providers_proxy.proxyprovider
    state: present
    identifiers:
      name: {Service Name} Forward Auth
    attrs:
      name: "{Service Name} Forward Auth"
      mode: forward_domain
      external_host: "http://{service_name}.zoi.local"
      authorization_flow: !Find [authentik_flows.flow, [slug, "default-provider-authorization-explicit-consent"]]
      invalidation_flow: !Find [authentik_flows.flow, [slug, "default-invalidation-flow"]]
      
      # Skip authentication for API/webhook paths
      skip_path_regex: '^/(api|webhook)/.*$'

  # OAuth2 Application
  - model: authentik_core.application
    state: present
    identifiers:
      name: {Service Name} OAuth2 API
    attrs:
      name: "{Service Name} OAuth2 API"
      slug: "{service_name}-oauth2-api"
      provider: !Find [authentik_providers_oauth2.oauth2provider, [name, "{Service Name} OAuth2 Provider"]]
      policy_engine_mode: any
      group: "zoi-users"

  # Forward Auth Application  
  - model: authentik_core.application
    state: present
    identifiers:
      name: {Service Name} Frontend
    attrs:
      name: "{Service Name} Frontend"
      slug: "{service_name}-frontend"
      provider: !Find [authentik_providers_proxy.proxyprovider, [name, "{Service Name} Forward Auth"]]
      policy_engine_mode: any
      group: "zoi-users"

  # Policy Binding - Reuse existing group access
  - model: authentik_policies.policybinding
    state: present
    identifiers:
      target: !Find [authentik_core.application, [slug, "{service_name}-frontend"]]
      policy: !Find [authentik_policies_expression.expressionpolicy, [name, "dashy-users-group-policy"]]
    attrs:
      target: !Find [authentik_core.application, [slug, "{service_name}-frontend"]]
      policy: !Find [authentik_policies_expression.expressionpolicy, [name, "dashy-users-group-policy"]]
      order: 0
      enabled: true

  # Update Embedded Outpost (add new providers)
  - model: authentik_outposts.outpost
    state: present
    identifiers:
      name: "authentik Embedded Outpost"
    attrs:
      name: "authentik Embedded Outpost"
      type: proxy
      providers:
        - !Find [authentik_providers_proxy.proxyprovider, [name, "Dashy Forward Auth"]]
        - !Find [authentik_providers_proxy.proxyprovider, [name, "LiteLLM Forward Auth"]]
        - !Find [authentik_providers_proxy.proxyprovider, [name, "{Service Name} Forward Auth"]]
      config:
        authentik_host: http://auth.zoi.local
        authentik_host_insecure: true
        log_level: info
```

### **Step 8: Service Testing & Validation**

#### **8.1 Environment Variable Validation**
```bash
# Validate environment variables using Zod or similar
# Add to service startup validation
```

#### **8.2 Docker Compose Validation**
```bash
# Validate configuration
docker-compose config --quiet

# Test service startup
docker-compose up -d {service_name}

# Check service health
docker-compose ps {service_name}
docker-compose logs {service_name}
```

#### **8.3 Network Connectivity Tests**
```bash
# Test database connectivity
docker-compose exec {service_name} nc -zv postgres 5432

# Test Redis connectivity (if applicable)
docker-compose exec {service_name} nc -zv redis 6379

# Test MongoDB connectivity (if applicable)  
docker-compose exec {service_name} nc -zv mongo 27017

# Test Authentik connectivity
docker-compose exec {service_name} nc -zv authentik-server 9000
```

#### **8.4 Authentication Flow Testing**
```bash
# Test direct access (should work for API paths)
curl -I http://{service_name}.zoi.local/api/health

# Test UI access (should redirect to Authentik)
curl -I http://{service_name}.zoi.local/

# Test OAuth2 flow (if applicable)
curl -X POST "http://auth.zoi.local/application/o/token/" \
  -d "grant_type=client_credentials&client_id={service_name}-api-client&client_secret=${SERVICE_NAME}_OAUTH_CLIENT_SECRET"
```

### **Step 9: Documentation & README Updates**

#### **9.1 Update Main README**
Add service to main project README with:
- Service description and purpose
- Access URLs
- Authentication requirements
- API documentation links

#### **9.2 Create Service-Specific Documentation**
**File**: `docs/{service_name}-integration.md`
- Configuration details
- API usage examples
- Troubleshooting guide
- Integration patterns

---

## 🔒 **Authentication Patterns**

### **Pattern 1: Forward Auth Only** (Dashboard/UI services)
- UI protected by Authentik forward auth
- No API authentication needed
- Example: Dashy, monitoring dashboards

### **Pattern 2: Hybrid Auth** (API + UI services)  
- UI protected by forward auth
- API accessible without auth OR with API keys
- Example: N8N (webhooks bypass auth, UI protected)

### **Pattern 3: OAuth2 + Forward Auth** (Full SSO integration)
- UI protected by forward auth
- API accessible with OAuth2 JWT tokens
- Example: LiteLLM (master key + JWT + forward auth)

### **Pattern 4: Service-Specific Auth** (Legacy/Limited SSO)
- Service handles own authentication
- Authentik used only for forward auth protection
- Example: Services without native OAuth2 support

---

## 🌐 **Environment Variable Standards**

### **Naming Conventions**
```bash
# Service-specific variables
{SERVICE_NAME}_HOST=             # Service hostname  
{SERVICE_NAME}_PORT=             # Service port
{SERVICE_NAME}_USER=             # Service admin user
{SERVICE_NAME}_PASS=             # Service admin password
{SERVICE_NAME}_API_KEY=          # Service API key
{SERVICE_NAME}_OAUTH_CLIENT_ID=  # OAuth2 client ID
{SERVICE_NAME}_OAUTH_CLIENT_SECRET= # OAuth2 client secret

# Database variables
DB_TYPE=                         # Database type (postgresdb, mongodb, etc.)
DB_POSTGRESDB_HOST=             # PostgreSQL hostname
DB_POSTGRESDB_DATABASE=         # Database name
DB_POSTGRESDB_USER=             # Database user
DB_POSTGRESDB_PASSWORD=         # Database password

# Email variables (if applicable)
{SERVICE_NAME}_SMTP_HOST=       # SMTP server
{SERVICE_NAME}_SMTP_PORT=       # SMTP port  
{SERVICE_NAME}_SMTP_USER=       # SMTP username
{SERVICE_NAME}_SMTP_PASS=       # SMTP password
{SERVICE_NAME}_SMTP_SENDER=     # Default sender address
```

### **Fallback Patterns**
All environment variables MUST use fallback patterns:
```bash
VARIABLE_NAME=${VARIABLE_NAME:-default_value}
```

### **Validation Requirements**
- All environment variables must be documented in `.env.example`
- Runtime validation using Zod or similar validation library
- Error handling for missing critical variables
- Consistent default values across all services

---

## 🚀 **Deployment Checklist**

### **Pre-Deployment**
- [ ] Configuration directory created
- [ ] Environment file configured with all required variables
- [ ] `.env.example` updated with new variables
- [ ] Database integration configured (if needed)
- [ ] Docker Compose service definition added
- [ ] Volume definition added (if needed)
- [ ] Traefik middleware configured (if authentication needed)
- [ ] Authentik blueprint created (if authentication needed)
- [ ] Health check configured
- [ ] Network assignments verified

### **Deployment**
- [ ] Configuration validation: `docker-compose config --quiet`
- [ ] Service startup: `docker-compose up -d {service_name}`
- [ ] Health check verification: `docker-compose ps {service_name}`
- [ ] Log review: `docker-compose logs {service_name}`
- [ ] Network connectivity tests
- [ ] Authentication flow tests (if applicable)

### **Post-Deployment**
- [ ] Service accessible via domain: `http://{service_name}.zoi.local`
- [ ] Authentication working (if applicable)
- [ ] API endpoints responding (if applicable)
- [ ] Database connectivity verified (if applicable)
- [ ] Documentation updated
- [ ] Monitoring configured (if applicable)

---

## 🔧 **Troubleshooting Guide**

### **Common Issues**

#### **Service Won't Start**
```bash
# Check configuration
docker-compose config --quiet

# Check dependencies
docker-compose ps postgres redis mongo traefik authentik-server

# Check logs
docker-compose logs {service_name}

# Check environment variables
docker-compose exec {service_name} env | grep {SERVICE_NAME}
```

#### **Database Connection Issues**
```bash
# Verify database exists
docker-compose exec postgres psql -U postgres -l | grep {service_name}

# Test connectivity
docker-compose exec {service_name} nc -zv postgres 5432

# Check database user
docker-compose exec postgres psql -U postgres -c "\du" | grep {service_name}
```

#### **Authentication Issues**
```bash
# Check Authentik blueprint status
docker-compose logs authentik-server | grep blueprint

# Test forward auth endpoint
curl -I "http://auth.zoi.local/outpost.goauthentik.io/auth/traefik"

# Check Traefik routing
curl -I "http://{service_name}.zoi.local"
```

#### **Traefik Routing Issues**
```bash
# Check Traefik dashboard
open http://traefik.zoi.local

# Verify service labels
docker inspect {service_name} | grep traefik

# Check middleware configuration
cat config/traefik/dynamic/middleware.yml
```

---

## 📚 **Reference Examples**

### **Complete Example: N8N Integration**
The N8N service integration serves as the reference implementation for this guide:
- **Configuration**: `config/n8n/n8n.env`
- **Docker Compose**: Service definition with hybrid auth pattern
- **Traefik**: Multiple routers (webhooks, frontend, outpost)
- **Authentication**: Forward auth for UI, direct access for webhooks/API
- **Database**: PostgreSQL integration with auto-creation
- **Environment**: Comprehensive variable configuration with fallbacks

### **Research Sources**
- **Context7 Documentation**: Use `task-master research` for service-specific patterns
- **Authentik Official Docs**: [Forward Auth Configuration](https://docs.goauthentik.io/docs/add-secure-apps/providers/proxy/server_traefik)
- **Traefik Documentation**: [Docker Provider](https://doc.traefik.io/traefik/providers/docker/)
- **Project Memory**: Stored patterns and troubleshooting solutions

---

## ✅ **Success Metrics**

A successfully integrated service should achieve:

1. **✅ Configuration Compliance**: Follows all established patterns
2. **✅ Authentication Integration**: Proper Authentik/forward auth setup
3. **✅ Network Connectivity**: All required services accessible
4. **✅ Health Monitoring**: Service health checks passing
5. **✅ Documentation**: Complete integration documentation
6. **✅ Environment Validation**: All variables properly configured with fallbacks
7. **✅ Domain Access**: Service accessible via `{service_name}.zoi.local`
8. **✅ Database Integration**: Proper database setup and connectivity (if applicable)
9. **✅ Security Compliance**: Authentication and authorization working correctly
10. **✅ Monitoring Ready**: Service ready for monitoring integration

---

**🎯 This guide ensures consistent, secure, and maintainable service integration following Zoi project standards.**