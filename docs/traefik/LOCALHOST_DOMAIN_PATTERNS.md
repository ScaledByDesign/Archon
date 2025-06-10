# Localhost Domain Patterns for Development

## ⚠️ **CRITICAL: Never Replace (sub).localhost with just localhost**

When working with local development using `*.localhost` domains, **NEVER** replace subdomain patterns like `auth.localhost`, `dashy.localhost`, etc. with just `localhost`. This causes false redirect loops and breaks service routing.

## ✅ **Correct Domain Patterns**

### Environment Configuration
```bash
# .env file
DOMAIN=localhost

# Services use pattern: {service}.${DOMAIN:-localhost}
# Results in: auth.localhost, dashy.localhost, qdrant.localhost, etc.
```

### Traefik Router Rules
```yaml
# ✅ CORRECT - Uses subdomain pattern
labels:
  - "traefik.http.routers.authentik.rule=Host(`auth.${DOMAIN:-localhost}`)"
  - "traefik.http.routers.dashy.rule=Host(`dashy.${DOMAIN:-localhost}`)"

# ❌ WRONG - Would break routing
labels:
  - "traefik.http.routers.authentik.rule=Host(`${DOMAIN:-localhost}`)"  # NO subdomain
```

### Authentik Configuration
```bash
# ✅ CORRECT - Uses full subdomain
AUTHENTIK_HOST_BROWSER=https://auth.localhost
AUTHENTIK_ISSUER=https://auth.localhost/application/o/default/

# ❌ WRONG - Missing subdomain
AUTHENTIK_HOST_BROWSER=https://localhost  # Would cause redirect loops
```

### Blueprint Configuration
```yaml
# ✅ CORRECT - Matches Traefik routing
external_host: https://auth.localhost

# ❌ WRONG - Mismatched domain
external_host: https://localhost  # Would cause authentication failures
```

## 🌐 **DNS Resolution in Development**

Modern browsers automatically resolve `*.localhost` to `127.0.0.1`:
- `auth.localhost` → `127.0.0.1:443` (via Traefik)
- `dashy.localhost` → `127.0.0.1:443` (via Traefik)
- `api.localhost` → `127.0.0.1:443` (via Traefik)

No `/etc/hosts` modifications needed for `*.localhost` domains.

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

### ❌ False Localhost Replacement
```bash
# NEVER do this replacement:
sed 's/auth\.localhost/localhost/g'  # Breaks routing!
```

### ❌ Missing Subdomain in External Host
```yaml
# WRONG - Missing auth subdomain
external_host: https://localhost
```

### ❌ Protocol Mismatch
```bash
# WRONG - HTTP instead of HTTPS for browser access
AUTHENTIK_HOST_BROWSER=http://auth.localhost  # Should be HTTPS
```

### ❌ Port Conflicts
```bash
# WRONG - Including port when Traefik handles SSL termination
AUTHENTIK_HOST_BROWSER=https://auth.localhost:9000  # Remove :9000
```

## ✅ **Validation Checklist**

- [ ] All services use `{service}.${DOMAIN:-localhost}` pattern
- [ ] Authentik `external_host` matches Traefik routing domain
- [ ] `AUTHENTIK_HOST_BROWSER` uses HTTPS with correct subdomain
- [ ] No hardcoded `localhost` replacements in middleware
- [ ] Blueprint domains match environment configuration
- [ ] DNS resolution works for all `*.localhost` subdomains

## 🔧 **Troubleshooting Domain Issues**

1. **Redirect Loops**: Check external_host matches Traefik routing
2. **404 Errors**: Verify subdomain patterns are consistent
3. **DNS Issues**: Ensure `*.localhost` resolves to `127.0.0.1`
4. **SSL Issues**: Check HTTPS is used for browser-facing URLs
