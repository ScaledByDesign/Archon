# 🌀 Zoi LLM Stack (Local AI Infrastructure)

A comprehensive local AI stack with intelligent model routing, vector storage, and workflow automation.

## 🏗️ Architecture

### Core Services
- **LiteLLM** → Unified API gateway with intelligent routing (Host Network Mode)
- **LLM Studio (RTX 5070 Ti)** → High-speed inference for coding tasks (Qwen 14B)
- **LLM Studio (RTX 3090)** → Advanced reasoning & embeddings (Qwen 30B + NOMIC)
- **Weaviate** → Vector database for RAG and embeddings
- **Elysia** → Agentic platform for Weaviate data analysis
- **LangFlow** → Visual AI workflow builder
- **Neo4j** → Graph database for structured reasoning
- **Archon** → AI knowledge base and task management with MCP integration

### Supporting Infrastructure
- **PostgreSQL** → Persistence for LiteLLM, LangFlow, and Neo4j
- **Redis** → Caching and session management

## 🌐 Service Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| **LiteLLM API** | http://localhost:7010/v1 | Main API gateway (Host Network) |
| **RTX 5070 Ti** | http://192.168.8.135:1234/v1 | High-speed coding inference (Qwen 14B) |
| **RTX 3090** | http://192.168.8.241:1234/v1 | Advanced reasoning (Qwen 30B + NOMIC) |
| **Weaviate** | http://localhost:7080 | Vector database & collections |
| **Elysia** | http://localhost:7085 | Agentic analysis platform |
| Neo4j Browser | http://localhost:7061 | Graph database UI |
| Neo4j Bolt | bolt://localhost:7062 | Graph database API |
| PostgreSQL | localhost:7063 | Database |
| Redis | localhost:7064 | Cache |
| LangFlow | http://localhost:7070 | Workflow builder |

### Traefik Domain Routing

When using with the platform Traefik proxy, services are also available via domain routing:

| Service | Domain URL | Purpose |
|---------|------------|---------|
| **LiteLLM API** | http://litellm.zoi.local | Main API gateway |
| **Ollama API** | http://ollama.zoi.local | Local model API |
| **vLLM API** | http://vllm.zoi.local | High-performance inference |
| **Qdrant** | http://qdrant.zoi.local | Vector database UI |
| **Neo4j Browser** | http://neo4j.zoi.local | Graph database UI |
| **LangFlow** | http://langflow.zoi.local | Workflow builder |
| Archon UI | http://localhost:7080 | Knowledge base & task management |
| Archon API | http://localhost:7081 | Archon backend API |
| Archon MCP | http://localhost:7082 | Model Context Protocol server |
| Archon Agents | http://localhost:7083 | ML/Reranking service |

## 🚀 Quick Start

### 1. Start the Stack
```powershell
docker compose up -d
```

### 2. Pull Required Models
```powershell
# Pull the helper model for Ollama
docker exec -it ollama bash -lc "ollama pull qwen2.5-coder:7b-instruct"
```

### 3. Verify Services
```powershell
# Check LiteLLM health
curl http://localhost:7010/health

# Check available models
curl http://localhost:7010/v1/models

# Check Ollama models
curl http://localhost:7040/api/tags

# Check vLLM models
curl http://localhost:7030/v1/models
```

## 🤖 Model Usage

### Available Models

| Model Name | GPU Hardware | Use Case | Performance |
|------------|--------------|----------|-------------|
| **`zoi-coder`** | RTX 5070 Ti | Fast coding & development | High Speed |
| **`zoi-planner`** | RTX 3090 | Complex reasoning & analysis | Maximum Power |
| **`zoi-embed`** | RTX 3090 | Vector embeddings | Specialized |
| **`gpt-3.5-turbo`** | RTX 5070 Ti (alias) | OpenAI API compatibility | High Speed |
| **`gpt-4`** | RTX 3090 (alias) | OpenAI API compatibility | Maximum Power |

#### Hardware Specifications
- **RTX 5070 Ti (ioz.zoi.local)**: Qwen/Qwen3-14B optimized for speed
- **RTX 3090 (astra.zoi.local)**: Qwen/Qwen3-Coder-30B + NOMIC embeddings

### Example API Calls

#### Direct Model Access
```bash
# Use RTX 3090 for complex reasoning and analysis
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zoi-planner",
    "messages": [{"role": "user", "content": "Design a microservices architecture for an e-commerce platform"}],
    "temperature": 0.1,
    "max_tokens": 4096
  }'

# Use RTX 5070 Ti for fast coding tasks
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zoi-coder",
    "messages": [{"role": "user", "content": "Fix this Python syntax error and explain the solution"}],
    "temperature": 0.2,
    "max_tokens": 2048
  }'

# Use embeddings model for vector operations
curl -X POST http://localhost:7010/v1/embeddings \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zoi-embed",
    "input": ["Document text to embed", "Another document"]
  }'
```

#### OpenAI API Compatibility
```bash
# Use familiar OpenAI model names (automatically routed)
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Analyze this complex algorithm"}]
  }'
```

## 🏛️ Archon Integration (Knowledge Base & Task Management)

Archon provides persistent memory and task management capabilities to your AI models through the Model Context Protocol (MCP).

### 🎯 What is Archon?

Archon is a **command center for AI coding assistants** that serves as an **MCP server**, providing:

- **📚 Knowledge Management**: Document storage, search, and retrieval
- **📋 Task Management**: Create, update, and track tasks with AI assistance
- **🔍 Smart Search**: Advanced RAG with contextual embeddings and reranking
- **🌐 Web Integration**: Crawl websites and add content to knowledge base
- **🤖 AI Enhancement**: Persistent memory for your AI conversations

### 🛠️ Archon MCP Toolset

Your AI models now have access to these tools through the MCP integration:

#### 📚 Knowledge Management Tools
- **`search_documents`** - Search through uploaded documents and knowledge base
- **`add_document`** - Add new documents to the knowledge base
- **`get_document_content`** - Retrieve specific document content
- **`upload_file`** - Upload files for processing and indexing

#### 📋 Task Management Tools
- **`create_task`** - Create new tasks with descriptions and priorities
- **`update_task`** - Update existing task details and status
- **`get_task_context`** - Retrieve task information and context
- **`list_tasks`** - List all tasks with filtering options

#### 🔍 Search & Discovery Tools
- **`list_tools`** - List all available MCP tools
- **`semantic_search`** - Perform semantic search across knowledge base
- **`hybrid_search`** - Use both keyword and semantic search

#### 🌐 Web Integration Tools
- **`crawl_website`** - Crawl websites and add content to knowledge base
- **`search_web_content`** - Search through crawled web content

### 🚀 Using Archon with Your AI Models

#### Example: Task Management
```bash
# Create a task using AI
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zoi-auto",
    "messages": [
      {"role": "user", "content": "Create a task to implement user authentication with JWT tokens"}
    ],
    "tools": [{
      "type": "mcp",
      "server_label": "archon",
      "server_url": "http://archon-mcp:7082"
    }]
  }'
```

#### Example: Knowledge Search
```bash
# Search your knowledge base
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zoi-auto",
    "messages": [
      {"role": "user", "content": "Search my knowledge base for information about API authentication patterns"}
    ],
    "tools": [{
      "type": "mcp",
      "server_label": "knowledge",
      "server_url": "http://archon-mcp:7082"
    }]
  }'
```

#### Example: Web Content Integration
```bash
# Add web content to knowledge base
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zoi-auto",
    "messages": [
      {"role": "user", "content": "Crawl the FastAPI documentation and add it to my knowledge base"}
    ],
    "tools": [{
      "type": "mcp",
      "server_label": "docs",
      "server_url": "http://archon-mcp:7082"
    }]
  }'
```

### 🔧 Archon Configuration

Archon is configured to use your local infrastructure:

- **Database**: Uses your local PostgreSQL (`archon` database)
- **AI Models**: Routes through your LiteLLM proxy with `zoi-auto` model
- **Embeddings**: Uses `text-embedding-3-small` for document indexing
- **Network**: Connected to your LiteLLM network for seamless integration

### 📊 MCP Aliases

For convenience, these aliases are configured in LiteLLM:

- `archon` → Full Archon MCP server access
- `knowledge` → Knowledge management focus
- `tasks` → Task management focus
- `docs` → Document and web content focus

### 💰 Cost Tracking

MCP operations are tracked with these costs:
- Default operations: $0.001 per query
- Document search: $0.002 per query
- Web crawling: $0.005 per query
- Task operations: $0.001 per query

## 🔧 Setup & Configuration

### Prerequisites
- Docker and Docker Compose
- At least 16GB RAM (recommended)
- NVIDIA GPU (optional, for vLLM acceleration)

### Initial Setup
1. **Start the core stack**:
   ```powershell
   docker compose up -d
   ```

2. **Pull required models**:
   ```powershell
   # Pull Ollama model
   docker exec -it ollama bash -lc "ollama pull qwen2.5-coder:7b-instruct"
   ```

3. **Start Archon** (if not already running):
   ```powershell
   # Navigate to Archon directory and start
   cd ../archon-mcp
   docker-compose up -d
   ```

4. **Verify integration**:
   ```powershell
   # Test LiteLLM with Archon MCP
   curl -X POST http://localhost:7010/v1/chat/completions \
     -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "zoi-auto",
       "messages": [{"role": "user", "content": "List available tools"}],
       "tools": [{"type": "mcp", "server_label": "archon", "server_url": "http://archon-mcp:7082"}]
     }'
   ```

### 🔍 Troubleshooting

#### Service Health Checks
```powershell
# Check all services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check LiteLLM health
curl http://localhost:7010/health

# Test RTX GPU connectivity
curl -X POST http://192.168.8.135:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen3-14b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'

curl -X POST http://192.168.8.241:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen3-coder-30b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'

# Test LiteLLM model routing
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{"model": "zoi-coder", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'

# Check Weaviate collections
curl http://localhost:7080/v1/meta

# Check Elysia health
curl http://localhost:7085/api/health
```

#### Common Issues

**Archon not connecting to PostgreSQL**:
- Ensure PostgreSQL is running: `docker ps --filter name=postgres`
- Check database exists: `docker exec -i postgres psql -U postgres -c "\l"`

**MCP tools not available**:
- Verify Archon MCP is healthy: `docker logs Archon-MCP --tail 10`
- Check network connectivity: `docker network inspect zoi-llm_ai`
- Restart LiteLLM: `docker-compose restart litellm`

**Models not loading**:
- Check vLLM logs: `docker logs vllm --tail 20`
- Verify Ollama models: `curl http://localhost:7040/api/tags`
- Check GPU availability: `nvidia-smi` (if using GPU)

## 📈 Performance & Scaling

### Resource Requirements

| Service | CPU | RAM | Storage | GPU |
|---------|-----|-----|---------|-----|
| LiteLLM | 1 core | 1GB | 1GB | No |
| vLLM | 4+ cores | 8GB | 10GB | Optional |
| Ollama | 2+ cores | 4GB | 5GB | No |
| Archon | 2 cores | 2GB | 2GB | No |
| PostgreSQL | 1 core | 1GB | 5GB | No |
| Qdrant | 1 core | 2GB | 10GB | No |

### Optimization Tips

1. **Use GPU acceleration** for vLLM when available
2. **Increase PostgreSQL shared_buffers** for better database performance
3. **Configure Redis memory limits** based on your caching needs
4. **Monitor Qdrant vector storage** and optimize collection settings
5. **Use Archon's hybrid search** for better knowledge retrieval performance

## 🎯 Next Steps

1. **📚 Build your knowledge base**: Upload documents through Archon UI
2. **📋 Create your first tasks**: Use AI to help manage your projects
3. **🔗 Integrate with your tools**: Connect external APIs through MCP
4. **📊 Monitor usage**: Track costs and performance through LiteLLM analytics
5. **🚀 Scale up**: Add more models and services as needed

---

## 🌐 Traefik Integration

The LLM stack is configured with Traefik labels for seamless reverse proxy integration with the platform stack.

### Domain Access
When running with the platform Traefik proxy, services are accessible via clean domain names:

```bash
# API Access
curl http://litellm.zoi.local/v1/models
curl http://ollama.zoi.local/api/tags
curl http://vllm.zoi.local/v1/models

# Web Interfaces
open http://langflow.zoi.local    # Workflow builder
open http://qdrant.zoi.local      # Vector database
open http://neo4j.zoi.local       # Graph database
```

### Network Configuration
- **Internal Network**: `zoi-llm_ai` for service-to-service communication
- **Traefik Integration**: Automatic service discovery via Docker labels
- **Load Balancing**: Built-in health checks and failover

### SSL/TLS Support
When Traefik is configured with SSL certificates:
- All services automatically get HTTPS endpoints
- Automatic HTTP to HTTPS redirects
- Let's Encrypt integration for production deployments

---

**🎉 Your local AI infrastructure with persistent memory and task management is ready!**
