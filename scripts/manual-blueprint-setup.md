# Manual Authentik Blueprint Setup Guide

Since we're in a development environment, we'll apply the blueprints manually through the Authentik web interface.

## Step 1: Add Local DNS Entry

Add the following line to your `/etc/hosts` file:

```bash
127.0.0.1 auth.localhost
```

You can do this by running:
```bash
echo "127.0.0.1 auth.localhost" | sudo tee -a /etc/hosts
```

## Step 2: Access Authentik Admin Interface

1. Open your browser and navigate to: `https://localhost:9443/if/admin/`
2. Accept the self-signed certificate warning
3. Login with:
   - **Email**: `admin@localhost` (from AUTHENTIK_BOOTSTRAP_EMAIL)
   - **Password**: `change-me-authentik-admin` (from AUTHENTIK_BOOTSTRAP_PASSWORD)

## Step 3: Apply Blueprints in Order

Navigate to **System** → **Blueprints** and apply the following blueprints in this exact order:

### 3.1 OAuth2 Flows (`oauth2-flows.yaml`)
- Click **Create** → **Import Blueprint**
- Upload: `config/authentik/blueprints/oauth2-flows.yaml`
- Click **Create** to apply

### 3.2 OAuth2 Scopes (`oauth2-scopes.yaml`)
- Upload: `config/authentik/blueprints/oauth2-scopes.yaml`
- Click **Create** to apply

### 3.3 Users and Groups (`users.yaml`)
- Upload: `config/authentik/blueprints/users.yaml`
- Click **Create** to apply

### 3.4 Applications (`applications.yaml`)
- Upload: `config/authentik/blueprints/applications.yaml`
- Click **Create** to apply

### 3.5 Access Policies (`access-policies.yaml`)
- Upload: `config/authentik/blueprints/access-policies.yaml`
- Click **Create** to apply

## Step 4: Verify Blueprint Application

After applying all blueprints, verify the following:

### Applications Created
Navigate to **Applications** → **Applications**
You should see:
- FastAPI Backend
- Chat Interface  
- Workflow Automation

### OAuth2 Providers Created
Navigate to **Applications** → **Providers**
You should see:
- fastapi-oauth2
- webui-oauth2
- n8n-oauth2

### Custom Scopes Created
Navigate to **Applications** → **Scopes**
You should see:
- rag:api
- rag:chat
- rag:workflow

### Users and Groups Created
Navigate to **Directory** → **Users**
You should see:
- admin (superuser)
- user (regular user)

Navigate to **Directory** → **Groups**
You should see:
- admins
- users

## Step 5: Extract Client Secrets

For each OAuth2 provider, you'll need to extract the client secrets:

1. Go to **Applications** → **Providers**
2. Click on each provider (fastapi-oauth2, webui-oauth2, n8n-oauth2)
3. Copy the **Client Secret** value
4. Update the corresponding environment variable in `.env`

Example:
```bash
FASTAPI_OAUTH_CLIENT_SECRET=<copied-secret-from-fastapi-oauth2>
WEBUI_OAUTH_CLIENT_SECRET=<copied-secret-from-webui-oauth2>
N8N_OAUTH_CLIENT_SECRET=<copied-secret-from-n8n-oauth2>
```

## Step 6: Test Access

After blueprint application, test access to:
- **OAuth2 Well-known Configuration**: `https://localhost:9443/application/o/fastapi-oauth2/.well-known/openid_configuration`
- **User Info Endpoint**: `https://localhost:9443/application/o/userinfo/`

## Troubleshooting

### Blueprint Import Fails
- Check blueprint syntax with: `./scripts/validate-blueprints.sh`
- Ensure dependencies are applied in correct order
- Check Authentik logs: `docker-compose logs authentik-server`

### Provider Not Created
- Verify blueprint application completed successfully
- Check for error messages in System → Events
- Restart Authentik services if needed: `docker-compose restart authentik-server authentik-worker`

### Client Secret Not Visible
- Ensure you're logged in as a superuser
- Check permissions for the admin user
- Verify the provider was created successfully

## Next Steps

After completing this setup:
1. Update `.env` file with actual client secrets
2. Test OAuth2 flows with each application
3. Configure redirect URIs for production domains
4. Set up additional identity providers (optional)
