#!/usr/bin/env python3
"""
Direct test of model router logic without network calls
"""

import sys
import asyncio
import json
from unittest.mock import AsyncMock, patch

# Add src to path
sys.path.insert(0, '/app/src')

async def test_router_logic():
    """Test router logic with mocked LiteLLM responses"""
    print("🧠 Testing Model Router Logic")
    print("=" * 35)
    
    try:
        from services.model_router import ModelRouter, RouteStrategy, TaskComplexity
        
        # Create router
        router = ModelRouter(
            litellm_base_url="http://litellm:4000",
            api_key="sk-change-me-to-random-string"
        )
        
        # Mock the get_available_models method to return known models
        mock_models = [
            "gpt-4", "gpt-3.5-turbo", "claude-3-haiku", 
            "claude-3-sonnet", "llama3.2-1b", "gpt-4-turbo"
        ]
        
        with patch.object(router, 'get_available_models', return_value=mock_models):
            print(f"✅ Router created with {len(mock_models)} mock models")
            
            # Test 1: Simple routing
            print("\n📝 Test 1: Simple Chat Request")
            request_data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 100
            }
            
            decision = await router.route_request(request_data)
            print(f"   Selected model: {decision.selected_model}")
            print(f"   Strategy: {decision.strategy_used}")
            print(f"   Confidence: {decision.confidence}")
            print(f"   Reasoning: {decision.reasoning}")
            
            # Test 2: Code generation request
            print("\n💻 Test 2: Code Generation Request")
            code_request = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Write a Python function to sort a list"}],
                "max_tokens": 500
            }
            
            decision = await router.route_request(code_request)
            print(f"   Selected model: {decision.selected_model}")
            print(f"   Strategy: {decision.strategy_used}")
            print(f"   Confidence: {decision.confidence}")
            print(f"   Reasoning: {decision.reasoning}")
            
            # Test 3: Privacy-sensitive request
            print("\n🔒 Test 3: Privacy-Sensitive Request")
            private_request = {
                "model": "llama3.2-1b",
                "messages": [{"role": "user", "content": "Analyze this confidential document"}],
                "max_tokens": 300,
                "metadata": {"privacy_level": "high"}
            }
            
            decision = await router.route_request(private_request)
            print(f"   Selected model: {decision.selected_model}")
            print(f"   Strategy: {decision.strategy_used}")
            print(f"   Confidence: {decision.confidence}")
            print(f"   Reasoning: {decision.reasoning}")
            
            # Test 4: Fast response request
            print("\n⚡ Test 4: Fast Response Request")
            fast_request = {
                "model": "claude-3-haiku",
                "messages": [{"role": "user", "content": "Quick question: what's 2+2?"}],
                "max_tokens": 50,
                "metadata": {"speed_priority": "high"}
            }
            
            decision = await router.route_request(fast_request)
            print(f"   Selected model: {decision.selected_model}")
            print(f"   Strategy: {decision.strategy_used}")
            print(f"   Confidence: {decision.confidence}")
            print(f"   Reasoning: {decision.reasoning}")
            
            return True
            
    except Exception as e:
        print(f"❌ Router logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_routing_rules():
    """Test routing rules and strategies"""
    print("\n🎯 Testing Routing Rules")
    print("=" * 25)
    
    try:
        from services.model_router import ModelRouter
        
        router = ModelRouter(
            litellm_base_url="http://litellm:4000",
            api_key="sk-change-me-to-random-string"
        )
        
        print(f"✅ Loaded {len(router.routing_rules)} routing rules")
        for i, rule in enumerate(router.routing_rules[:3]):  # Show first 3
            print(f"   Rule {i+1}: {rule.get('name', 'Unnamed rule')}")
            
        print(f"✅ Loaded {len(router.model_groups)} model groups")
        for group_name, models in list(router.model_groups.items())[:3]:  # Show first 3
            print(f"   {group_name}: {len(models)} models")
            
        print(f"✅ Loaded {len(router.fallback_chains)} fallback chains")
        for model, chain in list(router.fallback_chains.items())[:3]:  # Show first 3
            print(f"   {model}: {len(chain)} fallbacks")
            
        return True
        
    except Exception as e:
        print(f"❌ Routing rules test failed: {e}")
        return False

async def test_model_capabilities():
    """Test model capability detection"""
    print("\n🎯 Testing Model Capabilities")
    print("=" * 30)
    
    try:
        from services.model_router import ModelRouter
        
        router = ModelRouter(
            litellm_base_url="http://litellm:4000",
            api_key="sk-change-me-to-random-string"
        )
        
        # Test capability detection
        test_models = ["gpt-4", "claude-3-haiku", "llama3.2-1b"]
        
        for model in test_models:
            capabilities = router._get_model_capabilities(model)
            print(f"   {model}: {', '.join(capabilities)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model capabilities test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Model Router Direct Tests")
    print("=" * 35)
    
    # Test router logic
    logic_ok = await test_router_logic()
    
    # Test routing rules
    rules_ok = await test_routing_rules()
    
    # Test model capabilities
    capabilities_ok = await test_model_capabilities()
    
    # Summary
    print("\n" + "=" * 35)
    print("📊 Direct Test Results:")
    print(f"   Router Logic: {'✅ PASS' if logic_ok else '❌ FAIL'}")
    print(f"   Routing Rules: {'✅ PASS' if rules_ok else '❌ FAIL'}")
    print(f"   Model Capabilities: {'✅ PASS' if capabilities_ok else '❌ FAIL'}")
    
    overall = logic_ok and rules_ok and capabilities_ok
    print(f"   Overall: {'✅ ALL PASS' if overall else '❌ SOME FAILED'}")
    
    return overall

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
