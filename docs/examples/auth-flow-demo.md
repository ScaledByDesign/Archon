# 🔐 LiteLLM + Authentik Hybrid Authentication

## Authentication Strategy

### **Hybrid Approach: UI + Direct API**
```
UI Access (/) → Authentik Authentication → Protected Web Interface
API Access (/v1/*) → Direct Master Key → Bypass Authentik
```

### **Why This Approach?**
- **Web UI**: Protected by Authentik SSO for user management
- **API Access**: Direct access with master key for programmatic use
- **Best of Both**: Security for humans, simplicity for code

## Authentication Flows

### 1. **Web UI Access (Protected)**
```mermaid
sequenceDiagram
    participant User
    participant Traefik
    participant Authentik
    participant LiteLLM

    User->>Traefik: GET /
    Traefik->>Authentik: Check authentication
    alt Not authenticated
        Authentik->>User: Redirect to login
        User->>Authentik: Login (OAuth2)
        Authentik->>User: Set session cookie
    end
    Authentik->>Traefik: Auth OK
    Traefik->>LiteLLM: Forward request
    LiteLLM->>User: Web UI
```

### 2. **API Access (Direct)**
```mermaid
sequenceDiagram
    participant Client
    participant Traefik
    participant LiteLLM

    Client->>Traefik: GET /v1/models + API Key
    Note over Traefik: skip_path_regex: ^/v1/.*$
    Traefik->>LiteLLM: Direct forward (no auth check)
    LiteLLM->>LiteLLM: Validate master key
    LiteLLM->>Client: API Response
```

## Usage Examples

### 1. **Web Interface**
```bash
# This requires login through Authentik
open http://llm.zoi.local
```

### 2. **Direct API Access**
```bash
# Direct API access with master key
curl -H "Authorization: Bearer sk-6df5295f77391ff7611a0fab11b989287012f48e46f58ae0" \
     http://llm.zoi.local/v1/models
```

### 3. **Programmatic Access**
```python
import requests

# Direct API access - no Authentik authentication needed
headers = {
    'Authorization': 'Bearer sk-6df5295f77391ff7611a0fab11b989287012f48e46f58ae0',
    'Content-Type': 'application/json'
}

response = requests.post(
    'http://llm.zoi.local/v1/chat/completions',
    headers=headers,
    json={
        'model': 'gpt-4',
        'messages': [{'role': 'user', 'content': 'Hello!'}]
    }
)
```

### 4. **JavaScript/Frontend**
```javascript
// For API calls from web apps
const response = await fetch('/v1/chat/completions', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer sk-6df5295f77391ff7611a0fab11b989287012f48e46f58ae0',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        model: 'gpt-4',
        messages: [{ role: 'user', content: 'Hello!' }]
    })
});
```

## Configuration Details

### **Blueprint Configuration**
```yaml
# Forward Auth Provider
skip_path_regex: ^/v1/.*$  # Skip API paths for direct access
```

### **Traefik Middleware**
```yaml
# Only forward auth (no master key injection)
middlewares=authentik-forward-auth@file
```

### **Path Behavior**
- `/` → Authentik authentication required
- `/docs` → Authentik authentication required  
- `/health` → Authentik authentication required
- `/v1/*` → **Direct access** (master key required)

## Security Benefits

### **Web UI Security**
✅ **Single Sign-On**: Users login once via Authentik  
✅ **Session Management**: Handled by Authentik  
✅ **User Groups**: `zoi-users` group access control  
✅ **Audit Trail**: All web access logged  

### **API Security**
✅ **Direct Access**: No authentication overhead for APIs  
✅ **Master Key**: Strong API key validation  
✅ **Performance**: No proxy authentication delays  
✅ **Simplicity**: Standard API key usage patterns  

## Best Practices

### **API Key Management**
- Use strong, unique master keys
- Rotate keys regularly
- Store in secure environment variables
- Monitor usage through LiteLLM logs

### **Network Security**
- Use HTTPS in production
- Consider VPN for additional API security
- Monitor API usage patterns
- Set up rate limiting if needed

### **User Management**
- Manage web users through Authentik
- Use `zoi-users` group for access control
- Regular access reviews via Authentik admin

## Production Considerations

- **HTTPS**: Use TLS certificates for production
- **API Rate Limiting**: Consider per-key rate limits
- **Monitoring**: Monitor both web and API usage
- **Key Security**: Secure master key storage
- **Backup Authentication**: Consider backup access methods
