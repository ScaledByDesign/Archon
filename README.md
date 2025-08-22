# 🌀 Zoi AI Ecosystem

> **A comprehensive, self-hosted AI infrastructure with intelligent model routing, vector storage, workflow automation, and knowledge management.**

[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docker.com)
[![AI Models](https://img.shields.io/badge/AI-18%20Models-green?logo=openai)](http://localhost:7010)
[![Vector DB](https://img.shields.io/badge/Vector-Qdrant-purple?logo=qdrant)](http://localhost:7060)
[![Workflows](https://img.shields.io/badge/Workflows-LangFlow-orange?logo=langflow)](http://localhost:7070)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quick Start](#-quick-start)
- [🌐 Service Directory](#-service-directory)
- [🤖 AI Models & Capabilities](#-ai-models--capabilities)
- [📁 Project Structure](#-project-structure)
- [🔧 Configuration](#-configuration)
- [🚦 Management Commands](#-management-commands)
- [🔍 Monitoring & Health](#-monitoring--health)
- [🎯 Use Cases](#-use-cases)
- [🔧 Advanced Configuration](#-advanced-configuration)
- [🚨 Troubleshooting](#-troubleshooting)
- [📊 Performance Metrics](#-performance-metrics)
- [🔐 Security](#-security)
- [🚀 Production Deployment](#-production-deployment)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [🙏 Acknowledgments](#-acknowledgments)

## 🎯 Overview

Zoi is a production-ready, self-hosted AI ecosystem that provides:

- **🤖 Multi-Model AI Gateway** - Unified API for 18+ AI models with intelligent routing
- **🧠 Vector Knowledge Base** - RAG-enabled semantic search and document understanding  
- **🔄 Visual Workflows** - No-code AI automation with LangFlow and n8n
- **💬 Modern Chat Interfaces** - OpenWebUI and LobeChat with multi-model support
- **📊 Knowledge Management** - Archon MCP for structured knowledge and task management
- **🔐 Enterprise Security** - Authentik SSO, Traefik reverse proxy, and network isolation

## 🏗️ Architecture

### Microservices Stack
```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│   🌀 CORE       │  🏢 PLATFORM    │   🛠️ TOOLS      │  📚 KNOWLEDGE   │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ • LiteLLM       │ • Traefik       │ • n8n           │ • Archon MCP    │
│ • vLLM          │ • Authentik     │ • OpenWebUI     │ • Neo4j         │
│ • Ollama        │ • PostgreSQL    │ • LobeChat      │ • Vector Store  │
│ • Qdrant        │ • Redis         │                 │                 │
│ • LangFlow      │ • MongoDB       │                 │                 │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

### Network Architecture
- **🌐 zoi-network** - Unified Docker network for secure inter-service communication
- **🔒 SSL Termination** - Traefik handles HTTPS and domain routing
- **🛡️ Authentication** - Authentik provides SSO and OAuth2 flows
- **📊 Monitoring** - Comprehensive observability with Grafana and Prometheus

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (v2.20+)
- **16GB+ RAM** (32GB recommended for optimal performance)
- **NVIDIA GPU** (optional, for accelerated inference)
- **50GB+ Storage** (for models and data)

### 1. Clone & Setup
```bash
git clone https://github.com/ScaledByDesign/zoi.git
cd zoi
cp .env.example .env
# Edit .env with your configuration
```

### 2. Bootstrap System
```bash
# Automated bootstrap (recommended)
make bootstrap

# Or manual startup
make start
```

### 3. Access Services
```bash
# Core AI Services
open http://localhost:7010  # LiteLLM API Gateway
open http://localhost:7070  # LangFlow Workflows
open http://localhost:7060  # Qdrant Vector DB

# Chat Interfaces  
open http://localhost:7301  # OpenWebUI
open http://localhost:7302  # LobeChat

# Knowledge Management
open http://localhost:7080  # Archon MCP
```

## 🌐 Service Directory

### 🌀 Core AI Services
| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **LiteLLM Gateway** | 7010 | http://localhost:7010 | Unified AI API with 18+ models |
| **vLLM Inference** | 7050 | http://localhost:7050 | High-performance model serving |
| **Ollama API** | 7040 | http://localhost:7040 | Local model management |
| **Qdrant Vector DB** | 7060 | http://localhost:7060 | Vector storage & semantic search |
| **LangFlow Builder** | 7070 | http://localhost:7070 | Visual AI workflow automation |
| **Neo4j Graph DB** | 7061 | http://localhost:7061 | Knowledge graph & reasoning |

### 🏢 Platform Services
| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Traefik Dashboard** | 8080 | http://localhost:8080 | Reverse proxy & load balancer |
| **Authentik SSO** | 7208 | http://localhost:7208 | Authentication & identity |
| **PostgreSQL** | 7063 | localhost:7063 | Primary database |
| **Redis Cache** | 7064 | localhost:7064 | Caching & sessions |
| **MongoDB** | 7202 | localhost:7202 | Document storage |

### 🛠️ Productivity Tools
| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **n8n Workflows** | 7300 | http://localhost:7300 | Automation & integrations |
| **OpenWebUI** | 7301 | http://localhost:7301 | Modern AI chat interface |
| **LobeChat** | 7302 | http://localhost:7302 | Advanced AI chat with plugins |

### 📚 Knowledge Management
| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Archon UI** | 7080 | http://localhost:7080 | Knowledge base dashboard |
| **Archon API** | 7081 | http://localhost:7081 | Backend API service |
| **Archon MCP** | 7082 | http://localhost:7082 | Model Context Protocol |
| **Archon Agents** | 7083 | http://localhost:7083 | AI processing service |

## 🤖 AI Models & Capabilities

### Available Models (18 Total)
```yaml
Local Models:
  • zoi-thinker      → General reasoning (Qwen2.5-7B)
  • zoi-helper       → Assistant tasks (Qwen2.5-7B)  
  • zoi-coder-vllm   → Code generation (Qwen2.5-Coder-7B)
  • zoi-embed        → Embeddings (mxbai-embed-large)
  • zoi-rag-helper   → RAG assistance
  • zoi-rag-thinker  → RAG reasoning

API Compatible:
  • gpt-3.5-turbo, gpt-4, gpt-4o-mini
  • claude-3-5-sonnet, claude-3-opus, claude-3-haiku
  • Auto-routing with zoi:auto
```

### Smart Features
- **🎯 Auto-Routing** - Intelligent model selection based on query type
- **🧠 RAG Integration** - Context-aware responses with vector search
- **💾 Response Caching** - Redis-based caching for performance
- **📊 Usage Tracking** - Comprehensive analytics and cost monitoring
- **🔄 Load Balancing** - Automatic failover and scaling

## 📁 Project Structure

```
zoi/
├── 📁 apps/                    # Service stacks
│   ├── 🌀 core/               # AI infrastructure
│   ├── 🏢 platform/           # Base services  
│   ├── 🛠️ tools/              # Productivity apps
│   ├── 📚 archon-mcp/         # Knowledge management
│   └── 📊 monitor/            # Observability
├── 📁 config/                 # Centralized configuration
│   ├── 🤖 litellm/           # AI gateway config
│   ├── 🗄️ qdrant/            # Vector DB config
│   ├── 🔐 authentik/         # Auth config
│   └── 🌐 traefik/           # Proxy config
├── 📁 scripts/               # Automation scripts
├── 📁 docs/                  # Documentation
├── 🐳 docker-compose.yml     # Stack orchestrator
├── ⚙️ .env                   # Environment config
└── 📋 Makefile              # Build automation
```

## 🔧 Configuration

### Environment Variables
Key settings in `.env`:
```bash
# AI Configuration
LITELLM_MASTER_KEY="your-api-key"
OLLAMA_PORT=7040
QDRANT_PORT=7060
LANGFLOW_PORT=7070

# Database Settings  
POSTGRES_PASSWORD="secure-password"
REDIS_PASSWORD="redis-password"

# Domain Configuration
DOMAIN=zoi.local
```

### Model Configuration
Models are configured in `config/litellm/config.yaml`:
- Model routing rules
- Performance settings
- Vector store integration
- Caching policies

## 🚦 Management Commands

```bash
# System Management
make bootstrap    # Complete system setup
make start       # Start all services
make stop        # Stop all services  
make restart     # Restart all services
make status      # Check service health

# Stack Management
make start-core      # Start AI services
make start-platform  # Start infrastructure
make start-tools     # Start productivity apps
make start-archon    # Start knowledge management

# Maintenance
make logs        # View all logs
make clean       # Clean up containers
make update      # Update all images
```

## 🔍 Monitoring & Health

### Health Checks
- **Service Status**: `make status`
- **API Health**: http://localhost:7010/health
- **Vector DB**: http://localhost:7060/dashboard
- **Traefik Dashboard**: http://localhost:8080

### Logs & Debugging
```bash
# View logs for specific services
docker compose logs -f litellm
docker compose logs -f qdrant
docker compose logs -f langflow

# System-wide logs
make logs
```

## 🎯 Use Cases

### 🤖 AI Development
- **Multi-Model Testing** - Compare responses across different AI models
- **RAG Applications** - Build context-aware AI applications
- **Workflow Automation** - Create complex AI pipelines with LangFlow
- **API Integration** - OpenAI-compatible API for existing applications

### 📚 Knowledge Management
- **Document Processing** - Intelligent document analysis and extraction
- **Semantic Search** - Find information by meaning, not just keywords
- **Knowledge Graphs** - Build structured knowledge representations
- **Task Management** - AI-powered project and task organization

### 🏢 Enterprise Applications
- **Internal ChatGPT** - Private AI assistant for your organization
- **Process Automation** - Streamline workflows with n8n integration
- **Data Analysis** - AI-powered insights from your data
- **Content Generation** - Automated content creation and editing

## 🔧 Advanced Configuration

### GPU Acceleration
For NVIDIA GPU support, ensure Docker has GPU access:
```bash
# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Custom Models
Add your own models to `config/litellm/config.yaml`:
```yaml
model_list:
  - model_name: my-custom-model
    litellm_params:
      model: ollama/my-model:latest
      api_base: http://ollama:11434
```

### Domain Configuration
For custom domains, update `/etc/hosts`:
```bash
127.0.0.1 zoi.local
127.0.0.1 auth.zoi.local
127.0.0.1 traefik.zoi.local
127.0.0.1 llm.zoi.local
127.0.0.1 chat.zoi.local
```

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Verify network exists
docker network ls | grep zoi-network

# Check port conflicts
netstat -tulpn | grep :7010
```

#### Out of Memory
```bash
# Check system resources
docker stats

# Reduce model concurrency in config/litellm/config.yaml
# Increase Docker memory limits
```

#### GPU Not Detected
```bash
# Verify GPU access
nvidia-smi
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi
```

### Performance Tuning

#### Database Optimization
```sql
-- PostgreSQL tuning for AI workloads
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '8GB';
ALTER SYSTEM SET work_mem = '256MB';
SELECT pg_reload_conf();
```

#### Vector Database Tuning
```yaml
# config/qdrant/config.yaml
storage:
  performance:
    max_search_threads: 8
    max_optimization_threads: 4
```

## 📊 Performance Metrics

### Typical Performance
- **Response Time**: 200-2000ms (depending on model)
- **Throughput**: 10-50 requests/second
- **Memory Usage**: 8-16GB (with models loaded)
- **Storage**: 20-50GB (models + data)

### Scaling Recommendations
- **Small Team (1-10 users)**: 16GB RAM, 4 CPU cores
- **Medium Team (10-50 users)**: 32GB RAM, 8 CPU cores, GPU
- **Large Team (50+ users)**: 64GB RAM, 16 CPU cores, Multiple GPUs

## 🔐 Security

### Authentication & Authorization
- **Authentik SSO** - Enterprise-grade identity provider
- **OAuth2/OIDC** - Standard authentication protocols
- **Role-Based Access** - Granular permission control
- **API Key Management** - Secure API access tokens

### Network Security
- **Docker Network Isolation** - Services communicate via private networks
- **Traefik SSL Termination** - HTTPS encryption for all services
- **Internal Service Communication** - No external exposure of internal APIs
- **Firewall Ready** - Easy to configure with iptables/ufw

### Data Protection
- **Encrypted Storage** - Database encryption at rest
- **Secure Secrets** - Environment-based secret management
- **Audit Logging** - Comprehensive access and activity logs
- **Backup Strategy** - Automated backup procedures

## 🚀 Production Deployment

### Infrastructure Requirements
```yaml
Minimum Production Setup:
  CPU: 8 cores (16 recommended)
  RAM: 32GB (64GB recommended)
  Storage: 500GB SSD (1TB recommended)
  Network: 1Gbps connection
  GPU: NVIDIA RTX 4090 or better (optional)
```

### Deployment Checklist
- [ ] **Security Hardening** - Change default passwords, enable SSL
- [ ] **Backup Strategy** - Configure automated backups
- [ ] **Monitoring Setup** - Deploy Grafana/Prometheus stack
- [ ] **Load Testing** - Verify performance under load
- [ ] **Disaster Recovery** - Document recovery procedures
- [ ] **Update Strategy** - Plan for rolling updates

### High Availability Setup
```bash
# Multi-node deployment with Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.prod.yml zoi

# Or with Kubernetes
kubectl apply -f k8s/
```

## 🤝 Contributing

### Development Setup
```bash
# Clone with development branch
git clone -b develop https://github.com/ScaledByDesign/zoi.git
cd zoi

# Install development dependencies
pip install -r requirements-dev.txt
npm install -g @commitlint/cli @commitlint/config-conventional

# Run tests
make test
```

### Contribution Guidelines
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'feat: add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards
- **Python**: Black formatting, type hints, docstrings
- **JavaScript**: ESLint, Prettier formatting
- **Docker**: Multi-stage builds, security scanning
- **Documentation**: Clear README files for all components

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with amazing open-source projects:
- [LiteLLM](https://github.com/BerriAI/litellm) - AI Gateway
- [Qdrant](https://github.com/qdrant/qdrant) - Vector Database
- [LangFlow](https://github.com/langflow-ai/langflow) - Visual Workflows
- [Traefik](https://github.com/traefik/traefik) - Reverse Proxy
- [Authentik](https://github.com/goauthentik/authentik) - Authentication

---

**🌟 Star this repo if you find it useful!**

For detailed documentation, visit our [docs](./docs/) directory or check individual service READMEs in the `apps/` folder.
