# Refact.ai AI Coding Assistant - Zoi Integration

This directory contains the **Refact.ai** open-source AI coding assistant, integrated into the Zoi ecosystem for seamless AI-powered development.

## 🏗️ Architecture Overview

The Refact coder stack consists of four main components:

### 🐍 **Refact Server** (`refact-server/`)
- **Purpose**: Main AI inference server with web UI for model management
- **Tech Stack**: Python, FastAPI, PyTorch, Transformers
- **Database**: PostgreSQL (integrated with Zoi's shared database)
- **Features**: 
  - Self-hosted AI models (Qwen2.5-Coder, Llama3.1, etc.)
  - Fine-tuning capabilities
  - Model sharding and GPU optimization
  - Integration with LiteLLM for model routing

### 🦀 **Refact Agent** (`refact-agent/engine/`)
- **Purpose**: LSP server for IDE integration, maintains AST and vector indexes
- **Tech Stack**: Rust, Tree-sitter, SQLite, Vector embeddings
- **Features**:
  - Real-time code completion with RAG
  - AST parsing for multiple languages
  - Tool integration (Git, Docker, debuggers)
  - Chat with codebase understanding

### ⚛️ **Refact GUI** (`refact-agent/gui/`)
- **Purpose**: Modern React-based chat interface
- **Tech Stack**: React, TypeScript, Vite, GraphQL
- **Features**: Interactive chat, code highlighting, file management

### 📚 **Documentation** (`docs/`)
- **Purpose**: Astro-based documentation site
- **Tech Stack**: Astro, Starlight theme
- **Features**: Comprehensive documentation and guides

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- NVIDIA GPU with CUDA support (for AI inference)
- At least 8GB GPU memory recommended

### 1. Start the Zoi Ecosystem
```bash
# From the root zoi directory
docker compose up -d
```

This will start all services including:
- ✅ PostgreSQL database with `refact` database created
- ✅ Redis cache for session management
- ✅ LiteLLM for AI model routing
- ✅ Qdrant for vector embeddings
- ✅ Refact Server, Agent, GUI, and Documentation

### 2. Access the Services

| Service | URL | Purpose |
|---------|-----|---------|
| **Refact Server** | http://refact.zoi.local | Main AI server and model management |
| **Refact Chat** | http://refact-chat.zoi.local | Interactive chat interface |
| **Refact Agent** | http://refact-agent.zoi.local | LSP server for IDE integration |
| **Documentation** | http://refact-docs.zoi.local | Comprehensive guides and docs |

### 3. IDE Integration

#### VS Code
1. Install the [Refact.ai extension](https://marketplace.visualstudio.com/items?itemName=smallcloud.codify)
2. Configure the inference URL: `http://localhost:7401` (Refact Agent)
3. Set API key: `refact-admin-token-zoi-2024-secure`

#### JetBrains IDEs
1. Install the [Refact.ai plugin](https://plugins.jetbrains.com/plugin/20647-refact-ai)
2. Go to Settings > Tools > Refact.ai > Advanced
3. Set Inference URL: `http://localhost:7401`
4. Set API key: `refact-admin-token-zoi-2024-secure`

## 🔧 Configuration

### Environment Variables
Key configuration variables in `.env`:

```bash
# Refact Service Ports
REFACT_SERVER_PORT=7400    # Main server
REFACT_AGENT_PORT=7401     # LSP agent
REFACT_GUI_PORT=7402       # Chat interface
REFACT_DOCS_PORT=7403      # Documentation

# Authentication
REFACT_ADMIN_TOKEN=refact-admin-token-zoi-2024-secure
```

### Database Integration
- **Database**: PostgreSQL (shared with other Zoi services)
- **Schema**: Automatically created in `refact` database
- **Tables**: users, models, chat_sessions, code_completions, code_embeddings
- **Vector Search**: Integrated with pgvector for code similarity search

### LiteLLM Integration
Refact is configured to use Zoi's LiteLLM gateway for:
- Model routing and load balancing
- API key management
- Request logging and monitoring
- Cost tracking

## 🎯 Features

### Code Completion
- **Context-aware**: Uses RAG with codebase understanding
- **Multi-language**: Python, JavaScript, TypeScript, Rust, Java, etc.
- **Real-time**: Sub-second response times
- **Customizable**: Adjustable completion length and creativity

### Chat Interface
- **Codebase Chat**: Ask questions about your code
- **File Context**: Reference specific files with @file mentions
- **Tool Integration**: Execute commands, search code, debug issues
- **Memory**: Persistent chat history

### Model Management
- **Self-hosted Models**: Run models locally for privacy
- **Fine-tuning**: Customize models on your codebase
- **Model Switching**: Easy switching between different models
- **GPU Optimization**: Automatic model sharding and optimization

## 🔍 Monitoring

### Health Checks
All services include health checks accessible via:
- Refact Server: `http://localhost:7400/health`
- Refact Agent: `http://localhost:7401/health`
- Refact GUI: `http://localhost:7402/health`

### Logs
View service logs:
```bash
# All Refact services
docker compose logs -f refact-server refact-agent refact-gui

# Specific service
docker compose logs -f refact-server
```

### Database Monitoring
Access PostgreSQL monitoring:
```sql
-- Connect to refact database
\c refact

-- View active sessions
SELECT * FROM monitoring.active_connections;

-- Check database health
SELECT * FROM monitoring.health_check();
```

## 🛠️ Development

### Building from Source
```bash
# Build all services
docker compose build

# Build specific service
docker compose build refact-server
```

### Local Development
For local development without Docker:

#### Refact Server
```bash
cd refact-server
pip install -e .
python -m self_hosting_machinery.watchdog.docker_watchdog
```

#### Refact Agent
```bash
cd refact-agent/engine
cargo build --release
./target/release/refact-lsp --http-port 8001
```

#### GUI
```bash
cd refact-agent/gui
npm install
npm run dev
```

## 🔐 Security

- **API Keys**: Secure token-based authentication
- **Network**: Services communicate over internal Docker network
- **Database**: Encrypted connections with PostgreSQL
- **HTTPS**: Traefik handles SSL termination (in production)

## 📊 Performance

### Resource Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ system memory
- **GPU**: 8GB+ VRAM for local model inference
- **Storage**: 50GB+ for models and data

### Optimization Tips
- Use GPU acceleration for model inference
- Enable Redis caching for better response times
- Configure model sharding for large models
- Use SSD storage for better I/O performance

## 🆘 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
docker compose ps

# View logs
docker compose logs refact-server

# Restart service
docker compose restart refact-server
```

#### Database Connection Issues
```bash
# Check PostgreSQL connectivity
docker compose exec refact-server pg_isready -h postgres -p 5432

# Verify database exists
docker compose exec postgres psql -U postgres -l
```

#### GPU Not Detected
```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi

# Verify GPU access in container
docker compose exec refact-server nvidia-smi
```

## 📚 Additional Resources

- [Refact.ai Official Documentation](https://docs.refact.ai/)
- [Zoi Ecosystem Overview](../../README.md)
- [LiteLLM Integration Guide](../core/README.md)
- [PostgreSQL Configuration](../../config/postgres/README.md)

## 🤝 Contributing

Contributions are welcome! Please see:
- [Refact Contributing Guide](./CONTRIBUTING.md)
- [Zoi Development Guidelines](../../docs/development.md)

## 📄 License

This integration maintains the original Refact.ai BSD-3-Clause license. See [LICENSE](./LICENSE) for details.
