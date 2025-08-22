# 🏛️ Archon MCP Integration Guide

## 🎯 Overview

Your LiteLLM proxy is now configured to use **Archon** as an MCP (Model Context Protocol) server, providing your AI models with access to:

- **📚 Knowledge Base**: Document search and retrieval
- **📋 Task Management**: Create, update, and track tasks
- **🔍 Smart Search**: Advanced RAG capabilities
- **🌐 Web Crawling**: Add new content to knowledge base

## 🔧 Configuration Summary

### MCP Server Configuration
```yaml
# In litellm-config.yaml
mcp_servers:
  archon_mcp_server:
    url: "http://archon-mcp:8051"
    transport: "http"
    description: "Archon knowledge base, document search, and task management"
    auth_type: "none"
    spec_version: "2025-03-26"
```

### Available Aliases
- `archon` → `archon_mcp_server`
- `knowledge` → `archon_mcp_server`
- `tasks` → `archon_mcp_server`
- `docs` → `archon_mcp_server`

## 🚀 Quick Start

### 1. Start Both Services
```bash
# Start Archon
cd apps/Archon
docker-compose up -d

# Start LiteLLM Stack
cd apps/llm-local
docker-compose up -d
```

### 2. Connect Networks
```powershell
# Run the integration setup script
cd apps/llm-local
./setup-archon-integration.ps1
```

### 3. Test Integration
```bash
# Test the MCP connection
cd apps/llm-local
python test-archon-mcp.py
```

## 💡 Usage Examples

### Using OpenAI SDK with LiteLLM Proxy

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-wqn0xwq_vha4MVM2yzw",
    base_url="http://localhost:7010"
)

# Knowledge search example
response = client.chat.completions.create(
    model="zoi-auto",  # Uses intelligent routing
    messages=[
        {"role": "user", "content": "Search my knowledge base for API documentation"}
    ],
    tools=[{
        "type": "mcp",
        "server_label": "archon",
        "server_url": "http://archon-mcp:8051"
    }]
)

# Task management example
response = client.chat.completions.create(
    model="zoi-auto",
    messages=[
        {"role": "user", "content": "Create a task to implement user authentication"}
    ],
    tools=[{
        "type": "mcp",
        "server_label": "knowledge",
        "server_url": "http://archon-mcp:8051"
    }]
)
```

### Using cURL

```bash
# Knowledge search
curl -X POST "http://localhost:7010/v1/chat/completions" \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zoi-auto",
    "messages": [
      {"role": "user", "content": "What documentation do we have about database schemas?"}
    ],
    "tools": [{
      "type": "mcp",
      "server_label": "docs",
      "server_url": "http://archon-mcp:8051"
    }]
  }'

# Task creation
curl -X POST "http://localhost:7010/v1/chat/completions" \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zoi-auto",
    "messages": [
      {"role": "user", "content": "Create a task to optimize database queries"}
    ],
    "tools": [{
      "type": "mcp",
      "server_label": "tasks",
      "server_url": "http://archon-mcp:8051"
    }]
  }'
```

## 🔍 Available MCP Tools

Based on Archon's capabilities, the following tools should be available:

### 📚 Knowledge Management
- `search_documents` - Search through uploaded documents
- `get_document_content` - Retrieve specific document content
- `add_document` - Add new documents to knowledge base

### 📋 Task Management
- `create_task` - Create new tasks
- `update_task` - Update existing tasks
- `get_task_context` - Retrieve task information
- `list_tasks` - List all tasks with filters

### 🌐 Web Integration
- `crawl_website` - Add web content to knowledge base
- `search_web_content` - Search crawled web content

## 💰 Cost Tracking

Configured costs for Archon MCP operations:
- Default: $0.001 per query
- Document search: $0.002 per query
- Task operations: $0.001 per query
- Web crawling: $0.005 per query

## 🔗 Service URLs

- **Archon UI**: http://localhost:3737
- **Archon MCP Server**: http://localhost:8051
- **Archon API Server**: http://localhost:8181
- **LiteLLM Proxy**: http://localhost:7010

## 🛠️ Troubleshooting

### Check Service Health
```bash
# Archon MCP Server
curl http://localhost:8051/health

# LiteLLM Proxy
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/health

# Archon Main Server
curl http://localhost:8181/health
```

### Check Docker Networks
```bash
# List networks
docker network ls

# Check container connections
docker network inspect zoi-llm_ai
docker network inspect archon_app-network
```

### Restart Services
```bash
# Restart LiteLLM to pick up config changes
cd apps/llm-local
docker-compose restart litellm

# Restart Archon services
cd apps/Archon
docker-compose restart
```

## 🎯 Integration Benefits

1. **🧠 Enhanced AI Context**: Your models now have access to your knowledge base
2. **📋 Task Automation**: AI can help create and manage tasks
3. **🔍 Smart Search**: Advanced RAG capabilities for better responses
4. **🔄 Real-time Updates**: Knowledge base stays current with new content
5. **💰 Cost Control**: Track MCP operation costs
6. **🛡️ Centralized Management**: All through your LiteLLM proxy

## 📚 Next Steps

1. **Add Content**: Upload documents to Archon's knowledge base
2. **Create Tasks**: Start using AI-assisted task management
3. **Test Integration**: Run the test script to verify everything works
4. **Scale Usage**: Integrate with your existing applications
5. **Monitor Costs**: Track MCP usage through LiteLLM analytics

---

**🎉 Your AI models now have access to persistent knowledge and task management through Archon MCP!**