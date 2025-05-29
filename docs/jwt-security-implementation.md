# JWT Security Implementation Guide

## Overview

This document provides a comprehensive guide to the JWT (JSON Web Token) security implementation in the Production RAG System. The implementation ensures secure authentication and authorization across all services while maintaining high performance and reliability.

## Architecture

### Components

1. **JWT Handler** (`src/auth/jwt_handler.py`)
   - Core JWT validation and security logic
   - JWKS (JSON Web Key Set) management
   - Token validation with comprehensive security checks

2. **JWT Middleware** (`src/auth/jwt_middleware.py`)
   - FastAPI middleware for authentication
   - Scope-based authorization
   - Optional authentication support

3. **Token Storage** (`src/auth/token_storage.py`)
   - Secure token storage with encryption
   - Redis-based backend for scalability
   - Token lifecycle management

4. **Security Configuration** (`config/authentik/jwt-security-config.yaml`)
   - Centralized security settings
   - Environment-specific configurations
   - Compliance and audit settings

## Security Features

### 1. Token Validation

#### Signature Verification
- **Algorithm**: RS256 (RSA with SHA-256)
- **Key Management**: JWKS endpoint integration
- **Key Rotation**: Automatic key rotation support
- **Verification**: Mandatory signature verification

#### Claims Validation
- **Required Claims**: `sub`, `iat`, `exp`, `iss`, `aud`
- **Issuer Validation**: Strict issuer verification
- **Audience Validation**: Multi-audience support
- **Expiration**: Mandatory expiration checking
- **Not Before**: Optional NBF claim validation

#### Security Checks
- **Clock Skew Tolerance**: Configurable (default: 30 seconds)
- **Maximum Auth Age**: Configurable (default: 24 hours)
- **Scope Validation**: Fine-grained permission checking
- **Group Membership**: Role-based access control

### 2. Token Storage Security

#### Encryption
- **Algorithm**: Fernet (AES 128 in CBC mode with HMAC)
- **Key Derivation**: PBKDF2 with SHA-256
- **Salt**: Configurable salt for key derivation
- **Rotation**: Support for key rotation

#### Storage Backend
- **Primary**: Redis with TTL support
- **Encryption**: All tokens encrypted at rest
- **Indexing**: User-based token indexing
- **Cleanup**: Automatic expired token cleanup

#### Token Lifecycle
- **Creation**: Secure token generation and storage
- **Retrieval**: Decryption and validation on access
- **Revocation**: Immediate token invalidation
- **Expiration**: Automatic cleanup of expired tokens

### 3. Rate Limiting and Protection

#### Request Limits
- **Token Validation**: 60 requests per minute per IP
- **Failed Attempts**: 5 attempts before lockout
- **Lockout Duration**: 15 minutes
- **Concurrent Sessions**: Configurable per user

#### Security Headers
- **CORS**: Configurable origin restrictions
- **CSP**: Content Security Policy enforcement
- **HSTS**: HTTP Strict Transport Security
- **X-Frame-Options**: Clickjacking protection

## Configuration

### Environment Variables

#### Core JWT Settings
```bash
# Token Lifetimes (seconds)
JWT_ACCESS_TOKEN_LIFETIME=3600      # 1 hour
JWT_REFRESH_TOKEN_LIFETIME=86400    # 24 hours
JWT_ID_TOKEN_LIFETIME=3600          # 1 hour

# Security Settings
JWT_ALGORITHM=RS256
JWT_AUDIENCE=rag-system
JWT_CLOCK_SKEW_TOLERANCE=30
JWT_MAX_AUTH_AGE=86400

# Validation Options
JWT_REQUIRE_EXP=true
JWT_REQUIRE_IAT=true
JWT_REQUIRE_NBF=false
JWT_VERIFY_SIGNATURE=true
JWT_VERIFY_AUDIENCE=true
JWT_VERIFY_ISSUER=true

# JWKS Configuration
JWKS_CACHE_TTL=3600
AUTHENTIK_ISSUER=https://auth.localhost/application/o/default/
```

#### Token Storage Security
```bash
# Encryption
TOKEN_ENCRYPTION_KEY=your-32-byte-encryption-key
MAX_TOKENS_PER_USER=10
MAX_CONCURRENT_SESSIONS=5

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password
```

### Authentik Configuration

#### OAuth2 Provider Settings
```yaml
# In Authentik Admin Panel
name: "RAG System OAuth2"
authorization_flow: "default-authorization-flow"
client_type: "confidential"
client_id: "rag-system"
redirect_uris:
  - "http://localhost:8000/api/auth/callback"
  - "https://localhost:8000/api/auth/callback"

# Token Settings
access_token_validity: "hours=1"
refresh_token_validity: "days=1"
include_claims_in_id_token: true

# Scopes
scopes:
  - "openid"
  - "profile" 
  - "email"
  - "groups"
  - "rag:api"
  - "rag:search"
  - "rag:write"
  - "admin"
```

#### Property Mappings
```python
# User Information Mapping
return {
    "sub": user.uuid,
    "preferred_username": user.username,
    "name": user.name,
    "given_name": user.first_name,
    "family_name": user.last_name,
    "email": user.email,
    "email_verified": user.email_verified,
    "groups": [group.name for group in user.ak_groups.all()],
    "locale": user.locale or "en-US"
}

# Scope Mapping
if "rag:api" in request.scope:
    return {"api_access": True}
if "admin" in request.scope:
    return {"admin_access": True, "all_permissions": True}
```

## Usage Examples

### 1. FastAPI Integration

#### Basic Authentication
```python
from src.auth.jwt_middleware import require_auth

@app.get("/protected")
async def protected_endpoint(user: dict = Depends(require_auth)):
    return {"message": f"Hello {user['username']}!"}
```

#### Scope-Based Authorization
```python
from src.auth.jwt_middleware import require_scopes

@app.post("/admin/users")
async def create_user(user: dict = Depends(require_scopes("admin"))):
    # Admin-only functionality
    pass

@app.get("/search")
async def search(user: dict = Depends(require_scopes("rag:search"))):
    # Search functionality
    pass
```

#### Optional Authentication
```python
from src.auth.jwt_middleware import optional_auth

@app.get("/public")
async def public_endpoint(user: dict = Depends(optional_auth)):
    if user:
        return {"message": f"Welcome back, {user['username']}!"}
    else:
        return {"message": "Welcome, guest!"}
```

### 2. Token Management

#### Storing Tokens
```python
from src.auth.token_storage import get_token_manager

async def login_callback(tokens: dict, user_id: str):
    token_manager = await get_token_manager()
    
    token_ids = await token_manager.store_user_tokens(
        user_id=user_id,
        access_token=tokens['access_token'],
        refresh_token=tokens['refresh_token'],
        id_token=tokens['id_token'],
        scopes=['openid', 'profile', 'rag:api'],
        device_id=request.headers.get('X-Device-ID'),
        ip_address=request.client.host
    )
    
    return token_ids
```

#### Token Revocation
```python
async def logout(user_id: str, device_id: str = None):
    token_manager = await get_token_manager()
    await token_manager.logout_user(user_id, device_id)
```

### 3. Health Monitoring

#### JWT System Health Check
```python
from src.auth.jwt_middleware import jwt_health_check

@app.get("/health/jwt")
async def jwt_health():
    return await jwt_health_check()
```

#### Token Storage Statistics
```python
from src.auth.token_storage import get_token_storage

@app.get("/admin/token-stats")
async def token_stats(user: dict = Depends(require_admin)):
    storage = await get_token_storage()
    return await storage.get_storage_stats()
```

## Security Testing

### Automated Testing

Run the comprehensive security test suite:

```bash
cd /Users/nova/Sites/zoi
python scripts/test-jwt-security.py
```

### Test Coverage

The test suite validates:

1. **Configuration Validation**
   - JWT security settings
   - Environment variable validation
   - Algorithm and key validation

2. **Token Validation Security**
   - Signature verification
   - Claims validation
   - Expiration handling
   - Malformed token rejection

3. **Integration Testing**
   - JWKS endpoint connectivity
   - FastAPI middleware integration
   - Redis storage functionality

4. **Security Features**
   - Rate limiting
   - Security headers
   - CORS configuration

### Manual Testing

#### Valid Token Test
```bash
# Test with valid token
curl -H "Authorization: Bearer <valid_token>" \
     http://localhost:8000/api/protected
```

#### Invalid Token Test
```bash
# Test with invalid token
curl -H "Authorization: Bearer invalid_token" \
     http://localhost:8000/api/protected
```

#### Scope Testing
```bash
# Test scope requirements
curl -H "Authorization: Bearer <token_without_admin_scope>" \
     http://localhost:8000/api/admin/users
```

## Monitoring and Logging

### Log Levels

- **INFO**: Successful authentications, token operations
- **WARNING**: Failed authentication attempts, expired tokens
- **ERROR**: System errors, configuration issues
- **DEBUG**: Detailed validation steps (development only)

### Key Metrics

Monitor these metrics for security and performance:

1. **Authentication Metrics**
   - Successful/failed authentication rates
   - Token validation latency
   - JWKS fetch frequency

2. **Security Metrics**
   - Failed authentication attempts per IP
   - Blacklisted token access attempts
   - Unusual access patterns

3. **Performance Metrics**
   - Token validation response time
   - Redis connection pool usage
   - Memory usage for token storage

### Alerting

Set up alerts for:

- High failed authentication rates
- JWKS endpoint unavailability
- Redis connection failures
- Unusual token access patterns
- Configuration validation failures

## Troubleshooting

### Common Issues

#### 1. Token Validation Failures

**Symptoms**: 401 Unauthorized errors
**Causes**:
- Clock skew between services
- Incorrect JWKS endpoint
- Network connectivity issues
- Invalid configuration

**Solutions**:
```bash
# Check timezone synchronization
docker exec <container> date

# Verify JWKS endpoint
curl https://auth.localhost/application/o/default/jwks/

# Check configuration
python -c "from src.auth.jwt_handler import JWTSecurityConfig; print(JWTSecurityConfig().__dict__)"
```

#### 2. Redis Connection Issues

**Symptoms**: Token storage failures
**Causes**:
- Redis server unavailable
- Authentication failures
- Network connectivity

**Solutions**:
```bash
# Test Redis connectivity
redis-cli ping

# Check Redis logs
docker logs zoi-redis-1

# Verify environment variables
echo $REDIS_URL
```

#### 3. Performance Issues

**Symptoms**: Slow authentication
**Causes**:
- JWKS caching issues
- Redis latency
- Network delays

**Solutions**:
- Increase JWKS cache TTL
- Optimize Redis configuration
- Use connection pooling
- Monitor network latency

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export JWT_DEBUG=true
```

## Security Best Practices

### Production Deployment

1. **Environment Security**
   - Use strong encryption keys (32+ bytes)
   - Rotate keys regularly
   - Secure environment variable storage
   - Enable HTTPS everywhere

2. **Token Management**
   - Short access token lifetimes (≤1 hour)
   - Secure refresh token storage
   - Implement token rotation
   - Monitor token usage patterns

3. **Network Security**
   - Use TLS 1.3 for all connections
   - Implement proper CORS policies
   - Enable security headers
   - Use secure cookie settings

4. **Monitoring**
   - Log all authentication events
   - Monitor for suspicious patterns
   - Set up security alerts
   - Regular security audits

### Compliance

The implementation supports compliance with:

- **OWASP**: Web Application Security Guidelines
- **OAuth 2.1**: Latest OAuth security recommendations
- **OIDC**: OpenID Connect security requirements
- **GDPR**: Data protection and privacy requirements

## Migration and Updates

### Version Updates

When updating JWT libraries or configurations:

1. Test in development environment
2. Verify backward compatibility
3. Update security tests
4. Monitor production deployment
5. Have rollback plan ready

### Key Rotation

For rotating signing keys:

1. Add new key to JWKS endpoint
2. Update Authentik configuration
3. Allow grace period for old keys
4. Remove old keys after validation
5. Update monitoring and alerts

## Support and Resources

### Documentation
- [JWT.io](https://jwt.io/) - JWT debugging tools
- [Authentik Documentation](https://goauthentik.io/docs/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

### Tools
- JWT debugger: https://jwt.io/
- JWKS validator: Custom validation scripts
- Security scanner: OWASP ZAP integration

For additional support or security concerns, contact the development team or create an issue in the project repository.
