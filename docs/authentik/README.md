# Authentik Forward Authentication Documentation

This directory contains comprehensive documentation for the Authentik + Traefik forward authentication setup implemented in the ZOI platform.

## 📚 Documentation Index

### 🚀 [Complete Setup Guide](forward-auth-setup.md)
**The definitive guide for implementing Authentik forward authentication**

Contains:
- Complete architecture overview with diagrams
- Blueprint-by-blueprint configuration details
- Docker Compose setup with critical labels
- Traefik middleware configuration
- Automated deployment scripts
- Security considerations and production hardening
- Step-by-step verification procedures

**Start here if:** You're implementing forward auth from scratch or need a complete reference.

### 🔧 [Troubleshooting Guide](troubleshooting-guide.md) 
**Comprehensive diagnostic and resolution procedures**

Contains:
- Quick diagnostic script for health checking
- HTTP error code reference and solutions
- Database diagnostic queries
- Step-by-step issue resolution procedures
- Recovery and reset procedures
- Monitoring and log aggregation setup

**Start here if:** You're experiencing issues with an existing setup or need to debug authentication problems.

## 🎯 Quick Start

For those familiar with the setup who just need the essentials:

```bash
# 1. Deploy the stack
docker-compose up -d

# 2. Wait for blueprint application (automatic)
docker-compose logs -f authentik-server | grep "Blueprint.*completed"

# 3. Run post-deployment permissions fix
./scripts/post-deploy-setup.sh

# 4. Verify setup
curl -I http://dashy.zoi.local  # Should return 302 redirect to auth
```

## 🔍 Architecture Summary

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    User     │───▶│   Traefik   │───▶│ Forward Auth│
│   Browser   │    │    Proxy    │    │ Middleware  │
└─────────────┘    └─────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Protected   │◀───│   Authentik │◀───│ Embedded    │
│ Application │    │   Server    │    │  Outpost    │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Key Components:**
- **Embedded Outpost**: Built-in forward auth provider
- **Forward Domain Mode**: Single provider protects multiple subdomains  
- **Blueprint Automation**: Infrastructure-as-code configuration
- **Group-based Access**: Fine-grained permission control

## 📋 Configuration Files

### Blueprints (Infrastructure as Code)
```
config/authentik/blueprints/
├── 00-flows.yaml                    # Authentication flows
├── 01-users.yaml                    # Users and groups
├── 02-provider.yaml                 # Proxy provider & application
├── 03-simple-policy.yaml            # Access policies  
├── 04-outpost-provider-assignment.yaml  # Outpost configuration
└── 05-outpost-permissions.yaml      # Group permissions
```

### Traefik Integration
```
config/traefik/dynamic/
└── middleware.yml                   # Forward auth middleware
```

### Automation Scripts
```
config/authentik/startup-scripts/
└── apply-blueprints.sh             # Automated blueprint application

scripts/
├── post-deploy-setup.sh            # Post-deployment permissions fix
├── diagnose-auth.sh                # Health diagnostic tool
├── monitor-auth.sh                 # Real-time monitoring
└── health-check.sh                 # Automated health checks
```

## 🛡️ Security Features

### Authentication
- **OAuth2/OIDC**: Standards-compliant authentication flow
- **Single Sign-On**: Seamless access across applications
- **Session Management**: Secure cookie handling with proper domain scope

### Authorization  
- **Group-based Access**: Role-based permission system
- **Policy Engine**: Flexible expression-based access control
- **Application Isolation**: Per-application access policies

### Network Security
- **Forward Auth Pattern**: No direct application authentication
- **Secure Headers**: Proper forwarding of user context
- **Domain Isolation**: Subdomain-based application separation

## 🔄 Maintenance Procedures

### Regular Tasks
```bash
# Health check (run daily)
./scripts/health-check.sh

# Log monitoring (continuous)
./scripts/monitor-auth.sh

# Configuration backup (weekly)
tar -czf authentik-backup-$(date +%Y%m%d).tar.gz config/authentik/
```

### Updates
```bash
# Update Authentik
docker-compose pull authentik-server
docker-compose up -d authentik-server

# Verify configuration after update  
./scripts/post-deploy-setup.sh
./scripts/diagnose-auth.sh
```

### Recovery
```bash
# Quick fix for common issues
./scripts/post-deploy-setup.sh

# Full reset (if needed)
docker-compose down
docker volume rm zoi_authentik_media zoi_authentik_templates
docker-compose up -d
```

## 🐛 Common Issues & Quick Fixes

| Issue | Quick Fix | Documentation |
|-------|-----------|---------------|
| 403 Forbidden from outpost | `./scripts/post-deploy-setup.sh` | [Troubleshooting Guide](troubleshooting-guide.md#issue-1-forward-auth-returns-403-forbidden) |
| Infinite redirect loops | Check callback route configuration | [Troubleshooting Guide](troubleshooting-guide.md#issue-2-infinite-redirect-loop) |
| 404 on auth endpoint | Verify outpost provider assignment | [Troubleshooting Guide](troubleshooting-guide.md#issue-3-application-not-found--404-errors) |
| OAuth callback errors | Check redirect URI configuration | [Troubleshooting Guide](troubleshooting-guide.md#issue-4-oauth-callback-errors) |

## 📞 Support Resources

### Logs
```bash
# Authentik logs
docker-compose logs authentik-server

# Traefik logs (forward auth requests)
docker-compose logs traefik | grep outpost

# Full diagnostic
./scripts/diagnose-auth.sh
```

### Admin Access
- **Authentik Admin UI**: http://auth.zoi.local/if/admin/
- **Default Credentials**: admin@zoi.local / admin123!
- **Traefik Dashboard**: http://localhost:8080 (if enabled)

### Database Access
```bash
# Direct database queries
docker-compose exec postgres psql -U authentik -d authentik

# Configuration audit
docker-compose exec postgres psql -U authentik -d authentik -f docs/authentik/audit-queries.sql
```

## 📈 Performance Considerations

### Optimization Tips
1. **Enable Redis caching** for session storage
2. **Use external domains** for production (avoid localhost)
3. **Implement proper SSL/TLS** in production environments
4. **Monitor resource usage** of Authentik and outpost containers
5. **Configure appropriate timeouts** for forward auth requests

### Scaling
- **Horizontal scaling**: Multiple Authentik instances with load balancer
- **Database scaling**: PostgreSQL read replicas for large deployments  
- **Outpost scaling**: External outposts for distributed applications
- **CDN integration**: Static asset caching for Authentik UI

## 🔗 External Resources

- [Authentik Documentation](https://docs.goauthentik.io/)
- [Traefik Forward Auth Guide](https://doc.traefik.io/traefik/middlewares/http/forwardauth/)
- [OAuth2 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OIDC Specification](https://openid.net/connect/)

---

**Note**: This documentation assumes familiarity with Docker, Docker Compose, and basic authentication concepts. For production deployments, consult the security considerations in the setup guide and implement appropriate hardening measures.
