# Basic Auth Setup Guide
## Simple Authentik Forward Auth with Traefik & Dashy

This guide focuses on getting **basic forward authentication** working with Authentik, Traefik, and Dashy - no complex JWT features, just simple SSO.

## 🎯 **Goal: Basic Forward Auth**

```
User → http://dashy.localhost → Traefik → Authentik Login → Back to Dashy
```

## 🔑 **Core Credentials (Keep It Simple)**

### Bootstrap Admin Credentials
```bash
URL: http://localhost:9000/if/admin/
Username: admin@localhost
Password: change-me-authentik-admin
```

### Service URLs
```bash
Authentik:    http://localhost:9000
Traefik:      http://localhost:8080
Dashy:        http://localhost:4001 (direct)
Dashy+Auth:   https://dashy.localhost (via forward auth)
```

## 📋 **Simple Setup Process**

### Step 1: Clean Start
```bash
# Complete reset
docker-compose -f docker-compose.core.yml down --volumes --remove-orphans

# Fresh deployment
docker-compose -f docker-compose.core.yml up --build -d

# Verify services
docker-compose -f docker-compose.core.yml ps
```

### Step 2: Access Authentik Admin
1. Go to: `http://localhost:9000/if/admin/`
2. Login: `admin@localhost` / `change-me-authentik-admin`
3. Verify you can access the admin interface

### Step 3: Fix System Settings (CRITICAL)
**This is the key fix for the `0.0.0.0:9000` redirect issue:**

Navigate to: **System → Global Settings**

Set these values:
```
authentik_host: http://localhost:9000
authentik_host_browser: http://localhost:9000
```

### Step 4: Create Forward Auth Application

#### 4.1 Create OAuth2 Provider
1. Go to: **Applications → Providers**
2. Click **Create**
3. Select **OAuth2/OpenID Provider**
4. Configure:
   ```
   Name: Dashy Forward Auth Provider
   Authorization flow: default-authorization-flow
   Client type: Confidential
   Client ID: dashy-client
   Client secret: (auto-generated)
   Redirect URIs: https://dashy.localhost/outpost.goauthentik.io/callback
   ```

#### 4.2 Create Application
1. Go to: **Applications → Applications** 
2. Click **Create**
3. Configure:
   ```
   Name: Dashy
   Slug: dashy
   Provider: (select the provider from step 4.1)
   ```

#### 4.3 Create Forward Auth Outpost
1. Go to: **Applications → Outposts**
2. Click **Create**
3. Select **Proxy Provider**
4. Configure:
   ```
   Name: Forward Auth Outpost
   Type: Proxy
   Applications: [Select Dashy]
   Configuration:
     external_host: http://dashy.localhost
     internal_host: https://dashy:4001
     internal_host_ssl_validation: false
   ```

## 🧪 **Testing Basic Auth**

### Test 1: Direct Access
```bash
# This should work (bypass auth)
curl -I http://localhost:4001
```

### Test 2: Forward Auth Access  
```bash
# This should redirect to Authentik
curl -I https://dashy.localhost
```

### Test 3: Playwright Test (Updated for Basic Auth)
Use your existing Playwright tests with the correct selectors:
```javascript
// Correct field selectors
'input[name="uidField"]'  // Username (camelCase!)
'input[id="ak-stage-password-input"]'  // Password

// Credentials
username: 'admin@localhost'
password: 'change-me-authentik-admin'
```

## ✅ **Simple Verification Checklist**

### Services Running
- [ ] `docker ps` shows all containers healthy
- [ ] Authentik accessible at `http://localhost:9000`
- [ ] Traefik dashboard at `http://localhost:8080`
- [ ] Dashy direct access at `http://localhost:4001`

### Authentication Working
- [ ] Can login to Authentik admin with bootstrap credentials
- [ ] System Settings configured with `localhost:9000` URLs
- [ ] Forward auth application and outpost created
- [ ] `https://dashy.localhost` redirects to Authentik login
- [ ] After login, redirected back to Dashy content
- [ ] **No `0.0.0.0:9000` URLs in redirects** ✅

### Playwright Tests
- [ ] Tests use correct field selectors (camelCase `uidField`)
- [ ] Tests use bootstrap credentials (`admin@localhost`)
- [ ] Authentication flow completes successfully

## 🚨 **Common Basic Auth Issues**

### Issue: `0.0.0.0:9000` redirects
**Solution:** Configure System Settings via admin interface (not just env vars)

### Issue: "Application not found"
**Solution:** Ensure outpost is properly configured with correct internal host

### Issue: Login loop
**Solution:** Check redirect URIs match outpost configuration

### Issue: Traefik not routing
**Solution:** Verify docker labels on dashy service match outpost config

## 🔧 **Basic Auth Configuration Files**

### Current Configuration Status:
- ✅ `config/authentik/authentik.env` - Basic configuration (no complex JWT)
- ✅ `docker-compose.core.yml` - Service definitions
- ✅ Traefik labels on Dashy service
- ✅ Bootstrap credentials configured

### What You DON'T Need for Basic Auth:
- ❌ Complex JWT validation
- ❌ Token encryption
- ❌ FastAPI middleware
- ❌ JWKS endpoints
- ❌ Scope-based authorization
- ❌ Rate limiting (beyond basic)

## 🎯 **Success Criteria**

**You'll know basic auth is working when:**
1. `https://dashy.localhost` redirects to Authentik login
2. Login with `admin@localhost` / `change-me-authentik-admin` works
3. After login, you see Dashy content (not Authentik page)
4. No `0.0.0.0:9000` URLs appear anywhere
5. Playwright tests can complete the auth flow

## 🚀 **Next Steps After Basic Auth Works**

Once basic forward auth is working:
1. Add more users/groups in Authentik
2. Test with different applications
3. Consider adding OAuth2 applications (optional)
4. **Later**: Implement advanced JWT security if needed

**Keep it simple first - get the basic flow working before adding complexity!** 