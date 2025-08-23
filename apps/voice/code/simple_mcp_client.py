#!/usr/bin/env python3
"""
Simple MCP Client for RealtimeVoiceChat
Executes tools on external MCP servers based on voice commands
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """
    Simple MCP client that executes tools on external MCP servers.
    
    This is the correct approach - the voice app is an MCP CLIENT that
    uses external MCP servers to perform actions based on voice commands.
    """
    
    def __init__(self):
        """Initialize the simple MCP client."""
        self.servers = self._load_server_configs()
        self.processes = {}  # Track running server processes
    
    def _load_server_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load MCP server configurations - using archon-mcp HTTP server."""
        return {
            "archon": {
                "url": os.environ.get("ARCHON_MCP_URL", "http://localhost:7082"),
                "description": "Archon knowledge base and task management",
                "tools": [
                    "health_check", "session_info",
                    "create_task", "get_task", "update_task", "delete_task", "list_tasks",
                    "create_project", "get_project", "update_project", "list_projects",
                    "search_documents", "get_document", "upload_document"
                ],
                "transport": "http"
            }
        }
    
    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool on an MCP server.

        Args:
            server_name: Name of the MCP server (e.g., "archon")
            tool_name: Name of the tool to execute (e.g., "create_task", "search_documents")
            arguments: Arguments to pass to the tool

        Returns:
            str: Formatted result for voice response
        """
        try:
            logger.info(f"🚀 Executing {server_name}:{tool_name} with args: {arguments}")

            # Validate server exists
            if server_name not in self.servers:
                return f"Unknown server: {server_name}. Available servers: {list(self.servers.keys())}"

            # Security check
            if not self._is_tool_allowed(server_name, tool_name, arguments):
                return f"Tool {server_name}:{tool_name} is not permitted"

            config = self.servers[server_name]

            # Execute via HTTP or stdio based on transport
            if config.get("transport") == "http":
                result = await self._execute_http_tool(server_name, tool_name, arguments)
            else:
                # Fallback to stdio (legacy)
                if not await self._ensure_server_running(server_name):
                    return f"Failed to start {server_name} server"
                result = await self._execute_json_rpc(server_name, tool_name, arguments)

            # Format result for voice
            return self._format_for_voice(server_name, tool_name, result)

        except Exception as e:
            error_msg = f"Error executing {server_name}:{tool_name}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return error_msg

    async def _execute_http_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool via HTTP MCP server using JSON-RPC over SSE."""
        import aiohttp
        import json
        import uuid

        config = self.servers[server_name]
        base_url = config["url"]

        # Construct the MCP SSE endpoint
        mcp_url = f"{base_url}/mcp"

        # Create JSON-RPC 2.0 request
        request_id = str(uuid.uuid4())
        json_rpc_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        async with aiohttp.ClientSession() as session:
            try:
                logger.info(f"🌐 SSE MCP call to {mcp_url}: {tool_name}")

                # Send JSON-RPC request via POST with SSE headers
                async with session.post(
                    mcp_url,
                    json=json_rpc_request,
                    headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json"
                    },
                    timeout=30
                ) as response:
                    if response.status == 200:
                        # Read SSE response
                        result_text = ""
                        async for line in response.content:
                            line_str = line.decode().strip()
                            if line_str.startswith("data: "):
                                data_str = line_str[6:]  # Remove "data: " prefix
                                try:
                                    data = json.loads(data_str)
                                    if data.get("id") == request_id:
                                        if "result" in data:
                                            result = data["result"]
                                            # Extract text content from MCP result
                                            if isinstance(result, dict) and "content" in result:
                                                content = result["content"]
                                                for item in content:
                                                    if item.get("type") == "text":
                                                        result_text += item.get("text", "")
                                            else:
                                                result_text = str(result)
                                            break
                                        elif "error" in data:
                                            error = data["error"]
                                            raise Exception(f"MCP Error {error.get('code', 0)}: {error.get('message', 'Unknown error')}")
                                except json.JSONDecodeError:
                                    continue

                        logger.info(f"✅ SSE MCP call successful")
                        return {"content": [{"type": "text", "text": result_text}]}
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")

            except Exception as e:
                logger.error(f"❌ SSE MCP call failed: {e}")
                raise e

    async def _ensure_server_running(self, server_name: str) -> bool:
        """Ensure MCP server is running."""
        if server_name in self.processes:
            # Check if process is still alive
            process = self.processes[server_name]
            if process.returncode is None:
                return True
        
        # Start the server
        try:
            config = self.servers[server_name]
            env = {**os.environ, **config.get("env", {})}
            
            logger.info(f"🚀 Starting MCP server: {server_name}")
            
            process = await asyncio.create_subprocess_exec(
                *config["command"],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            self.processes[server_name] = process
            
            # Initialize server with handshake
            await self._initialize_server(server_name)
            
            logger.info(f"✅ Started MCP server: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start server {server_name}: {e}")
            return False
    
    async def _initialize_server(self, server_name: str):
        """Initialize MCP server with handshake."""
        process = self.processes[server_name]
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "RealtimeVoiceChat", "version": "1.0.0"}
            }
        }
        
        await self._send_request(process, init_request)
        response = await self._read_response(process)
        
        if "error" in response:
            raise Exception(f"Server initialization failed: {response['error']}")
    
    async def _execute_json_rpc(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool via JSON-RPC."""
        process = self.processes[server_name]
        
        # Create tool call request
        request = {
            "jsonrpc": "2.0",
            "id": f"tool_{tool_name}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        # Send request and get response
        await self._send_request(process, request)
        response = await self._read_response(process)
        
        if "error" in response:
            raise Exception(f"Tool execution failed: {response['error']}")
        
        return response.get("result", {})
    
    async def _send_request(self, process: asyncio.subprocess.Process, request: Dict[str, Any]):
        """Send JSON-RPC request to server."""
        request_data = json.dumps(request) + "\n"
        process.stdin.write(request_data.encode())
        await process.stdin.drain()
    
    async def _read_response(self, process: asyncio.subprocess.Process) -> Dict[str, Any]:
        """Read JSON-RPC response from server."""
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=30.0)
        return json.loads(response_line.decode().strip())
    
    def _is_tool_allowed(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Check if tool execution is allowed (basic security)."""
        # Get allowed tools from server config
        config = self.servers.get(server_name, {})
        allowed_tools = config.get("tools", [])

        if tool_name not in allowed_tools:
            logger.warning(f"🚫 Tool {tool_name} not allowed for server {server_name}")
            return False

        # Basic argument validation for archon tools
        if server_name == "archon":
            # Validate project_id format if present
            project_id = arguments.get("project_id", "")
            if project_id and not self._is_valid_uuid(project_id):
                logger.warning(f"🚫 Invalid project_id format: {project_id}")
                return False

            # Validate task titles are reasonable
            title = arguments.get("title", "")
            if title and len(title) > 200:
                logger.warning(f"🚫 Task title too long: {len(title)} characters")
                return False

        return True

    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID format."""
        import re
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(uuid_string))
    
    def _format_for_voice(self, server_name: str, tool_name: str, result: Any) -> str:
        """Format MCP result for natural voice response."""
        try:
            # Extract content from MCP result
            content = result.get("content", [])
            if not content:
                return f"I executed {tool_name} successfully"

            # Process text content
            text_parts = []
            for item in content:
                if item.get("type") == "text":
                    text_parts.append(item.get("text", ""))

            if not text_parts:
                return f"I executed {tool_name} successfully"

            result_text = "\n".join(text_parts)

            # Format based on server and tool type
            if server_name == "archon":
                return self._format_archon_result(tool_name, result_text)
            else:
                # Generic formatting for other servers
                if len(result_text) > 300:
                    return f"I executed {tool_name}. Result: {result_text[:300]}... (truncated for voice)"
                else:
                    return f"I executed {tool_name}. Result: {result_text}"

        except Exception as e:
            logger.error(f"❌ Error formatting result: {e}")
            return f"I executed {tool_name} but couldn't format the result properly"

    def _format_archon_result(self, tool_name: str, result_text: str) -> str:
        """Format Archon-specific tool results for voice."""
        try:
            # Try to parse JSON result
            import json
            result_data = json.loads(result_text)

            if tool_name == "create_task":
                if result_data.get("success"):
                    task_title = result_data.get("task", {}).get("title", "task")
                    return f"I created the task '{task_title}' successfully"
                else:
                    error = result_data.get("error", "Unknown error")
                    return f"Failed to create task: {error}"

            elif tool_name == "search_documents":
                if result_data.get("success"):
                    results = result_data.get("results", [])
                    if results:
                        return f"I found {len(results)} documents related to your search"
                    else:
                        return "I didn't find any documents matching your search"
                else:
                    return "Search failed"

            elif tool_name == "health_check":
                if result_data.get("success"):
                    status = result_data.get("status", "unknown")
                    return f"Archon system is {status}"
                else:
                    return "Archon health check failed"

            elif tool_name == "list_projects":
                if result_data.get("success"):
                    projects = result_data.get("projects", [])
                    if projects:
                        project_names = [p.get("name", "Unnamed") for p in projects[:3]]
                        if len(projects) > 3:
                            return f"I found {len(projects)} projects including: {', '.join(project_names)} and {len(projects)-3} more"
                        else:
                            return f"I found {len(projects)} projects: {', '.join(project_names)}"
                    else:
                        return "No projects found"
                else:
                    return "Failed to list projects"

            else:
                # Generic success/error handling
                if result_data.get("success"):
                    return f"I executed {tool_name} successfully"
                else:
                    error = result_data.get("error", "Unknown error")
                    return f"Failed to execute {tool_name}: {error}"

        except json.JSONDecodeError:
            # Not JSON, treat as plain text
            if len(result_text) > 300:
                return f"I executed {tool_name}. Result: {result_text[:300]}... (truncated for voice)"
            else:
                return f"I executed {tool_name}. Result: {result_text}"
        except Exception as e:
            logger.error(f"❌ Error formatting Archon result: {e}")
            return f"I executed {tool_name} but couldn't format the result properly"
    
    async def get_available_tools(self) -> Dict[str, List[str]]:
        """Get list of available tools for each server."""
        return {server: config["tools"] for server, config in self.servers.items()}
    
    async def cleanup(self):
        """Clean up running server processes."""
        for server_name, process in self.processes.items():
            try:
                process.terminate()
                await process.wait()
                logger.info(f"🔌 Stopped MCP server: {server_name}")
            except Exception as e:
                logger.error(f"❌ Error stopping server {server_name}: {e}")
        
        self.processes.clear()

# Global simple MCP client instance
simple_mcp_client = SimpleMCPClient()

async def execute_voice_tool_call(tool_call: Dict[str, Any]) -> str:
    """
    Execute a tool call from voice command using simple MCP client.
    
    Args:
        tool_call: Dict with 'tool' and 'arguments' keys
        
    Returns:
        str: Formatted result for voice response
    """
    try:
        tool_name = tool_call.get("tool", "")
        arguments = tool_call.get("arguments", {})
        
        # Parse server:tool format
        if ":" not in tool_name:
            return f"Invalid tool format: {tool_name}. Expected 'server:tool'"
        
        server_name, tool_name_only = tool_name.split(":", 1)
        
        # Execute via simple MCP client
        result = await simple_mcp_client.execute_tool(server_name, tool_name_only, arguments)
        
        return result
        
    except Exception as e:
        error_msg = f"Error executing voice tool call: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg
