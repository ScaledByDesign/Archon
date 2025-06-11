#!/usr/bin/env python3
"""
Simple test script for LiteLLM with local Ollama model
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

LITELLM_BASE_URL = "http://zoi.local:4000"
API_KEY = "sk-change-me-to-random-string"

async def test_local_model():
    """Test LiteLLM with local Ollama model"""
    print("🧪 Testing LiteLLM with Local Ollama Model")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        
        # Test 1: Check if local model is available
        print("\n1. Checking available models...")
        try:
            async with session.get(f"{LITELLM_BASE_URL}/v1/models", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    local_models = [model for model in data.get('data', []) if 'llama3.2' in model.get('id', '')]
                    if local_models:
                        print(f"✅ Found local model: {local_models[0]['id']}")
                    else:
                        print("❌ No local models found")
                        return False
                else:
                    print(f"❌ Failed to get models: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error getting models: {e}")
            return False
        
        # Test 2: Simple chat completion with local model
        print("\n2. Testing chat completion with local model...")
        try:
            payload = {
                "model": "llama3.2-1b",
                "messages": [{"role": "user", "content": "Say hello in one word"}],
                "max_tokens": 5
            }
            
            async with session.post(f"{LITELLM_BASE_URL}/v1/chat/completions", 
                                  headers=headers, 
                                  json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    message = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    print(f"✅ Local model response: {message.strip()}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Chat completion failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error in chat completion: {e}")
            import traceback
            traceback.print_exc()
            return False

async def main():
    """Main test function"""
    print("🔍 Testing LiteLLM Local Integration")
    print("==================================")
    
    success = await test_local_model()
    
    if success:
        print("\n🎉 Local LiteLLM integration test PASSED!")
        print("The LiteLLM service is successfully communicating with Ollama.")
        sys.exit(0)
    else:
        print("\n💥 Local LiteLLM integration test FAILED!")
        print("Check the logs for more details.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
