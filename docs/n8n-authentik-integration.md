# n8n + Authentik Hybrid Authentication Integration

## Overview

This document describes the successful integration of n8n with Authentik using a hybrid authentication approach that provides:

- **Frontend UI Protection**: Single sign-on via Authentik for web interface access
- **Direct API/Webhook Access**: Unprotected access for webhooks and API endpoints
- **Selective Routing**: Traefik-based routing with different middleware for different paths

## Architecture

```
[External Request] → [Traefik] → [Authentik Forward Auth] → [n8n Container]
                        ↓
                [Route Decision]
                        ↓
    ┌─────────────────────┴─────────────────────┐
    │                                           │
[Webhook/API Paths]                    [Frontend UI Paths]
Priority: 100                          Priority: 50
No Authentication                      Authentik Forward Auth
Direct Access                          SSO Required
```

## Configuration Details

### 1. n8n Service Configuration

**Container Setup:**
- Image: `n8nio/n8n:latest`
- Port: `5678`
- PostgreSQL database backend
- Basic auth disabled (using Authentik instead)

**Environment Variables:**
```bash
N8N_BASIC_AUTH_ACTIVE=false
N8N_HOST=n8n.zoi.local
WEBHOOK_URL=http://n8n.zoi.local/
```

### 2. Traefik Routing Configuration

**Two Router Strategy:**

1. **Webhook/API Router** (Higher Priority)
   - Rule: `Host('n8n.zoi.local') && (PathPrefix('/webhook') || PathPrefix('/api'))`
   - Priority: `100`
   - Middleware: None (direct access)
   - Service: `n8n`

2. **Frontend Router** (Lower Priority)
   - Rule: `Host('n8n.zoi.local')`
   - Priority: `50`
   - Middleware: `n8n-frontend-auth@file`
   - Service: `n8n`

3. **Outpost Callback Router** (Highest Priority)
   - Rule: `Host('n8n.zoi.local') && PathPrefix('/outpost.goauthentik.io/')`
   - Priority: `200`
   - Middleware: None
   - Service: `authentik`

### 3. Traefik Middleware Configuration

**n8n Frontend Authentication:**
```yaml
n8n-frontend-auth:
  chain:
    middlewares:
      - authentik-forward-auth
```

**Authentik Forward Auth:**
```yaml
authentik-forward-auth:
  forwardAuth:
    address: "http://auth.zoi.local/outpost.goauthentik.io/auth/traefik"
    trustForwardHeader: true
    authResponseHeaders:
      - "X-authentik-username"
      - "X-authentik-groups"
      - "X-authentik-email"
      # ... additional headers
```

### 4. Authentik Configuration

**Forward Auth Provider:**
```yaml
name: "n8n Forward Auth"
mode: forward_domain
external_host: http://n8n.zoi.local
internal_host: http://n8n:5678
cookie_domain: zoi.local
skip_path_regex: ^/(webhook|api)/.*$  # Critical for bypassing auth on webhooks/API
```

**Application Settings:**
- Group: `zoi-users`
- Launch URL: `http://n8n.zoi.local`
- Policy: Group-based access control

**Outpost Assignment:**
- Provider assigned to "authentik Embedded Outpost"
- Outpost configured with internal Docker network address

## Testing and Verification

### 1. Frontend Access Test
```bash
curl -I http://n8n.zoi.local/
# Expected: 302 redirect to Authentik authorization endpoint
```

### 2. Webhook Access Test
```bash
curl -I http://n8n.zoi.local/webhook/test
# Expected: 404 Not Found (direct access, no auth redirect)
```

### 3. API Access Test
```bash
curl -I http://n8n.zoi.local/api/v1/workflows
# Expected: 405 Method Not Allowed (direct access, no auth redirect)
```

## Key Success Factors

1. **DNS Resolution**: Added `n8n.zoi.local` to `/etc/hosts`
2. **Router Priorities**: Webhook/API routes have higher priority than frontend routes
3. **Skip Path Regex**: Properly configured in Authentik provider to bypass authentication
4. **Outpost Configuration**: Uses internal Docker network addresses
5. **Group-based Access**: Leverages existing `zoi-users` group for authorization

## Security Considerations

### Protected Resources
- Web UI (`/` and all UI paths)
- Editor interface
- Workflow management

### Unprotected Resources  
- Webhook endpoints (`/webhook/*`)
- API endpoints (`/api/*`)
- Outpost callbacks (`/outpost.goauthentik.io/*`)

### Access Control
- UI access restricted to `zoi-users` group members
- Webhook/API access open for external services
- Single sign-on session management via Authentik

## Troubleshooting Guide

### Issue: Cannot resolve n8n.zoi.local
**Solution**: Add domain to `/etc/hosts`:
```bash
echo "127.0.0.1 n8n.zoi.local" | sudo tee -a /etc/hosts
```

### Issue: Webhooks being blocked by authentication
**Check**: 
1. Verify `skip_path_regex: ^/(webhook|api)/.*$` in Authentik provider
2. Confirm webhook router has higher priority (100 vs 50)
3. Test webhook endpoint directly

### Issue: UI not redirecting to Authentik
**Check**:
1. Authentik provider configuration
2. Outpost health and assignment
3. Traefik middleware configuration

### Issue: Authentication loops
**Solution**: Ensure outpost callback router is properly configured with highest priority

## Benefits Achieved

✅ **Single Sign-On**: Users authenticate once via Authentik for UI access  
✅ **Webhook Compatibility**: External services can call webhooks without authentication  
✅ **API Access**: Direct API access for integrations and automation  
✅ **Group-based Security**: Access control via Authentik groups  
✅ **Unified Management**: Centralized authentication with other services  
✅ **Flexible Routing**: Path-based authentication policies  

## Related Documentation

- [LiteLLM + Authentik Integration](./examples/auth-flow-demo.md)
- [Authentik Blueprint Configuration](../config/authentik/blueprints/)
- [Traefik Middleware Configuration](../config/traefik/dynamic/middleware.yml)

---

**Integration Status**: ✅ **SUCCESSFUL**  
**Date**: June 12, 2025  
**Version**: n8n latest, Authentik 2025.2.4, Traefik latest
