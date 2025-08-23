#!/usr/bin/env python3
"""
MCP Bridge Server - HTTP API for MCP tool execution in Docker
Provides a REST API interface to MCP servers running in the container
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Bridge Server",
    description="HTTP bridge for Model Context Protocol servers",
    version="1.0.0"
)

class ToolCallRequest(BaseModel):
    server: str
    tool: str
    arguments: Dict[str, Any]

class ToolCallResponse(BaseModel):
    success: bool
    result: str
    error: Optional[str] = None

class ServerInfo(BaseModel):
    name: str
    status: str
    tools: List[str]
    last_health_check: float

class MCPServerManager:
    """Manages MCP server processes and tool execution."""
    
    def __init__(self):
        self.servers = {}
        self.initialize_servers()
    
    def initialize_servers(self):
        """Initialize MCP server configurations."""
        self.servers = {
            "filesystem": {
                "command": ["mcp-server-filesystem", "/workspace"],
                "process": None,
                "status": "stopped",
                "tools": [],
                "last_health_check": 0
            },
            "git": {
                "command": ["mcp-server-git"],
                "process": None,
                "status": "stopped", 
                "tools": [],
                "last_health_check": 0,
                "cwd": "/workspace"
            }
        }
        
        # Add GitHub server if token is available
        if os.environ.get("GITHUB_TOKEN"):
            self.servers["github"] = {
                "command": ["mcp-server-github"],
                "process": None,
                "status": "stopped",
                "tools": [],
                "last_health_check": 0,
                "env": {"GITHUB_TOKEN": os.environ["GITHUB_TOKEN"]}
            }
    
    async def start_server(self, server_name: str) -> bool:
        """Start an MCP server process."""
        if server_name not in self.servers:
            raise ValueError(f"Unknown server: {server_name}")
        
        config = self.servers[server_name]
        
        # Check if already running
        if config["process"] is not None:
            try:
                # Check if process is still alive
                if config["process"].returncode is None:
                    return True
            except:
                pass
        
        try:
            logger.info(f"🚀 Starting MCP server: {server_name}")
            
            # Prepare environment
            env = {**os.environ, **config.get("env", {})}
            
            # Start process
            process = await asyncio.create_subprocess_exec(
                *config["command"],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=config.get("cwd"),
                env=env
            )
            
            config["process"] = process
            config["status"] = "running"
            config["last_health_check"] = time.time()
            
            # Initialize server and discover tools
            await self._initialize_server_session(server_name)
            
            logger.info(f"✅ Started MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start server {server_name}: {e}")
            config["status"] = "error"
            return False
    
    async def _initialize_server_session(self, server_name: str):
        """Initialize MCP server session and discover tools."""
        config = self.servers[server_name]
        process = config["process"]
        
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": "init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True}
                    },
                    "clientInfo": {
                        "name": "MCP-Bridge-Server",
                        "version": "1.0.0"
                    }
                }
            }
            
            # Send request
            request_data = json.dumps(init_request) + "\n"
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            # Read response
            response_data = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
            response = json.loads(response_data.decode())
            
            if "error" not in response:
                # Discover tools
                await self._discover_tools(server_name)
                
        except Exception as e:
            logger.warning(f"⚠️ Server initialization failed for {server_name}: {e}")
    
    async def _discover_tools(self, server_name: str):
        """Discover available tools from server."""
        config = self.servers[server_name]
        process = config["process"]
        
        try:
            # Send tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "id": "tools",
                "method": "tools/list",
                "params": {}
            }
            
            request_data = json.dumps(tools_request) + "\n"
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            # Read response
            response_data = await asyncio.wait_for(process.stdout.readline(), timeout=5.0)
            response = json.loads(response_data.decode())
            
            if "result" in response:
                tools = response["result"].get("tools", [])
                config["tools"] = [tool["name"] for tool in tools]
                logger.info(f"🛠️ Discovered {len(config['tools'])} tools for {server_name}: {config['tools']}")
                
        except Exception as e:
            logger.warning(f"⚠️ Tool discovery failed for {server_name}: {e}")
    
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool on an MCP server."""
        # Ensure server is running
        if not await self.start_server(server_name):
            raise Exception(f"Failed to start server: {server_name}")
        
        config = self.servers[server_name]
        process = config["process"]
        
        # Create JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "id": f"tool_{int(time.time() * 1000)}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        try:
            logger.info(f"🚀 Executing {server_name}:{tool_name} with args: {arguments}")
            
            # Send request
            request_data = json.dumps(request) + "\n"
            process.stdin.write(request_data.encode())
            await process.stdin.drain()
            
            # Read response with timeout
            response_data = await asyncio.wait_for(process.stdout.readline(), timeout=30.0)
            response = json.loads(response_data.decode())
            
            if "error" in response:
                error_msg = response["error"].get("message", "Unknown error")
                raise Exception(f"MCP Error: {error_msg}")
            
            # Format result for voice response
            result = response.get("result", {})
            content = result.get("content", [])
            
            if content:
                text_parts = []
                for item in content:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                
                if text_parts:
                    result_text = "\n".join(text_parts)
                    # Truncate long results for voice
                    if len(result_text) > 500:
                        result_text = result_text[:500] + "... (truncated for voice)"
                    return result_text
            
            return "Tool executed successfully"
            
        except asyncio.TimeoutError:
            raise Exception(f"Tool execution timed out for {server_name}:{tool_name}")
        except Exception as e:
            logger.error(f"❌ Tool execution error: {e}")
            raise
    
    def get_server_info(self) -> List[ServerInfo]:
        """Get information about all servers."""
        info = []
        for name, config in self.servers.items():
            info.append(ServerInfo(
                name=name,
                status=config["status"],
                tools=config["tools"],
                last_health_check=config["last_health_check"]
            ))
        return info

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
        logger.error(f"❌ Tool execution failed: {e}")
        return ToolCallResponse(success=False, result="", error=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "servers": {name: config["status"] for name, config in mcp_manager.servers.items()}
    }

@app.get("/servers", response_model=List[ServerInfo])
async def list_servers():
    """List all MCP servers and their status."""
    return mcp_manager.get_server_info()

@app.post("/servers/{server_name}/start")
async def start_server(server_name: str):
    """Start a specific MCP server."""
    try:
        success = await mcp_manager.start_server(server_name)
        if success:
            return {"message": f"Server {server_name} started successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to start server {server_name}")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🌉 Starting MCP Bridge Server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
