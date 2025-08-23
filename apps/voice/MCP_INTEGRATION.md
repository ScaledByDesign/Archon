# MCP Integration for RealtimeVoiceChat

This document describes the integration of Model Context Protocol (MCP) tools with the RealtimeVoiceChat system, enabling voice-controlled file operations and other tool executions.

## Overview

The MCP integration allows users to execute real tools through voice commands. When the AI detects a tool call request, it executes the appropriate MCP tool and speaks the result back to the user.

### Architecture

```
Voice Input → STT → LLM → Tool Call Detection → MCP Execution → TTS → Voice Output
```

**Key Components:**
- `mcp_bridge.py`: Core MCP integration and tool management
- `speech_pipeline_manager.py`: Modified to detect and execute tool calls
- `server.py`: Updated with MCP initialization
- `system_prompt.txt`: Enhanced with tool call instructions

## Features

✅ **Voice-Controlled File Operations**
- Read files and directories
- Write files
- Create directories
- Search for files

✅ **Security Controls**
- Tool whitelisting system
- Blocked dangerous operations (delete, etc.)
- Input validation and sanitization

✅ **Error Handling**
- Graceful failure handling
- User-friendly error messages
- Fallback to normal conversation

✅ **Real-time Integration**
- Low-latency tool execution
- Streaming response integration
- Maintains conversation flow

## Installation & Setup

### Prerequisites

1. **Node.js and npm** (for MCP servers)
2. **Python 3.9+** (RealtimeVoiceChat requires < 3.13)
3. **MCP Python SDK** (already included in requirements.txt)

### MCP Server Installation

```bash
# Install filesystem MCP server
npm install -g @modelcontextprotocol/server-filesystem

# Verify installation
mcp-server-filesystem /path/to/workspace
```

### Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

## Configuration

### Tool Whitelist

Edit `ALLOWED_TOOLS` in `mcp_bridge.py` to control which tools can be executed:

```python
ALLOWED_TOOLS = {
    "fs:read_file",           # Read file contents
    "fs:read_directory",      # List directory contents  
    "fs:write_file",          # Write content to file
    "fs:create_directory",    # Create new directory
    "fs:move_file",           # Move/rename files
    "fs:search_files",        # Search for files by pattern
}
```

### MCP Server Configuration

Modify `bootstrap_mcp()` in `mcp_bridge.py` to configure server connections:

```python
# Connect to filesystem server with custom root path
fs_success = await mcp_manager.connect(
    "fs", 
    ["mcp-server-filesystem", "/your/workspace/path"]
)
```

## Usage Examples

### Voice Commands

**File Operations:**
- "Read the contents of README.md"
- "List the files in the current directory"
- "Create a new file called notes.txt with the content 'Hello World'"
- "Create a directory called new_project"
- "Search for all Python files in the current directory"

### Tool Call Format

The LLM emits structured JSON for tool calls:

```json
{"tool": "fs:read_file", "arguments": {"path": "README.md"}}
{"tool": "fs:read_directory", "arguments": {"path": "."}}
{"tool": "fs:write_file", "arguments": {"path": "notes.txt", "content": "Hello World"}}
```

## Testing

Run the integration test to verify everything works:

```bash
cd apps/voice
python test_mcp.py
```

Expected output:
```
🚀 Testing MCP Integration...
✅ MCP bootstrap successful
✅ Tool discovery successful
✅ Tool call parsing test completed
✅ Tool whitelisting test completed
✅ Tool execution successful
✅ Error handling test completed
🎉 All MCP integration tests completed successfully!
```

## Development Notes

### Current Implementation Status

- ✅ Core MCP bridge architecture
- ✅ Tool call detection and parsing
- ✅ Security controls and whitelisting
- ✅ Error handling and fallbacks
- ✅ Integration with speech pipeline
- ⚠️ Using mock implementation (real MCP connection needs refinement)

### Mock vs Real MCP

Currently using a mock implementation for testing. To enable real MCP connections:

1. Fix the `stdio_client` connection handling in `mcp_bridge.py`
2. Ensure MCP servers are running and accessible
3. Update the `connect()` method to use proper MCP protocol

### Adding New Tools

1. Install the MCP server: `npm install -g @modelcontextprotocol/server-<name>`
2. Add connection in `bootstrap_mcp()`
3. Update `ALLOWED_TOOLS` whitelist
4. Update system prompt with new tool examples

## Troubleshooting

### Common Issues

**MCP Server Not Found:**
```bash
# Verify MCP server installation
which mcp-server-filesystem
npm list -g @modelcontextprotocol/server-filesystem
```

**Tool Not Allowed:**
- Check `ALLOWED_TOOLS` whitelist in `mcp_bridge.py`
- Verify tool name format: `server:tool_name`

**Connection Errors:**
- Ensure MCP servers are accessible
- Check file permissions for workspace paths
- Verify Node.js and npm are properly installed

### Debug Mode

Enable debug logging in `mcp_bridge.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

- **Whitelist Only**: Only explicitly allowed tools can be executed
- **Path Validation**: File paths should be validated and sandboxed
- **User Confirmation**: Consider adding confirmation for destructive operations
- **Audit Logging**: Log all tool executions for security auditing

## Future Enhancements

- [ ] Real MCP server connections (replace mock)
- [ ] Additional MCP servers (database, web, etc.)
- [ ] User confirmation for destructive operations
- [ ] Tool execution history and undo functionality
- [ ] Custom tool development framework
- [ ] Multi-user access controls
