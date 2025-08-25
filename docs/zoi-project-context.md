# 🌀 ZOI AI Ecosystem - Comprehensive Project Context

> **Complete knowledge base record for RAG system - Understanding the ZOI project architecture, vision, and current state**

## 🎯 Project Overview

**ZOI** is a **production-ready, self-hosted AI ecosystem** designed as an autonomous, self-evolving AI organism that grows its intelligence, capabilities, and resources without human bottlenecks.

### Core Vision
- **Autonomous AI Infrastructure** - Self-managing, self-improving AI ecosystem
- **Multi-Model Intelligence** - Unified access to 18+ AI models with intelligent routing
- **Knowledge-Driven Architecture** - RAG-enabled semantic search and document understanding
- **Visual Workflow Automation** - No-code AI automation with LangFlow and n8n
- **Enterprise-Grade Security** - Authentik SSO, Traefik reverse proxy, network isolation

## 🏗️ Architecture Overview

### Microservices Stack Organization
```
zoi/
├── apps/                    # Microservice stacks
│   ├── core/               # AI infrastructure (LiteLLM, vLLM, Ollama, Qdrant)
│   ├── platform/           # Base services (Traefik, Authentik, DBs)
│   ├── tools/              # Productivity (n8n, OpenWebUI, LobeChat)
│   ├── archon-mcp/         # Knowledge management with MCP
│   ├── voice/              # Real-time voice chat with TTS/STT
│   ├── coder/              # AI code assistant (Refact)
│   └── monitor/            # Observability (Grafana, Prometheus)
├── config/                 # Centralized configuration
├── scripts/               # Automation and utilities
├── docs/                  # Documentation
└── docker-compose.yml     # Root orchestrator
```

### Network Architecture
- **🌐 zoi-network** - Unified Docker network for secure inter-service communication
- **🔒 SSL Termination** - Traefik handles HTTPS and domain routing (`zoi.local`)
- **🛡️ Authentication** - Authentik provides SSO and OAuth2 flows
- **📊 Monitoring** - Comprehensive observability with Grafana and Prometheus

## 🤖 AI Infrastructure (Core Stack)

### Model Serving Architecture
- **LiteLLM Gateway** (Port 7010) - Unified API for 18+ models with intelligent routing
- **vLLM** (Port 7050) - High-performance inference (Qwen2.5-Coder-7B-Instruct)
- **Ollama** (Port 7040) - Local model serving (Qwen2.5-7B variants)
- **Auto-routing** - Cost-based routing between vLLM and Ollama based on query complexity

### Available Models (18 Total)
```yaml
Local Models:
  • zoi-thinker      → General reasoning (Qwen2.5-7B)
  • zoi-helper       → Assistant tasks (Qwen2.5-7B)  
  • zoi-coder-vllm   → Code generation (Qwen2.5-Coder-7B)
  • zoi-embed        → Embeddings (mxbai-embed-large)
  • zoi-rag-helper   → RAG assistance
  • zoi-rag-thinker  → RAG reasoning
  • zoi-auto         → Smart auto-routing
  • gpt-5-mini       → LobeChat compatibility alias
```

### Vector Database & Knowledge Management
- **Qdrant** (Port 7060) - Vector database with 8 specialized collections
- **PostgreSQL** - Shared embeddings table for cross-service knowledge
- **Neo4j** (Port 7061) - Graph database for structured reasoning
- **Unified RAG Service** (Port 7090) - Cross-collection search across all knowledge sources

## 📊 Knowledge Base Collections

### Qdrant Collections (8 Active)
1. **zoi_knowledge_base** - Primary knowledge repository
2. **code_embeddings** - Code snippets and documentation
3. **archon_knowledge** - AI agent knowledge base
4. **openwebui_conversations** - Chat history and context
5. **n8n_workflows** - Automation workflows
6. **lobechat_agents** - Agent configurations
7. **user_preferences** - User settings
8. **litellm_cache** - Cached LLM responses

### Cross-Database Integration
- **PostgreSQL shared.embeddings** - Cross-service vector storage
- **Neo4j graph_relationships** - Concept relationships and connections
- **Unified RAG Service** - 100% context access across all 10 collections

## 🛠️ Service Ecosystem

### Core AI Services (7000-7099)
- 7010: LiteLLM Gateway
- 7040: Ollama API
- 7050: vLLM Inference
- 7060: Qdrant Vector DB
- 7061: Neo4j Browser
- 7062: Neo4j Bolt
- 7063: PostgreSQL
- 7064: Redis
- 7070: LangFlow
- 7090: Unified RAG Service

### Platform Services (7200-7299)
- 7202: MongoDB
- 7208: Authentik Server
- 7209: Authentik HTTPS
- 7210: Traefik Dashboard
- 7211: Traefik API

### Productivity Tools (7300-7399)
- 7301: n8n Workflows
- 7302: LobeChat
- 7303: OpenWebUI

### Knowledge Management (7080-7089)
- 7080: Archon UI Dashboard
- 7081: Archon API Service
- 7082: Archon MCP Server
- 7083: Archon Agents

### Monitoring (7400-7499)
- 7400: Grafana Dashboard
- 7401: Prometheus Metrics

## 🔄 Recent Development Focus

### Current Implementation Status
- ✅ **Multi-model AI gateway** with intelligent routing
- ✅ **Vector database integration** with RAG capabilities
- ✅ **Cross-collection search** via unified RAG service
- ✅ **Real-time voice chat** with TTS/STT pipeline
- ✅ **Visual workflow automation** with LangFlow
- ✅ **Enterprise authentication** with Authentik SSO
- ✅ **Comprehensive monitoring** with Grafana dashboards

### Recent Major Updates
1. **Hybrid RAG Architecture** - LiteLLM native + custom unified RAG
2. **Voice Interface** - Real-time voice chat with MCP integration
3. **Refact AI Integration** - AI code assistant with IDE support
4. **Network Refactoring** - Unified zoi-network for all services
5. **Monitoring Enhancement** - Advanced Grafana dashboards for AI services

## 🎯 Technology Stack

### Core Technologies
- **Docker Compose** - Microservices orchestration
- **Python/FastAPI** - Backend services and APIs
- **PostgreSQL** - Primary database with pgvector extension
- **Redis** - Caching and session management
- **Traefik** - Reverse proxy and load balancer
- **Authentik** - Identity provider and SSO

### AI/ML Technologies
- **LiteLLM** - Multi-provider AI gateway
- **vLLM** - High-performance model inference
- **Ollama** - Local model serving
- **Qdrant** - Vector database for embeddings
- **Whisper** - Speech-to-text transcription
- **Coqui TTS** - Text-to-speech synthesis

### Automation & Workflows
- **LangFlow** - Visual AI workflow builder
- **n8n** - Workflow automation platform
- **MCP (Model Context Protocol)** - AI agent communication

## 🚀 Key Features & Capabilities

### AI Model Management
- **Intelligent Routing** - Automatic model selection based on query complexity
- **Cost Optimization** - Cost-based routing to minimize inference costs
- **Fallback Handling** - Robust error handling and model fallbacks
- **Function Calling** - Tool use and function calling capabilities

### Knowledge Management
- **RAG Integration** - Retrieval-augmented generation across all collections
- **Cross-Collection Search** - Unified search across 10 knowledge sources
- **Document Processing** - Automatic chunking and embedding of uploaded documents
- **Graph Relationships** - Neo4j for complex knowledge relationships

### User Interfaces
- **LobeChat** - Modern chat interface with plugin ecosystem
- **OpenWebUI** - Multi-model chat interface
- **Voice Interface** - Real-time voice chat with AI
- **Archon Dashboard** - Knowledge base management
- **Grafana Monitoring** - System observability and metrics

## 🔐 Security & Authentication

### Authentication Flow
- **Authentik SSO** - Centralized identity management
- **OAuth2/OIDC** - Standard authentication protocols
- **Role-Based Access** - Granular permission management
- **API Key Protection** - Secure API access with bearer tokens

### Network Security
- **Network Isolation** - Services communicate via secure Docker network
- **SSL Termination** - HTTPS encryption via Traefik
- **Reverse Proxy** - Traefik handles all external traffic
- **Service Discovery** - Automatic service registration and routing

## 📈 Performance & Scalability

### Hardware Requirements
- **16GB+ RAM** (32GB recommended)
- **NVIDIA GPU** (optional, for accelerated inference)
- **50GB+ Storage** (for models and data)
- **Docker & Docker Compose** (v2.20+)

### Performance Optimizations
- **GPU Acceleration** - NVIDIA GPU support for model inference
- **Caching Layers** - Redis for session management and response caching
- **Connection Pooling** - PostgreSQL connection pooling
- **Load Balancing** - Traefik load balancing across services

## 🎯 Use Cases & Applications

### Development & Coding
- **AI Code Assistant** - Refact integration with IDE support
- **Code Generation** - Specialized coding models (Qwen2.5-Coder)
- **Documentation** - Automatic code documentation and explanation
- **Code Review** - AI-powered code analysis and suggestions

### Knowledge Management
- **Document Q&A** - RAG-powered document question answering
- **Knowledge Base** - Centralized knowledge repository
- **Search & Discovery** - Semantic search across all content
- **Task Management** - Archon MCP for project and task management

### Automation & Workflows
- **Visual Workflows** - LangFlow for AI workflow creation
- **Process Automation** - n8n for business process automation
- **Voice Commands** - Voice-controlled AI actions via MCP
- **Monitoring & Alerts** - Automated system monitoring and alerting

This comprehensive context provides the foundation for understanding the ZOI AI ecosystem's architecture, capabilities, and current development state.
