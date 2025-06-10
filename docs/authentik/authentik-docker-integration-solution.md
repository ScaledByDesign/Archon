# 🎯 Authentik + Traefik Docker Integration - Complete Solution

## 🚨 The Core Problem

When using Authentik forward authentication with Traefik in Docker, Authentik returns redirect URLs with internal Docker hostnames (e.g., `http://authentik-server:9000/flows/...`) instead of external browser-accessible URLs (e.g., `https://auth.localhost/flows/...`). This causes "site cannot be reached" errors in browsers.

## ✅ Root Cause & Solution

### **Root Cause:**
- Authentik doesn't know its external hostname when generating redirects
- Docker internal service names are used instead of public domain names
- Missing environment variables that tell Authentik how it's accessed externally

### **Solution Strategy:**
1. **Environment Variables**: Tell Authentik its external hostname
2. **Middleware Headers**: Ensure Traefik forwards proper host information
3. **Application Endpoint**: Use `/application/o/` not `/outpost/` for forward auth
4. **Proxy Provider Configuration**: Set external_host correctly in Authentik admin

---

## 🔧 Complete Configuration

### **1. Authentik Environment Variables (.env)**

```bash
# CRITICAL: External hostname configuration for proper redirects
AUTHENTIK_DEFAULT__BASE_URL=https://auth.localhost
AUTHENTIK_HOST_BROWSER=https://auth.localhost
AUTHENTIK_URL=https://auth.localhost

# Host configuration for proper external access
AUTHENTIK_HOST=https://auth.localhost
AUTHENTIK_EXTERNAL_HOST=https://auth.localhost

# Standard config
AUTHENTIK_LISTEN__HTTPS=0.0.0.0:9443
AUTHENTIK_LISTEN__HTTP=0.0.0.0:9000
```

### **2. Traefik Middleware Configuration**

```yaml
http:
  middlewares:
    # Optimized Authentik Forward Auth
    authentik-forward-auth:
      forwardAuth:
        address: "http://authentik-server:9000/application/o/traefik-forward-auth/"
        trustForwardHeader: true
        authRequestHeaders:
          - "Accept"
          - "Authorization" 
          - "Content-Type"
          - "X-Forwarded-For"
          - "X-Forwarded-Proto"
          - "X-Forwarded-Host"
          - "X-Forwarded-Uri"
          - "X-Forwarded-Method"
          - "X-Forwarded-Port"
          - "X-Real-IP"
          - "Host"
        authResponseHeaders:
          - "X-authentik-username"
          - "X-authentik-groups" 
          - "X-authentik-email"
          - "X-authentik-name"
          - "X-authentik-uid"
          - "X-authentik-jwt"
          - "Authorization"

    # External hostname headers
    authentik-external-headers:
      headers:
        customRequestHeaders:
          X-Forwarded-Proto: "https"
          X-Forwarded-Host: "auth.localhost"
          X-Forwarded-Port: "443"
          X-Original-URL: "https://auth.localhost"

    # Production-ready chain
    authentik-secure:
      chain:
        middlewares:
          - authentik-external-headers
          - authentik-forward-auth
          - secure-headers
```

### **3. Service Labels (Docker Compose)**

```yaml
services:
  protected-service:
    image: your-service
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.service.rule=Host(`service.localhost`)"
      - "traefik.http.routers.service.middlewares=authentik-secure@file"
      - "traefik.http.routers.service.tls=true"
```

---

## 🏗️ Authentik Admin Configuration

### **1. Create Proxy Provider**
1. Go to **Applications** → **Providers** → **Create**
2. Select **Proxy Provider**
3. Configuration:
   - **Name**: `Traefik Forward Auth`
   - **Authorization flow**: `default-provider-authorization-explicit-consent`
   - **Mode**: `Forward auth (domain level)`
   - **External host**: `https://auth.localhost` (CRITICAL!)
   - **Cookie domain**: `localhost`

### **2. Create Application** 
1. Go to **Applications** → **Applications** → **Create**
2. Configuration:
   - **Name**: `Traefik Forward Auth`
   - **Slug**: `traefik-forward-auth` (MUST match middleware URL)
   - **Provider**: Select the proxy provider created above

### **3. Assign to Outpost**
1. Go to **Applications** → **Outposts**
2. Edit **authentik Embedded Outpost**
3. Add your application to **Selected applications**

---

## 🧪 Testing & Verification

### **1. Check Service Status**
```bash
docker-compose ps traefik authentik-server
curl -I http://localhost:9000/application/o/traefik-forward-auth/
```

### **2. Test Forward Auth**
```bash
# Should return 302 redirect to https://auth.localhost (NOT internal hostname)
curl -k -I https://protected-service.localhost
```

### **3. Verify Headers**
```bash
# Check that proper headers are being forwarded
curl -k -v https://protected-service.localhost 2>&1 | grep -i location
```

---

## 🚀 Key Success Factors

### **✅ What Works:**
- Use `/application/o/traefik-forward-auth/` endpoint
- Set ALL external hostname environment variables
- Forward proper `X-Forwarded-*` headers
- Configure proxy provider with correct external_host

### **❌ Common Mistakes:**
- Using `/outpost/` endpoint (causes 404s)
- Missing `AUTHENTIK_HOST_BROWSER` environment variable
- Not setting external_host in proxy provider
- Applying authentik middleware to authentik service itself (circular dependency)

---

## 🛡️ Security Considerations

1. **Keep Traefik Dashboard Open**: Don't apply authentik middleware to Traefik dashboard
2. **Use HTTPS**: Configure proper TLS certificates for production
3. **Cookie Security**: Set proper cookie domain and secure flags
4. **Headers**: Ensure sensitive headers are properly handled

---

## 📋 Troubleshooting Checklist

- [ ] Environment variables set in authentik .env
- [ ] Proxy provider configured with external_host
- [ ] Application slug matches middleware URL path
- [ ] Services are running and healthy
- [ ] No circular middleware dependencies
- [ ] Proper X-Forwarded headers configured
- [ ] DNS resolution works for *.localhost domains

## 🎉 Result

With this configuration, Authentik will generate redirects using `https://auth.localhost` instead of internal Docker hostnames, resolving the browser "site cannot be reached" errors and providing seamless authentication flow.
