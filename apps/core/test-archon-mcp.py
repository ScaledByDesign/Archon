#!/usr/bin/env python3
"""
Test script for Archon MCP integration with LiteLLM
Tests the connection and available tools from Archon MCP server
"""

import requests
import json
import time
from typing import List, Dict

# Configuration
LITELLM_URL = "http://localhost:7010/v1/chat/completions"
ARCHON_MCP_URL = "http://localhost:8051"
API_KEY = "sk-wqn0xwq_vha4MVM2yzw"

def test_archon_mcp_health():
    """Test if Archon MCP server is healthy"""
    try:
        print("🔍 Testing Archon MCP server health...")
        response = requests.get(f"{ARCHON_MCP_URL}/health", timeout=10)

        if response.status_code == 200:
            print("✅ Archon MCP server is healthy")
            return True
        else:
            print(f"❌ Archon MCP server health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Archon MCP server: {str(e)}")
        return False

def test_litellm_models():
    """Test if LiteLLM can see available models"""
    try:
        print("🔍 Testing LiteLLM models endpoint...")
        response = requests.get(
            "http://localhost:7010/v1/models",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=10
        )

        if response.status_code == 200:
            models = response.json()
            model_names = [model['id'] for model in models.get('data', [])]
            print(f"✅ LiteLLM is running with {len(model_names)} models")

            # Check if zoi-auto is available
            if 'zoi-auto' in model_names:
                print("✅ zoi-auto model is available for MCP routing")
            else:
                print("⚠️  zoi-auto model not found in available models")

            return True
        else:
            print(f"❌ LiteLLM models endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to LiteLLM: {str(e)}")
        return False

def test_archon_mcp_with_litellm():
    """Test Archon MCP integration through LiteLLM"""

    # Test queries that should trigger Archon MCP tools
    test_queries = [
        {
            "query": "Search my knowledge base for information about API documentation",
            "expected_tool": "search_documents",
            "category": "Knowledge Search"
        },
        {
            "query": "Create a new task to implement user authentication",
            "expected_tool": "create_task",
            "category": "Task Management"
        },
        {
            "query": "What tasks do I have related to database optimization?",
            "expected_tool": "get_task_context",
            "category": "Task Retrieval"
        }
    ]

    print("\n🧪 Testing Archon MCP integration through LiteLLM...")

    for i, test_case in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {test_case['category']} ---")
        print(f"📝 Query: {test_case['query']}")

        payload = {
            "model": "zoi-auto",  # Use auto-routing model
            "messages": [
                {"role": "user", "content": test_case['query']}
            ],
            "max_tokens": 150,
            "temperature": 0.1,
            "tools": [
                {
                    "type": "mcp",
                    "server_label": "archon",
                    "server_url": "http://archon-mcp:8051",
                    "require_approval": "never"
                }
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        try:
            start_time = time.time()
            response = requests.post(LITELLM_URL, json=payload, headers=headers, timeout=30)
            end_time = time.time()

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: Success")
                print(f"⏱️  Response Time: {end_time - start_time:.2f}s")

                # Check if tools were called
                choice = result.get('choices', [{}])[0]
                message = choice.get('message', {})
                tool_calls = message.get('tool_calls', [])

                if tool_calls:
                    print(f"🔧 Tools Called: {len(tool_calls)}")
                    for tool_call in tool_calls:
                        tool_name = tool_call.get('function', {}).get('name', 'unknown')
                        print(f"   - {tool_name}")
                else:
                    print("ℹ️  No tools were called (may be expected for some queries)")

                content = message.get('content', 'No response')
                print(f"📄 Response Preview: {content[:100]}...")

            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(f"📄 Response: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {str(e)}")

        # Small delay between tests
        time.sleep(1)

def main():
    """Run all Archon MCP integration tests"""

    print("🚀 Starting Archon MCP Integration Tests")
    print("=" * 60)

    # Test 1: Archon MCP Health
    archon_healthy = test_archon_mcp_health()

    # Test 2: LiteLLM Models
    litellm_healthy = test_litellm_models()

    if not archon_healthy or not litellm_healthy:
        print("\n❌ Prerequisites not met. Please ensure both services are running:")
        print("   - Archon: cd apps/Archon && docker-compose up -d")
        print("   - LiteLLM: cd apps/llm-local && docker-compose up -d")
        return

    # Test 3: MCP Integration
    test_archon_mcp_with_litellm()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print("✅ Archon MCP server is accessible")
    print("✅ LiteLLM proxy is running")
    print("🔗 MCP integration configured")

    print("\n💡 Next Steps:")
    print("  1. Start using Archon MCP tools in your applications")
    print("  2. Add documents to Archon's knowledge base")
    print("  3. Create tasks and let AI assistants help manage them")
    print("  4. Use aliases: 'archon', 'knowledge', 'tasks', 'docs'")

if __name__ == "__main__":
    main()