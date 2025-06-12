# LiteLLM Security with Authentik Integration

## Overview

This document outlines the security architecture for protecting LiteLLM using Authentik as the authentication provider. This approach provides enterprise-grade security without requiring LiteLLM Enterprise features.

## Security Architecture

### 1. **Forward Authentication Pattern**

```
Internet → Traefik (Reverse Proxy) → Authentik (Auth Check) → LiteLLM (API)
```

- **Traefik** acts as the reverse proxy and enforces authentication
- **Authentik** validates all authentication requests via forward auth
- **LiteLLM** is never directly exposed to the internet
- All requests must pass Authentik authentication before reaching LiteLLM

### 2. **Multi-Layer Security**

#### Layer 1: Network Security
- LiteLLM runs in isolated Docker networks
- No direct internet exposure
- Only accessible through Traefik reverse proxy

#### Layer 2: Authentication (Authentik)
- OAuth2/OIDC authentication flow
- User management and group-based access control
- Session management and token validation
- Multi-factor authentication support

#### Layer 3: Authorization (LiteLLM + Authentik)
- Master key authentication for API access
- Group-based access control via Authentik (`zoi-users`)
- Header-based user context passing

## Configuration Details

### LiteLLM Configuration
```yaml
general_settings:
  # Master key for API authentication
  master_key: sk-6df5295f77391ff7611a0fab11b989287012f48e46f58ae0
  
  # CORS settings for web integration
  allowed_origins: ["*"]
  allowed_methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
  allowed_headers: ["*"]
  
  # UI access control
  ui_access_mode: "all"
```

### Traefik Configuration
```yaml
# Forward auth middleware
http:
  middlewares:
    authentik:
      forwardAuth:
        address: "http://authentik-server:9000/outpost.goauthentik.io/auth/traefik"
        trustForwardHeader: true
        authResponseHeaders:
          - X-authentik-username
          - X-authentik-groups
          - X-authentik-email
          - X-authentik-name
          - X-authentik-uid
```

### Authentik Blueprint Integration
- OAuth2 provider for web authentication flows
- Forward auth provider for API protection
- Group-based access policies (`zoi-users`)
- Embedded outpost for Traefik integration

## Security Benefits

### 1. **No Direct API Exposure**
- LiteLLM API is only accessible through authenticated proxy
- Prevents unauthorized direct access attempts
- Centralizes all access logging and monitoring

### 2. **Centralized Authentication**
- Single sign-on across all services
- Consistent user management
- Audit trail for all authentication events

### 3. **Granular Access Control**
- Group-based permissions via Authentik
- User context headers passed to LiteLLM
- Ability to implement role-based API access

### 4. **Session Management**
- Secure session handling by Authentik
- Token expiration and refresh
- Session invalidation capabilities

## API Access Patterns

### 1. **Web UI Access**
```
User → OAuth2 Login (Authentik) → Traefik → LiteLLM UI
```

### 2. **API Access**
```
Client → API Key + Auth Headers → Traefik → Authentik Check → LiteLLM API
```

### 3. **Programmatic Access**
```python
import requests

headers = {
    'Authorization': 'Bearer sk-6df5295f77391ff7611a0fab11b989287012f48e46f58ae0',
    'Content-Type': 'application/json'
}

# Must go through Traefik (authenticated) endpoint
response = requests.post(
    'https://llm.zoi.local/v1/chat/completions',
    headers=headers,
    json={
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': 'Hello'}]
    }
)
```

## Security Best Practices

### 1. **API Key Management**
- Use strong, unique master keys
- Rotate keys regularly
- Store keys in secure environment variables
- Monitor API key usage through LiteLLM logging

### 2. **Network Security**
- Use Docker networks for service isolation
- Implement firewall rules if needed
- Consider VPN access for additional security

### 3. **Monitoring and Logging**
- Enable LiteLLM request logging
- Monitor Authentik authentication events
- Set up alerts for failed authentication attempts
- Track API usage patterns

### 4. **Access Control**
- Regularly review user group memberships
- Implement principle of least privilege
- Use Authentik's audit logs for access reviews

## Alternatives Considered

### 1. **LiteLLM Enterprise OAuth2**
- **Pros**: Native OAuth2 integration
- **Cons**: Requires enterprise license
- **Decision**: Not viable for open-source deployment

### 2. **JWT Authentication**
- **Pros**: Standards-based token validation
- **Cons**: LiteLLM's JWT auth has limited external provider support
- **Decision**: Forward auth provides better integration

### 3. **Basic Auth/API Keys Only**
- **Pros**: Simple implementation
- **Cons**: No user management, session handling, or audit trails
- **Decision**: Insufficient for multi-user environments

## Troubleshooting

### Common Issues

1. **LiteLLM Startup Failures**
   - Remove any invalid JWT/OAuth2 config from `config.yaml`
   - Ensure only supported configuration options are used

2. **Authentication Loops**
   - Check Traefik middleware configuration
   - Verify Authentik forward auth provider settings

3. **API Access Denied**
   - Confirm user is in `zoi-users` group
   - Check Authentik access policies
   - Verify API key format and validity

### Debug Commands
```bash
# Check LiteLLM logs
docker compose logs litellm -f

# Check Authentik logs
docker compose logs authentik-server -f

# Test API endpoint
curl -H "Authorization: Bearer sk-..." https://llm.zoi.local/v1/models
```

## Conclusion

This security architecture provides robust protection for LiteLLM using open-source components:

- **Authentication**: Handled by Authentik with OAuth2/OIDC
- **Authorization**: Group-based access control
- **Network Security**: Reverse proxy with no direct exposure
- **Audit Trail**: Comprehensive logging across all layers

The setup is production-ready and provides enterprise-grade security without requiring commercial licenses.
