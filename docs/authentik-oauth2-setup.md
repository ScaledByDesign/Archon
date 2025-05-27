# Authentik OAuth2 and OIDC Configuration

This document outlines the OAuth2 and OpenID Connect (OIDC) configuration for the Production RAG System using Authentik.

## Overview

Authentik serves as the centralized identity provider for all services in the RAG system, providing:
- Single Sign-On (SSO) across all applications
- OAuth2 and OIDC authentication flows
- Role-based access control (RBAC)
- User and group management
- Secure token management

## Application Configurations

### FastAPI Backend (`fastapi-client`)
- **Client Type**: Confidential
- **Grant Type**: Authorization Code
- **Redirect URIs**: 
  - `https://api.localhost/auth/callback`
  - `http://localhost:8000/auth/callback`
- **Scopes**: `openid`, `email`, `profile`, `rag:api`
- **Access Policy**: API Access (admins, users, api-users groups)

### Open WebUI (`webui-client`)
- **Client Type**: Public
- **Grant Type**: Authorization Code
- **Redirect URIs**: 
  - `https://chat.localhost/auth/callback`
  - `http://localhost:3000/auth/callback`
- **Scopes**: `openid`, `email`, `profile`, `rag:chat`
- **Access Policy**: User Access (any authenticated user)

### n8n Workflows (`n8n-client`)
- **Client Type**: Confidential
- **Grant Type**: Authorization Code
- **Redirect URIs**: 
  - `https://n8n.localhost/rest/oauth2-credential/callback`
- **Scopes**: `openid`, `email`, `profile`, `rag:workflows`
- **Access Policy**: Workflow Access (admins only)

## Custom Scope Definitions

### `rag:api`
Provides access to RAG system API endpoints with user context:
```json
{
  "api_access": true,
  "user_id": "user-pk",
  "username": "username",
  "groups": ["group1", "group2"],
  "is_admin": false
}
```

### `rag:chat`
Provides access to the chat interface with user preferences:
```json
{
  "chat_access": true,
  "user_id": "user-pk",
  "username": "username",
  "preferences": {
    "theme": "auto",
    "language": "en"
  }
}
```

### `rag:workflows`
Provides access to workflow automation features:
```json
{
  "workflow_access": true,
  "user_id": "user-pk",
  "username": "username",
  "can_create_workflows": true
}
```

## Authentication Flows

### Default Authentication Flow
1. User accesses protected application
2. Redirected to Authentik login page
3. User enters credentials
4. Password validation stage
5. User login stage (session creation)
6. Redirect back to application

### Default Authorization Flow
1. Application requests authorization
2. User consent stage (if required)
3. Authorization code generated
4. Application exchanges code for tokens

### Default Invalidation Flow
1. User initiates logout
2. User logout stage
3. Session termination
4. Redirect to logout page

## Access Control Policies

### Admin Access Policy
- Grants access to admin-level applications
- Checks for superuser status or "admins" group membership
- Applied to: Traefik Dashboard, RabbitMQ Management, Redis Insight

### User Access Policy
- Grants access to standard user applications
- Requires authentication only
- Applied to: Open WebUI

### API Access Policy
- Grants access to API endpoints
- Checks for membership in: "admins", "users", "api-users" groups
- Applied to: FastAPI Backend

### Workflow Access Policy
- Grants access to workflow automation
- Restricted to "admins" group initially
- Applied to: n8n

## Group Structure

### `admins`
- Full system access
- Can manage users and applications
- Access to all admin interfaces
- Workflow creation privileges

### `users`
- Standard user access
- Chat interface access
- API access for personal use
- Read-only access to most features

### `api-users`
- Specialized group for API access
- Programmatic access to RAG system
- No web interface access by default

## Environment Variables

Required environment variables for OAuth2 configuration:

```bash
# Authentik Core
AUTHENTIK_SECRET_KEY=your-secret-key-here
AUTHENTIK_BOOTSTRAP_PASSWORD=admin-password
AUTHENTIK_BOOTSTRAP_TOKEN=bootstrap-token
AUTHENTIK_BOOTSTRAP_EMAIL=admin@localhost

# OAuth2 Client Secrets (generated automatically)
FASTAPI_OAUTH_CLIENT_SECRET=generated-secret
WEBUI_OAUTH_CLIENT_SECRET=generated-secret
N8N_OAUTH_CLIENT_SECRET=generated-secret

# Database
PG_PASS=postgresql-password
AUTHENTIK_REDIS_PASS=redis-password
```

## Security Considerations

1. **Client Secrets**: Confidential clients use secure random secrets
2. **Token Validity**: 
   - Access tokens: 60 minutes
   - Refresh tokens: 30 days
3. **HTTPS Only**: All production URLs use HTTPS
4. **Scope Limitation**: Each application gets minimal required scopes
5. **Policy Enforcement**: Role-based access control at application level

## Integration Points

### Service Configuration
Each service needs to be configured with:
- OAuth2 client credentials
- Authentik endpoints
- Redirect URIs
- Required scopes

### Example Environment Variables for Services
```bash
# FastAPI
OAUTH2_CLIENT_ID=fastapi-client
OAUTH2_CLIENT_SECRET=${FASTAPI_OAUTH_CLIENT_SECRET}
OAUTH2_AUTHORIZATION_URL=https://auth.localhost/application/o/authorize/
OAUTH2_TOKEN_URL=https://auth.localhost/application/o/token/
OAUTH2_USERINFO_URL=https://auth.localhost/application/o/userinfo/

# Open WebUI
OAUTH_CLIENT_ID=webui-client
OAUTH_CLIENT_SECRET=${WEBUI_OAUTH_CLIENT_SECRET}
OAUTH_PROVIDER_NAME=Authentik
OAUTH_REDIRECT_URI=https://chat.localhost/auth/callback
```

## Troubleshooting

### Common Issues
1. **Redirect URI Mismatch**: Ensure all URIs are properly configured
2. **Scope Issues**: Verify required scopes are included in provider
3. **Policy Denials**: Check user group membership
4. **Token Expiry**: Verify refresh token functionality

### Debug Endpoints
- Authentik Admin: `https://auth.localhost/if/admin/`
- Well-known Configuration: `https://auth.localhost/application/o/{provider}/.well-known/openid_configuration`
- User Info: `https://auth.localhost/application/o/userinfo/`

## Next Steps

1. Deploy Authentik services
2. Apply blueprint configurations
3. Test OAuth2 flows with each application
4. Configure service-specific OAuth2 clients
5. Validate access policies and permissions
