# Authentik & Traefik Integration Fix Documentation

## Overview
This document outlines the current state, identified issues, and solutions for integrating Authentik with Traefik to secure the Dashy dashboard and other services.

## Current System Setup

### Services Configuration (docker-compose.core.yml)
- **Traefik v3.0**: Ports 80/443/8080/8081 with Docker and file providers
- **Authentik Server**: Port 9000, routed to `auth.${DOMAIN:-localhost}`
- **Authentik Worker**: Background service for Authentik tasks
- **Dashy**: Port 4001:8080, configured with `authentik-forward-auth@file` middleware
- **PostgreSQL & Redis**: Shared database services for all applications

### Network Architecture
- `frontend_network`: External-facing services
- `backend_network`: Internal service communication
- `auth_network`: Authentication services
- `database_network`: Database connections

## Identified Issues

### 1. ✅ FIXED: Forward Auth Endpoint
**Problem**: Traefik middleware was pointing to wrong Authentik endpoint
- **Incorrect**: `http://authentik-server:9000/application/o/traefik-forward-auth/`
- **Correct**: `http://authentik-server:9000/outpost.goauthentik.io/auth/traefik`

**Status**: Fixed in `config/traefik/dynamic/middleware.yml`

### 2. 🔧 PENDING: Domain Configuration Mismatch
**Problem**: Multiple domain configurations causing confusion
- **Docker Compose**: Uses `${DOMAIN:-localhost}` (defaults to localhost)
- **Dashy Config**: Hardcoded to `zoi.cc` domains
- **Authentik Blueprints**: Mixed localhost/domain references

**Solution Needed**: 
- Create `.env` file with `DOMAIN=localhost` for development
- Update Dashy config to use `localhost` domains
- Verify Authentik blueprints use correct domain variables

### 3. 🔧 PENDING: Authentik Configuration
**Problem**: Several Authentik configuration issues
- Default secret key needs to be changed
- Default bootstrap credentials need to be updated
- Forward auth provider needs proper configuration

**Current Authentik Environment**:
```env
AUTHENTIK_SECRET_KEY=change-me-to-a-long-random-string-at-least-50-chars
AUTHENTIK_BOOTSTRAP_PASSWORD=change-me-authentik-admin
AUTHENTIK_BOOTSTRAP_TOKEN=change-me-authentik-token
```

### 4. 🔧 PENDING: Blueprint Configuration
**Current Blueprint Issues**:
- `forward-auth.yaml`: Uses `${AUTHENTIK_HOST:-localhost}` variable
- `applications.yaml`: Has hardcoded localhost references
- Missing proper provider configuration for embedded outpost

## Required Actions

### Immediate Fixes Needed

1. **Create Environment Configuration**
```env
# .env file (to be created)
DOMAIN=localhost
PG_PASS=secretpass
REDIS_PASSWORD=change-me-redis-pass
MONGO_PASS=change-me-mongo-pass
```

2. **Update Authentik Configuration**
```env
# Generate new secret key
AUTHENTIK_SECRET_KEY=<64-character-random-string>
AUTHENTIK_BOOTSTRAP_PASSWORD=admin123!
AUTHENTIK_BOOTSTRAP_EMAIL=admin@localhost
```

3. **Fix Dashy Configuration**
Update `config/dashy/conf.yml` to use localhost domains instead of zoi.cc

4. **Verify Blueprint Configuration**
Ensure `config/authentik/blueprints/forward-auth.yaml` properly configures the embedded outpost

### Traefik Middleware Status
✅ **Fixed**: `authentik-forward-auth` middleware now points to correct endpoint:
```yaml
authentik-forward-auth:
  forwardAuth:
    address: "http://authentik-server:9000/outpost.goauthentik.io/auth/traefik"
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

## Testing Strategy

### Manual Testing Flow
1. **Setup Environment**: Ensure `.env` file with `DOMAIN=localhost`
2. **Start Services**: `docker-compose -f docker-compose.core.yml up -d`
3. **Configure Authentik**: 
   - Access `http://auth.localhost:9000`
   - Complete initial setup with admin user
   - Verify forward auth provider is configured
4. **Test Dashy Access**:
   - Navigate to `http://dashy.localhost`
   - Should redirect to Authentik login
   - After login, should redirect back to Dashy

### Playwright E2E Testing
- **Authentication Flow**: Test complete login/logout cycle
- **Session Persistence**: Verify user stays logged in across pages
- **Protected Routes**: Ensure all protected services require authentication
- **Error Handling**: Test invalid credentials and timeout scenarios

## Development vs Production

### Development (localhost)
- Uses `localhost` subdomains
- Self-signed certificates or HTTP
- Simplified authentication flows

### Production (zoi.cc)
- Requires DNS configuration for `*.zoi.cc`
- Let's Encrypt SSL certificates
- Production-grade secret management

## Playwright Testing Setup

### ✅ Completed Test Infrastructure

1. **Enhanced Test Suite**: Created `authentik-traefik-forward-auth.spec.js` with comprehensive tests:
   - Forward auth endpoint verification
   - Authentication header passing validation
   - Domain configuration testing
   - Redirect loop prevention
   - Complete authentication flow testing
   - Session persistence validation
   - Error handling and performance testing

2. **Environment Setup**: Created `test-setup.js` for automated environment verification:
   - Docker services health checking
   - Service endpoint validation
   - Hosts file configuration verification
   - Environment variable validation

3. **Integration Script**: Created `scripts/test-authentik-integration.sh` for complete workflow:
   - Prerequisites checking
   - Automated service startup
   - Health monitoring
   - Test execution
   - Report generation

### Running the Tests

```bash
# Complete integration test (recommended)
./scripts/test-authentik-integration.sh

# Just run tests (if services already running)
cd e2e-tests && npm run test:forward-auth

# Setup environment check only
cd e2e-tests && npm run setup:env

# All test suites
cd e2e-tests && npm run test:all
```

## Next Steps

1. ✅ Create this documentation
2. ✅ Set up Playwright testing environment  
3. ✅ Create comprehensive E2E tests
4. 🔧 Fix remaining configuration issues (create .env file)
5. 🔧 Test complete authentication flow
6. 🔧 Document deployment procedure

## Quick Start Testing

To test the integration immediately:

```bash
# 1. Ensure hosts file has entries (or tests will guide you)
sudo echo "127.0.0.1 dashy.localhost auth.localhost traefik.localhost api.localhost llm.localhost" >> /etc/hosts

# 2. Run the complete integration test
./scripts/test-authentik-integration.sh

# 3. View detailed results
cd e2e-tests && npm run show-report
```

## References
- [Authentik Traefik Forward Auth Documentation](https://docs.goauthentik.io/docs/add-secure-apps/providers/proxy/server_traefik)
- [Traefik v3.0 Documentation](https://doc.traefik.io/traefik/)
- [Dashy Authentication Documentation](https://dashy.to/docs/authentication) 