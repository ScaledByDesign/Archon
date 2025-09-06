#!/usr/bin/env python3
"""
Test script for LiteLLM Auto Router configuration
Tests different types of queries to ensure proper routing
"""

import requests
import json
import time
from typing import List, Dict

# LiteLLM endpoint
LITELLM_URL = "http://localhost:7010/v1/chat/completions"
API_KEY = "sk-wqn0xwq_vha4MVM2yzw"  # From your config

# Test queries for different routing scenarios
TEST_QUERIES = [
    {
        "query": "I need to plan a software architecture for a microservices system",
        "expected_route": "zoi-planner",
        "category": "Planning/Architecture"
    },
    {
        "query": "Help me fix this Python function that's throwing an error",
        "expected_route": "zoi-coder",
        "category": "Coding Help"
    },
    {
        "query": "Generate a complete web application with authentication and database",
        "expected_route": "zoi-planner",
        "category": "Complex Development"
    },
    {
        "query": "What does our documentation say about deployment procedures?",
        "expected_route": "zoi-rag",
        "category": "Knowledge Retrieval"
    },
    {
        "query": "What's the weather like today?",
        "expected_route": "zoi-coder",  # Default fallback
        "category": "General Query"
    }
]

def test_auto_router_query(query: str, expected_route: str, category: str) -> Dict:
    """Test a single query against the auto router"""

    payload = {
        "model": "zoi-auto",
        "messages": [
            {"role": "user", "content": query}
        ],
        "max_tokens": 100,  # Keep responses short for testing
        "temperature": 0.1
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        print(f"\n🧪 Testing: {category}")
        print(f"📝 Query: {query}")
        print(f"🎯 Expected Route: {expected_route}")

        start_time = time.time()
        response = requests.post(LITELLM_URL, json=payload, headers=headers, timeout=30)
        end_time = time.time()

        if response.status_code == 200:
            result = response.json()

            # Try to extract routing information from response metadata
            actual_route = "unknown"
            if hasattr(result, '_hidden_params') and 'model_id' in result._hidden_params:
                actual_route = result._hidden_params['model_id']

            # Get the actual response content
            content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response')

            print(f"✅ Status: Success")
            print(f"⏱️  Response Time: {end_time - start_time:.2f}s")
            print(f"🤖 Actual Route: {actual_route}")
            print(f"📄 Response Preview: {content[:100]}...")

            return {
                "success": True,
                "query": query,
                "category": category,
                "expected_route": expected_route,
                "actual_route": actual_route,
                "response_time": end_time - start_time,
                "content_preview": content[:200]
            }
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"📄 Response: {response.text}")

            return {
                "success": False,
                "query": query,
                "category": category,
                "expected_route": expected_route,
                "error": f"HTTP {response.status_code}: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {str(e)}")
        return {
            "success": False,
            "query": query,
            "category": category,
            "expected_route": expected_route,
            "error": str(e)
        }

def main():
    """Run all auto router tests"""

    print("🚀 Starting LiteLLM Auto Router Tests")
    print("=" * 60)

    results = []

    for test_case in TEST_QUERIES:
        result = test_auto_router_query(
            test_case["query"],
            test_case["expected_route"],
            test_case["category"]
        )
        results.append(result)

        # Small delay between requests
        time.sleep(1)

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    successful_tests = [r for r in results if r["success"]]
    failed_tests = [r for r in results if not r["success"]]

    print(f"✅ Successful Tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed Tests: {len(failed_tests)}/{len(results)}")

    if successful_tests:
        avg_response_time = sum(r.get("response_time", 0) for r in successful_tests) / len(successful_tests)
        print(f"⏱️  Average Response Time: {avg_response_time:.2f}s")

    if failed_tests:
        print("\n🔍 Failed Test Details:")
        for test in failed_tests:
            print(f"  - {test['category']}: {test.get('error', 'Unknown error')}")

    print("\n💡 Next Steps:")
    print("  1. Check that LiteLLM container is running: docker ps")
    print("  2. Verify auto router config is mounted correctly")
    print("  3. Check LiteLLM logs: docker logs litellm")
    print("  4. Ensure embedding model 'zoi-embed' is available")

if __name__ == "__main__":
    main()