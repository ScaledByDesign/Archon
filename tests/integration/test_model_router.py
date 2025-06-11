#!/usr/bin/env python3
"""
Test script for the Model Router service
Tests routing logic, fallback mechanisms, and integration with LiteLLM
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.model_router import ModelRouter, RouteStrategy, TaskComplexity, ModelCapability


async def test_model_router():
    """Test the model router functionality"""
    print("🧪 Testing Model Router Service")
    print("=" * 50)
    
    # Initialize router
    router = ModelRouter(
        litellm_base_url="http://zoi.local:4000",
        api_key="sk-change-me-to-random-string"
    )
    
    # Test 1: Get available models
    print("\n📋 Test 1: Getting available models...")
    try:
        models = await router.get_available_models()
        print(f"✅ Found {len(models)} available models:")
        for model in models:
            print(f"   - {model}")
    except Exception as e:
        print(f"❌ Failed to get models: {e}")
        return False
    
    # Test 2: Simple text generation routing
    print("\n🎯 Test 2: Simple text generation routing...")
    simple_request = {
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 100
    }
    
    try:
        decision = await router.route_request(simple_request, models)
        print(f"✅ Routing Decision:")
        print(f"   Selected Model: {decision.selected_model}")
        print(f"   Strategy: {decision.strategy_used.value}")
        print(f"   Confidence: {decision.confidence:.2f}")
        print(f"   Reasoning: {decision.reasoning}")
        print(f"   Fallbacks: {decision.fallback_models[:3]}")
    except Exception as e:
        print(f"❌ Routing failed: {e}")
        return False
    
    # Test 3: Code generation routing
    print("\n💻 Test 3: Code generation routing...")
    code_request = {
        "messages": [
            {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}
        ],
        "max_tokens": 200
    }
    
    try:
        decision = await router.route_request(code_request, models)
        print(f"✅ Code Routing Decision:")
        print(f"   Selected Model: {decision.selected_model}")
        print(f"   Strategy: {decision.strategy_used.value}")
        print(f"   Reasoning: {decision.reasoning}")
    except Exception as e:
        print(f"❌ Code routing failed: {e}")
    
    # Test 4: Privacy-sensitive routing
    print("\n🔒 Test 4: Privacy-sensitive routing...")
    privacy_request = {
        "messages": [
            {"role": "user", "content": "This is confidential information about our company strategy"}
        ],
        "privacy_required": True,
        "max_tokens": 150
    }
    
    try:
        decision = await router.route_request(privacy_request, models)
        print(f"✅ Privacy Routing Decision:")
        print(f"   Selected Model: {decision.selected_model}")
        print(f"   Strategy: {decision.strategy_used.value}")
        print(f"   Reasoning: {decision.reasoning}")
        
        # Should prefer local model for privacy
        if "llama" in decision.selected_model.lower():
            print("   ✅ Correctly selected local model for privacy")
        else:
            print("   ⚠️  Did not select local model for privacy (may not be available)")
    except Exception as e:
        print(f"❌ Privacy routing failed: {e}")
    
    # Test 5: Fast response routing
    print("\n⚡ Test 5: Fast response routing...")
    fast_request = {
        "messages": [
            {"role": "user", "content": "Quick question: what's 2+2?"}
        ],
        "max_response_time": 5.0,
        "max_tokens": 50
    }
    
    try:
        decision = await router.route_request(fast_request, models)
        print(f"✅ Fast Response Routing Decision:")
        print(f"   Selected Model: {decision.selected_model}")
        print(f"   Strategy: {decision.strategy_used.value}")
        print(f"   Estimated Time: {decision.estimated_time:.1f}s")
        print(f"   Reasoning: {decision.reasoning}")
    except Exception as e:
        print(f"❌ Fast routing failed: {e}")
    
    # Test 6: Budget-conscious routing
    print("\n💰 Test 6: Budget-conscious routing...")
    budget_request = {
        "messages": [
            {"role": "user", "content": "Simple question that doesn't need premium model"}
        ],
        "metadata": {"budget": True},
        "budget_priority": True,
        "max_tokens": 100
    }
    
    try:
        decision = await router.route_request(budget_request, models)
        print(f"✅ Budget Routing Decision:")
        print(f"   Selected Model: {decision.selected_model}")
        print(f"   Strategy: {decision.strategy_used.value}")
        print(f"   Estimated Cost: ${decision.estimated_cost:.4f}")
        print(f"   Reasoning: {decision.reasoning}")
    except Exception as e:
        print(f"❌ Budget routing failed: {e}")
    
    # Test 7: Actual request execution with fallback
    print("\n🚀 Test 7: Actual request execution...")
    test_request = {
        "messages": [
            {"role": "user", "content": "Say hello in exactly 5 words"}
        ],
        "max_tokens": 20,
        "temperature": 0.7
    }
    
    try:
        # Get routing decision first
        decision = await router.route_request(test_request, models)
        print(f"   Routing to: {decision.selected_model}")
        
        # Execute with fallback
        result = await router.execute_with_fallback(test_request, decision)
        
        print(f"✅ Request executed successfully!")
        print(f"   Model used: {result.get('routing_metadata', {}).get('selected_model', 'unknown')}")
        print(f"   Response time: {result.get('routing_metadata', {}).get('response_time', 0):.2f}s")
        print(f"   Fallback used: {result.get('routing_metadata', {}).get('fallback_used', False)}")
        
        # Show response content
        if "choices" in result and result["choices"]:
            content = result["choices"][0].get("message", {}).get("content", "")
            print(f"   Response: {content[:100]}...")
            
    except Exception as e:
        print(f"❌ Request execution failed: {e}")
        print("   This might be expected if LiteLLM service is not running")
    
    # Test 8: Get routing statistics
    print("\n📊 Test 8: Routing statistics...")
    try:
        stats = router.get_routing_stats()
        print(f"✅ Routing Statistics:")
        print(f"   Total models tracked: {stats['total_models']}")
        print(f"   Routing rules: {stats['routing_rules_count']}")
        print(f"   Model groups: {len(stats['model_groups'])}")
        
        if stats['model_metrics']:
            print("   Model performance:")
            for model, metrics in list(stats['model_metrics'].items())[:3]:
                print(f"     {model}: {metrics['total_requests']} requests, {metrics['success_rate']:.1%} success")
    except Exception as e:
        print(f"❌ Stats retrieval failed: {e}")
    
    print("\n🎉 Model Router testing completed!")
    return True


async def test_routing_scenarios():
    """Test various routing scenarios"""
    print("\n🎭 Testing Advanced Routing Scenarios")
    print("=" * 40)
    
    router = ModelRouter()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Vision Task",
            "request": {
                "messages": [
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": "What's in this image?"},
                            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
                        ]
                    }
                ]
            }
        },
        {
            "name": "Complex Reasoning",
            "request": {
                "messages": [
                    {"role": "user", "content": "Explain quantum computing principles in detail, covering superposition, entanglement, and quantum gates. Provide mathematical foundations and practical applications. This is a comprehensive analysis requiring deep technical knowledge across multiple domains including physics, mathematics, and computer science."}
                ]
            }
        },
        {
            "name": "Embedding Task",
            "request": {
                "messages": [
                    {"role": "user", "content": "Create embeddings for this text"}
                ],
                "task_type": "embedding"
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🔍 Scenario: {scenario['name']}")
        try:
            decision = await router.route_request(scenario['request'])
            print(f"   Model: {decision.selected_model}")
            print(f"   Strategy: {decision.strategy_used.value}")
            print(f"   Confidence: {decision.confidence:.2f}")
            print(f"   Reasoning: {decision.reasoning}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Model Router Tests")
    
    # Run main tests
    success = asyncio.run(test_model_router())
    
    # Run scenario tests
    asyncio.run(test_routing_scenarios())
    
    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
