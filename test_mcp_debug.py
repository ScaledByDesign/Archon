#!/usr/bin/env python3
"""
Debug script to test MCP connections step by step
"""

import asyncio
import aiohttp
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_archon_mcp_direct():
    """Test archon MCP server directly."""
    print("🔧 Testing Archon MCP Server Direct Connection...")
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            async with session.post(
                "http://localhost:7082/mcp",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            ) as response:
                print(f"📊 Archon MCP Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Archon MCP Tools: {json.dumps(result, indent=2)}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Archon MCP Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Archon MCP Connection Failed: {e}")
        return False

async def test_litellm_mcp_gateway():
    """Test LiteLLM MCP gateway."""
    print("\n🌐 Testing LiteLLM MCP Gateway...")
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            async with session.post(
                "http://localhost:7010/mcp/",
                json=payload,
                headers={
                    "Authorization": "Bearer sk-wqn0xwq_vha4MVM2yzw",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            ) as response:
                print(f"📊 LiteLLM MCP Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ LiteLLM MCP Tools: {json.dumps(result, indent=2)}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ LiteLLM MCP Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ LiteLLM MCP Connection Failed: {e}")
        return False

async def test_litellm_tool_call():
    """Test calling a specific tool through LiteLLM."""
    print("\n🔧 Testing LiteLLM Tool Call...")
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "archon:list_projects",
                    "arguments": {}
                }
            }
            
            async with session.post(
                "http://localhost:7010/mcp/",
                json=payload,
                headers={
                    "Authorization": "Bearer sk-wqn0xwq_vha4MVM2yzw",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            ) as response:
                print(f"📊 Tool Call Response Status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Tool Call Result: {json.dumps(result, indent=2)}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Tool Call Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Tool Call Failed: {e}")
        return False

async def test_voice_mcp_status():
    """Test voice service MCP status."""
    print("\n🎤 Testing Voice Service MCP Status...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/mcp-status") as response:
                print(f"📊 Voice MCP Status Response: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Voice MCP Status: {json.dumps(result, indent=2)}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Voice MCP Status Error: {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Voice MCP Status Failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 MCP Integration Debug Tests")
    print("=" * 50)
    
    # Wait for services to be ready
    print("⏳ Waiting for services to be ready...")
    await asyncio.sleep(10)
    
    results = []
    
    # Test 1: Direct Archon MCP
    results.append(await test_archon_mcp_direct())
    
    # Test 2: LiteLLM MCP Gateway
    results.append(await test_litellm_mcp_gateway())
    
    # Test 3: LiteLLM Tool Call
    results.append(await test_litellm_tool_call())
    
    # Test 4: Voice Service MCP Status
    results.append(await test_voice_mcp_status())
    
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary:")
    print(f"✅ Archon MCP Direct: {'PASS' if results[0] else 'FAIL'}")
    print(f"✅ LiteLLM MCP Gateway: {'PASS' if results[1] else 'FAIL'}")
    print(f"✅ LiteLLM Tool Call: {'PASS' if results[2] else 'FAIL'}")
    print(f"✅ Voice MCP Status: {'PASS' if results[3] else 'FAIL'}")
    
    if all(results):
        print("🎉 ALL TESTS PASSED! MCP Integration is working!")
    else:
        print("❌ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())
