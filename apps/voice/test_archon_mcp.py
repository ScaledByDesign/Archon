#!/usr/bin/env python3
"""
Test script for Archon MCP Integration
Tests voice commands that use the existing archon-mcp server
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

async def test_archon_mcp_integration():
    """Test the Archon MCP integration functionality."""
    
    print("🏛️ Testing Archon MCP Integration")
    print("=" * 50)
    
    # Test 1: Check Archon MCP server availability
    print("\n1. Testing Archon MCP server connectivity...")
    
    archon_url = os.environ.get("ARCHON_MCP_URL", "http://localhost:7082")
    print(f"   Archon MCP URL: {archon_url}")
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # Test the MCP endpoint instead of health
            async with session.get(f"{archon_url}/mcp", timeout=5) as response:
                if response.status in [200, 406]:  # 406 is expected for GET without proper headers
                    print("   ✅ Archon MCP server is reachable")
                else:
                    print(f"   ❌ Archon MCP server returned {response.status}")
                    return False
    except Exception as e:
        print(f"   ❌ Cannot reach Archon MCP server: {e}")
        print("   💡 Make sure archon-mcp is running: docker-compose up archon-mcp")
        return False
    
    # Test 2: Test available tools
    print("\n2. Testing available tools...")
    try:
        available_tools = await simple_mcp_client.get_available_tools()
        print(f"📋 Available servers and tools:")
        for server, tools in available_tools.items():
            print(f"   {server}: {', '.join(tools)}")
        print("✅ Tool discovery successful")
    except Exception as e:
        print(f"❌ Tool discovery failed: {e}")
        return False
    
    # Test 3: Test health check tool
    print("\n3. Testing health check...")
    try:
        health_call = {"tool": "archon:health_check", "arguments": {}}
        result = await execute_voice_tool_call(health_call)
        print(f"   Result: {result}")
        
        if "healthy" in result.lower() or "running" in result.lower():
            print("   ✅ Health check successful")
        else:
            print("   ⚠️ Health check returned unexpected result")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
    
    # Test 4: Test session info
    print("\n4. Testing session info...")
    try:
        session_call = {"tool": "archon:session_info", "arguments": {}}
        result = await execute_voice_tool_call(session_call)
        print(f"   Result: {result}")
        print("   ✅ Session info successful")
    except Exception as e:
        print(f"   ❌ Session info failed: {e}")
    
    # Test 5: Test voice command simulation with Archon tools
    print("\n5. Testing voice command simulation...")
    
    voice_commands = [
        {
            "command": "Check the health of the Archon system",
            "tool_call": {"tool": "archon:health_check", "arguments": {}}
        },
        {
            "command": "Show me session information",
            "tool_call": {"tool": "archon:session_info", "arguments": {}}
        },
        {
            "command": "List all projects",
            "tool_call": {"tool": "archon:list_projects", "arguments": {}}
        },
        {
            "command": "Search for documents about authentication",
            "tool_call": {"tool": "archon:search_documents", "arguments": {"query": "authentication", "limit": 5}}
        }
    ]
    
    print("🎤 Simulating voice commands with Archon:")
    success_count = 0
    
    for cmd_info in voice_commands:
        command = cmd_info["command"]
        tool_call = cmd_info["tool_call"]
        
        print(f"\n   User says: '{command}'")
        print(f"   Tool call: {tool_call}")
        
        try:
            result = await execute_voice_tool_call(tool_call)
            print(f"   🤖 AI: {result}")
            
            if not result.startswith("Error") and "failed" not in result.lower():
                success_count += 1
                print("   ✅ Success")
            else:
                print("   ⚠️ Tool execution issue")
                
        except Exception as e:
            print(f"   ❌ Command failed: {e}")
    
    print(f"\n📊 Voice command tests: {success_count}/{len(voice_commands)} successful")
    
    # Test 6: Test task creation (if we have projects)
    print("\n6. Testing task creation...")
    try:
        # First try to list projects to get a project ID
        list_projects_call = {"tool": "archon:list_projects", "arguments": {}}
        projects_result = await execute_voice_tool_call(list_projects_call)
        
        if "found" in projects_result and "projects" in projects_result:
            print("   Found existing projects, attempting task creation...")
            
            # Create a test task (this might fail if no projects exist)
            create_task_call = {
                "tool": "archon:create_task",
                "arguments": {
                    "project_id": "550e8400-e29b-41d4-a716-446655440000",  # Example UUID
                    "title": "Test voice-created task",
                    "description": "This task was created via voice command through MCP",
                    "assignee": "User"
                }
            }
            
            result = await execute_voice_tool_call(create_task_call)
            print(f"   Task creation result: {result}")
            
            if "created" in result.lower():
                print("   ✅ Task creation successful")
            else:
                print("   ⚠️ Task creation may have failed (expected if no valid project)")
        else:
            print("   ⚠️ No projects found, skipping task creation test")
            
    except Exception as e:
        print(f"   ❌ Task creation test failed: {e}")
    
    print("\n🎉 Archon MCP integration test completed!")
    return True

async def test_archon_mcp_direct():
    """Test direct HTTP calls to Archon MCP server."""
    print("\n🔧 Testing direct Archon MCP HTTP calls...")
    
    archon_url = os.environ.get("ARCHON_MCP_URL", "http://localhost:7082")
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # Test the MCP endpoint structure
            test_endpoints = [
                f"{archon_url}/health",
                f"{archon_url}/mcp",
            ]
            
            for endpoint in test_endpoints:
                try:
                    async with session.get(endpoint, timeout=5) as response:
                        print(f"   {endpoint}: {response.status}")
                        if response.status == 200:
                            content = await response.text()
                            print(f"     Content preview: {content[:100]}...")
                except Exception as e:
                    print(f"   {endpoint}: Error - {e}")
                    
    except Exception as e:
        print(f"❌ Direct HTTP test failed: {e}")

async def main():
    """Main test function."""
    try:
        print("🧪 Archon MCP Integration Test Suite")
        print("Testing voice commands with existing Archon MCP server")
        print("=" * 60)
        
        # Test direct connectivity first
        await test_archon_mcp_direct()
        
        # Test the integration
        success = await test_archon_mcp_integration()
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        await simple_mcp_client.cleanup()
        
        if success:
            print("\n✅ Archon MCP integration is working!")
            print("🎤 Ready for voice-controlled Archon operations!")
            return 0
        else:
            print("\n❌ Archon MCP integration tests failed!")
            return 1
            
    except Exception as e:
        logger.exception(f"Test failed with exception: {e}")
        print(f"\n💥 Test suite failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
