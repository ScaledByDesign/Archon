#!/usr/bin/env python3
"""
Test script to verify LiteLLM connection from within Docker network
This simulates how Langflow will connect to LiteLLM
"""

import requests
import json

# LiteLLM configuration (internal Docker network)
LITELLM_BASE_URL = "http://litellm:4000/v1"
LITELLM_API_KEY = "sk-zoi-master-key-2024-secure"

def test_litellm_connection():
    """Test connection to LiteLLM"""
    print("🔍 Testing LiteLLM Connection...")
    print(f"Base URL: {LITELLM_BASE_URL}")
    print(f"API Key: {LITELLM_API_KEY}")
    print("-" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{LITELLM_BASE_URL.replace('/v1', '')}/health", timeout=10)
        print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: List models
    try:
        response = requests.get(
            f"{LITELLM_BASE_URL}/models",
            headers={"Authorization": f"Bearer {LITELLM_API_KEY}"},
            timeout=10
        )
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Models endpoint: {len(models['data'])} models available")
            claude_models = [m for m in models['data'] if 'claude' in m['id']]
            print(f"🤖 Claude models: {len(claude_models)}")
            for model in claude_models[:3]:
                print(f"   - {model['id']}")
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Models endpoint error: {e}")
    
    # Test 3: Simple chat completion
    try:
        response = requests.post(
            f"{LITELLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {LITELLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-3-5-sonnet-20241022",
                "messages": [
                    {"role": "user", "content": "Say 'LiteLLM connection successful!' and nothing else."}
                ],
                "max_tokens": 50,
                "temperature": 0.1
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data["choices"][0]["message"]["content"]
            print(f"✅ Chat completion successful!")
            print(f"🤖 Model used: {data['model']}")
            print(f"💬 Response: {message}")
            print(f"📊 Usage: {data['usage']}")
        else:
            print(f"❌ Chat completion failed: {response.status_code}")
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Chat completion error: {e}")

if __name__ == "__main__":
    test_litellm_connection()
