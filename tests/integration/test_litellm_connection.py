#!/usr/bin/env python3
"""
Test LiteLLM connection and model availability
"""

import sys
import asyncio
import httpx
import json
import os

# Add src to path
sys.path.insert(0, '/app/src')

async def test_litellm_health():
    """Test LiteLLM health endpoint"""
    print("🏥 Testing LiteLLM Health")
    print("=" * 25)
    
    try:
        # Get the master key from environment
        master_key = os.getenv('LITELLM_MASTER_KEY', 'sk-change-me-to-random-string')
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try the health endpoint with auth
            response = await client.get(
                "http://litellm:4000/health",
                headers={"Authorization": f"Bearer {master_key}"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ LiteLLM is healthy")
                return True
            else:
                print(f"❌ LiteLLM health check failed: {response.status_code}")
                return False
    except httpx.ConnectTimeout:
        print("❌ Health check failed: Connection timed out")
        return False
    except httpx.NetworkError as e:
        print(f"❌ Health check failed: Network error - {e}")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def test_litellm_models():
    """Test LiteLLM models endpoint"""
    print("\n📋 Testing LiteLLM Models")
    print("=" * 25)
    
    try:
        # Get the master key from environment
        master_key = os.getenv('LITELLM_MASTER_KEY', 'sk-change-me-to-random-string')
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "http://litellm:4000/v1/models",
                headers={"Authorization": f"Bearer {master_key}"}
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                print(f"✅ Found {len(models)} models")
                for model in models[:5]:  # Show first 5
                    print(f"   - {model.get('id', 'Unknown')}")
                if len(models) > 5:
                    print(f"   ... and {len(models) - 5} more")
                return True
            else:
                print(f"❌ Models request failed: {response.text}")
                return False
    except httpx.ConnectTimeout:
        print("❌ Models request failed: Connection timed out")
        return False
    except httpx.NetworkError as e:
        print(f"❌ Models request failed: Network error - {e}")
        return False
    except Exception as e:
        print(f"❌ Models request failed: {e}")
        return False

async def test_model_router_get_models():
    """Test ModelRouter get_available_models method"""
    print("\n🤖 Testing ModelRouter.get_available_models()")
    print("=" * 45)
    
    try:
        from services.model_router import ModelRouter
        
        # Get the master key from environment
        master_key = os.getenv('LITELLM_MASTER_KEY', 'sk-change-me-to-random-string')
        
        router = ModelRouter(
            litellm_base_url="http://litellm:4000",
            api_key=master_key
        )
        
        models = await router.get_available_models()
        print(f"✅ Retrieved {len(models)} models via ModelRouter")
        for model in models[:5]:  # Show first 5
            print(f"   - {model}")
        if len(models) > 5:
            print(f"   ... and {len(models) - 5} more")
        return True
    except Exception as e:
        print(f"❌ ModelRouter.get_available_models() failed: {e}")
        return False

async def test_simple_routing():
    """Test simple routing decision"""
    print("\n🧭 Testing Simple Routing")
    print("=" * 25)
    
    try:
        from services.model_router import ModelRouter
        
        # Get the master key from environment
        master_key = os.getenv('LITELLM_MASTER_KEY', 'sk-change-me-to-random-string')
        
        router = ModelRouter(
            litellm_base_url="http://litellm:4000",
            api_key=master_key
        )
        
        # Simple request
        request_data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100
        }
        
        decision = await router.route_request(request_data)
        print(f"✅ Routing decision made")
        print(f"   Selected model: {decision.selected_model}")
        print(f"   Strategy: {decision.strategy}")
        print(f"   Confidence: {decision.confidence}")
        return True
    except Exception as e:
        print(f"❌ Simple routing failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🔗 LiteLLM Connection Tests")
    print("=" * 30)
    
    # Test health
    health_ok = await test_litellm_health()
    
    # Test models endpoint
    models_ok = await test_litellm_models() if health_ok else False
    
    # Test router models
    router_models_ok = await test_model_router_get_models() if models_ok else False
    
    # Test simple routing
    routing_ok = await test_simple_routing() if router_models_ok else False
    
    # Summary
    print("\n" + "=" * 30)
    print("📊 Connection Test Results:")
    print(f"   Health: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Models: {'✅ PASS' if models_ok else '❌ FAIL'}")
    print(f"   Router Models: {'✅ PASS' if router_models_ok else '❌ FAIL'}")
    print(f"   Routing: {'✅ PASS' if routing_ok else '❌ FAIL'}")
    
    overall = health_ok and models_ok and router_models_ok and routing_ok
    print(f"   Overall: {'✅ ALL PASS' if overall else '❌ SOME FAILED'}")
    
    return overall

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
