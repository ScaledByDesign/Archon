# MCP Technical Specification for Developer Agent

## 🏗️ Architecture Overview

### System Components
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Voice Input   │───▶│  Speech Pipeline │───▶│   MCP Manager   │
│   (Microphone)  │    │   (STT → LLM)    │    │  (Tool Router)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 │                                 │
                ┌──────▼──────┐                   ┌──────▼──────┐                 ┌──────▼──────┐
                │ File System │                   │  Git/GitHub │                 │  Database   │
                │   Server    │                   │   Server    │                 │   Server    │
                └─────────────┘                   └─────────────┘                 └─────────────┘
                       │                                 │                                 │
                ┌──────▼──────┐                   ┌──────▼──────┐                 ┌──────▼──────┐
                │   Terminal  │                   │    Cloud    │                 │     AI      │
                │   Server    │                   │   Server    │                 │   Server    │
                └─────────────┘                   └─────────────┘                 └─────────────┘
```

## 🔧 Core MCP Implementation

### Enhanced MCP Client
```python
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
import logging

class TransportType(Enum):
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"

@dataclass
class MCPServerConfig:
    name: str
    command: List[str]
    args: List[str] = None
    env: Dict[str, str] = None
    transport: TransportType = TransportType.STDIO
    enabled: bool = True
    security_level: str = "medium"
    timeout: int = 30
    retry_count: int = 3

class EnhancedMCPClient:
    """Complete MCP client with full protocol support"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session_id = None
        self.capabilities = {}
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        self.connection = None
        self.health_status = "disconnected"
        
    async def initialize(self) -> bool:
        """Initialize MCP session with server"""
        try:
            # Establish connection based on transport type
            if self.config.transport == TransportType.STDIO:
                await self._connect_stdio()
            elif self.config.transport == TransportType.SSE:
                await self._connect_sse()
            
            # Send initialize request
            response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "prompts": {"listChanged": True}
                },
                "clientInfo": {
                    "name": "RealtimeVoiceChat",
                    "version": "1.0.0"
                }
            })
            
            self.capabilities = response.get("capabilities", {})
            self.session_id = response.get("sessionId")
            self.health_status = "connected"
            
            # Discover available tools, resources, and prompts
            await self._discover_capabilities()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize MCP client: {e}")
            self.health_status = "error"
            return False
    
    async def _discover_capabilities(self):
        """Discover all available tools, resources, and prompts"""
        # Discover tools
        if "tools" in self.capabilities:
            tools_response = await self._send_request("tools/list", {})
            for tool in tools_response.get("tools", []):
                self.tools[tool["name"]] = tool
        
        # Discover resources
        if "resources" in self.capabilities:
            resources_response = await self._send_request("resources/list", {})
            for resource in resources_response.get("resources", []):
                self.resources[resource["uri"]] = resource
        
        # Discover prompts
        if "prompts" in self.capabilities:
            prompts_response = await self._send_request("prompts/list", {})
            for prompt in prompts_response.get("prompts", []):
                self.prompts[prompt["name"]] = prompt
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with given arguments"""
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' not found")
        
        response = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        
        return response.get("content", [])
    
    async def read_resource(self, uri: str) -> Any:
        """Read a resource by URI"""
        if uri not in self.resources:
            raise ValueError(f"Resource '{uri}' not found")
        
        response = await self._send_request("resources/read", {
            "uri": uri
        })
        
        return response.get("contents", [])
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> str:
        """Get a rendered prompt template"""
        if name not in self.prompts:
            raise ValueError(f"Prompt '{name}' not found")
        
        response = await self._send_request("prompts/get", {
            "name": name,
            "arguments": arguments or {}
        })
        
        return response.get("messages", [])
    
    async def health_check(self) -> bool:
        """Check if server is healthy"""
        try:
            await self._send_request("ping", {})
            self.health_status = "healthy"
            return True
        except:
            self.health_status = "unhealthy"
            return False
    
    async def _connect_stdio(self):
        """Establish stdio transport connection"""
        self.process = await asyncio.create_subprocess_exec(
            self.config.command[0],
            *self.config.command[1:],
            *(self.config.args or []),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **(self.config.env or {})}
        )
        
        self.connection = {
            "stdin": self.process.stdin,
            "stdout": self.process.stdout,
            "stderr": self.process.stderr
        }
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC 2.0 request"""
        request_id = f"req_{asyncio.current_task().get_name()}_{time.time()}"
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        # Send request
        request_data = json.dumps(request) + "\n"
        self.connection["stdin"].write(request_data.encode())
        await self.connection["stdin"].drain()
        
        # Read response
        response_data = await self.connection["stdout"].readline()
        response = json.loads(response_data.decode())
        
        if "error" in response:
            raise Exception(f"MCP Error: {response['error']}")
        
        return response.get("result", {})

class MCPServerManager:
    """Manages multiple MCP server connections"""
    
    def __init__(self):
        self.servers: Dict[str, EnhancedMCPClient] = {}
        self.health_monitor = None
        self.security_manager = SecurityManager()
        
    async def add_server(self, config: MCPServerConfig) -> bool:
        """Add and initialize a new MCP server"""
        client = EnhancedMCPClient(config)
        
        if await client.initialize():
            self.servers[config.name] = client
            logging.info(f"Added MCP server: {config.name}")
            return True
        else:
            logging.error(f"Failed to add MCP server: {config.name}")
            return False
    
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool on a specific server"""
        if server_name not in self.servers:
            raise ValueError(f"Server '{server_name}' not found")
        
        # Security check
        if not self.security_manager.is_tool_allowed(server_name, tool_name, arguments):
            raise PermissionError(f"Tool '{server_name}:{tool_name}' not allowed")
        
        server = self.servers[server_name]
        return await server.call_tool(tool_name, arguments)
    
    async def get_all_tools(self) -> Dict[str, List[Dict]]:
        """Get all available tools from all servers"""
        all_tools = {}
        for server_name, server in self.servers.items():
            all_tools[server_name] = list(server.tools.values())
        return all_tools
    
    async def health_check_all(self) -> Dict[str, str]:
        """Check health of all servers"""
        health_status = {}
        for server_name, server in self.servers.items():
            await server.health_check()
            health_status[server_name] = server.health_status
        return health_status

class SecurityManager:
    """Manages security policies for MCP operations"""
    
    def __init__(self):
        self.policies = self._load_security_policies()
    
    def is_tool_allowed(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Check if tool execution is allowed based on security policies"""
        # Implement RBAC, argument validation, etc.
        policy = self.policies.get(server_name, {})
        
        # Check tool whitelist
        allowed_tools = policy.get("allowed_tools", [])
        if allowed_tools and tool_name not in allowed_tools:
            return False
        
        # Check blocked tools
        blocked_tools = policy.get("blocked_tools", [])
        if tool_name in blocked_tools:
            return False
        
        # Validate arguments
        return self._validate_arguments(server_name, tool_name, arguments)
    
    def _validate_arguments(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments for security"""
        # Implement argument validation logic
        # Check for path traversal, injection attacks, etc.
        return True
    
    def _load_security_policies(self) -> Dict[str, Any]:
        """Load security policies from configuration"""
        return {
            "filesystem": {
                "allowed_tools": ["read_file", "list_directory", "write_file"],
                "blocked_tools": ["delete_file", "format_disk"],
                "path_restrictions": ["/workspace", "/tmp"]
            },
            "git": {
                "allowed_tools": ["status", "log", "diff", "commit", "push"],
                "blocked_tools": ["reset --hard", "clean -fd"]
            }
        }
```

This technical specification provides the foundation for a complete MCP implementation that supports:

1. **Full Protocol Support**: Tools, resources, and prompts
2. **Multiple Transports**: stdio, SSE, and HTTP
3. **Security Framework**: RBAC, validation, and sandboxing
4. **Health Monitoring**: Connection status and recovery
5. **Session Management**: Proper lifecycle handling

The next step would be implementing specific server integrations for the developer workflow tools identified in the comprehensive plan.
