# Manual API Token Creation for Authentik

Since the automated token creation is having issues with the modern SPA interface, here's how to manually create an API token:

## Steps:

1. **Open Authentik Admin Interface**:
   ```
   https://localhost:9443/if/admin/
   ```

2. **Login with admin credentials**:
   - Username: `akadmin`
   - Password: `change-me-authentik-admin`

3. **Navigate to Tokens**:
   - Go to `System` → `Tokens`
   - Or directly: https://localhost:9443/if/admin/#/core/tokens

4. **Create New Token**:
   - Click "Create" button
   - Set the following:
     - **Identifier**: `automation-token`
     - **Description**: `API token for OAuth2 automation`
     - **User**: Select `akadmin` (or leave as current user)
     - **Intent**: `API`
     - **Expiring**: Leave unchecked (no expiration)

5. **Copy the Token**:
   - After creation, copy the generated token key
   - It will look something like: `aksk_1234567890abcdef...`

6. **Add to Environment**:
   ```bash
   echo "AUTHENTIK_API_TOKEN=your_copied_token_here" >> .env
   ```

7. **Run OAuth2 Application Creation**:
   ```bash
   python scripts/auto-create-oauth2-app.py
   ```

## Alternative: Use the Simplified Script

I'll create a simplified version that just needs the API token.
