# 🔑 Master Credentials Reference Card

## Critical Login Credentials

### Authentik Bootstrap Admin
```
URL: http://localhost:9000/if/admin/
Username: admin@localhost
Password: change-me-authentik-admin
```

### Database Credentials  
```
Host: postgres (Docker) / localhost:5432 (external)
Database: authentik
Username: postgres  
Password: secretpass (from PG_PASS environment variable)
```

### Redis Credentials
```
Host: redis (Docker) / localhost:6379 (external)
Password: change-me-redis-pass (from REDIS_PASSWORD environment variable)
```

---

## 🧪 Playwright Test Selectors

### Correct Field Selectors (Updated 2025)
```javascript
// Username field (CAMELCASE - critical!)
'input[name="uidField"]'

// Password field  
'input[id="ak-stage-password-input"]'

// Submit button
'button[type="submit"]'
```

### Test Credentials
```javascript
const credentials = {
  username: 'admin@localhost',
  password: 'change-me-authentik-admin'
};
```

---

## 🌐 Service URLs

### Development URLs
```bash
Authentik Admin:    http://localhost:9000/if/admin/
Authentik API:      http://localhost:9000/api/v3/
Traefik Dashboard:  http://localhost:8080  
Dashy (Direct):     http://localhost:4001
Dashy (via Auth):   http://dashy.localhost
```

### Production URLs (when using real domain)
```bash
Authentik:          https://auth.yourdomain.com
Dashy:              https://dashy.yourdomain.com  
Traefik:            https://traefik.yourdomain.com
```

---

## 🔧 API Token Creation

### Manual Token Creation (Bootstrap Method)
1. Login to Authentik admin: `http://localhost:9000/if/admin/`
2. Username: `admin@localhost`
3. Password: `change-me-authentik-admin`
4. Go to: `Directory > Tokens & App passwords`
5. Create new token: `init-script-token`
6. Copy token for API calls

### System Settings to Configure
```json
{
  "authentik_host": "http://localhost:9000",
  "authentik_host_browser": "http://localhost:9000"
}
```

---

## ⚠️ Common Credential Issues

### Issue: "Invalid credentials" 
**Check:** Are you using `admin@localhost` (not just `admin`)?

### Issue: "User not found"
**Check:** Is `AUTHENTIK_BOOTSTRAP_EMAIL=admin@localhost` set correctly?

### Issue: Playwright can't find username field
**Check:** Using `input[name="uidField"]` (camelCase, not snake_case)?

### Issue: Password field not filling
**Check:** Using `input[id="ak-stage-password-input"]` selector?

### Issue: `0.0.0.0:9000` redirects
**Check:** System Settings configured via API (not just env vars)?

---

## 🚀 Quick Verification Commands

```bash
# Check services are running
docker-compose -f docker-compose.core.yml ps

# Test Authentik login API
curl -X POST "http://localhost:9000/api/v3/flows/executor/default-authentication-flow/" \
  -H "Content-Type: application/json" \
  -d '{"uid_field": "admin@localhost", "password": "change-me-authentik-admin"}'

# Check Dashy direct access
curl -I http://localhost:4001

# Check Traefik routing  
curl -I http://dashy.localhost
```

---

**📋 Copy this for quick reference during testing and deployment!** 