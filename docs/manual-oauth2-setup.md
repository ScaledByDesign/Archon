# Manual OAuth2 Application Setup in Authentik

## Overview
This guide walks you through manually creating the OAuth2 application in Authentik for the FastAPI integration.

## Prerequisites
- Authentik is running and accessible at https://zoi.local:9443
- You have admin access to Authentik
- FastAPI service is configured with OAuth2 environment variables

## Step 1: Access Authentik Admin Interface

1. Open your browser and navigate to: https://zoi.local:9443/if/admin/
2. If you see a certificate warning, accept it (this is expected for local development)
3. Log in with the admin credentials (check your Authentik configuration for default credentials)

## Step 2: Create OAuth2 Provider

1. In the Authentik admin interface, navigate to **Applications** → **Providers**
2. Click **Create** and select **OAuth2/OpenID Provider**
3. Configure the provider with these settings:

### Basic Settings
- **Name**: `FastAPI OAuth2 Provider`
- **Authentication flow**: `default-authentication-flow` (or your preferred flow)
- **Authorization flow**: `default-provider-authorization-explicit-consent`

### OAuth2 Settings
- **Client type**: `Confidential`
- **Client ID**: `fastapi-client` (must match FASTAPI_OAUTH_CLIENT_ID)
- **Client Secret**: Generate a new secret (copy this for later use)
- **Redirect URIs**: `http://zoi.local:8000/api/auth/callback`

### Advanced Settings
- **Scopes**: `openid email profile rag:api`
- **Subject mode**: `Based on the User's hashed ID`
- **Include claims in id_token**: ✅ Enabled

4. Click **Create** to save the provider

## Step 3: Create Application

1. Navigate to **Applications** → **Applications**
2. Click **Create**
3. Configure the application:

### Basic Settings
- **Name**: `FastAPI RAG System`
- **Slug**: `fastapi-rag`
- **Provider**: Select the provider you just created (`FastAPI OAuth2 Provider`)

### UI Settings
- **Launch URL**: `http://zoi.local:8000`
- **Icon**: (optional)

4. Click **Create** to save the application

## Step 4: Update FastAPI Configuration

1. Copy the **Client Secret** from the OAuth2 provider you created
2. Update the environment variable in your `.env` file:
   ```
   FASTAPI_OAUTH_CLIENT_SECRET=<your-actual-client-secret>
   ```
3. Restart the FastAPI service:
   ```bash
   docker-compose restart fastapi-1
   ```

## Step 5: Test the Integration

1. Test the OAuth2 status:
   ```bash
   curl -s http://zoi.local:8000/api/auth/status | jq .
   ```
   Should return: `"oauth_configured": true`

2. Test the login flow:
   ```bash
   curl -v http://zoi.local:8000/api/auth/login
   ```
   Should redirect to Authentik authorization page

3. Complete the flow by opening in browser:
   ```
   http://zoi.local:8000/api/auth/login
   ```

## Step 6: Verify Complete Flow

1. Open `http://zoi.local:8000/api/auth/login` in your browser
2. You should be redirected to Authentik
3. Log in with your Authentik credentials
4. Grant permissions to the application
5. You should be redirected back to the FastAPI callback endpoint
6. Check that you're authenticated:
   ```bash
   curl -s http://zoi.local:8000/api/auth/me
   ```

## Troubleshooting

### Common Issues

1. **"OAuth2 not configured" error**
   - Check that all environment variables are set correctly
   - Restart the FastAPI service after updating environment variables

2. **"Invalid client" error**
   - Verify the client ID matches between Authentik and FastAPI configuration
   - Check that the redirect URI is exactly the same in both places

3. **"Invalid redirect URI" error**
   - Ensure the redirect URI in Authentik includes the full URL: `http://zoi.local:8000/api/auth/callback`
   - Check for trailing slashes or typos

4. **Certificate errors**
   - For local development, you may need to accept self-signed certificates
   - Consider using HTTP for local testing if HTTPS causes issues

### Logs to Check

- FastAPI logs: `docker-compose logs fastapi-1`
- Authentik logs: `docker-compose logs authentik-server`

## Security Notes

- The client secret should be kept secure and not committed to version control
- In production, use proper HTTPS certificates
- Consider using environment-specific client IDs and secrets
- Regularly rotate client secrets

## Next Steps

After successful setup:
1. Test user authentication and authorization
2. Implement proper user session management
3. Add role-based access control if needed
4. Configure additional OAuth2 scopes as required
