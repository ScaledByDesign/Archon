# Authentik OAuth2 Setup Guide

## Overview
This guide walks through setting up OAuth2 applications in Authentik for the ZOI RAG System components.

## Prerequisites
- Authentik is running and accessible at https://localhost:9443
- Admin credentials: admin@localhost / change-me-authentik-admin

## Step 1: Access Authentik Admin Interface

1. Navigate to https://localhost:9443/if/admin/
2. Login with admin credentials
3. Accept any SSL certificate warnings (development environment)

## Step 2: Create OAuth2 Scopes

Navigate to **Applications > Providers > OAuth2/OpenID Scopes** and create the following scopes:

### Custom Scopes to Create:

1. **rag:api**
   - Name: `rag:api`
   - Description: `Access to RAG API endpoints`

2. **rag:chat**
   - Name: `rag:chat` 
   - Description: `Access to chat interface`

3. **rag:workflow**
   - Name: `rag:workflow`
   - Description: `Access to workflow automation`

4. **rag:admin**
   - Name: `rag:admin`
   - Description: `Administrative access to RAG system`

## Step 3: Create OAuth2 Applications

For each application below, follow this process:

1. Go to **Applications > Providers**
2. Click **Create** and select **OAuth2/OpenID Provider**
3. Fill in the provider details
4. Go to **Applications > Applications**
5. Click **Create** and link to the provider

### Application 1: FastAPI Backend

**OAuth2 Provider Settings:**
- Name: `FastAPI Backend OAuth2 Provider`
- Client ID: `fastapi-client`
- Client Type: `Confidential`
- Authorization Flow: `default-authorization-flow`
- Redirect URIs: 
  ```
  http://localhost:8000/auth/callback
  https://api.localhost/auth/callback
  ```
- Scopes: `openid email profile rag:api`
- Access Token Validity: `5 minutes`
- Refresh Token Validity: `30 days`

**Application Settings:**
- Name: `FastAPI Backend`
- Slug: `fastapi-backend`
- Provider: Select the provider created above
- Launch URL: `http://localhost:8000`

### Application 2: Chat Interface (Open WebUI)

**OAuth2 Provider Settings:**
- Name: `Chat Interface OAuth2 Provider`
- Client ID: `webui-client`
- Client Type: `Confidential`
- Authorization Flow: `default-authorization-flow`
- Redirect URIs:
  ```
  http://localhost:3000/auth/callback
  https://chat.localhost/auth/callback
  ```
- Scopes: `openid email profile rag:chat`
- Access Token Validity: `5 minutes`
- Refresh Token Validity: `30 days`

**Application Settings:**
- Name: `Chat Interface`
- Slug: `chat-interface`
- Provider: Select the provider created above
- Launch URL: `http://localhost:3000`

### Application 3: Workflow Automation (n8n)

**OAuth2 Provider Settings:**
- Name: `Workflow Automation OAuth2 Provider`
- Client ID: `n8n-client`
- Client Type: `Confidential`
- Authorization Flow: `default-authorization-flow`
- Redirect URIs:
  ```
  http://localhost:5678/rest/oauth2-credential/callback
  https://n8n.localhost/rest/oauth2-credential/callback
  ```
- Scopes: `openid email profile rag:workflow`
- Access Token Validity: `5 minutes`
- Refresh Token Validity: `30 days`

**Application Settings:**
- Name: `Workflow Automation`
- Slug: `workflow-automation`
- Provider: Select the provider created above
- Launch URL: `http://localhost:5678`

### Application 4: Admin Dashboard

**OAuth2 Provider Settings:**
- Name: `Admin Dashboard OAuth2 Provider`
- Client ID: `admin-client`
- Client Type: `Confidential`
- Authorization Flow: `default-authorization-flow`
- Redirect URIs:
  ```
  http://localhost:8080/auth/callback
  https://admin.localhost/auth/callback
  ```
- Scopes: `openid email profile rag:admin`
- Access Token Validity: `5 minutes`
- Refresh Token Validity: `30 days`

**Application Settings:**
- Name: `Admin Dashboard`
- Slug: `admin-dashboard`
- Provider: Select the provider created above
- Launch URL: `http://localhost:8080`

## Step 4: Record Client Credentials

After creating each provider, record the following information:

### FastAPI Backend
```bash
export FASTAPI_CLIENT_CLIENT_ID="fastapi-client"
export FASTAPI_CLIENT_CLIENT_SECRET="<generated_secret>"
```

### Chat Interface
```bash
export WEBUI_CLIENT_CLIENT_ID="webui-client"
export WEBUI_CLIENT_CLIENT_SECRET="<generated_secret>"
```

### Workflow Automation
```bash
export N8N_CLIENT_CLIENT_ID="n8n-client"
export N8N_CLIENT_CLIENT_SECRET="<generated_secret>"
```

### Admin Dashboard
```bash
export ADMIN_CLIENT_CLIENT_ID="admin-client"
export ADMIN_CLIENT_CLIENT_SECRET="<generated_secret>"
```

## Step 5: Update Environment Configuration

Add the client credentials to your `.env` file:

```bash
# OAuth2 Client Credentials
FASTAPI_OAUTH_CLIENT_ID=fastapi-client
FASTAPI_OAUTH_CLIENT_SECRET=<fastapi_secret>

WEBUI_OAUTH_CLIENT_ID=webui-client
WEBUI_OAUTH_CLIENT_SECRET=<webui_secret>

N8N_OAUTH_CLIENT_ID=n8n-client
N8N_OAUTH_CLIENT_SECRET=<n8n_secret>

ADMIN_OAUTH_CLIENT_ID=admin-client
ADMIN_OAUTH_CLIENT_SECRET=<admin_secret>

# Authentik Configuration
AUTHENTIK_URL=https://auth.localhost
AUTHENTIK_ISSUER=https://auth.localhost/application/o/default/
```

## Step 6: Test OAuth2 Flows

### Test URLs:
- **Authorization Endpoint**: `https://localhost:9443/application/o/authorize/`
- **Token Endpoint**: `https://localhost:9443/application/o/token/`
- **User Info Endpoint**: `https://localhost:9443/application/o/userinfo/`
- **JWKS Endpoint**: `https://localhost:9443/application/o/default/jwks/`

### Test Authorization Flow:
```bash
# Example authorization URL for FastAPI
https://localhost:9443/application/o/authorize/?response_type=code&client_id=fastapi-client&redirect_uri=http://localhost:8000/auth/callback&scope=openid%20email%20profile%20rag:api&state=random_state_string
```

## Step 7: Verify Setup

1. **Check Applications**: Go to Applications > Applications and verify all 4 applications are listed
2. **Check Providers**: Go to Applications > Providers and verify all 4 OAuth2 providers are listed
3. **Check Scopes**: Go to Applications > Providers > OAuth2/OpenID Scopes and verify custom scopes exist
4. **Test Login**: Try accessing each application's authorization URL

## Network Isolation Considerations

With the implemented network isolation:
- Authentik runs in the `zoi_auth` network (172.23.0.0/24)
- FastAPI can access Authentik through the `zoi_backend` network connection
- Frontend services access Authentik through the `zoi_frontend` network connection
- All OAuth2 flows work across network boundaries through the multi-network gateway configuration

## Troubleshooting

### Common Issues:
1. **SSL Certificate Errors**: Use `-k` flag with curl or accept certificate in browser
2. **Network Connectivity**: Ensure services are on the correct Docker networks
3. **Token Validation**: Check that client secrets are correctly copied
4. **Redirect URI Mismatch**: Ensure redirect URIs exactly match the configured values

### Verification Commands:
```bash
# Test Authentik accessibility
curl -k https://localhost:9443/application/o/default/.well-known/openid_configuration

# Check Docker networks
docker network ls | grep zoi

# Verify service connectivity
docker exec zoi-fastapi-1-1 curl -k https://zoi-authentik-server-1:9000/application/o/default/.well-known/openid_configuration
```

## Next Steps

After completing this setup:
1. Implement OAuth2 client code in FastAPI
2. Configure Open WebUI for Authentik authentication
3. Set up n8n OAuth2 integration
4. Test end-to-end authentication flows
5. Implement JWT token validation across services
