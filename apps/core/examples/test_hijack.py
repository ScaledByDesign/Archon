#!/usr/bin/env python3
"""
Quick test script to verify Claude API hijacking is working
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
LITELLM_BASE_URL = "http://localhost:7010/v1"
LITELLM_API_KEY = "sk-zoi-master-key-2024-secure"

def test_connection() -> bool:
    """Test if LiteLLM is accessible"""
    try:
        response = requests.get(f"{LITELLM_BASE_URL.replace('/v1', '')}/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def test_models() -> Dict[str, Any]:
    """Test if Claude models are available"""
    try:
        response = requests.get(
            f"{LITELLM_BASE_URL}/models",
            headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
            timeout=10
        )
        if response.status_code == 200:
            models = response.json()
            claude_models = [m for m in models["data"] if "claude" in m["id"]]
            return {"success": True, "claude_models": claude_models}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_claude_request(model: str = "claude-3-5-sonnet-20241022") -> Dict[str, Any]:
    """Test a Claude API request"""
    try:
        response = requests.post(
            f"{LITELLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LITELLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "user", "content": "Say 'Hello from hijacked Claude!' and nothing else."}
                ],
                "max_tokens": 50,
                "temperature": 0.1
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data["choices"][0]["message"]["content"],
                "model_used": data["model"],
                "usage": data["usage"]
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print("🔍 Testing Claude API Hijacking Setup")
    print("=" * 50)
    
    # Test 1: Connection
    print("\n1️⃣ Testing LiteLLM Connection...")
    if test_connection():
        print("✅ LiteLLM is accessible at localhost:7010")
    else:
        print("❌ Cannot connect to LiteLLM at localhost:7010")
        print("💡 Make sure your docker-compose stack is running:")
        print("   cd apps/llm-local && docker-compose up -d")
        sys.exit(1)
    
    # Test 2: Models
    print("\n2️⃣ Testing Claude Model Availability...")
    models_result = test_models()
    if models_result["success"]:
        claude_models = models_result["claude_models"]
        print(f"✅ Found {len(claude_models)} Claude models:")
        for model in claude_models:
            print(f"   - {model['id']}")
    else:
        print(f"❌ Error getting models: {models_result['error']}")
        sys.exit(1)
    
    # Test 3: Actual Request
    print("\n3️⃣ Testing Claude API Request...")
    test_model = "claude-3-5-sonnet-20241022"
    request_result = test_claude_request(test_model)
    
    if request_result["success"]:
        print(f"✅ Successfully hijacked {test_model}!")
        print(f"🤖 Model actually used: {request_result['model_used']}")
        print(f"💬 Response: {request_result['response']}")
        print(f"📊 Usage: {request_result['usage']}")
    else:
        print(f"❌ Error with Claude request: {request_result['error']}")
        sys.exit(1)
    
    # Test 4: Multiple Models
    print("\n4️⃣ Testing Multiple Claude Models...")
    test_models = [
        "claude-3-5-sonnet-20241022",
        "claude-3-sonnet-20240229", 
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307"
    ]
    
    for model in test_models:
        result = test_claude_request(model)
        if result["success"]:
            print(f"✅ {model} → {result['model_used']}")
        else:
            print(f"❌ {model} → Error: {result['error']}")
    
    print("\n" + "=" * 50)
    print("🎉 Claude API Hijacking Test Complete!")
    print("\n💡 Your applications can now use these endpoints:")
    print(f"   Base URL: {LITELLM_BASE_URL}")
    print(f"   API Key: {LITELLM_API_KEY}")
    print("\n📋 Example usage:")
    print("   curl -X POST http://localhost:7010/v1/chat/completions \\")
    print("     -H 'Authorization: Bearer sk-zoi-master-key-2024-secure' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"model\": \"claude-3-5-sonnet-20241022\", \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}'")

if __name__ == "__main__":
    main()
