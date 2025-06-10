# 🚀 AUTHENTIK QUICK SETUP - FIX BAD GATEWAY

## ✅ GOOD NEWS: Hostname redirect is FIXED!
- ❌ Before: Redirected to `http://authentik-server:9000`
- ✅ Now: Redirects to `https://auth.localhost`

## 🎯 CURRENT ISSUE: Application doesn't exist
**Bad Gateway** = The application `/application/o/traefik-forward-auth/` doesn't exist in Authentik yet.

---

## 🔧 QUICK FIX (2 minutes):

### 1. Access Authentik Admin
Open browser: **http://localhost:9000/if/admin/**
Login: `admin` / `admin123!`

### 2. Create Proxy Provider
- Applications → Providers → Create
- **Type**: Proxy Provider
- **Name**: `Traefik Forward Auth`
- **Mode**: `Forward auth (domain level)` ⭐
- **External host**: `https://auth.localhost` ⭐
- **Save**

### 3. Create Application
- Applications → Applications → Create  
- **Name**: `Traefik Forward Auth`
- **Slug**: `traefik-forward-auth` ⭐ (CRITICAL - matches URL)
- **Provider**: Select the provider from step 2
- **Save**

### 4. Assign to Outpost
- Applications → Outposts → Edit "authentik Embedded Outpost"
- **Selected applications**: Add your application
- **Save**

---

## 🧪 VERIFICATION

After setup, test again:
```bash
curl -k -I https://dashy.localhost
# Should now redirect to login page (not bad gateway)
```

---

## 📋 ALTERNATIVE: REST API SETUP

If you prefer automated setup:

```bash
# Get admin token first
AUTH_TOKEN=$(curl -s -X POST http://localhost:9000/api/v3/core/tokens/ \
  -H "Content-Type: application/json" \
  -d '{"identifier": "admin", "password": "admin123!"}' | jq -r .token)

# Create provider
curl -X POST http://localhost:9000/api/v3/providers/proxy/ \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Traefik Forward Auth",
    "mode": "forward_domain",
    "external_host": "https://auth.localhost"
  }'

# Get provider ID and create application
# (Additional API calls needed...)
```

**Recommendation**: Use the web interface - it's faster and more reliable for initial setup! 🎯
