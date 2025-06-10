# Master Configuration Guide - Authentik/Traefik/Dashy Setup

## 🔑 Core Credentials & Settings

### Bootstrap Admin Credentials
**These are the FIRST admin credentials created during Authentik initialization:**
```bash
AUTHENTIK_BOOTSTRAP_EMAIL=admin@localhost
AUTHENTIK_BOOTSTRAP_PASSWORD=change-me-authentik-admin
```

### Database Credentials
```bash
POSTGRES_USER=authentik
POSTGRES_PASSWORD=postgres-password
POSTGRES_DB=authentik
```

### Authentik Core Settings
```bash
AUTHENTIK_SECRET_KEY=your-secret-key-here-minimum-32-chars
AUTHENTIK_HOST=http://localhost:9000
AUTHENTIK_HOST_BROWSER=http://localhost:9000
AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS=172.16.0.0/12,10.0.0.0/8,192.168.0.0/16
```

---

## 📋 Step-by-Step Configuration Process

### Phase 1: Environment Setup

1. **Create/Update `config/authentik/authentik.env`:**
```env
# Database Configuration
POSTGRES_USER=authentik
POSTGRES_PASSWORD=postgres-password
POSTGRES_DB=authentik

# Authentik Core Configuration
AUTHENTIK_SECRET_KEY=your-secret-key-here-minimum-32-chars-long-and-secure
AUTHENTIK_HOST=http://localhost:9000
AUTHENTIK_HOST_BROWSER=http://localhost:9000

# Bootstrap Admin User (CRITICAL - Creates first admin)
AUTHENTIK_BOOTSTRAP_EMAIL=admin@localhost
AUTHENTIK_BOOTSTRAP_PASSWORD=change-me-authentik-admin

# Network & Security
AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS=172.16.0.0/12,10.0.0.0/8,192.168.0.0/16
AUTHENTIK_LISTEN__HTTP=0.0.0.0:9000

# Performance & Security
AUTHENTIK_LOG_LEVEL=info
AUTHENTIK_AVATARS=gravatar,initials
AUTHENTIK_FOOTER_LINKS='[{"name": "Documentation", "href": "https://docs.goauthentik.io/"}]'

# Error Reporting
AUTHENTIK_ERROR_REPORTING__ENABLED=false
AUTHENTIK_ERROR_REPORTING__SEND_PII=false

# Cache Configuration
AUTHENTIK_REDIS__CACHE_TIMEOUT=300
AUTHENTIK_REDIS__CACHE_TIMEOUT_FLOWS=300
AUTHENTIK_REDIS__CACHE_TIMEOUT_POLICIES=300

# Email Configuration (Optional)
AUTHENTIK_EMAIL__HOST=localhost
AUTHENTIK_EMAIL__PORT=587
AUTHENTIK_EMAIL__USE_TLS=true
AUTHENTIK_EMAIL__FROM=authentik@localhost
```

2. **Create/Update `.env` (root directory):**
```env
DOMAIN=localhost
AUTHENTIK_SECRET_KEY=your-secret-key-here-minimum-32-chars-long-and-secure
```

### Phase 2: Docker Deployment

3. **Clean Deployment:**
```bash
# Stop and remove everything
docker-compose -f docker-compose.core.yml down --volumes --remove-orphans

# Start fresh
docker-compose -f docker-compose.core.yml up --build -d

# Wait for services to be healthy (30-60 seconds)
docker-compose -f docker-compose.core.yml ps
```

4. **Verify Service Health:**
```bash
# All should show "healthy" or "running"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Phase 3: Authentik Configuration

5. **Access Authentik Admin Interface:**
   - URL: `http://localhost:9000/if/admin/`
   - Username: `admin@localhost`
   - Password: `change-me-authentik-admin`

6. **Configure System Settings (CRITICAL):**
   Navigate to: `System > Global Settings`
   ```
   authentik_host: http://localhost:9000
   authentik_host_browser: http://localhost:9000
   ```

7. **Create API Token:**
   - Go to `Directory > Tokens & App passwords`
   - Create new token with identifier: `init-script-token`
   - Copy the token value for API calls

### Phase 4: OAuth Application Setup

8. **Create OAuth Application:**
   - Go to `Applications > Applications`
   - Create new application:
     ```
     Name: Dashy
     Slug: dashy
     Provider: Create new OAuth2/OpenID Provider
     ```

9. **Configure OAuth Provider:**
   ```
   Name: Dashy OAuth Provider
   Client ID: dashy-client-id
   Client Secret: dashy-client-secret
   Redirect URIs: http://dashy.localhost/auth/callback
   Signing Key: (auto-generated)
   ```

### Phase 5: Forward Auth Configuration

10. **Create Forward Auth Outpost:**
    - Go to `Applications > Outposts`
    - Create new outpost:
      ```
      Name: Forward Auth Outpost
      Type: Proxy
      Applications: [Select Dashy]
      Configuration:
        external_host: http://dashy.localhost
        internal_host: http://dashy:4001
      ```

---

## 🧪 Testing Configuration

### Playwright Test Credentials
```javascript
// Use these exact credentials in tests
const credentials = {
  username: 'admin@localhost',  // AUTHENTIK_BOOTSTRAP_EMAIL
  password: 'change-me-authentik-admin'  // AUTHENTIK_BOOTSTRAP_PASSWORD
};

// Correct field selectors
const selectors = {
  usernameField: 'input[name="uidField"]',  // Note: camelCase
  passwordField: 'input[id="ak-stage-password-input"]',
  loginButton: 'button[type="submit"]'
};
```

### Test URLs
```bash
# Service endpoints
Authentik Admin: http://localhost:9000/if/admin/
Authentik API: http://localhost:9000/api/v3/
Traefik Dashboard: http://localhost:8080
Dashy Direct: http://localhost:4001
Dashy via Traefik: http://dashy.localhost
```

---

## 🔧 API Configuration Commands

### Get Admin Token (after manual login)
```bash
# Using bootstrap credentials
curl -X POST "http://localhost:9000/api/v3/core/tokens/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_MANUAL_TOKEN" \
  -d '{
    "identifier": "init-script-token",
    "description": "Token for initialization script",
    "expires": null
  }'
```

### Set System Settings via API
```bash
# Set authentik_host
curl -X PATCH "http://localhost:9000/api/v3/core/global-settings/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"authentik_host": "http://localhost:9000"}'

# Set authentik_host_browser
curl -X PATCH "http://localhost:9000/api/v3/core/global-settings/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"authentik_host_browser": "http://localhost:9000"}'
```

---

## ✅ Verification Checklist

### After Deployment
- [ ] All containers are healthy (`docker ps`)
- [ ] Authentik accessible at `http://localhost:9000`
- [ ] Can login with `admin@localhost` / `change-me-authentik-admin`
- [ ] Traefik dashboard accessible at `http://localhost:8080`
- [ ] Dashy accessible directly at `http://localhost:4001`

### After Authentik Configuration
- [ ] System Settings configured with correct localhost URLs
- [ ] OAuth application created for Dashy
- [ ] Forward auth outpost configured
- [ ] API token created and working

### After Integration
- [ ] `http://dashy.localhost` redirects to Authentik login
- [ ] Can authenticate with bootstrap credentials
- [ ] After auth, redirected back to Dashy content
- [ ] No `0.0.0.0:9000` URLs in redirects

---

## 🚨 Common Issues & Solutions

### Issue: `0.0.0.0:9000` in redirects
**Solution:** Ensure System Settings are configured via API, not just environment variables.

### Issue: Playwright tests fail on field selectors
**Solution:** Use correct selectors:
- Username: `input[name="uidField"]` (camelCase)
- Password: `input[id="ak-stage-password-input"]`

### Issue: Admin token creation fails
**Solution:** Bootstrap user must exist. Check `AUTHENTIK_BOOTSTRAP_EMAIL` and `AUTHENTIK_BOOTSTRAP_PASSWORD` are set correctly.

### Issue: Dashy shows Authentik page instead of content
**Solution:** Check forward auth outpost configuration and Traefik middleware setup.

---

## 📝 Notes

- **Environment variables are overridden by System Settings in Authentik 2025.x**
- **Bootstrap credentials only work on fresh installations**
- **System Settings MUST be configured via API or admin interface**
- **Always use `localhost:9000`, never `0.0.0.0:9000` in production**
- **Traefik labels must match the exact service configuration**

---

## 🔄 Quick Reset Commands

```bash
# Complete reset
docker-compose -f docker-compose.core.yml down --volumes --remove-orphans
docker system prune -f
docker volume prune -f

# Fresh start
docker-compose -f docker-compose.core.yml up --build -d

# Wait and verify
sleep 30 && docker-compose -f docker-compose.core.yml ps
```

This configuration ensures consistent, reproducible deployments with correct credentials from the start. 