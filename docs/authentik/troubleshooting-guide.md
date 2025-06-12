# Authentik Forward Auth Troubleshooting Guide

## Quick Diagnostic Script

Save this as `scripts/diagnose-auth.sh`:

```bash
#!/bin/bash

echo "🔍 Authentik Forward Auth Diagnostic Script"
echo "==========================================="

# Check service health
echo "📊 Service Health Check:"
docker-compose ps | grep -E "(authentik|traefik|dashy|postgres|redis)"

echo -e "\n🔌 Network Connectivity:"
# Test internal connectivity
docker-compose exec authentik-server curl -s -o /dev/null -w "%{http_code}" http://postgres:5432 2>/dev/null && echo "✅ Authentik → Postgres: OK" || echo "❌ Authentik → Postgres: FAIL"
docker-compose exec authentik-server curl -s -o /dev/null -w "%{http_code}" http://redis:6379 2>/dev/null && echo "✅ Authentik → Redis: OK" || echo "❌ Authentik → Redis: FAIL"

echo -e "\n🌐 External Connectivity:"
# Test external endpoints
curl -s -o /dev/null -w "✅ auth.zoi.local: %{http_code}\n" http://auth.zoi.local/ 2>/dev/null || echo "❌ auth.zoi.local: UNREACHABLE"
curl -s -o /dev/null -w "✅ dashy.zoi.local: %{http_code}\n" http://dashy.zoi.local/ 2>/dev/null || echo "❌ dashy.zoi.local: UNREACHABLE"

echo -e "\n🔐 Forward Auth Endpoint:"
FORWARD_AUTH_RESPONSE=$(curl -s -w "%{http_code}" "http://auth.zoi.local/outpost.goauthentik.io/auth/traefik" \
  -H "X-Forwarded-Proto: http" \
  -H "X-Forwarded-Host: dashy.zoi.local" \
  -H "X-Forwarded-Uri: /" 2>/dev/null)
if [[ "$FORWARD_AUTH_RESPONSE" == *"302"* ]]; then
    echo "✅ Forward Auth: OK (302 redirect)"
elif [[ "$FORWARD_AUTH_RESPONSE" == *"401"* ]]; then
    echo "✅ Forward Auth: OK (401 unauthorized)"
elif [[ "$FORWARD_AUTH_RESPONSE" == *"403"* ]]; then
    echo "❌ Forward Auth: 403 Forbidden (Outpost permissions issue)"
elif [[ "$FORWARD_AUTH_RESPONSE" == *"404"* ]]; then
    echo "❌ Forward Auth: 404 Not Found (Outpost not running)"
else
    echo "⚠️  Forward Auth: Unexpected response ($FORWARD_AUTH_RESPONSE)"
fi

echo -e "\n📋 Database Configuration:"
docker-compose exec postgres psql -U authentik -d authentik -t -c "
SELECT 
  'Applications: ' || COUNT(*) 
FROM authentik_core_application 
WHERE name = 'Dashy Forward Auth App'
UNION ALL
SELECT 'Providers: ' || COUNT(*) 
FROM authentik_providers_proxy_proxyprovider 
WHERE external_host LIKE '%dashy%'
UNION ALL
SELECT 'Outpost Users in Admin Group: ' || COUNT(*) 
FROM authentik_core_user u 
JOIN authentik_core_user_ak_groups ug ON u.id = ug.user_id 
JOIN authentik_core_group g ON ug.group_id = g.group_uuid 
WHERE u.username LIKE 'ak-outpost-%' 
AND g.name = 'authentik Admins';
" 2>/dev/null | sed 's/^/✅ /'

echo -e "\n🎯 Outpost Status:"
docker-compose exec postgres psql -U authentik -d authentik -t -c "
SELECT 
  o.name || ' | Providers: ' || COUNT(p.provider_id) || ' | Config: ' || 
  CASE WHEN o._config::text LIKE '%auth.zoi.local%' THEN 'External Domain' ELSE 'Internal Only' END
FROM authentik_outposts_outpost o 
LEFT JOIN authentik_outposts_outpost_providers p ON o.uuid = p.outpost_id 
GROUP BY o.name, o._config;
" 2>/dev/null | sed 's/^/✅ /'

echo -e "\n🔧 Common Fixes:"
echo "1. Fix outpost permissions: ./scripts/post-deploy-setup.sh"
echo "2. Restart authentik: docker-compose restart authentik-server"
echo "3. Check logs: docker-compose logs authentik-server | tail -50"
echo "4. Verify blueprints: docker-compose exec authentik-server ls -la /blueprints/custom/"
```

## Error Code Reference

### HTTP Status Codes from Forward Auth

| Code | Meaning | Cause | Solution |
|------|---------|-------|----------|
| 200 | Authenticated | User has valid session | Normal flow ✅ |
| 302 | Redirect to login | User not authenticated | Normal flow ✅ |
| 401 | Unauthorized | Invalid credentials | Check user/password |
| 403 | Forbidden | Outpost permissions issue | Run post-deploy script |
| 404 | Not Found | Outpost not configured | Check provider assignment |
| 500 | Server Error | Authentik internal error | Check logs |
| 502 | Bad Gateway | Traefik can't reach Authentik | Check network/DNS |
| 503 | Service Unavailable | Authentik service down | Check docker-compose ps |

### Authentik Log Patterns

```bash
# Search for common error patterns
docker-compose logs authentik-server | grep -E "(ERROR|exception|failed|denied)"

# Specific error searches:
# Outpost connection issues
docker-compose logs authentik-server | grep -i "outpost.*failed"

# Database connection issues  
docker-compose logs authentik-server | grep -i "postgresql.*failed"

# OAuth/Provider issues
docker-compose logs authentik-server | grep -i "oauth.*error"

# Blueprint application issues
docker-compose logs authentik-server | grep -i "blueprint.*failed"
```

## Database Diagnostic Queries

### Complete Configuration Audit

```sql
-- Run this in: docker-compose exec postgres psql -U authentik -d authentik

-- 1. User and Group Summary
SELECT 
  'Total Users' as metric, 
  COUNT(*) as count 
FROM authentik_core_user 
WHERE is_active = true
UNION ALL
SELECT 
  'Total Groups', 
  COUNT(*) 
FROM authentik_core_group
UNION ALL
SELECT 
  'Users in dashy-users', 
  COUNT(*) 
FROM authentik_core_user u 
JOIN authentik_core_user_ak_groups ug ON u.id = ug.user_id 
JOIN authentik_core_group g ON ug.group_id = g.group_uuid 
WHERE g.name = 'dashy-users'
UNION ALL
SELECT 
  'Outpost Users in Admins', 
  COUNT(*) 
FROM authentik_core_user u 
JOIN authentik_core_user_ak_groups ug ON u.id = ug.user_id 
JOIN authentik_core_group g ON ug.group_id = g.group_uuid 
WHERE u.username LIKE 'ak-outpost-%' 
AND g.name = 'authentik Admins';

-- 2. Application Configuration
SELECT 
  a.name,
  a.slug,
  a."group" as assigned_group,
  p.external_host,
  p.internal_host,
  p.mode
FROM authentik_core_application a
LEFT JOIN authentik_providers_proxy_proxyprovider p 
  ON a.provider_id = p.oauth2provider_ptr_id
WHERE a.name LIKE '%Dashy%';

-- 3. Outpost Status
SELECT 
  o.name,
  o.type,
  o._config,
  COUNT(op.provider_id) as provider_count
FROM authentik_outposts_outpost o
LEFT JOIN authentik_outposts_outpost_providers op ON o.uuid = op.outpost_id
GROUP BY o.name, o.type, o._config;

-- 4. Policy Bindings
SELECT 
  p.name as policy_name,
  pb.order,
  pb.enabled,
  a.name as application_name
FROM authentik_policies_policy p
JOIN authentik_policies_policybinding pb ON p.policy_uuid = pb.policy_id
JOIN authentik_core_application a ON pb.target_id = a.policybindingmodel_ptr_id
WHERE a.name LIKE '%Dashy%'
ORDER BY pb.order;

-- 5. OAuth2 Configuration
SELECT 
  o.client_id,
  o._redirect_uris,
  o.client_type
FROM authentik_providers_oauth2_oauth2provider o
JOIN authentik_providers_proxy_proxyprovider p 
  ON o.provider_ptr_id = p.oauth2provider_ptr_id
WHERE p.external_host LIKE '%dashy%';
```

## Step-by-Step Issue Resolution

### Issue 1: "Forward Auth Returns 403 Forbidden"

**Root Cause**: Outpost service account lacks admin permissions

**Diagnosis**:
```bash
# Check if outpost user exists but isn't in admin group
docker-compose exec postgres psql -U authentik -d authentik -c "
SELECT 
  u.username,
  CASE WHEN g.name IS NULL THEN 'Not in Admin Group' ELSE 'In Admin Group' END as status
FROM authentik_core_user u
LEFT JOIN authentik_core_user_ak_groups ug ON u.id = ug.user_id 
LEFT JOIN authentik_core_group g ON ug.group_id = g.group_uuid AND g.name = 'authentik Admins'
WHERE u.username LIKE 'ak-outpost-%';
"
```

**Resolution**:
```bash
# Method 1: Run post-deploy script
./scripts/post-deploy-setup.sh

# Method 2: Manual SQL fix
docker-compose exec postgres psql -U authentik -d authentik -c "
INSERT INTO authentik_core_user_ak_groups (user_id, group_id) 
SELECT u.id, g.group_uuid 
FROM authentik_core_user u, authentik_core_group g 
WHERE u.username LIKE 'ak-outpost-%' 
AND g.name = 'authentik Admins' 
ON CONFLICT DO NOTHING;
"

# Method 3: Via Admin UI
# 1. Go to http://auth.zoi.local/if/admin/
# 2. Directory → Users → Find outpost user (starts with 'ak-outpost-')
# 3. Edit user → Groups → Add "authentik Admins"
```

### Issue 2: "Infinite Redirect Loop"

**Root Cause**: Callback routes have forward auth middleware applied

**Diagnosis**:
```bash
# Check Traefik configuration
curl -s http://localhost:8080/api/rawdata | jq '.routers | 
  to_entries[] | 
  select(.key | contains("outpost")) | 
  {name: .key, rule: .value.rule, middlewares: .value.middlewares}'
```

**Resolution**:
Ensure callback routes have NO middleware:
```yaml
# ❌ Wrong - has middleware
- "traefik.http.routers.dashy-outpost.middlewares=authentik"

# ✅ Correct - no middleware  
- "traefik.http.routers.dashy-outpost.rule=Host(`dashy.zoi.local`) && PathPrefix(`/outpost.goauthentik.io/`)"
- "traefik.http.routers.dashy-outpost.service=authentik"
- "traefik.http.routers.dashy-outpost.priority=100"
```

### Issue 3: "Application Not Found / 404 Errors"

**Root Cause**: Blueprint application failed or provider not linked

**Diagnosis**:
```bash
# Check if application exists
docker-compose exec postgres psql -U authentik -d authentik -c "
SELECT name, slug, provider_id FROM authentik_core_application 
WHERE name LIKE '%Dashy%';
"

# Check if provider exists  
docker-compose exec postgres psql -U authentik -d authentik -c "
SELECT external_host, internal_host, mode FROM authentik_providers_proxy_proxyprovider
WHERE external_host LIKE '%dashy%';
"
```

**Resolution**:
```bash
# Re-apply blueprints
docker-compose exec authentik-server /blueprints/startup-scripts/apply-blueprints.sh

# Or apply specific blueprint
docker-compose exec authentik-server ak apply_blueprint /blueprints/custom/02-provider.yaml
```

### Issue 4: "OAuth Callback Errors"

**Root Cause**: Redirect URI mismatch or callback routing issues

**Diagnosis**:
```bash
# Check OAuth redirect URIs
docker-compose exec postgres psql -U authentik -d authentik -c "
SELECT _redirect_uris FROM authentik_providers_oauth2_oauth2provider o
JOIN authentik_providers_proxy_proxyprovider p 
  ON o.provider_ptr_id = p.oauth2provider_ptr_id
WHERE p.external_host LIKE '%dashy%';
"

# Test callback route
curl -I "http://dashy.zoi.local/outpost.goauthentik.io/callback?test=1"
```

**Resolution**:
1. **Verify Traefik callback routes are configured**
2. **Check external_host matches actual domain**
3. **Ensure callback routes point to Authentik service**

## Recovery Procedures

### Complete Reset

If everything breaks, here's how to reset:

```bash
# 1. Stop services
docker-compose down

# 2. Remove Authentik data (keeps other data)
docker volume rm zoi_authentik_media zoi_authentik_templates

# 3. Reset database (nuclear option)
# docker volume rm zoi_postgres_data

# 4. Restart and wait for blueprint application
docker-compose up -d

# 5. Wait for startup script to complete
docker-compose logs -f authentik-server | grep "Blueprint.*completed"

# 6. Run post-deployment fix
./scripts/post-deploy-setup.sh

# 7. Verify setup
./scripts/diagnose-auth.sh
```

### Partial Reset (Blueprints Only)

```bash
# Remove applications and providers only
docker-compose exec postgres psql -U authentik -d authentik -c "
DELETE FROM authentik_core_application WHERE name LIKE '%Dashy%';
DELETE FROM authentik_providers_proxy_proxyprovider WHERE external_host LIKE '%dashy%';
"

# Re-apply provider blueprint
docker-compose exec authentik-server ak apply_blueprint /blueprints/custom/02-provider.yaml

# Fix permissions
./scripts/post-deploy-setup.sh
```

## Monitoring Setup

### Log Aggregation

```bash
# Create log monitoring script
cat > scripts/monitor-auth.sh << 'EOF'
#!/bin/bash

echo "🔍 Real-time Authentication Monitoring"
echo "======================================"

# Monitor key log patterns
docker-compose logs -f authentik-server | grep --line-buffered -E "(ERROR|WARN|failed|denied|403|404|500)" | while read line; do
    echo "🚨 $(date): $line"
done &

# Monitor forward auth requests
docker-compose logs -f traefik | grep --line-buffered "outpost.goauthentik.io" | while read line; do
    echo "🔐 $(date): $line"  
done &

wait
EOF

chmod +x scripts/monitor-auth.sh
```

### Health Check Script

```bash
# Create automated health check
cat > scripts/health-check.sh << 'EOF'
#!/bin/bash

HEALTHY=true

# Check services
for service in authentik-server traefik dashy postgres redis; do
    if ! docker-compose ps --status running | grep -q $service; then
        echo "❌ $service is not running"
        HEALTHY=false
    fi
done

# Check forward auth endpoint
if ! curl -s -f "http://auth.zoi.local/outpost.goauthentik.io/auth/traefik" \
    -H "X-Forwarded-Host: dashy.zoi.local" > /dev/null; then
    echo "❌ Forward auth endpoint unhealthy"
    HEALTHY=false
fi

# Check outpost permissions
OUTPOST_ADMINS=$(docker-compose exec postgres psql -U authentik -d authentik -t -c "
SELECT COUNT(*) FROM authentik_core_user u 
JOIN authentik_core_user_ak_groups ug ON u.id = ug.user_id 
JOIN authentik_core_group g ON ug.group_id = g.group_uuid 
WHERE u.username LIKE 'ak-outpost-%' AND g.name = 'authentik Admins';
" 2>/dev/null | xargs)

if [[ "$OUTPOST_ADMINS" -eq 0 ]]; then
    echo "❌ Outpost users not in admin group"
    HEALTHY=false
fi

if $HEALTHY; then
    echo "✅ All systems healthy"
    exit 0
else
    echo "❌ System health check failed"
    exit 1
fi
EOF

chmod +x scripts/health-check.sh
```

This troubleshooting guide provides comprehensive diagnostic tools and step-by-step resolution procedures for the most common issues encountered with Authentik forward authentication setups.
