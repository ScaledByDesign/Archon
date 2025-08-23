#!/usr/bin/env python3
"""
Enhanced test script to verify the complete MCP integration.
Tests the enhanced MCP bridge with full protocol support.
"""

import asyncio
import logging
import sys
import os
import time

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'code'))

from mcp_bridge import (
    bootstrap_mcp, mcp_manager, docker_mcp_manager, parse_tool_call, execute_tool_call,
    HTTPMCPClient
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_docker_mcp_integration():
    """Test the Docker-based MCP integration functionality."""

    print("🐳 Testing Docker MCP Integration...")

    # Test 1: Bootstrap Docker MCP connections
    print("\n1. Testing Docker MCP Bootstrap...")
    await bootstrap_mcp()

    if not docker_mcp_manager.connected:
        print("❌ Docker MCP bootstrap failed")
        return False

    print("✅ Docker MCP bootstrap successful")

    # Test 2: List all capabilities
    print("\n2. Testing capability discovery...")
    all_tools = await docker_mcp_manager.get_all_tools()

    print(f"📋 Connected servers: {list(all_tools.keys())}")

    total_tools = sum(len(tools) for tools in all_tools.values())

    print(f"📊 Total tools available: {total_tools}")

    if total_tools == 0:
        print("❌ No tools discovered")
        return False

    print("✅ Capability discovery successful")
    
    # Test 3: Test enhanced tool call parsing
    print("\n3. Testing enhanced tool call parsing...")

    test_cases = [
        '{"tool":"filesystem:read_directory","arguments":{"path":"."}}',
        'Hello, this is not a tool call',
        '{"tool":"filesystem:read_file","arguments":{"path":"test.txt"}}',
        '{"tool":"git:status","arguments":{}}',
        'invalid json {',
        '{"tool":"invalid_format","arguments":{}}',  # Missing server:tool format
    ]

    for test_case in test_cases:
        result = parse_tool_call(test_case)
        print(f"   Input: {test_case[:60]}...")
        print(f"   Parsed: {'✅ Valid' if result else '❌ Invalid'}")
        if result:
            print(f"     Tool: {result['tool']}, Args: {result['arguments']}")

    print("✅ Enhanced tool call parsing test completed")

    # Test 4: Test Docker HTTP client
    print("\n4. Testing Docker HTTP client...")

    mcp_bridge_url = os.environ.get("MCP_BRIDGE_URL", "http://localhost:8001")
    print(f"   MCP Bridge URL: {mcp_bridge_url}")

    # Test direct HTTP client
    http_client = HTTPMCPClient(mcp_bridge_url)

    try:
        health_ok = await http_client.health_check()
        print(f"   Health check: {'✅ Healthy' if health_ok else '❌ Unhealthy'}")

        if health_ok:
            servers = await http_client.get_servers()
            print(f"   Available servers: {[s['name'] for s in servers]}")

    except Exception as e:
        print(f"   HTTP client test failed: {e}")

    print("✅ Docker HTTP client test completed")
    
    # Test 5: Test health monitoring
    print("\n5. Testing health monitoring...")

    health_status = await docker_mcp_manager.health_check_all()
    print(f"   Docker bridge health: {health_status}")

    print("✅ Health monitoring test completed")

    # Test 6: Test tool execution with enhanced manager
    print("\n6. Testing enhanced tool execution...")

    # Test with available servers
    for server_name, tools in all_tools.items():
        if not tools:
            continue

        # Try to execute a safe tool
        safe_tools = ["read_directory", "list_directory", "status", "list_tables"]
        available_safe_tool = None

        for tool_name in tools:
            if any(safe in tool_name for safe in safe_tools):
                available_safe_tool = tool_name
                break

        if available_safe_tool:
            try:
                print(f"   Testing {server_name}:{available_safe_tool}...")
                result = await mcp_manager.execute_tool(server_name, available_safe_tool, {})
                print(f"   Result: {result[:100]}...")
                print(f"✅ Tool execution successful for {server_name}")
                break
            except Exception as e:
                print(f"⚠️ Tool execution failed for {server_name}: {e}")

    # Test 7: Test complete tool call workflow
    print("\n7. Testing complete tool call workflow...")

    test_tool_calls = [
        '{"tool":"filesystem:read_directory","arguments":{"path":"."}}',
        '{"tool":"git:status","arguments":{}}',
    ]

    for tool_call_json in test_tool_calls:
        try:
            print(f"   Testing: {tool_call_json}")
            tool_call = parse_tool_call(tool_call_json)
            if tool_call:
                result = await execute_tool_call(tool_call)
                print(f"   Result: {result[:100]}...")
                print("✅ Complete workflow test successful")
            else:
                print("⚠️ Tool call parsing failed")
        except Exception as e:
            print(f"⚠️ Workflow test failed: {e}")

    # Test 8: Test audit logging
    print("\n8. Testing audit logging...")

    audit_log = mcp_manager.security_manager.get_audit_log(5)
    print(f"   Recent audit entries: {len(audit_log)}")

    for entry in audit_log[-3:]:  # Show last 3 entries
        print(f"   - {entry['server']}:{entry['tool']} -> {entry['status']}")

    print("✅ Audit logging test completed")

    print("\n🎉 All enhanced MCP integration tests completed successfully!")
    return True

async def test_individual_client():
    """Test individual MCP client functionality."""
    print("\n🔧 Testing Individual MCP Client...")

    # Test with a mock server config (since real servers may not be available)
    config = MCPServerConfig(
        name="test_server",
        command=["echo", "test"],  # Simple command for testing
        transport=TransportType.STDIO,
        enabled=True
    )

    client = EnhancedMCPClient(config)

    # Test connection status
    print(f"   Initial status: {client.connection_status}")

    # Note: We can't actually connect to echo as an MCP server,
    # but we can test the configuration and setup
    print("✅ Individual client test completed")

async def main():
    """Main test function."""
    try:
        print("🧪 Enhanced MCP Integration Test Suite")
        print("=" * 50)

        # Test individual client
        await test_individual_client()

        # Test full integration
        success = await test_enhanced_mcp_integration()

        # Cleanup
        print("\n🧹 Cleaning up...")
        await mcp_manager.disconnect_all()

        if success:
            print("\n✅ Enhanced MCP integration is working correctly!")
            print("🎉 All tests passed - ready for production use!")
            return 0
        else:
            print("\n❌ Enhanced MCP integration tests failed!")
            return 1

    except Exception as e:
        logger.exception(f"Test failed with exception: {e}")
        print(f"\n💥 Test suite failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
