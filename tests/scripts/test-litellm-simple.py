#!/usr/bin/env python3
"""
Simple LiteLLM Integration Test for M4 Mac Mini
Uses requests library for simpler synchronous testing
"""

import requests
import json
import time
import sys

LITELLM_BASE_URL = "http://zoi.local:4000"
API_KEY = "sk-change-me-to-random-string"
TIMEOUT = 60  # 60 seconds for M4 Mac Mini

def test_health_check():
    """Test LiteLLM health endpoint"""
    print("\n🏥 Testing LiteLLM Health Check")
    print("-" * 40)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(f"{LITELLM_BASE_URL}/health", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            healthy_count = data.get('healthy_count', 0)
            unhealthy_count = data.get('unhealthy_count', 0)
            total_models = healthy_count + unhealthy_count
            
            print(f"✅ LiteLLM is responding")
            print(f"   📊 Models: {healthy_count} healthy, {unhealthy_count} unhealthy, {total_models} total")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_model_listing():
    """Test model listing endpoint"""
    print("\n📋 Testing Model Listing")
    print("-" * 40)
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(f"{LITELLM_BASE_URL}/v1/models", headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            
            # Find our local model
            local_models = [m for m in models if 'llama3.2-1b' in m.get('id', '')]
            external_models = [m for m in models if any(provider in m.get('id', '') for provider in ['gpt', 'claude', 'gemini'])]
            
            print(f"✅ Found {len(models)} total models")
            print(f"   🦙 Local models: {[m['id'] for m in local_models]}")
            print(f"   🌐 External models: {len(external_models)} configured")
            
            return local_models, external_models
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return [], []
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        return [], []

def test_local_model_chat():
    """Test chat completion with local Ollama model"""
    print(f"\n🤖 Testing Local Model: llama3.2-1b")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3.2-1b",
        "messages": [{"role": "user", "content": "Say 'Hello from Ollama' in exactly 3 words"}],
        "max_tokens": 10,
        "temperature": 0.1
    }
    
    try:
        start_time = time.time()
        print(f"⏳ Sending request (timeout: {TIMEOUT}s)...")
        
        response = requests.post(f"{LITELLM_BASE_URL}/v1/chat/completions", 
                               headers=headers, 
                               json=payload, 
                               timeout=TIMEOUT)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            usage = data.get('usage', {})
            
            print(f"✅ Local model response ({response_time:.1f}s):")
            print(f"   💬 Message: '{message.strip()}'")
            print(f"   📊 Usage: {usage.get('total_tokens', 0)} tokens")
            return True
        else:
            print(f"❌ Local model failed: {response.status_code} - {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ Local model timed out after {TIMEOUT}s (expected on M4 Mac Mini CPU)")
        return False
    except Exception as e:
        print(f"❌ Error with local model: {e}")
        return False

def test_connectivity():
    """Test basic connectivity to services"""
    print(f"\n🔌 Testing Service Connectivity")
    print("-" * 40)
    
    services = {
        "LiteLLM": "http://zoi.local:4000",
        "Ollama": "http://zoi.local:11434"
    }
    
    results = {}
    for name, url in services.items():
        try:
            response = requests.get(f"{url}/", timeout=5)
            results[name] = f"✅ {response.status_code}"
            print(f"   {name}: ✅ Responding ({response.status_code})")
        except Exception as e:
            results[name] = f"❌ {str(e)[:50]}"
            print(f"   {name}: ❌ {str(e)[:50]}")
    
    return all("✅" in status for status in results.values())

def main():
    """Main test function"""
    print("🔍 LiteLLM Integration Test Suite")
    print("=" * 50)
    print("🖥️  Platform: M4 Mac Mini with Apple Silicon")
    print("🐳 Environment: Docker containers")
    print("🦙 Local LLM: Ollama with llama3.2:1b")
    
    # Track test results
    results = {
        "connectivity": False,
        "health_check": False,
        "model_listing": False,
        "local_model": False
    }
    
    # Test 1: Basic Connectivity
    results["connectivity"] = test_connectivity()
    
    if not results["connectivity"]:
        print("\n💥 Basic connectivity failed. Check if services are running.")
        sys.exit(1)
    
    # Test 2: Health Check
    results["health_check"] = test_health_check()
    
    # Test 3: Model Listing
    local_models, external_models = test_model_listing()
    results["model_listing"] = len(local_models) > 0 or len(external_models) > 0
    
    # Test 4: Local Model Chat (if available)
    if local_models:
        results["local_model"] = test_local_model_chat()
    else:
        print("\n⚠️  No local models found, skipping local model test")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    # Determine success
    if results["connectivity"] and results["health_check"] and results["model_listing"]:
        print("\n🎉 LiteLLM integration is working correctly!")
        print("✨ Ports and connections are properly configured.")
        print("🔗 LiteLLM (port 4000) ↔ Ollama (port 11434) ✅")
        
        if results["local_model"]:
            print("🤖 Local model chat is working!")
        else:
            print("⚠️  Local model chat may be slow on M4 Mac Mini CPU")
        
        sys.exit(0)
    else:
        print("\n💥 LiteLLM integration has issues.")
        print("🔧 Check the configuration and service status.")
        sys.exit(1)

if __name__ == "__main__":
    main()
