# Authentik SSO Deployment and Testing Guide

This guide provides step-by-step instructions for deploying and testing the Authentik SSO integration for the Production RAG System.

## Prerequisites

1. **Docker and Docker Compose** installed and running
2. **Environment variables** configured in `.env` file
3. **DNS/Hosts setup** for local domains (if testing locally)
4. **SSL certificates** (self-signed for development)

## Deployment Steps

### Step 1: Verify Configuration

```bash
# Validate Docker Compose configuration
docker-compose config

# Validate Authentik blueprints
./scripts/validate-blueprints.sh

# Check environment variables
grep -E "^AUTHENTIK_|^PG_PASS|^DOMAIN" .env
```

### Step 2: Setup Local DNS (Development Only)

Add the following entries to your `/etc/hosts` file for local testing:

```bash
# Add to /etc/hosts
127.0.0.1 localhost
127.0.0.1 auth.localhost
127.0.0.1 api.localhost
127.0.0.1 chat.localhost
127.0.0.1 n8n.localhost
127.0.0.1 traefik.localhost
```

### Step 3: Deploy Core Infrastructure

Start the core services in order:

```bash
# Start databases and cache first
docker-compose up -d authentik-db authentik-redis

# Wait for databases to be healthy
docker-compose ps authentik-db authentik-redis

# Start Traefik reverse proxy
docker-compose up -d traefik

# Start Authentik services
docker-compose up -d authentik-server authentik-worker
```

### Step 4: Monitor Service Health

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs -f authentik-server
docker-compose logs -f authentik-worker

# Check health status
docker-compose exec authentik-server ak healthcheck
```

### Step 5: Access Authentik Admin Interface

1. Open browser and navigate to: `https://auth.localhost/if/admin/`
2. Login with bootstrap credentials:
   - Email: Value from `AUTHENTIK_BOOTSTRAP_EMAIL`
   - Password: Value from `AUTHENTIK_BOOTSTRAP_PASSWORD`

### Step 6: Apply Blueprint Configurations

#### Method 1: Web Interface
1. Navigate to **System** → **Blueprints**
2. Upload blueprint files from `config/authentik/blueprints/`
3. Apply blueprints in this order:
   - `oauth2-flows.yaml`
   - `oauth2-scopes.yaml`
   - `users.yaml`
   - `applications.yaml`
   - `access-policies.yaml`

#### Method 2: API (Recommended)
```bash
# Apply blueprints via API
./scripts/apply-blueprints.sh
```

### Step 7: Verify Blueprint Application

Check that the following have been created:

1. **Flows**: Navigate to **Flows** → **Flows**
   - Default Authorization Flow
   - Default Authentication Flow
   - Default Invalidation Flow

2. **Applications**: Navigate to **Applications** → **Applications**
   - FastAPI Backend
   - Chat Interface
   - Workflow Automation

3. **Providers**: Navigate to **Applications** → **Providers**
   - fastapi-oauth2
   - webui-oauth2
   - n8n-oauth2

4. **Users & Groups**: Navigate to **Directory** → **Users** and **Groups**
   - Groups: admins, users
   - Users: admin, user

## Testing the SSO Integration

### Test 1: Authentication Flow

1. **Access Protected Application**:
   ```bash
   curl -I https://api.localhost/protected
   ```
   Should redirect to Authentik login

2. **Login via Web Interface**:
   - Navigate to `https://chat.localhost`
   - Should redirect to `https://auth.localhost/if/flow/default-authentication-flow/`
   - Login with test credentials
   - Should redirect back to application

### Test 2: OAuth2 Token Flow

```bash
# Test OAuth2 authorization code flow
AUTHORIZATION_URL="https://auth.localhost/application/o/authorize/"
CLIENT_ID="fastapi-client"
REDIRECT_URI="https://api.localhost/auth/callback"
SCOPES="openid email profile rag:api"

# Construct authorization URL
AUTH_URL="${AUTHORIZATION_URL}?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=${SCOPES}"

echo "Visit this URL to test OAuth2 flow:"
echo $AUTH_URL
```

### Test 3: Token Validation

```bash
# Get access token (after completing OAuth2 flow)
ACCESS_TOKEN="your-access-token-here"

# Validate token with userinfo endpoint
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
     https://auth.localhost/application/o/userinfo/
```

### Test 4: Application Access Policies

1. **Admin Access Test**:
   ```bash
   # Try accessing admin-only applications
   curl -I https://traefik.localhost/dashboard/
   ```

2. **User Access Test**:
   ```bash
   # Try accessing user applications
   curl -I https://chat.localhost/
   ```

### Test 5: Cross-Service SSO

1. Login to one application (e.g., Open WebUI)
2. Navigate to another application (e.g., n8n)
3. Should automatically be logged in (SSO)

## Troubleshooting

### Common Issues and Solutions

#### 1. Service Startup Issues

```bash
# Check container logs
docker-compose logs authentik-server

# Common issues:
# - Database connection failed → Check authentik-db health
# - Redis connection failed → Check authentik-redis health
# - Bootstrap token error → Verify AUTHENTIK_BOOTSTRAP_TOKEN
```

#### 2. Blueprint Application Failures

```bash
# Check blueprint syntax
./scripts/validate-blueprints.sh

# Common issues:
# - Missing dependencies → Apply blueprints in correct order
# - Invalid references → Check !KeyOf and !Find references
# - Syntax errors → Validate YAML structure
```

#### 3. OAuth2 Flow Issues

```bash
# Check provider configuration
curl https://auth.localhost/application/o/fastapi-oauth2/.well-known/openid_configuration

# Common issues:
# - Redirect URI mismatch → Check application redirect_uris
# - Invalid client credentials → Verify client_id/client_secret
# - Scope errors → Ensure required scopes are mapped
```

#### 4. Access Policy Failures

```bash
# Check user group membership
# In Authentik admin: Directory → Users → [username] → Groups

# Common issues:
# - User not in required group → Add user to appropriate group
# - Policy expression errors → Check policy syntax
# - Missing permissions → Verify policy bindings
```

### Debug Commands

```bash
# View all container logs
docker-compose logs

# Check service health
docker-compose exec authentik-server ak healthcheck

# Validate Authentik configuration
docker-compose exec authentik-server ak config

# Test database connection
docker-compose exec authentik-db pg_isready -U authentik

# Test Redis connection
docker-compose exec authentik-redis redis-cli ping
```

### Log Locations

- **Authentik Server**: `docker-compose logs authentik-server`
- **Authentik Worker**: `docker-compose logs authentik-worker`
- **PostgreSQL**: `docker-compose logs authentik-db`
- **Redis**: `docker-compose logs authentik-redis`
- **Traefik**: `docker-compose logs traefik`

## Performance Tuning

### Production Optimizations

1. **Database Connection Pooling**:
   ```yaml
   # In authentik.env
   AUTHENTIK_POSTGRESQL__MAX_CONNS=20
   AUTHENTIK_POSTGRESQL__CONN_MAX_AGE=300
   ```

2. **Redis Memory Optimization**:
   ```yaml
   # In redis configuration
   maxmemory 512mb
   maxmemory-policy allkeys-lru
   ```

3. **Worker Scaling**:
   ```yaml
   # Scale worker instances
   docker-compose up -d --scale authentik-worker=3
   ```

### Monitoring Setup

```bash
# Enable metrics collection
docker-compose exec authentik-server ak config set prometheus.enabled true

# Access metrics endpoint
curl https://auth.localhost/metrics
```

## Security Considerations

1. **Secret Management**: Ensure all secrets are properly secured
2. **HTTPS Only**: Use HTTPS for all production endpoints
3. **Token Expiry**: Configure appropriate token lifetimes
4. **Rate Limiting**: Enable rate limiting on authentication endpoints
5. **Audit Logging**: Enable comprehensive audit logging

## Next Steps

After successful deployment and testing:

1. Configure production DNS and SSL certificates
2. Set up backup procedures for Authentik data
3. Implement monitoring and alerting
4. Configure additional identity sources (LDAP, SAML, etc.)
5. Integrate remaining services with OAuth2 authentication

## Support and Documentation

- **Authentik Documentation**: https://goauthentik.io/docs/
- **OAuth2 Specification**: https://tools.ietf.org/html/rfc6749
- **OpenID Connect**: https://openid.net/connect/
- **Project Documentation**: `docs/authentik-oauth2-setup.md`
