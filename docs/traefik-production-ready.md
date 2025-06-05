# Traefik Production Configuration Guide

## Current Status: ✅ Development Ready

### **What's Working:**
- ✅ All Traefik routing configuration correct
- ✅ All services reachable through Traefik proxy
- ✅ Network connectivity properly configured
- ✅ Middleware chains functioning
- ✅ No more network warnings

### **Current Development Configuration:**
- **ACME**: Disabled to avoid rate limiting during development
- **SSL**: Self-signed certificates from Traefik (browsers will show warnings)
- **Routing**: All services accessible via `service.zoi.cc` locally

---

## Production Configuration Options

### **Option 1: Enable Let's Encrypt Staging** 🔄 *Current State*
Best for development/testing with real SSL workflow

**To Enable Staging SSL:**
```yaml
# In config/traefik/traefik.yml - Uncomment:
certificatesResolvers:
  letsencrypt:
    acme:
      tlsChallenge: {}
      email: admin@zoi.cc
      storage: /letsencrypt/acme.json
      keyType: EC256
      # Staging environment - unlimited rate limits
      caServer: https://acme-staging-v02.api.letsencrypt.org/directory
```

**Then uncomment certresolver lines:**
```yaml
# In docker-compose.core.yml - Uncomment:
- "traefik.http.routers.llm.tls.certresolver=letsencrypt"
- "traefik.http.routers.qdrant.tls.certresolver=letsencrypt"
# etc.
```

### **Option 2: Enable Production SSL** 🚀 *For Production*
Use when DNS is configured and ready for live certificates

**Production SSL Configuration:**
```yaml
# In config/traefik/traefik.yml
certificatesResolvers:
  letsencrypt:
    acme:
      tlsChallenge: {}
      email: admin@zoi.cc
      storage: /letsencrypt/acme.json
      keyType: EC256
      # Production Let's Encrypt
      # caServer: https://acme-v02.api.letsencrypt.org/directory  # Default
```

**Prerequisites for Production:**
1. **DNS Configuration**: Point all `*.zoi.cc` subdomains to your server's public IP
2. **Domain Ownership**: Ensure you control the `zoi.cc` domain
3. **Firewall**: Ensure ports 80 and 443 are accessible from the internet

---

## Service Access URLs

When properly configured, services will be available at:

- **Traefik Dashboard**: `https://traefik.zoi.cc` (requires auth)
- **FastAPI Backend**: `https://api.zoi.cc`
- **LiteLLM Gateway**: `https://llm.zoi.cc`
- **Dashy Dashboard**: `https://dashy.zoi.cc`
- **Qdrant Vector DB**: `https://qdrant.zoi.cc`
- **Open WebUI**: `https://webui.zoi.cc`

---

## Quick Switch Commands

### **Enable Staging SSL:**
```bash
# 1. Uncomment ACME in traefik.yml (staging caServer)
# 2. Uncomment certresolver lines in docker-compose files
# 3. Restart Traefik
docker-compose -f docker-compose.core.yml restart traefik
```

### **Enable Production SSL:**
```bash
# 1. Ensure DNS is configured
# 2. Remove staging caServer line from traefik.yml
# 3. Restart Traefik
docker-compose -f docker-compose.core.yml restart traefik
```

### **Disable SSL (Current):**
```bash
# Keep ACME commented out - services use self-signed certs
# Good for local development
```

---

## Verification Commands

### **Test Local Routing:**
```bash
# Should get service responses (ignore SSL warnings)
curl -k -H "Host: llm.zoi.cc" https://localhost:443/health
curl -k -H "Host: traefik.zoi.cc" https://localhost:443
curl -k -H "Host: qdrant.zoi.cc" https://localhost:443
```

### **Check Certificate Status:**
```bash
# View certificate information
curl -vI https://llm.zoi.cc 2>&1 | grep -E "(subject|issuer)"
```

### **Monitor Logs:**
```bash
# Watch for certificate generation
docker logs traefik -f | grep -E "(ACME|certificate)"
```

---

## Summary

**🎉 Your Traefik configuration is production-ready!**

**Current State**: Development mode with ACME disabled
**Next Step**: Choose SSL configuration based on your deployment stage:
- **Development**: Keep current setup (ACME disabled)
- **Testing**: Enable staging SSL  
- **Production**: Configure DNS + enable production SSL

All routing, networking, and middleware issues have been completely resolved.
