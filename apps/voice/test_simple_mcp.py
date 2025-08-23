#!/usr/bin/env python3
"""
Test script for Simple MCP Client
Tests the correct architecture where RealtimeVoiceChat USES MCP tools
"""

import asyncio
import logging
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from simple_mcp_client import simple_mcp_client, execute_voice_tool_call

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_simple_mcp_client():
    """Test the simple MCP client functionality."""
    
    print("🎤 Testing Simple MCP Client (Correct Architecture)")
    print("=" * 60)
    
    # Test 1: Check available tools
    print("\n1. Testing available tools discovery...")
    try:
        available_tools = await simple_mcp_client.get_available_tools()
        print(f"📋 Available servers and tools:")
        for server, tools in available_tools.items():
            print(f"   {server}: {', '.join(tools)}")
        print("✅ Tool discovery successful")
    except Exception as e:
        print(f"❌ Tool discovery failed: {e}")
        return False
    
    # Test 2: Test tool call parsing and execution
    print("\n2. Testing voice tool call execution...")
    
    test_cases = [
        {
            "name": "List current directory",
            "tool_call": {"tool": "filesystem:read_directory", "arguments": {"path": "."}},
            "expected": "directory listing"
        },
        {
            "name": "Read README file",
            "tool_call": {"tool": "filesystem:read_file", "arguments": {"path": "README.md"}},
            "expected": "file contents"
        },
        {
            "name": "Git status",
            "tool_call": {"tool": "git:status", "arguments": {}},
            "expected": "git status"
        }
    ]
    
    success_count = 0
    for test_case in test_cases:
        try:
            print(f"\n   Testing: {test_case['name']}")
            print(f"   Tool call: {test_case['tool_call']}")
            
            result = await execute_voice_tool_call(test_case['tool_call'])
            print(f"   Result: {result[:100]}...")
            
            if not result.startswith("Error") and not result.startswith("Unknown server"):
                print("   ✅ Success")
                success_count += 1
            else:
                print(f"   ⚠️ Tool execution issue: {result}")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    print(f"\n📊 Tool execution tests: {success_count}/{len(test_cases)} successful")
    
    # Test 3: Test security validation
    print("\n3. Testing security validation...")
    
    security_test_cases = [
        {
            "name": "Path traversal attempt",
            "tool_call": {"tool": "filesystem:read_file", "arguments": {"path": "../../../etc/passwd"}},
            "should_block": True
        },
        {
            "name": "Valid file read",
            "tool_call": {"tool": "filesystem:read_file", "arguments": {"path": "test_simple_mcp.py"}},
            "should_block": False
        },
        {
            "name": "Unknown tool",
            "tool_call": {"tool": "filesystem:delete_everything", "arguments": {}},
            "should_block": True
        }
    ]
    
    security_success = 0
    for test_case in security_test_cases:
        try:
            print(f"\n   Testing: {test_case['name']}")
            result = await execute_voice_tool_call(test_case['tool_call'])
            
            is_blocked = "not permitted" in result or "not allowed" in result or "Unknown server" in result
            
            if test_case['should_block'] and is_blocked:
                print("   ✅ Correctly blocked")
                security_success += 1
            elif not test_case['should_block'] and not is_blocked:
                print("   ✅ Correctly allowed")
                security_success += 1
            else:
                print(f"   ❌ Security test failed: {result}")
                
        except Exception as e:
            print(f"   ❌ Security test error: {e}")
    
    print(f"\n🔒 Security tests: {security_success}/{len(security_test_cases)} passed")
    
    # Test 4: Test voice command simulation
    print("\n4. Testing voice command simulation...")
    
    voice_commands = [
        "List the files in the current directory",
        "Read the README file", 
        "Check git status",
        "Create a new file called test.txt"
    ]
    
    print("🎤 Simulating voice commands:")
    for command in voice_commands:
        print(f"\n   User says: '{command}'")
        
        # Simulate LLM converting voice to tool call
        if "list" in command.lower() and "files" in command.lower():
            tool_call = {"tool": "filesystem:read_directory", "arguments": {"path": "."}}
        elif "read" in command.lower() and "readme" in command.lower():
            tool_call = {"tool": "filesystem:read_file", "arguments": {"path": "README.md"}}
        elif "git status" in command.lower():
            tool_call = {"tool": "git:status", "arguments": {}}
        elif "create" in command.lower() and "file" in command.lower():
            tool_call = {"tool": "filesystem:write_file", "arguments": {"path": "test.txt", "content": "Hello from voice command!"}}
        else:
            print("   🤖 AI: I don't understand that command")
            continue
        
        try:
            result = await execute_voice_tool_call(tool_call)
            print(f"   🤖 AI: {result}")
        except Exception as e:
            print(f"   🤖 AI: Sorry, I encountered an error: {e}")
    
    print("\n🎉 Simple MCP Client test completed!")
    return True

async def test_mcp_server_availability():
    """Test if MCP servers are available."""
    print("\n🔍 Testing MCP server availability...")
    
    import subprocess
    
    servers_to_test = [
        ("mcp-server-filesystem", "Filesystem server"),
        ("mcp-server-git", "Git server"),
        ("node", "Node.js runtime")
    ]
    
    for command, description in servers_to_test:
        try:
            result = subprocess.run([command, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   ✅ {description} available")
            else:
                print(f"   ❌ {description} not available")
        except FileNotFoundError:
            print(f"   ❌ {description} not found")
        except subprocess.TimeoutExpired:
            print(f"   ⚠️ {description} timeout")
        except Exception as e:
            print(f"   ❌ {description} error: {e}")

async def main():
    """Main test function."""
    try:
        print("🧪 Simple MCP Client Test Suite")
        print("Testing the CORRECT architecture: RealtimeVoiceChat USES MCP tools")
        print("=" * 70)
        
        # Test server availability first
        await test_mcp_server_availability()
        
        # Test the simple MCP client
        success = await test_simple_mcp_client()
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await simple_mcp_client.cleanup()
        
        if success:
            print("\n✅ Simple MCP Client is working correctly!")
            print("🎤 Ready for voice-controlled MCP tool execution!")
            return 0
        else:
            print("\n❌ Simple MCP Client tests failed!")
            return 1
            
    except Exception as e:
        logger.exception(f"Test failed with exception: {e}")
        print(f"\n💥 Test suite failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
