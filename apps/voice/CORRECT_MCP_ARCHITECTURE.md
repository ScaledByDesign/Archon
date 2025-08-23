# Correct MCP Architecture for Voice-Controlled Actions

## 🎯 Clarified Architecture

### What We're Building
**RealtimeVoiceChat as an MCP Client** that executes tools on external MCP servers based on voice commands.

```
┌─────────────────────────────────────────────────────────────────┐
│                    RealtimeVoiceChat App                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Voice     │───▶│     LLM     │───▶│   MCP Tool Call     │  │
│  │   Input     │    │  Processing │    │    Detection        │  │
│  │   (STT)     │    │             │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                   │              │
│  ┌─────────────┐    ┌─────────────┐              │              │
│  │   Voice     │◀───│   Format    │◀─────────────┘              │
│  │  Response   │    │  Response   │                             │
│  │   (TTS)     │    │             │                             │
│  └─────────────┘    └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Client Bridge                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Parse     │───▶│   Security  │───▶│    Execute Tool     │  │
│  │ Tool Call   │    │    Check    │    │    on MCP Server    │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External MCP Servers                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ Filesystem  │    │     Git     │    │      GitHub         │  │
│  │   Server    │    │   Server    │    │      Server         │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ Database    │    │   Docker    │    │       AWS           │  │
│  │   Server    │    │   Server    │    │      Server         │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🎤 Voice Command Flow

### Example: "List the files in the current directory"

1. **Voice Input**: User speaks "List the files in the current directory"
2. **STT**: Speech converted to text
3. **LLM Processing**: AI determines this needs a filesystem operation
4. **Tool Call Generation**: LLM outputs: `{"tool":"filesystem:read_directory","arguments":{"path":"."}}`
5. **MCP Client**: Parses tool call and connects to filesystem MCP server
6. **Tool Execution**: Executes `read_directory` tool with path "."
7. **Result Processing**: Formats file list for voice response
8. **TTS**: Speaks result: "I found 5 files: README.md, package.json, src folder..."

## 🏗️ Simplified Implementation

### 1. MCP Servers (External - Run in Docker)
```yaml
# docker-compose.yml
services:
  # Filesystem MCP Server
  mcp-filesystem:
    image: node:18-alpine
    command: ["mcp-server-filesystem", "/workspace"]
    volumes:
      - ./:/workspace
    ports:
      - "9001:9001"  # Expose for HTTP if needed
  
  # Git MCP Server  
  mcp-git:
    image: node:18-alpine
    command: ["mcp-server-git"]
    volumes:
      - ./:/workspace
    working_dir: /workspace
    ports:
      - "9002:9002"
  
  # GitHub MCP Server
  mcp-github:
    image: node:18-alpine
    command: ["mcp-server-github"]
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    ports:
      - "9003:9003"
```

### 2. MCP Client (Inside RealtimeVoiceChat)
```python
# apps/voice/code/mcp_client.py
import asyncio
import json
from typing import Dict, Any

class SimpleMCPClient:
    """Simple MCP client for executing tools on external servers."""
    
    def __init__(self):
        self.servers = {
            "filesystem": {"host": "mcp-filesystem", "port": 9001},
            "git": {"host": "mcp-git", "port": 9002}, 
            "github": {"host": "mcp-github", "port": 9003}
        }
    
    async def execute_tool(self, server: str, tool: str, args: Dict[str, Any]) -> str:
        """Execute a tool on an MCP server."""
        if server not in self.servers:
            return f"Unknown server: {server}"
        
        try:
            # Connect to MCP server via stdio or HTTP
            result = await self._call_mcp_server(server, tool, args)
            return self._format_for_voice(result)
        except Exception as e:
            return f"Error executing {server}:{tool}: {str(e)}"
    
    def _format_for_voice(self, result: Any) -> str:
        """Format MCP result for voice response."""
        # Convert MCP result to natural language
        if isinstance(result, list):
            return f"Found {len(result)} items: {', '.join(str(r) for r in result[:5])}"
        return str(result)
```

### 3. Voice Command Processing (Updated)
```python
# apps/voice/code/speech_pipeline_manager.py
async def _handle_tool_call(self, tool_call_data: dict, gen_id: int) -> str:
    """Handle MCP tool execution from voice command."""
    try:
        tool_name = tool_call_data.get("tool", "")
        arguments = tool_call_data.get("arguments", {})
        
        # Parse server:tool format
        if ":" not in tool_name:
            return "Invalid tool format. Expected 'server:tool'"
        
        server, tool = tool_name.split(":", 1)
        
        # Execute via MCP client
        mcp_client = SimpleMCPClient()
        result = await mcp_client.execute_tool(server, tool, arguments)
        
        return f"I executed the command. {result}"
        
    except Exception as e:
        return f"Sorry, I couldn't execute that command: {str(e)}"
```

## 🎯 Voice Commands → MCP Tools Mapping

### File Operations
- **"List files"** → `filesystem:read_directory {"path": "."}`
- **"Read README"** → `filesystem:read_file {"path": "README.md"}`
- **"Create new file"** → `filesystem:write_file {"path": "new.txt", "content": "..."}`

### Git Operations  
- **"Git status"** → `git:status {}`
- **"Commit changes"** → `git:commit {"message": "..."}`
- **"Push to main"** → `git:push {"branch": "main"}`

### GitHub Operations
- **"Create issue"** → `github:create_issue {"title": "...", "body": "..."}`
- **"List my repos"** → `github:list_repositories {}`
- **"Show pull requests"** → `github:list_pull_requests {}`

## 🚀 Deployment Strategy

### Option 1: Docker Compose (Recommended)
```bash
# Start all MCP servers and voice app
docker-compose up -d

# Voice app connects to MCP servers via Docker network
# User speaks → Voice app → MCP servers → Results → Voice response
```

### Option 2: Local MCP Servers
```bash
# Install MCP servers locally
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-git

# Start servers manually
mcp-server-filesystem /workspace &
mcp-server-git &

# Voice app connects via stdio/TCP
```

## 🎯 Key Benefits

1. **Clear Separation**: Voice app is MCP client, servers are external
2. **Scalable**: Easy to add more MCP servers for new capabilities  
3. **Maintainable**: Each MCP server handles one domain (files, git, etc.)
4. **Secure**: MCP servers can be sandboxed and access-controlled
5. **Testable**: Can test MCP integration independently

This is the correct architecture - RealtimeVoiceChat **uses** MCP tools to perform actions based on voice commands, rather than being an MCP server itself.
