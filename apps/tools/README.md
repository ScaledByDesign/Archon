# 🛠️ Zoi Tools Stack

Productivity and automation tools for the Zoi ecosystem, including workflow automation and AI chat interfaces.

## 🏗️ Architecture

### Productivity Tools
- **n8n** → Visual workflow automation and integration platform
- **OpenWebUI** → Modern AI chat interface with multi-model support

### Integration Features
- **Traefik Integration** → Clean domain routing and SSL termination
- **Authentik Authentication** → SSO integration with role-based access
- **Network Isolation** → Secure communication between services

## 🌐 Service Endpoints

| Service | URL | Port | Purpose |
|---------|-----|------|---------|
| **n8n** | http://localhost:7300 | 7300 | Workflow automation |
| **OpenWebUI** | http://localhost:7301 | 7301 | AI chat interface |

### Traefik Domain Routing

When using with the platform Traefik proxy, services are also available via domain routing:

| Service | Domain URL | Purpose |
|---------|------------|---------|
| **n8n** | http://n8n.zoi.local | Workflow automation |
| **OpenWebUI** | http://openwebui.zoi.local | AI chat interface |

## 🚀 Quick Start

### Prerequisites
- Platform stack running (PostgreSQL, Redis, Traefik, Authentik)
- LLM stack running (for OpenWebUI AI integration)

### 1. Start Tools Stack
```powershell
# Start all tools services
docker compose up -d

# Check service status
docker compose ps
```

### 2. Access Services
```powershell
# Open n8n workflow builder
start http://localhost:7300

# Open OpenWebUI chat interface
start http://localhost:7301

# Or via domains (if using Traefik)
start http://n8n.zoi.local
start http://openwebui.zoi.local
```

### 3. Initial Configuration

**n8n Setup:**
1. Access http://localhost:7300
2. Create admin account on first visit
3. Configure database connection (uses platform PostgreSQL)
4. Import workflows from `./config/n8n/workflows/`

**OpenWebUI Setup:**
1. Access http://localhost:7301
2. Create admin account on first visit
3. Configure LiteLLM connection (automatic via environment)
4. Start chatting with your local AI models

## 🔧 Configuration

### n8n Workflow Automation

**Features:**
- **Visual Workflow Builder** with drag-and-drop interface
- **400+ Integrations** including APIs, databases, and services
- **Webhook Support** for external triggers
- **Scheduled Workflows** with cron-like scheduling
- **Database Integration** with platform PostgreSQL

**Environment Configuration:**
```bash
# Database (uses platform PostgreSQL)
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=postgres
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n
DB_POSTGRESDB_PASSWORD=n8n_password123

# Security
N8N_BASIC_AUTH_ACTIVE=false  # Using Authentik instead
N8N_DISABLE_PRODUCTION_MAIN_PROCESS=false

# Webhooks
WEBHOOK_URL=http://n8n.zoi.local
N8N_PAYLOAD_SIZE_MAX=16
```

**Common Use Cases:**
- **AI Workflow Automation** - Connect AI models with business processes
- **Data Processing** - ETL pipelines and data transformation
- **API Integration** - Connect different services and APIs
- **Notification Systems** - Automated alerts and messaging
- **Content Management** - Automated content creation and publishing

### OpenWebUI AI Chat Interface

**Features:**
- **Multi-Model Support** via LiteLLM integration
- **Chat History** with conversation management
- **Model Switching** between different AI models
- **File Upload** for document analysis
- **Custom Prompts** and templates
- **User Management** with role-based access

**Environment Configuration:**
```bash
# LiteLLM Integration
OPENAI_API_BASE_URL=http://litellm:4000/v1
OPENAI_API_KEY=sk-wqn0xwq_vha4MVM2yzw

# Interface Settings
WEBUI_NAME=Zoi AI Chat
WEBUI_URL=http://openwebui.zoi.local
DEFAULT_MODELS=zoi-auto,qwen2.5-coder:7b-instruct

# Features
ENABLE_RAG=true
ENABLE_WEB_SEARCH=false
ENABLE_IMAGE_GENERATION=false
```

**Model Access:**
- **zoi-auto** - Intelligent routing to best model
- **Qwen2.5-Coder** - Code-focused conversations
- **All LiteLLM Models** - Access to your entire model fleet

## 🔐 Authentication & Security

### Authentik Integration

Both services integrate with Authentik for SSO:

**n8n Authentication:**
- **Frontend Access** - Protected by Authentik forward auth
- **API/Webhook Access** - Direct access for automation
- **Role-Based Access** - Admin, Editor, Viewer roles

**OpenWebUI Authentication:**
- **Frontend Access** - Protected by Authentik forward auth
- **API Access** - Direct access for integrations
- **User Management** - Synced with Authentik users

### Security Features
- **Network Isolation** - Services communicate via secure networks
- **SSL Termination** - HTTPS via Traefik when configured
- **Access Control** - Role-based permissions
- **Audit Logging** - All actions logged and tracked

## 🔍 Troubleshooting

### Health Checks
```powershell
# Check all services
docker compose ps

# View service logs
docker compose logs n8n
docker compose logs openwebui

# Test service endpoints
curl http://localhost:7300/healthz  # n8n
curl http://localhost:7301/health   # OpenWebUI
```

### Common Issues

**n8n Database Connection Issues:**
```powershell
# Check PostgreSQL connection
docker exec -it n8n n8n info

# Verify database exists
docker exec -it postgres psql -U postgres -c "\l" | findstr n8n

# Check network connectivity
docker network inspect zoi-tools_database_network
```

**OpenWebUI LiteLLM Connection Issues:**
```powershell
# Test LiteLLM connection
curl http://litellm:4000/v1/models

# Check OpenWebUI logs
docker compose logs openwebui

# Verify environment variables
docker exec openwebui printenv | findstr OPENAI
```

**Authentik Authentication Issues:**
```powershell
# Check Authentik integration
curl http://authentik:9000/api/v3/core/applications/

# Verify forward auth middleware
curl -I http://n8n.zoi.local

# Check Traefik routing
curl http://traefik:8080/api/rawdata
```

## 📈 Performance & Resource Usage

### Resource Requirements

| Service | CPU | RAM | Storage | Notes |
|---------|-----|-----|---------|-------|
| n8n | 1 core | 1GB | 2GB | Scales with workflows |
| OpenWebUI | 0.5 core | 512MB | 1GB | Lightweight interface |

### Optimization Tips

1. **n8n Performance:**
   - Use database for workflow storage
   - Enable workflow caching
   - Optimize webhook endpoints
   - Monitor execution times

2. **OpenWebUI Performance:**
   - Configure model caching
   - Optimize chat history retention
   - Use efficient model routing
   - Monitor response times

## 🔗 Integration Examples

### n8n Workflow Examples

**AI Content Generation:**
```javascript
// Trigger: Webhook
// Action: Call LiteLLM API
// Output: Save to database/send notification
```

**Data Processing Pipeline:**
```javascript
// Trigger: Schedule (daily)
// Action: Fetch data from API
// Transform: Process with AI model
// Output: Store results in database
```

### OpenWebUI Integration

**Custom Model Configuration:**
```json
{
  "models": [
    {
      "name": "zoi-auto",
      "description": "Intelligent model routing"
    },
    {
      "name": "qwen2.5-coder:7b-instruct", 
      "description": "Code-focused AI assistant"
    }
  ]
}
```

## 🎯 Next Steps

1. **🔧 Configure Workflows**: Set up n8n workflows for your automation needs
2. **🤖 Customize AI Chat**: Configure OpenWebUI with your preferred models
3. **🔐 Setup Authentication**: Configure Authentik integration for SSO
4. **📊 Monitor Usage**: Track workflow executions and chat usage
5. **🚀 Scale Services**: Add more instances based on usage patterns

---

**🛠️ Your productivity and automation tools are ready to enhance your Zoi ecosystem!**
