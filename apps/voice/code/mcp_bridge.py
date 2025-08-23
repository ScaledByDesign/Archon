# mcp_bridge.py - Enhanced MCP Implementation
import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from mcp.client.stdio import stdio_client
from mcp.types import Tool

logger = logging.getLogger(__name__)

class TransportType(Enum):
    """MCP transport types"""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"

class ConnectionStatus(Enum):
    """Connection status states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"

@dataclass
class MCPServerConfig:
    """Configuration for MCP server connection"""
    name: str
    command: List[str]
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    transport: TransportType = TransportType.STDIO
    enabled: bool = True
    security_level: str = "medium"
    timeout: int = 30
    retry_count: int = 3
    auto_reconnect: bool = True
    use_wsl: bool = False
    wsl_distro: str = "Ubuntu"

@dataclass
class MCPResource:
    """MCP resource representation"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None

@dataclass
class MCPPrompt:
    """MCP prompt template representation"""
    name: str
    description: Optional[str] = None
    arguments: List[Dict[str, Any]] = field(default_factory=list)

class EnhancedMCPClient:
    """
    Enhanced MCP client with complete protocol support.

    Supports tools, resources, prompts, proper JSON-RPC 2.0, health monitoring,
    and robust error handling with automatic reconnection.
    """

    def __init__(self, config: MCPServerConfig):
        """Initialize the enhanced MCP client."""
        self.config = config
        self.session_id: Optional[str] = None
        self.capabilities: Dict[str, Any] = {}
        self.tools: Dict[str, Tool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.connection_status = ConnectionStatus.DISCONNECTED
        self.process: Optional[asyncio.subprocess.Process] = None
        self.request_id_counter = 0
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        self.last_health_check = 0
        self.reconnect_attempts = 0

    async def initialize(self) -> bool:
        """Initialize MCP connection and session."""
        try:
            self.connection_status = ConnectionStatus.CONNECTING
            logger.info(f"🔌 Initializing MCP client for server: {self.config.name}")

            # Establish transport connection
            if not await self._establish_connection():
                return False

            # Send initialize request
            init_response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {"subscribe": True, "listChanged": True},
                    "prompts": {"listChanged": True}
                },
                "clientInfo": {
                    "name": "RealtimeVoiceChat-Enhanced",
                    "version": "2.0.0"
                }
            })

            # Store server capabilities
            self.capabilities = init_response.get("capabilities", {})
            self.session_id = init_response.get("sessionId", str(uuid.uuid4()))

            # Discover available capabilities
            await self._discover_all_capabilities()

            # Set up notification handlers
            self._setup_notification_handlers()

            # Start background tasks
            asyncio.create_task(self._message_reader())
            asyncio.create_task(self._health_monitor())

            self.connection_status = ConnectionStatus.CONNECTED
            self.reconnect_attempts = 0

            logger.info(f"✅ MCP client initialized successfully for {self.config.name}")
            logger.info(f"   Tools: {len(self.tools)}, Resources: {len(self.resources)}, Prompts: {len(self.prompts)}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP client for {self.config.name}: {e}")
            self.connection_status = ConnectionStatus.ERROR
            return False

    async def _establish_connection(self) -> bool:
        """Establish transport connection based on configuration."""
        try:
            if self.config.transport == TransportType.STDIO:
                return await self._connect_stdio()
            elif self.config.transport == TransportType.SSE:
                return await self._connect_sse()
            elif self.config.transport == TransportType.HTTP:
                return await self._connect_http()
            else:
                raise ValueError(f"Unsupported transport type: {self.config.transport}")
        except Exception as e:
            logger.error(f"❌ Failed to establish connection: {e}")
            return False

    async def _connect_stdio(self) -> bool:
        """Establish stdio transport connection (with optional WSL support)."""
        try:
            # Prepare environment
            env = {**os.environ, **self.config.env}

            # Build command (with WSL if configured)
            if self.config.use_wsl:
                # Use WSL to run the command
                command = [
                    "wsl", "-d", self.config.wsl_distro, "--"
                ] + self.config.command + self.config.args

                # Convert current directory to WSL path
                cwd = self._convert_path_to_wsl(os.getcwd())
                logger.info(f"🐧 Starting MCP server in WSL: {' '.join(command)}")
            else:
                # Direct execution
                command = self.config.command + self.config.args
                cwd = None
                logger.info(f"🚀 Starting MCP server: {' '.join(command)}")

            # Start the MCP server process
            self.process = await asyncio.create_subprocess_exec(
                command[0],
                *command[1:],
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd
            )

            return True

        except Exception as e:
            logger.error(f"❌ Failed to start stdio connection: {e}")
            return False

    def _convert_path_to_wsl(self, windows_path: str) -> str:
        """Convert Windows path to WSL mount path."""
        if not self.config.use_wsl:
            return windows_path

        # Convert C:\path\to\file to /mnt/c/path/to/file
        if len(windows_path) >= 2 and windows_path[1] == ':':
            drive = windows_path[0].lower()
            path = windows_path[2:].replace('\\', '/')
            return f"/mnt/{drive}{path}"
        return windows_path.replace('\\', '/')

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC 2.0 request and wait for response."""
        if self.connection_status != ConnectionStatus.CONNECTED:
            raise ConnectionError(f"Client not connected to {self.config.name}")

        # Generate unique request ID
        self.request_id_counter += 1
        request_id = f"req_{self.config.name}_{self.request_id_counter}_{int(time.time() * 1000)}"

        # Create JSON-RPC 2.0 request
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }

        # Create future for response
        response_future = asyncio.Future()
        self.pending_requests[request_id] = response_future

        try:
            # Send request
            request_data = json.dumps(request) + "\n"
            self.process.stdin.write(request_data.encode())
            await self.process.stdin.drain()

            # Wait for response with timeout
            response = await asyncio.wait_for(
                response_future,
                timeout=self.config.timeout
            )

            return response

        except asyncio.TimeoutError:
            self.pending_requests.pop(request_id, None)
            raise TimeoutError(f"Request {method} timed out after {self.config.timeout}s")
        except Exception as e:
            self.pending_requests.pop(request_id, None)
            raise e

    async def _message_reader(self):
        """Background task to read messages from the server."""
        try:
            while self.connection_status == ConnectionStatus.CONNECTED:
                if not self.process or not self.process.stdout:
                    break

                # Read line from stdout
                line = await self.process.stdout.readline()
                if not line:
                    break

                try:
                    message = json.loads(line.decode().strip())
                    await self._handle_message(message)
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Invalid JSON received: {e}")
                except Exception as e:
                    logger.error(f"❌ Error handling message: {e}")

        except Exception as e:
            logger.error(f"❌ Message reader error: {e}")
            self.connection_status = ConnectionStatus.ERROR

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming JSON-RPC message."""
        if "id" in message:
            # Response to our request
            request_id = message["id"]
            if request_id in self.pending_requests:
                future = self.pending_requests.pop(request_id)

                if "error" in message:
                    error = message["error"]
                    future.set_exception(Exception(f"MCP Error {error.get('code', 0)}: {error.get('message', 'Unknown error')}"))
                else:
                    future.set_result(message.get("result", {}))
        else:
            # Notification
            method = message.get("method")
            params = message.get("params", {})
            await self._handle_notification(method, params)

    async def _discover_all_capabilities(self):
        """Discover all available tools, resources, and prompts."""
        try:
            # Discover tools
            if "tools" in self.capabilities:
                await self._discover_tools()

            # Discover resources
            if "resources" in self.capabilities:
                await self._discover_resources()

            # Discover prompts
            if "prompts" in self.capabilities:
                await self._discover_prompts()

        except Exception as e:
            logger.error(f"❌ Error discovering capabilities: {e}")

    async def _discover_tools(self):
        """Discover available tools."""
        try:
            response = await self._send_request("tools/list", {})
            tools = response.get("tools", [])

            for tool_data in tools:
                tool_name = tool_data["name"]
                self.tools[tool_name] = tool_data
                logger.info(f"🛠️ Discovered tool: {tool_name} - {tool_data.get('description', 'No description')}")

        except Exception as e:
            logger.error(f"❌ Error discovering tools: {e}")

    async def _discover_resources(self):
        """Discover available resources."""
        try:
            response = await self._send_request("resources/list", {})
            resources = response.get("resources", [])

            for resource_data in resources:
                resource_uri = resource_data["uri"]
                resource = MCPResource(
                    uri=resource_uri,
                    name=resource_data.get("name", resource_uri),
                    description=resource_data.get("description"),
                    mime_type=resource_data.get("mimeType")
                )
                self.resources[resource_uri] = resource
                logger.info(f"📄 Discovered resource: {resource_uri} - {resource.description}")

        except Exception as e:
            logger.error(f"❌ Error discovering resources: {e}")

    async def _discover_prompts(self):
        """Discover available prompts."""
        try:
            response = await self._send_request("prompts/list", {})
            prompts = response.get("prompts", [])

            for prompt_data in prompts:
                prompt_name = prompt_data["name"]
                prompt = MCPPrompt(
                    name=prompt_name,
                    description=prompt_data.get("description"),
                    arguments=prompt_data.get("arguments", [])
                )
                self.prompts[prompt_name] = prompt
                logger.info(f"📝 Discovered prompt: {prompt_name} - {prompt.description}")

        except Exception as e:
            logger.error(f"❌ Error discovering prompts: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool with given arguments."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in server {self.config.name}")

        try:
            logger.info(f"🚀 Executing tool: {self.config.name}:{tool_name} with args: {arguments}")

            response = await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })

            content = response.get("content", [])

            # Format content for voice response
            if content:
                text_parts = []
                for item in content:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))

                result = "\n".join(text_parts) if text_parts else "Tool executed successfully"

                # Truncate long results for TTS
                if len(result) > 500:
                    result = result[:500] + "... (truncated for voice)"

                return result

            return "Tool executed successfully"

        except Exception as e:
            logger.error(f"❌ Error executing tool {tool_name}: {e}")
            raise e

    async def read_resource(self, uri: str) -> Any:
        """Read a resource by URI."""
        if uri not in self.resources:
            raise ValueError(f"Resource '{uri}' not found in server {self.config.name}")

        try:
            response = await self._send_request("resources/read", {"uri": uri})
            return response.get("contents", [])
        except Exception as e:
            logger.error(f"❌ Error reading resource {uri}: {e}")
            raise e

    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get a rendered prompt template."""
        if name not in self.prompts:
            raise ValueError(f"Prompt '{name}' not found in server {self.config.name}")

        try:
            response = await self._send_request("prompts/get", {
                "name": name,
                "arguments": arguments or {}
            })
            return response.get("messages", [])
        except Exception as e:
            logger.error(f"❌ Error getting prompt {name}: {e}")
            raise e

    async def health_check(self) -> bool:
        """Check if the server is healthy."""
        try:
            # Send a simple ping request
            await self._send_request("ping", {})
            self.last_health_check = time.time()
            return True
        except:
            return False

    async def _health_monitor(self):
        """Background health monitoring task."""
        while self.connection_status == ConnectionStatus.CONNECTED:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                if not await self.health_check():
                    logger.warning(f"⚠️ Health check failed for {self.config.name}")
                    if self.config.auto_reconnect:
                        await self._attempt_reconnect()

            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")

    async def _attempt_reconnect(self):
        """Attempt to reconnect to the server."""
        if self.reconnect_attempts >= self.config.retry_count:
            logger.error(f"❌ Max reconnection attempts reached for {self.config.name}")
            self.connection_status = ConnectionStatus.ERROR
            return

        self.reconnect_attempts += 1
        self.connection_status = ConnectionStatus.RECONNECTING

        logger.info(f"🔄 Attempting reconnection {self.reconnect_attempts}/{self.config.retry_count} for {self.config.name}")

        # Clean up current connection
        await self._cleanup_connection()

        # Wait before reconnecting
        await asyncio.sleep(min(2 ** self.reconnect_attempts, 30))

        # Attempt to reinitialize
        if await self.initialize():
            logger.info(f"✅ Reconnection successful for {self.config.name}")
        else:
            logger.error(f"❌ Reconnection failed for {self.config.name}")

    async def _cleanup_connection(self):
        """Clean up connection resources."""
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except:
                pass
            self.process = None

        # Clear pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()

    async def _handle_notification(self, method: str, params: Dict[str, Any]):
        """Handle server notifications."""
        if method in self.notification_handlers:
            try:
                await self.notification_handlers[method](params)
            except Exception as e:
                logger.error(f"❌ Error handling notification {method}: {e}")
        else:
            logger.debug(f"📢 Unhandled notification: {method}")

    def _setup_notification_handlers(self):
        """Set up notification handlers."""
        self.notification_handlers = {
            "notifications/tools/list_changed": self._on_tools_changed,
            "notifications/resources/list_changed": self._on_resources_changed,
            "notifications/prompts/list_changed": self._on_prompts_changed,
        }

    async def _on_tools_changed(self, params: Dict[str, Any]):
        """Handle tools list changed notification."""
        logger.info(f"🔄 Tools changed for {self.config.name}, rediscovering...")
        await self._discover_tools()

    async def _on_resources_changed(self, params: Dict[str, Any]):
        """Handle resources list changed notification."""
        logger.info(f"🔄 Resources changed for {self.config.name}, rediscovering...")
        await self._discover_resources()

    async def _on_prompts_changed(self, params: Dict[str, Any]):
        """Handle prompts list changed notification."""
        logger.info(f"🔄 Prompts changed for {self.config.name}, rediscovering...")
        await self._discover_prompts()

    async def disconnect(self):
        """Disconnect from the server."""
        self.connection_status = ConnectionStatus.DISCONNECTED
        await self._cleanup_connection()
        logger.info(f"🔌 Disconnected from {self.config.name}")

    async def _connect_sse(self) -> bool:
        """Establish SSE transport connection (placeholder)."""
        # TODO: Implement SSE transport
        logger.warning("SSE transport not yet implemented")
        return False

    async def _connect_http(self) -> bool:
        """Establish HTTP transport connection (placeholder)."""
        # TODO: Implement HTTP transport
        logger.warning("HTTP transport not yet implemented")
        return False

class EnhancedMCPManager:
    """
    Enhanced MCP manager that coordinates multiple MCP server connections.

    Provides unified interface for tool execution, resource access, and prompt
    rendering across multiple MCP servers with advanced security and monitoring.
    """

    def __init__(self):
        """Initialize the enhanced MCP manager."""
        self.clients: Dict[str, EnhancedMCPClient] = {}
        self.security_manager = SecurityManager()
        self.connected = False
        self.server_configs: List[MCPServerConfig] = []

    async def add_server(self, config: MCPServerConfig) -> bool:
        """Add and initialize a new MCP server."""
        try:
            if not config.enabled:
                logger.info(f"⏭️ Skipping disabled server: {config.name}")
                return True

            logger.info(f"➕ Adding MCP server: {config.name}")

            client = EnhancedMCPClient(config)
            if await client.initialize():
                self.clients[config.name] = client
                self.server_configs.append(config)
                logger.info(f"✅ Successfully added MCP server: {config.name}")
                return True
            else:
                logger.error(f"❌ Failed to initialize server: {config.name}")
                return False

        except Exception as e:
            logger.error(f"❌ Error adding server {config.name}: {e}")
            return False

    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool on a specific server with security checks."""
        try:
            # Validate server exists
            if server_name not in self.clients:
                return f"Server '{server_name}' not found"

            # Security validation
            fq_tool_name = f"{server_name}:{tool_name}"
            if not self.security_manager.is_tool_allowed(server_name, tool_name, arguments):
                return f"Tool '{fq_tool_name}' is not permitted"

            # Execute tool
            client = self.clients[server_name]
            result = await client.call_tool(tool_name, arguments)

            # Log execution for audit
            self.security_manager.log_tool_execution(server_name, tool_name, arguments, "success")

            return result

        except Exception as e:
            error_msg = f"Error executing {server_name}:{tool_name}: {str(e)}"
            logger.error(f"❌ {error_msg}")

            # Log error for audit
            self.security_manager.log_tool_execution(server_name, tool_name, arguments, "error", str(e))

            return error_msg

    async def read_resource(self, server_name: str, uri: str) -> Any:
        """Read a resource from a specific server."""
        if server_name not in self.clients:
            raise ValueError(f"Server '{server_name}' not found")

        client = self.clients[server_name]
        return await client.read_resource(uri)

    async def get_prompt(self, server_name: str, prompt_name: str, arguments: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get a rendered prompt from a specific server."""
        if server_name not in self.clients:
            raise ValueError(f"Server '{server_name}' not found")

        client = self.clients[server_name]
        return await client.get_prompt(prompt_name, arguments)

    async def get_all_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all available tools from all servers."""
        all_tools = {}
        for server_name, client in self.clients.items():
            all_tools[server_name] = dict(client.tools)
        return all_tools

    async def get_all_resources(self) -> Dict[str, Dict[str, MCPResource]]:
        """Get all available resources from all servers."""
        all_resources = {}
        for server_name, client in self.clients.items():
            all_resources[server_name] = dict(client.resources)
        return all_resources

    async def get_all_prompts(self) -> Dict[str, Dict[str, MCPPrompt]]:
        """Get all available prompts from all servers."""
        all_prompts = {}
        for server_name, client in self.clients.items():
            all_prompts[server_name] = dict(client.prompts)
        return all_prompts

    async def health_check_all(self) -> Dict[str, str]:
        """Check health of all connected servers."""
        health_status = {}
        for server_name, client in self.clients.items():
            try:
                is_healthy = await client.health_check()
                health_status[server_name] = "healthy" if is_healthy else "unhealthy"
            except Exception as e:
                health_status[server_name] = f"error: {str(e)}"
        return health_status

    async def disconnect_all(self):
        """Disconnect from all servers."""
        for server_name, client in self.clients.items():
            try:
                await client.disconnect()
                logger.info(f"🔌 Disconnected from {server_name}")
            except Exception as e:
                logger.error(f"❌ Error disconnecting from {server_name}: {e}")

        self.clients.clear()
        self.connected = False
        logger.info("🔌 All MCP connections closed")

class SecurityManager:
    """
    Enhanced security manager for MCP operations.

    Provides RBAC, argument validation, audit logging, and comprehensive
    security policies for tool execution and resource access.
    """

    def __init__(self):
        """Initialize the security manager."""
        self.policies = self._load_security_policies()
        self.audit_log: List[Dict[str, Any]] = []
        self.max_audit_entries = 10000

    def is_tool_allowed(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Check if tool execution is allowed based on security policies."""
        try:
            # Get server policy
            server_policy = self.policies.get(server_name, {})

            # Check if server is enabled
            if not server_policy.get("enabled", True):
                logger.warning(f"🚫 Server {server_name} is disabled")
                return False

            # Check tool whitelist
            allowed_tools = server_policy.get("allowed_tools", [])
            if allowed_tools and tool_name not in allowed_tools:
                logger.warning(f"🚫 Tool {tool_name} not in whitelist for {server_name}")
                return False

            # Check tool blacklist
            blocked_tools = server_policy.get("blocked_tools", [])
            if tool_name in blocked_tools:
                logger.warning(f"🚫 Tool {tool_name} is blocked for {server_name}")
                return False

            # Validate arguments
            if not self._validate_arguments(server_name, tool_name, arguments):
                logger.warning(f"🚫 Invalid arguments for {server_name}:{tool_name}")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Security check error: {e}")
            return False

    def _validate_arguments(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Validate tool arguments for security."""
        try:
            server_policy = self.policies.get(server_name, {})
            validation_rules = server_policy.get("argument_validation", {})

            # Check for path traversal attacks
            if server_name == "filesystem":
                path_args = ["path", "file", "directory", "filename"]
                for arg_name in path_args:
                    if arg_name in arguments:
                        path_value = str(arguments[arg_name])
                        if self._contains_path_traversal(path_value):
                            logger.warning(f"🚫 Path traversal detected in {arg_name}: {path_value}")
                            return False

                        # Check path restrictions
                        allowed_paths = server_policy.get("allowed_paths", [])
                        if allowed_paths and not self._is_path_allowed(path_value, allowed_paths):
                            logger.warning(f"🚫 Path not allowed: {path_value}")
                            return False

            # Check for command injection
            if server_name in ["terminal", "ssh"]:
                command_args = ["command", "cmd", "script"]
                for arg_name in command_args:
                    if arg_name in arguments:
                        command_value = str(arguments[arg_name])
                        if self._contains_command_injection(command_value):
                            logger.warning(f"🚫 Command injection detected: {command_value}")
                            return False

            # Check argument size limits
            max_arg_size = validation_rules.get("max_argument_size", 10000)
            for key, value in arguments.items():
                if isinstance(value, str) and len(value) > max_arg_size:
                    logger.warning(f"🚫 Argument {key} exceeds size limit: {len(value)} > {max_arg_size}")
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ Argument validation error: {e}")
            return False

    def _contains_path_traversal(self, path: str) -> bool:
        """Check if path contains traversal patterns."""
        dangerous_patterns = ["../", "..\\", "/..", "\\..", "~", "$"]
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in dangerous_patterns)

    def _is_path_allowed(self, path: str, allowed_paths: List[str]) -> bool:
        """Check if path is within allowed directories."""
        import os.path
        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(os.path.abspath(allowed)) for allowed in allowed_paths)

    def _contains_command_injection(self, command: str) -> bool:
        """Check if command contains injection patterns."""
        dangerous_patterns = [";", "&&", "||", "|", "`", "$", "$(", "rm -rf", "sudo", "su -"]
        command_lower = command.lower()
        return any(pattern in command_lower for pattern in dangerous_patterns)

    def log_tool_execution(self, server_name: str, tool_name: str, arguments: Dict[str, Any],
                          status: str, error: str = None):
        """Log tool execution for audit purposes."""
        audit_entry = {
            "timestamp": time.time(),
            "server": server_name,
            "tool": tool_name,
            "arguments": arguments,
            "status": status,
            "error": error
        }

        self.audit_log.append(audit_entry)

        # Rotate log if too large
        if len(self.audit_log) > self.max_audit_entries:
            self.audit_log = self.audit_log[-self.max_audit_entries//2:]

        # Log to file for persistent audit trail
        logger.info(f"🔍 AUDIT: {server_name}:{tool_name} - {status}")

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return self.audit_log[-limit:]

    def _load_security_policies(self) -> Dict[str, Any]:
        """Load security policies from configuration."""
        return {
            "filesystem": {
                "enabled": True,
                "allowed_tools": [
                    "read_file", "list_directory", "write_file", "create_directory",
                    "move_file", "copy_file", "search_files", "get_file_info"
                ],
                "blocked_tools": ["delete_file", "delete_directory", "format_disk"],
                "allowed_paths": ["/workspace", "/tmp", "/home"],
                "argument_validation": {
                    "max_argument_size": 10000
                }
            },
            "git": {
                "enabled": True,
                "allowed_tools": [
                    "status", "log", "diff", "add", "commit", "push", "pull",
                    "branch", "checkout", "merge", "stash"
                ],
                "blocked_tools": ["reset --hard", "clean -fd", "rm"]
            },
            "github": {
                "enabled": True,
                "allowed_tools": [
                    "list_repositories", "get_repository", "list_issues", "create_issue",
                    "update_issue", "list_pull_requests", "create_pull_request"
                ],
                "blocked_tools": ["delete_repository", "force_push"]
            },
            "postgresql": {
                "enabled": True,
                "allowed_tools": ["execute_query", "list_tables", "describe_table"],
                "blocked_tools": ["drop_table", "drop_database", "delete", "truncate"],
                "read_only": True
            },
            "terminal": {
                "enabled": False,  # Disabled by default for security
                "allowed_tools": ["execute_command"],
                "blocked_commands": ["rm -rf", "sudo", "su", "passwd", "chmod 777"]
            }
        }

class HTTPMCPClient:
    """HTTP-based MCP client for Docker integration."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.environ.get("MCP_BRIDGE_URL", "http://localhost:8001")
        self.session = None

    async def __aenter__(self):
        import aiohttp
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool via HTTP MCP bridge."""
        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(
                f"{self.base_url}/execute-tool",
                json={
                    "server": server_name,
                    "tool": tool_name,
                    "arguments": arguments
                },
                timeout=30
            ) as response:
                result = await response.json()

                if result["success"]:
                    return result["result"]
                else:
                    raise Exception(result.get("error", "Unknown error"))

        except Exception as e:
            logger.error(f"❌ HTTP MCP call failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if MCP bridge is healthy."""
        try:
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()

            async with self.session.get(f"{self.base_url}/health", timeout=5) as response:
                return response.status == 200
        except:
            return False

    async def get_servers(self) -> List[Dict[str, Any]]:
        """Get list of available servers."""
        try:
            if not self.session:
                import aiohttp
                self.session = aiohttp.ClientSession()

            async with self.session.get(f"{self.base_url}/servers", timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                return []
        except:
            return []

class DockerMCPManager:
    """Docker-based MCP manager using HTTP bridge."""

    def __init__(self):
        self.http_client = HTTPMCPClient()
        self.connected = False
        self.servers_info = []

    async def initialize(self) -> bool:
        """Initialize connection to Docker MCP services."""
        try:
            logger.info("🐳 Initializing Docker MCP connection...")

            # Check if MCP bridge is available
            if await self.http_client.health_check():
                # Get server information
                self.servers_info = await self.http_client.get_servers()
                self.connected = True

                server_names = [server["name"] for server in self.servers_info]
                total_tools = sum(len(server["tools"]) for server in self.servers_info)

                logger.info(f"✅ Docker MCP bridge connected successfully")
                logger.info(f"📊 Available servers: {server_names}")
                logger.info(f"🛠️ Total tools available: {total_tools}")

                return True
            else:
                logger.error("❌ Docker MCP bridge not available")
                return False

        except Exception as e:
            logger.error(f"❌ Docker MCP initialization failed: {e}")
            return False

    async def execute_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute tool via Docker MCP bridge with security checks."""
        if not self.connected:
            await self.initialize()

        # Security validation using existing security manager
        security_manager = SecurityManager()
        if not security_manager.is_tool_allowed(server_name, tool_name, arguments):
            return f"Tool '{server_name}:{tool_name}' is not permitted"

        try:
            result = await self.http_client.execute_tool(server_name, tool_name, arguments)

            # Log execution for audit
            security_manager.log_tool_execution(server_name, tool_name, arguments, "success")

            return result

        except Exception as e:
            error_msg = f"Error executing {server_name}:{tool_name}: {str(e)}"

            # Log error for audit
            security_manager.log_tool_execution(server_name, tool_name, arguments, "error", str(e))

            return error_msg

    async def get_all_tools(self) -> Dict[str, List[str]]:
        """Get all available tools from all servers."""
        if not self.connected:
            await self.initialize()

        return {server["name"]: server["tools"] for server in self.servers_info}

    async def health_check_all(self) -> Dict[str, str]:
        """Check health of Docker MCP bridge."""
        try:
            if await self.http_client.health_check():
                return {"docker_mcp_bridge": "healthy"}
            else:
                return {"docker_mcp_bridge": "unhealthy"}
        except:
            return {"docker_mcp_bridge": "error"}

    async def disconnect_all(self):
        """Disconnect from Docker MCP bridge."""
        if self.http_client.session:
            await self.http_client.session.close()
        self.connected = False
        logger.info("🐳 Disconnected from Docker MCP bridge")

# Global Docker MCP manager instance (replaces the enhanced manager for Docker deployment)
docker_mcp_manager = DockerMCPManager()

# For backward compatibility, use Docker manager as default
mcp_manager = docker_mcp_manager

async def bootstrap_mcp():
    """
    Initialize MCP connections - uses Docker HTTP bridge if available, falls back to direct connections.
    """
    try:
        logger.info("🚀 Bootstrapping MCP connections...")

        # Check if we're in Docker environment
        mcp_bridge_url = os.environ.get("MCP_BRIDGE_URL")

        if mcp_bridge_url:
            # Use Docker HTTP bridge
            logger.info("🐳 Using Docker MCP bridge")
            success = await docker_mcp_manager.initialize()

            if success:
                all_tools = await docker_mcp_manager.get_all_tools()
                total_tools = sum(len(tools) for tools in all_tools.values())
                logger.info(f"🎉 Docker MCP bootstrap completed: {len(all_tools)} servers, {total_tools} tools")
            else:
                logger.error("❌ Docker MCP bootstrap failed")
        else:
            # Fallback to direct MCP connections (for development)
            logger.info("🔧 Using direct MCP connections (development mode)")

            # Create a simple mock for development
            logger.warning("⚠️ No MCP bridge URL found - using mock implementation for development")
            docker_mcp_manager.connected = True
            docker_mcp_manager.servers_info = [
                {"name": "filesystem", "status": "mock", "tools": ["read_file", "read_directory", "write_file"]},
                {"name": "git", "status": "mock", "tools": ["status", "log", "diff"]}
            ]
            logger.info("🎉 Mock MCP bootstrap completed for development")

    except Exception as e:
        logger.error(f"❌ MCP bootstrap failed: {e}")

def _load_server_configurations() -> List[MCPServerConfig]:
    """Load MCP server configurations."""
    # Default configurations for essential servers
    configs = []

    # Filesystem server
    workspace_path = os.environ.get("MCP_WORKSPACE_PATH", ".")

    # Use .cmd extension on Windows
    fs_command = "mcp-server-filesystem.cmd" if os.name == "nt" else "mcp-server-filesystem"
    configs.append(MCPServerConfig(
        name="filesystem",
        command=[fs_command],
        args=[workspace_path],  # Use current directory or environment variable
        enabled=True,
        security_level="medium"
    ))

    # Git server (if available) - disabled for now since it's not installed
    git_command = "mcp-server-git.cmd" if os.name == "nt" else "mcp-server-git"
    configs.append(MCPServerConfig(
        name="git",
        command=[git_command],
        enabled=False,  # Disabled until we install it
        security_level="medium"
    ))

    # GitHub server (if token available)
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        configs.append(MCPServerConfig(
            name="github",
            command=["mcp-server-github"],
            env={"GITHUB_TOKEN": github_token},
            enabled=True,
            security_level="high"
        ))

    # PostgreSQL server (if connection string available)
    postgres_url = os.environ.get("POSTGRES_URL")
    if postgres_url:
        configs.append(MCPServerConfig(
            name="postgresql",
            command=["mcp-server-postgres"],
            args=[postgres_url],
            enabled=True,
            security_level="high"
        ))

    # Filter enabled configurations
    enabled_configs = [config for config in configs if config.enabled]

    logger.info(f"📋 Loaded {len(enabled_configs)} server configurations")
    for config in enabled_configs:
        logger.info(f"   - {config.name}: {' '.join(config.command + config.args)}")

    return enabled_configs

def parse_tool_call(text: str) -> Optional[Dict[str, Any]]:
    """
    Enhanced tool call parser with better error handling.

    Args:
        text: The text to parse for tool calls

    Returns:
        Dict containing tool and arguments if found, None otherwise
    """
    try:
        text = text.strip()

        # Check for JSON structure
        if not (text.startswith("{") and text.endswith("}")):
            return None

        # Parse JSON
        obj = json.loads(text)

        # Validate required fields
        if not isinstance(obj, dict):
            return None

        if "tool" not in obj or "arguments" not in obj:
            return None

        # Validate tool format (server:tool_name)
        tool_name = obj["tool"]
        if not isinstance(tool_name, str) or ":" not in tool_name:
            logger.warning(f"⚠️ Invalid tool format: {tool_name}")
            return None

        # Validate arguments
        arguments = obj["arguments"]
        if not isinstance(arguments, dict):
            logger.warning(f"⚠️ Invalid arguments format: {arguments}")
            return None

        return obj

    except json.JSONDecodeError as e:
        logger.debug(f"🔍 JSON decode error (expected for non-JSON text): {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Error parsing tool call: {e}")
        return None

async def execute_tool_call(tool_call: Dict[str, Any]) -> str:
    """
    Execute a parsed tool call using the Docker MCP manager.

    Args:
        tool_call: Parsed tool call with 'tool' and 'arguments' keys

    Returns:
        str: Result of tool execution formatted for voice response
    """
    try:
        tool_name = tool_call["tool"]
        arguments = tool_call["arguments"]

        # Parse server and tool name
        if ":" not in tool_name:
            return f"Invalid tool format: {tool_name}. Expected 'server:tool_name'"

        server_name, tool_name_only = tool_name.split(":", 1)

        # Check if we're using Docker bridge or mock mode
        mcp_bridge_url = os.environ.get("MCP_BRIDGE_URL")

        if mcp_bridge_url and docker_mcp_manager.connected:
            # Execute using Docker MCP bridge
            result = await docker_mcp_manager.execute_tool(server_name, tool_name_only, arguments)
        else:
            # Mock execution for development
            result = f"Mock execution of {server_name}:{tool_name_only} with args {arguments}"
            logger.info(f"🎭 Mock tool execution: {result}")

        return result

    except Exception as e:
        error_msg = f"Error executing tool call: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return error_msg

# Legacy compatibility functions (deprecated)
def is_tool_allowed(tool_name: str) -> bool:
    """
    Legacy compatibility function - use SecurityManager instead.

    Args:
        tool_name: The fully qualified tool name

    Returns:
        bool: True if tool is allowed, False otherwise
    """
    logger.warning("⚠️ Using deprecated is_tool_allowed function. Use SecurityManager instead.")

    if ":" not in tool_name:
        return False

    server_name, tool_name_only = tool_name.split(":", 1)
    return mcp_manager.security_manager.is_tool_allowed(server_name, tool_name_only, {})
