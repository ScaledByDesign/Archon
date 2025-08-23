# Docker-Based MCP Integration

## 🎯 Why Docker for MCP Integration?

### Advantages Over WSL
- ✅ **Cross-Platform**: Works on Windows, macOS, and Linux
- ✅ **Isolated Environment**: Clean, reproducible MCP server environment
- ✅ **Easy Deployment**: Single docker-compose command
- ✅ **Version Control**: Dockerfile ensures consistent environment
- ✅ **Scalability**: Easy to add more MCP servers as containers
- ✅ **No Host Dependencies**: No need to install Node.js/npm on host
- ✅ **Network Isolation**: Secure communication between containers

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│  RealtimeVoiceChat Container (Python)                      │
│  ├── FastAPI Server                                        │
│  ├── Speech Pipeline (STT/TTS)                            │
│  └── MCP Bridge (HTTP/TCP to MCP containers)              │
├─────────────────────────────────────────────────────────────┤
│  MCP Services Container (Node.js)                          │
│  ├── mcp-server-filesystem                                 │
│  ├── mcp-server-git                                        │
│  ├── mcp-server-github                                     │
│  └── HTTP/TCP MCP Bridge Server                           │
├─────────────────────────────────────────────────────────────┤
│  Shared Volumes                                            │
│  ├── /workspace (project files)                           │
│  ├── /git (git repositories)                              │
│  └── /logs (application logs)                             │
└─────────────────────────────────────────────────────────────┘
```

## 🐳 Implementation Plan

### Phase 1: MCP Services Container

#### 1.1 MCP Services Dockerfile
```dockerfile
# apps/voice/docker/mcp-services/Dockerfile
FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache git openssh-client curl

# Create app directory
WORKDIR /app

# Install MCP servers globally
RUN npm install -g \
    @modelcontextprotocol/server-filesystem \
    @modelcontextprotocol/server-git \
    @modelcontextprotocol/server-github

# Install Python for MCP bridge server
RUN apk add --no-cache python3 py3-pip
RUN pip3 install fastapi uvicorn mcp

# Copy MCP bridge server
COPY mcp-bridge-server.py /app/
COPY requirements.txt /app/
RUN pip3 install -r requirements.txt

# Create workspace directory
RUN mkdir -p /workspace /git /logs

# Expose port for HTTP MCP bridge
EXPOSE 8001

# Start the MCP bridge server
CMD ["python3", "mcp-bridge-server.py"]
```

#### 1.2 MCP Bridge Server (HTTP API)
```python
# apps/voice/docker/mcp-services/mcp-bridge-server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import subprocess
import json
import logging
from typing import Dict, Any, List

app = FastAPI(title="MCP Bridge Server", version="1.0.0")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolCallRequest(BaseModel):
    server: str
    tool: str
    arguments: Dict[str, Any]

class ToolCallResponse(BaseModel):
    success: bool
    result: str
    error: str = None

class MCPServerManager:
    def __init__(self):
        self.servers = {
            "filesystem": {
                "command": ["mcp-server-filesystem", "/workspace"],
                "process": None
            },
            "git": {
                "command": ["mcp-server-git"],
                "process": None,
                "cwd": "/workspace"
            }
        }
    
    async def start_server(self, server_name: str):
        """Start an MCP server process."""
        if server_name not in self.servers:
            raise ValueError(f"Unknown server: {server_name}")
        
        config = self.servers[server_name]
        if config["process"] is not None:
            return  # Already running
        
        try:
            process = await asyncio.create_subprocess_exec(
                *config["command"],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=config.get("cwd")
            )
            config["process"] = process
            logger.info(f"Started MCP server: {server_name}")
        except Exception as e:
            logger.error(f"Failed to start server {server_name}: {e}")
            raise
    
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool on an MCP server."""
        await self.start_server(server_name)
        
        config = self.servers[server_name]
        process = config["process"]
        
        # Create JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            # Send request
            request_data = json.dumps(request) + "\n"
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            # Read response
            response_data = await process.stdout.readline()
            response = json.loads(response_data.decode())
            
            if "error" in response:
                raise Exception(f"MCP Error: {response['error']}")
            
            # Format result
            content = response.get("result", {}).get("content", [])
            if content:
                text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
                return "\n".join(text_parts) if text_parts else "Tool executed successfully"
            
            return "Tool executed successfully"
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            raise

# Global manager instance
mcp_manager = MCPServerManager()

@app.post("/execute-tool", response_model=ToolCallResponse)
async def execute_tool(request: ToolCallRequest):
    """Execute a tool on an MCP server."""
    try:
        result = await mcp_manager.execute_tool(
            request.server,
            request.tool,
            request.arguments
        )
        return ToolCallResponse(success=True, result=result)
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return ToolCallResponse(success=False, result="", error=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "servers": list(mcp_manager.servers.keys())}

@app.get("/servers")
async def list_servers():
    """List available MCP servers."""
    return {"servers": list(mcp_manager.servers.keys())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Phase 2: Updated Docker Compose

#### 2.1 Enhanced docker-compose.yml
```yaml
# apps/voice/docker-compose.yml
version: '3.8'

services:
  # Main RealtimeVoiceChat application
  realtime-voice-chat:
    build: .
    container_name: realtime-voice-chat-app
    ports:
      - "8000:8000"
    volumes:
      - ./:/workspace
      - voice_logs:/var/log/voice
    environment:
      - MCP_BRIDGE_URL=http://mcp-services:8001
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - ollama
      - mcp-services
    restart: unless-stopped

  # MCP Services container
  mcp-services:
    build:
      context: ./docker/mcp-services
      dockerfile: Dockerfile
    container_name: realtime-voice-chat-mcp
    ports:
      - "8001:8001"
    volumes:
      - ./:/workspace
      - git_repos:/git
      - mcp_logs:/logs
    environment:
      - NODE_ENV=production
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Ollama service (existing)
  ollama:
    image: ollama/ollama:latest
    container_name: realtime-voice-chat-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

volumes:
  ollama_data:
    driver: local
  voice_logs:
    driver: local
  mcp_logs:
    driver: local
  git_repos:
    driver: local
```

### Phase 3: HTTP-Based MCP Bridge

#### 3.1 Enhanced MCP Bridge (HTTP Client)
```python
# apps/voice/code/mcp_bridge.py (updated sections)
import aiohttp
import os

class HTTPMCPClient:
    """HTTP-based MCP client for Docker integration."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.environ.get("MCP_BRIDGE_URL", "http://localhost:8001")
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool via HTTP MCP bridge."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(
                f"{self.base_url}/execute-tool",
                json={
                    "server": server_name,
                    "tool": tool_name,
                    "arguments": arguments
                }
            ) as response:
                result = await response.json()
                
                if result["success"]:
                    return result["result"]
                else:
                    raise Exception(result.get("error", "Unknown error"))
                    
        except Exception as e:
            logger.error(f"HTTP MCP call failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if MCP bridge is healthy."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except:
            return False

class DockerMCPManager:
    """Docker-based MCP manager using HTTP bridge."""
    
    def __init__(self):
        self.http_client = HTTPMCPClient()
        self.connected = False
    
    async def initialize(self) -> bool:
        """Initialize connection to Docker MCP services."""
        try:
            logger.info("🐳 Initializing Docker MCP connection...")
            
            # Check if MCP bridge is available
            if await self.http_client.health_check():
                self.connected = True
                logger.info("✅ Docker MCP bridge connected successfully")
                return True
            else:
                logger.error("❌ Docker MCP bridge not available")
                return False
                
        except Exception as e:
            logger.error(f"❌ Docker MCP initialization failed: {e}")
            return False
    
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute tool via Docker MCP bridge."""
        if not self.connected:
            await self.initialize()
        
        return await self.http_client.execute_tool(server_name, tool_name, arguments)

# Global Docker MCP manager
docker_mcp_manager = DockerMCPManager()

async def bootstrap_docker_mcp():
    """Bootstrap Docker-based MCP integration."""
    try:
        logger.info("🐳 Bootstrapping Docker MCP integration...")
        
        success = await docker_mcp_manager.initialize()
        
        if success:
            logger.info("🎉 Docker MCP bootstrap completed successfully")
        else:
            logger.error("❌ Docker MCP bootstrap failed")
            
    except Exception as e:
        logger.error(f"❌ Docker MCP bootstrap error: {e}")
```

### Phase 4: Voice Command Integration

#### 4.1 Updated Tool Execution
```python
async def execute_docker_tool_call(tool_call: Dict[str, Any]) -> str:
    """Execute tool call using Docker MCP bridge."""
    try:
        tool_name = tool_call["tool"]
        arguments = tool_call["arguments"]
        
        if ":" not in tool_name:
            return f"Invalid tool format: {tool_name}"
        
        server_name, tool_name_only = tool_name.split(":", 1)
        
        # Execute via Docker MCP bridge
        result = await docker_mcp_manager.execute_tool(server_name, tool_name_only, arguments)
        
        return result
        
    except Exception as e:
        return f"Error executing Docker tool call: {str(e)}"
```

## 🚀 Deployment Instructions

### 1. Build and Start Services
```bash
# Build and start all services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f mcp-services
```

### 2. Test MCP Integration
```bash
# Test MCP bridge health
curl http://localhost:8001/health

# Test tool execution
curl -X POST http://localhost:8001/execute-tool \
  -H "Content-Type: application/json" \
  -d '{
    "server": "filesystem",
    "tool": "read_directory",
    "arguments": {"path": "/workspace"}
  }'
```

### 3. Voice Commands
Once running, voice commands will work seamlessly:
- "List files in the current directory"
- "Read the README file"
- "Check git status"

## 🎯 Benefits

- **✅ Cross-Platform**: Works on any system with Docker
- **✅ Isolated**: Clean environment for MCP servers
- **✅ Scalable**: Easy to add more MCP servers
- **✅ Maintainable**: Version-controlled Docker configuration
- **✅ Secure**: Network isolation between services
- **✅ Reliable**: Health checks and automatic restarts

This Docker-based approach provides a robust, portable solution for MCP integration without the complexity of WSL or Windows-specific issues.
