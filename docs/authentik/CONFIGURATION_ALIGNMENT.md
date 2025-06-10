# Configuration Alignment Guide
## Bridging Basic Authentik Setup with Comprehensive JWT Security

This document aligns your current Authentik/Traefik/Dashy setup with the comprehensive JWT security implementation described in the security guides.

## 🔄 **Configuration Gaps Identified**

### 1. **JWT Security Implementation Missing**
Your JWT security guides describe a sophisticated implementation that's not currently configured:

**Missing Components:**
- FastAPI JWT middleware (`src/auth/jwt_middleware.py`)
- JWT handler (`src/auth/jwt_handler.py`) 
- Token storage with encryption (`src/auth/token_storage.py`)
- Security dependencies (`src/auth/dependencies.py`)

### 2. **Environment Variable Misalignment**
**Current Setup:** Basic Authentik variables
**Required:** Comprehensive JWT security variables

## 📋 **Step-by-Step Alignment Process**

### Phase 1: Update Environment Configuration

1. **Updated `config/authentik/authentik.env`** ✅ (Already Done)
   - Added JWT security configuration
   - Included token lifetime settings
   - Added validation requirements
   - Configured JWKS settings

2. **Create FastAPI JWT Environment Configuration:**

```bash
# Add to .env or create config/fastapi/jwt.env
AUTHENTIK_URL=http://localhost:9000
AUTHENTIK_ISSUER=http://localhost:9000/application/o/default/
AUTHENTIK_API_TOKEN=your-api-token-here

# JWT Configuration (matching authentik.env)
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=86400
JWT_ID_TOKEN_LIFETIME=3600
JWT_ALGORITHM=RS256
JWT_AUDIENCE=rag-system
JWKS_CACHE_TTL=3600

# OAuth2 Client Credentials  
FASTAPI_OAUTH_CLIENT_ID=dashy-client-id
FASTAPI_OAUTH_CLIENT_SECRET=dashy-client-secret
FASTAPI_OAUTH_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Session Configuration
SESSION_SECRET_KEY=your-session-secret-key-32-chars-min

# Token Storage Security
TOKEN_ENCRYPTION_KEY=your-32-byte-encryption-key-for-token-storage
MAX_TOKENS_PER_USER=10
MAX_CONCURRENT_SESSIONS=5
```

### Phase 2: Authentik OAuth2 Provider Configuration

Update your Authentik OAuth2 provider to match JWT security requirements:

#### 2.1 **OAuth2 Provider Settings** (In Authentik Admin)
```yaml
Name: "Dashy OAuth2 Provider"
Authorization Flow: "default-authorization-flow"
Client Type: "confidential"
Client ID: "dashy-client-id"
Client Secret: "dashy-client-secret"

# Token Settings (CRITICAL - matches JWT config)
Access Token Validity: "hours=1"        # JWT_ACCESS_TOKEN_LIFETIME
Refresh Token Validity: "days=1"        # JWT_REFRESH_TOKEN_LIFETIME
Include Claims in ID Token: true

# Algorithm Settings
Algorithm: "RS256"                       # JWT_ALGORITHM
```

#### 2.2 **Required Scopes Configuration**
```yaml
Scopes:
  - "openid"
  - "profile"
  - "email" 
  - "groups"
  - "rag:api"        # Main API access
  - "rag:search"     # Search functionality
  - "rag:write"      # Write permissions
  - "admin"          # Admin access
```

#### 2.3 **Property Mappings for JWT Claims**
Create these mappings in Authentik:

**User Information Mapping:**
```python
# Name: jwt-user-mapping
return {
    "sub": user.uuid,
    "preferred_username": user.username,
    "name": user.name,
    "given_name": user.first_name,
    "family_name": user.last_name,
    "email": user.email,
    "email_verified": user.email_verified,
    "groups": [group.name for group in user.ak_groups.all()],
    "locale": user.locale or "en-US",
    "aud": "rag-system"  # JWT_AUDIENCE
}
```

**Scope-Specific Claims:**
```python
# Name: jwt-scope-mapping
claims = {}
if "rag:api" in request.scope:
    claims["api_access"] = True
if "admin" in request.scope:
    claims["admin_access"] = True
    claims["all_permissions"] = True
if "rag:search" in request.scope:
    claims["search_access"] = True
if "rag:write" in request.scope:
    claims["write_access"] = True
return claims
```

### Phase 3: FastAPI Integration Implementation

#### 3.1 **Create JWT Handler** (Missing Component)
```python
# File: src/auth/jwt_handler.py
from src.auth.jwt_handler import JWTHandler

# Initialize with Authentik JWKS endpoint
handler = JWTHandler("http://localhost:9000")

# Validate tokens with comprehensive security
claims = await handler.validate_access_token(access_token)
```

#### 3.2 **Implement JWT Middleware** (Missing Component)
```python
# File: src/auth/jwt_middleware.py
from src.auth.middleware import JWTAuthenticationMiddleware

app.add_middleware(
    JWTAuthenticationMiddleware,
    protected_paths=["/api/"],
    excluded_paths=["/api/auth/", "/docs", "/health"],
    jwks_url="http://localhost:9000/application/o/default/jwks/",
    algorithm="RS256",
    audience="rag-system"
)
```

#### 3.3 **Add FastAPI Dependencies** (Missing Component)
```python
# File: src/auth/dependencies.py
from src.auth.dependencies import get_current_user, require_scopes

@app.get("/api/protected")
async def protected_endpoint(user: dict = Depends(get_current_user)):
    return {"user": user['email']}

@app.get("/api/admin")  
async def admin_endpoint(user: dict = Depends(require_scopes("admin"))):
    return {"message": "Admin access granted"}
```

### Phase 4: Token Storage Implementation

#### 4.1 **Implement Encrypted Token Storage** (Missing Component)
```python
# File: src/auth/token_storage.py
from src.auth.token_storage import get_token_manager

# Store tokens securely with encryption
token_manager = await get_token_manager()
token_ids = await token_manager.store_user_tokens(
    user_id=user_id,
    access_token=tokens['access_token'],
    refresh_token=tokens['refresh_token'],
    id_token=tokens['id_token']
)
```

### Phase 5: Security Headers & Rate Limiting

#### 5.1 **Security Middleware** (Missing Component)
```python
# File: src/auth/middleware.py
app.add_middleware(
    CORSAndSecurityMiddleware,
    allowed_origins=["http://localhost:3000", "http://dashy.localhost"],
    allow_credentials=True
)
```

#### 5.2 **Rate Limiting Configuration**
```python
# Authentication endpoints: 5 attempts per 15 minutes per IP
# Token refresh: 10 attempts per hour per user
# Failed validation: Exponential backoff
```

## ✅ **Updated Verification Checklist**

### After Environment Alignment
- [ ] JWT security variables configured in `authentik.env`
- [ ] FastAPI JWT environment variables set
- [ ] Token encryption keys generated and configured
- [ ] Redis configuration includes token storage settings

### After Authentik OAuth2 Configuration  
- [ ] OAuth2 provider configured with RS256 algorithm
- [ ] Token lifetimes match JWT security requirements
- [ ] Required scopes defined (rag:api, rag:search, etc.)
- [ ] Property mappings created for JWT claims
- [ ] Audience claim set to "rag-system"

### After FastAPI Implementation
- [ ] JWT handler implemented and working
- [ ] JWT middleware configured with JWKS validation
- [ ] FastAPI dependencies working (get_current_user, require_scopes)
- [ ] Token storage with encryption functional
- [ ] Security headers and rate limiting active

### After Full Integration
- [ ] End-to-end JWT validation working
- [ ] JWKS endpoint accessible: `http://localhost:9000/application/o/default/jwks/`
- [ ] Token validation matches security requirements
- [ ] Rate limiting and security headers active
- [ ] Encrypted token storage working
- [ ] Scope-based authorization functional

## 🚨 **Critical Implementation Notes**

1. **Algorithm Consistency**: Ensure RS256 is used throughout (Authentik → FastAPI)
2. **Audience Validation**: "rag-system" must match across all configurations  
3. **JWKS Endpoint**: Must be accessible from FastAPI for signature validation
4. **Token Lifetimes**: Must match between Authentik and FastAPI configurations
5. **Encryption Keys**: Generate secure 32-byte keys for token storage
6. **Security Headers**: Implement comprehensive security headers per JWT guides

## 🔧 **Next Steps**

1. **Implement Missing FastAPI Components**: JWT handler, middleware, dependencies
2. **Configure Authentik OAuth2 Provider**: RS256, scopes, property mappings
3. **Test JWT Validation Flow**: Comprehensive end-to-end testing
4. **Implement Token Storage**: Encrypted Redis-based storage
5. **Add Security Features**: Rate limiting, security headers, monitoring

This alignment ensures your setup matches the sophisticated JWT security implementation described in your security guides. 