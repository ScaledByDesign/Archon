# WSL Integration for Enhanced MCP Implementation

## 🎯 Why WSL for MCP Integration?

### Current Windows Issues
- ❌ MCP servers expect Unix-like environment
- ❌ Path handling differences (forward vs backslashes)
- ❌ Executable format issues (.cmd vs native binaries)
- ❌ Environment variable handling inconsistencies
- ❌ Process management complexities

### WSL Benefits
- ✅ **Native Unix Environment**: MCP servers run as intended
- ✅ **Consistent Paths**: Standard Unix path handling
- ✅ **Better Process Management**: Native stdio handling
- ✅ **Package Management**: Easy npm/pip installations
- ✅ **Development Tools**: Git, SSH, terminal tools work seamlessly
- ✅ **Performance**: Near-native Linux performance
- ✅ **Integration**: Seamless Windows-WSL file system access

## 🏗️ WSL Integration Architecture

```
Windows Host (RealtimeVoiceChat)
├── FastAPI Server (Python)
├── Speech Pipeline (STT/TTS)
└── MCP Bridge
    │
    └── WSL2 Ubuntu
        ├── Node.js + MCP Servers
        ├── Python MCP SDK
        ├── Git + Development Tools
        └── File System Access
```

## 🚀 Implementation Plan

### Phase 1: WSL Setup & Configuration

#### 1.1 WSL Installation
```powershell
# Install WSL2 with Ubuntu
wsl --install -d Ubuntu

# Update to WSL2
wsl --set-default-version 2
wsl --set-version Ubuntu 2
```

#### 1.2 Development Environment Setup
```bash
# Inside WSL Ubuntu
sudo apt update && sudo apt upgrade -y

# Install Node.js (latest LTS)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install development tools
sudo apt install git curl wget build-essential -y
```

#### 1.3 MCP Servers Installation
```bash
# Install MCP servers in WSL
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-github

# Install Python MCP SDK
pip3 install mcp

# Verify installations
which mcp-server-filesystem
which mcp-server-git
mcp-server-filesystem --help
```

### Phase 2: Enhanced MCP Bridge for WSL

#### 2.1 WSL Command Execution
```python
class WSLMCPClient(EnhancedMCPClient):
    """Enhanced MCP client that executes commands in WSL."""
    
    def __init__(self, config: MCPServerConfig):
        super().__init__(config)
        self.wsl_distro = config.wsl_distro or "Ubuntu"
    
    async def _connect_stdio(self) -> bool:
        """Establish stdio connection via WSL."""
        try:
            # Build WSL command
            wsl_command = [
                "wsl", "-d", self.wsl_distro, "--"
            ] + self.config.command + self.config.args
            
            # Prepare environment for WSL
            env = {**os.environ, **self.config.env}
            
            # Start process in WSL
            self.process = await asyncio.create_subprocess_exec(
                *wsl_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self._convert_path_to_wsl(os.getcwd())
            )
            
            logger.info(f"🐧 Started MCP server in WSL: {' '.join(wsl_command)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start WSL connection: {e}")
            return False
    
    def _convert_path_to_wsl(self, windows_path: str) -> str:
        """Convert Windows path to WSL path."""
        # Convert C:\path\to\file to /mnt/c/path/to/file
        if len(windows_path) >= 2 and windows_path[1] == ':':
            drive = windows_path[0].lower()
            path = windows_path[2:].replace('\\', '/')
            return f"/mnt/{drive}{path}"
        return windows_path.replace('\\', '/')
```

#### 2.2 Enhanced Server Configuration
```python
@dataclass
class WSLMCPServerConfig(MCPServerConfig):
    """WSL-specific MCP server configuration."""
    wsl_distro: str = "Ubuntu"
    wsl_user: str = None
    mount_paths: Dict[str, str] = field(default_factory=dict)

def _load_wsl_server_configurations() -> List[WSLMCPServerConfig]:
    """Load WSL-optimized server configurations."""
    configs = []
    
    # Filesystem server with WSL paths
    configs.append(WSLMCPServerConfig(
        name="filesystem",
        command=["mcp-server-filesystem"],
        args=["/mnt/c/zoi/apps/voice"],  # WSL path to workspace
        wsl_distro="Ubuntu",
        enabled=True,
        security_level="medium"
    ))
    
    # Git server
    configs.append(WSLMCPServerConfig(
        name="git",
        command=["mcp-server-git"],
        wsl_distro="Ubuntu",
        enabled=True,
        security_level="medium"
    ))
    
    # GitHub server
    github_token = os.environ.get("GITHUB_TOKEN")
    if github_token:
        configs.append(WSLMCPServerConfig(
            name="github",
            command=["mcp-server-github"],
            env={"GITHUB_TOKEN": github_token},
            wsl_distro="Ubuntu",
            enabled=True,
            security_level="high"
        ))
    
    return configs
```

### Phase 3: File System Integration

#### 3.1 Path Translation
```python
class WSLPathManager:
    """Manages path translation between Windows and WSL."""
    
    @staticmethod
    def windows_to_wsl(path: str) -> str:
        """Convert Windows path to WSL mount path."""
        if os.path.isabs(path) and len(path) >= 2 and path[1] == ':':
            drive = path[0].lower()
            wsl_path = path[2:].replace('\\', '/')
            return f"/mnt/{drive}{wsl_path}"
        return path.replace('\\', '/')
    
    @staticmethod
    def wsl_to_windows(path: str) -> str:
        """Convert WSL path to Windows path."""
        if path.startswith('/mnt/'):
            parts = path[5:].split('/', 1)
            if len(parts) >= 1:
                drive = parts[0].upper()
                rest = parts[1] if len(parts) > 1 else ""
                return f"{drive}:\\{rest.replace('/', '\\')}"
        return path
    
    @staticmethod
    def normalize_for_voice(path: str) -> str:
        """Normalize path for voice response."""
        # Convert to relative path for cleaner voice output
        if path.startswith('/mnt/c/zoi/apps/voice/'):
            return path.replace('/mnt/c/zoi/apps/voice/', './')
        return path
```

#### 3.2 Enhanced Tool Execution
```python
async def execute_wsl_tool_call(tool_call: Dict[str, Any]) -> str:
    """Execute tool call with WSL path translation."""
    try:
        tool_name = tool_call["tool"]
        arguments = tool_call["arguments"]
        
        # Translate Windows paths to WSL paths in arguments
        translated_args = {}
        for key, value in arguments.items():
            if key in ["path", "file", "directory", "filename"] and isinstance(value, str):
                translated_args[key] = WSLPathManager.windows_to_wsl(value)
            else:
                translated_args[key] = value
        
        # Execute with translated arguments
        server_name, tool_name_only = tool_name.split(":", 1)
        result = await mcp_manager.execute_tool(server_name, tool_name_only, translated_args)
        
        # Translate paths in result back for voice response
        result = WSLPathManager.normalize_for_voice(result)
        
        return result
        
    except Exception as e:
        return f"Error executing WSL tool call: {str(e)}"
```

### Phase 4: Development Tools Integration

#### 4.1 Git Operations in WSL
```bash
# Configure Git in WSL
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set up SSH keys for GitHub (if needed)
ssh-keygen -t ed25519 -C "your.email@example.com"
```

#### 4.2 Database Connections
```bash
# Install database tools in WSL
sudo apt install postgresql-client mysql-client redis-tools -y

# Install database MCP servers
npm install -g @modelcontextprotocol/server-postgres
npm install -g @modelcontextprotocol/server-mysql
```

### Phase 5: Testing & Validation

#### 5.1 WSL Integration Test
```python
async def test_wsl_integration():
    """Test WSL-based MCP integration."""
    print("🐧 Testing WSL MCP Integration...")
    
    # Test WSL availability
    result = subprocess.run(["wsl", "--status"], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ WSL not available")
        return False
    
    print("✅ WSL is available")
    
    # Test MCP server availability in WSL
    test_commands = [
        ["wsl", "--", "which", "mcp-server-filesystem"],
        ["wsl", "--", "which", "node"],
        ["wsl", "--", "which", "npm"]
    ]
    
    for cmd in test_commands:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {cmd[-1]} available in WSL")
        else:
            print(f"❌ {cmd[-1]} not found in WSL")
    
    return True
```

## 🎯 Benefits of WSL Integration

### Technical Benefits
- **Native MCP Environment**: Servers run in their intended Unix environment
- **Better Performance**: Near-native Linux performance for MCP operations
- **Simplified Path Handling**: No more Windows path conversion issues
- **Process Management**: Proper stdio handling and process lifecycle
- **Package Management**: Easy installation of development tools

### Developer Experience
- **Familiar Environment**: Standard Unix tools and commands
- **Better Debugging**: Native Linux debugging tools
- **Consistent Behavior**: Same behavior as production Linux environments
- **Tool Ecosystem**: Access to full Linux development ecosystem

### Voice Command Examples
```
"List files in the current directory" → WSL: ls -la /mnt/c/zoi/apps/voice
"Check git status" → WSL: git status
"Read package.json" → WSL: cat /mnt/c/zoi/apps/voice/package.json
"Install npm package lodash" → WSL: npm install lodash
```

## 🚀 Implementation Steps

1. **Install WSL2 with Ubuntu**
2. **Set up development environment in WSL**
3. **Install MCP servers in WSL**
4. **Update MCP bridge to use WSL commands**
5. **Implement path translation utilities**
6. **Test complete integration**
7. **Update documentation and setup scripts**

This WSL integration will provide a robust, native Unix environment for MCP servers while maintaining seamless integration with the Windows-based RealtimeVoiceChat application.
