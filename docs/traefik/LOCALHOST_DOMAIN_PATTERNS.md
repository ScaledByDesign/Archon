# zoi.local Domain Patterns for Development

## ⚠️ **CRITICAL: Never Replace (sub).zoi.local with just zoi.local**

When working with local development using `*.zoi.local` domains, **NEVER** replace subdomain patterns like `auth.zoi.local`, `dashy.zoi.local`, etc. with just `zoi.local`. This causes false redirect loops and breaks service routing.

## ✅ **Correct Domain Patterns**

### Environment Configuration
```bash
# .env file
DOMAIN=zoi.local

# Services use pattern: {service}.${DOMAIN:-zoi.local}
# Results in: auth.zoi.local, dashy.zoi.local, qdrant.zoi.local, etc.
```

### Traefik Router Rules
```yaml
# ✅ CORRECT - Uses subdomain pattern
labels:
  - "traefik.http.routers.authentik.rule=Host(`auth.${DOMAIN:-zoi.local}`)"
  - "traefik.http.routers.dashy.rule=Host(`dashy.${DOMAIN:-zoi.local}`)"

# ❌ WRONG - Would break routing
labels:
  - "traefik.http.routers.authentik.rule=Host(`${DOMAIN:-zoi.local}`)"  # NO subdomain
```

### Authentik Configuration
```bash
# ✅ CORRECT - Uses full subdomain
AUTHENTIK_HOST_BROWSER=https://auth.zoi.local
AUTHENTIK_ISSUER=https://auth.zoi.local/application/o/default/

# ❌ WRONG - Missing subdomain
AUTHENTIK_HOST_BROWSER=https://zoi.local  # Would cause redirect loops
```

### Blueprint Configuration
```yaml
# ✅ CORRECT - Matches Traefik routing
external_host: https://auth.zoi.local

# ❌ WRONG - Mismatched domain
external_host: https://zoi.local  # Would cause authentication failures
```

## 🌐 **DNS Resolution in Development**

Modern browsers automatically resolve `*.zoi.local` to `127.0.0.1`:
- `auth.zoi.local` → `127.0.0.1:443` (via Traefik)
- `dashy.zoi.local` → `127.0.0.1:443` (via Traefik)
- `api.zoi.local` → `127.0.0.1:443` (via Traefik)

No `/etc/hosts` modifications needed for `*.zoi.local` domains.

## 🔄 **Production Domain Switching**

To switch from development to production:

1. **Update .env**:
   ```bash
   DOMAIN=yourdomain.com
   ```

2. **Update Authentik Environment**:
   ```bash
   AUTHENTIK_HOST_BROWSER=https://auth.yourdomain.com
   AUTHENTIK_ISSUER=https://auth.yourdomain.com/application/o/default/
   ```

3. **Update Blueprint**:
   ```yaml
   external_host: https://auth.yourdomain.com
   ```

4. **Restart Services**:
   ```bash
   docker-compose down && docker-compose up -d
   ```

## 🚫 **Common Anti-Patterns to Avoid**

### ❌ False zoi.local Replacement
```bash
# NEVER do this replacement:
sed 's/auth\.zoi.local/zoi.local/g'  # Breaks routing!
```

### ❌ Missing Subdomain in External Host
```yaml
# WRONG - Missing auth subdomain
external_host: https://zoi.local
```

### ❌ Protocol Mismatch
```bash
# WRONG - HTTP instead of HTTPS for browser access
AUTHENTIK_HOST_BROWSER=http://auth.zoi.local  # Should be HTTPS
```

### ❌ Port Conflicts
```bash
# WRONG - Including port when Traefik handles SSL termination
AUTHENTIK_HOST_BROWSER=https://auth.zoi.local:9000  # Remove :9000
```

## ✅ **Validation Checklist**

- [ ] All services use `{service}.${DOMAIN:-zoi.local}` pattern
- [ ] Authentik `external_host` matches Traefik routing domain
- [ ] `AUTHENTIK_HOST_BROWSER` uses HTTPS with correct subdomain
- [ ] No hardcoded `zoi.local` replacements in middleware
- [ ] Blueprint domains match environment configuration
- [ ] DNS resolution works for all `*.zoi.local` subdomains

## 🔧 **Troubleshooting Domain Issues**

1. **Redirect Loops**: Check external_host matches Traefik routing
2. **404 Errors**: Verify subdomain patterns are consistent
3. **DNS Issues**: Ensure `*.zoi.local` resolves to `127.0.0.1`
4. **SSL Issues**: Check HTTPS is used for browser-facing URLs
