#!/usr/bin/env python3
"""
Docker-based test script for the Model Router service
Tests routing logic and integration with LiteLLM in the containerized environment
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime

# Add src to path for Docker environment
sys.path.insert(0, '/app/src')

try:
    from services.model_router import ModelRouter, RouteStrategy, TaskComplexity, ModelCapability
    print("✅ Successfully imported ModelRouter")
except ImportError as e:
    print(f"❌ Failed to import ModelRouter: {e}")
    sys.exit(1)


async def test_docker_environment():
    """Test the model router in Docker environment"""
    print("🐳 Testing Model Router in Docker Environment")
    print("=" * 55)
    
    # Initialize router with Docker network URLs
    router = ModelRouter(
        litellm_base_url="http://litellm:4000",  # Docker service name
        api_key="sk-change-me-to-random-string"
    )
    
    print(f"🔧 Router initialized with LiteLLM URL: http://litellm:4000")
    
    # Test 1: Check LiteLLM connectivity
    print("\n🌐 Test 1: LiteLLM Connectivity...")
    try:
        models = await router.get_available_models()
        if models:
            print(f"✅ Connected to LiteLLM! Found {len(models)} models:")
            for i, model in enumerate(models[:10]):  # Show first 10
                print(f"   {i+1:2d}. {model}")
            if len(models) > 10:
                print(f"   ... and {len(models) - 10} more models")
        else:
            print("⚠️  Connected but no models available")
            return False
    except Exception as e:
        print(f"❌ LiteLLM connection failed: {e}")
        print("   Make sure LiteLLM service is running and accessible")
        return False
    
    # Test 2: Routing decision tests
    print("\n🎯 Test 2: Routing Decision Tests...")
    
    test_cases = [
        {
            "name": "Simple Chat",
            "request": {
                "messages": [{"role": "user", "content": "Hello, how are you?"}],
                "max_tokens": 50
            }
        },
        {
            "name": "Code Generation",
            "request": {
                "messages": [{"role": "user", "content": "Write a Python function to sort a list"}],
                "max_tokens": 200
            }
        },
        {
            "name": "Privacy Request",
            "request": {
                "messages": [{"role": "user", "content": "This is confidential company data"}],
                "privacy_required": True,
                "max_tokens": 100
            }
        },
        {
            "name": "Fast Response",
            "request": {
                "messages": [{"role": "user", "content": "Quick: what's 2+2?"}],
                "max_response_time": 3.0,
                "max_tokens": 20
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   🔍 {test_case['name']}:")
        try:
            decision = await router.route_request(test_case['request'], models)
            print(f"      Model: {decision.selected_model}")
            print(f"      Strategy: {decision.strategy_used.value}")
            print(f"      Confidence: {decision.confidence:.2f}")
            print(f"      Reasoning: {decision.reasoning}")
        except Exception as e:
            print(f"      ❌ Failed: {e}")
    
    # Test 3: Actual request execution
    print("\n🚀 Test 3: Request Execution...")
    test_request = {
        "messages": [
            {"role": "user", "content": "Say 'Hello from Docker!' in exactly 3 words"}
        ],
        "max_tokens": 10,
        "temperature": 0.1
    }
    
    try:
        # Get routing decision
        decision = await router.route_request(test_request, models)
        print(f"   Routing to: {decision.selected_model}")
        
        # Execute request
        start_time = time.time()
        result = await router.execute_with_fallback(test_request, decision)
        execution_time = time.time() - start_time
        
        print(f"✅ Request executed successfully!")
        print(f"   Model used: {result.get('routing_metadata', {}).get('selected_model', 'unknown')}")
        print(f"   Execution time: {execution_time:.2f}s")
        print(f"   Fallback used: {result.get('routing_metadata', {}).get('fallback_used', False)}")
        
        # Show response
        if "choices" in result and result["choices"]:
            content = result["choices"][0].get("message", {}).get("content", "")
            print(f"   Response: '{content.strip()}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Request execution failed: {e}")
        print("   This might be expected if models are slow or unavailable")
        return False


async def test_vault_integration():
    """Test HashiCorp Vault integration"""
    print("\n🔐 Testing HashiCorp Vault Integration")
    print("=" * 40)
    
    try:
        # Test if Vault client is available
        sys.path.insert(0, '/app/src')
        from secrets.vault_client import VaultClient
        print("✅ VaultClient imported successfully")
        
        # Test Vault connectivity
        vault_client = VaultClient()
        print(f"🔧 Vault URL: {vault_client.url}")
        
        # Test basic Vault operations
        test_secret_path = "test/model-router"
        test_data = {
            "api_key": "test-key-123",
            "model_config": "test-config",
            "created_at": datetime.utcnow().isoformat()
        }
        
        print(f"\n📝 Testing secret write to: {test_secret_path}")
        try:
            vault_client.write_secret(test_secret_path, test_data)
            print("✅ Secret written successfully")
        except Exception as e:
            print(f"❌ Secret write failed: {e}")
            return False
        
        print(f"\n📖 Testing secret read from: {test_secret_path}")
        try:
            retrieved_data = vault_client.read_secret(test_secret_path)
            if retrieved_data:
                print("✅ Secret read successfully")
                print(f"   Retrieved keys: {list(retrieved_data.keys())}")
                
                # Verify data integrity
                if retrieved_data.get("api_key") == test_data["api_key"]:
                    print("✅ Data integrity verified")
                else:
                    print("❌ Data integrity check failed")
            else:
                print("❌ No data retrieved")
                return False
        except Exception as e:
            print(f"❌ Secret read failed: {e}")
            return False
        
        # Test secret deletion
        print(f"\n🗑️  Testing secret deletion: {test_secret_path}")
        try:
            vault_client.delete_secret(test_secret_path)
            print("✅ Secret deleted successfully")
        except Exception as e:
            print(f"❌ Secret deletion failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ VaultClient import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Vault test failed: {e}")
        return False


async def test_environment_variables():
    """Test environment variable access"""
    print("\n🌍 Testing Environment Variables")
    print("=" * 35)
    
    # Check critical environment variables
    env_vars = [
        "LITELLM_API_KEY",
        "VAULT_ADDR", 
        "VAULT_TOKEN",
        "VAULT_NAMESPACE",
        "ENVIRONMENT"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "token" in var.lower() or "key" in var.lower():
                masked_value = f"{value[:8]}..." if len(value) > 8 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")


async def main():
    """Main test function"""
    print("🚀 Starting Docker Environment Tests")
    print("=" * 50)
    print(f"🕐 Test started at: {datetime.utcnow().isoformat()}")
    
    # Test environment variables
    await test_environment_variables()
    
    # Test model router
    router_success = await test_docker_environment()
    
    # Test Vault integration
    vault_success = await test_vault_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   Model Router: {'✅ PASS' if router_success else '❌ FAIL'}")
    print(f"   Vault Integration: {'✅ PASS' if vault_success else '❌ FAIL'}")
    
    overall_success = router_success and vault_success
    print(f"   Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return overall_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
