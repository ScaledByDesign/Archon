# Zoi Project - Crush Agent Configuration

## Frequently Used Commands

### Docker & Services
```bash
# Start Ollama service
cd apps/llm-local && docker-compose up -d ollama

# Check running containers
docker ps

# View Ollama logs
docker logs ollama

# Stop all services
docker-compose down
```

### Development
```bash
# Test Crush with local models
crush run "test message"

# Interactive mode
crush -d

# View Crush logs
crush logs --tail 100
crush logs --follow
```

### System Commands
```bash
# Check WSL2 status
wsl --list --verbose

# Navigate to project
cd /mnt/d/zoi

# Check Ollama API
curl -s http://localhost:7040/v1/models
```

## Project Structure

- **apps/llm-local/**: Local LLM services (Ollama Docker setup)
- **D:/models/ollama**: Model storage location
- **.crush.json**: Crush configuration (global and local)
- **docker-compose.yml**: Main services
- **docker-compose.monitoring.yml**: Monitoring stack

## Code Style Preferences

- Use TypeScript for new JavaScript code
- Follow existing patterns in the codebase
- Prefer explicit types over implicit
- Use meaningful variable and function names
- Add comments only when necessary for complex logic

## Agentic Development Guidelines

- Always check existing code patterns before implementing
- Use the `agent` tool for efficient file searching
- Test changes thoroughly before completion
- Follow the project's existing architecture
- Update documentation when making significant changes

## Local Model Configuration

- **Primary Model**: Qwen 2.5 Coder 7B (coding tasks)
- **Secondary Model**: Qwen 2.5 7B (general tasks)
- **API Endpoint**: http://localhost:7040/v1/
- **Storage**: D:/models/ollama (shared Windows/WSL2)

## Environment Setup

- **Windows**: PowerShell with Docker Desktop
- **WSL2**: Ubuntu 24.04 with VS Code dark theme
- **Global Config**: ~/.crush.json (both Windows and WSL2)
- **Passwordless Sudo**: Configured for WSL2
