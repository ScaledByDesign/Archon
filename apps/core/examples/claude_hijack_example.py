#!/usr/bin/env python3
"""
Example: Using LiteLLM to hijack Claude API calls and route them to local models

This script demonstrates how to use your LiteLLM setup (localhost:7010) to intercept
Claude API calls and route them to your local models while maintaining full tracking.

Usage:
    python claude_hijack_example.py

Requirements:
    pip install openai anthropic requests
"""

import os
import requests
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from anthropic import Anthropic

# Configuration
LITELLM_BASE_URL = "http://localhost:7010/v1"
LITELLM_API_KEY = "sk-zoi-master-key-2024-secure"  # Your LiteLLM master key

class ClaudeHijacker:
    """
    A class that demonstrates different ways to hijack Claude API calls
    and route them through LiteLLM to your local models.
    """
    
    def __init__(self, litellm_base_url: str = LITELLM_BASE_URL, api_key: str = LITELLM_API_KEY):
        self.base_url = litellm_base_url
        self.api_key = api_key
        
        # Initialize OpenAI client pointing to LiteLLM
        self.openai_client = OpenAI(
            base_url=litellm_base_url,
            api_key=api_key
        )
    
    def method_1_openai_client(self, prompt: str, model: str = "claude-3-5-sonnet-20241022") -> Dict[str, Any]:
        """
        Method 1: Use OpenAI client with Claude model names
        This will be routed to your local models via LiteLLM configuration
        """
        try:
            response = self.openai_client.chat.completions.create(
                model=model,  # This will be hijacked by LiteLLM
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "model_used": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def method_2_direct_http(self, prompt: str, model: str = "claude-3-sonnet-20240229") -> Dict[str, Any]:
        """
        Method 2: Direct HTTP calls to LiteLLM with Claude model names
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.2
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "response": data["choices"][0]["message"]["content"],
                "model_used": data["model"],
                "usage": data["usage"]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def method_3_anthropic_client_hijack(self, prompt: str) -> Dict[str, Any]:
        """
        Method 3: Monkey-patch Anthropic client to use LiteLLM
        This is more advanced and requires modifying the Anthropic client's base URL
        """
        try:
            # Create Anthropic client but point it to LiteLLM
            # Note: This requires LiteLLM to support Anthropic's API format
            client = Anthropic(
                api_key=self.api_key,
                base_url=self.base_url.replace("/v1", "")  # Remove /v1 for Anthropic format
            )
            
            # This might not work directly as LiteLLM uses OpenAI format
            # But it shows the concept
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return {
                "success": True,
                "response": message.content[0].text,
                "model_used": message.model,
                "usage": message.usage
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        Get list of available models from LiteLLM
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "models": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics from LiteLLM (if available)
        """
        try:
            # This endpoint might vary depending on your LiteLLM setup
            response = requests.get(
                f"{self.base_url.replace('/v1', '')}/spend/tags",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30
            )
            if response.status_code == 200:
                return {"success": True, "stats": response.json()}
            else:
                return {"success": False, "error": f"Stats endpoint returned {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    """
    Demonstration of Claude API hijacking
    """
    print("🔄 Claude API Hijacking Demo - Routing to Local Models via LiteLLM")
    print("=" * 70)
    
    hijacker = ClaudeHijacker()
    
    # Test prompt
    test_prompt = "Explain the concept of API hijacking in software development. Keep it concise."
    
    print(f"\n📝 Test Prompt: {test_prompt}")
    print("-" * 50)
    
    # Method 1: OpenAI Client with Claude model names
    print("\n🔧 Method 1: OpenAI Client with Claude Model Names")
    result1 = hijacker.method_1_openai_client(test_prompt)
    if result1["success"]:
        print(f"✅ Success! Model used: {result1['model_used']}")
        print(f"📊 Usage: {result1['usage']}")
        print(f"💬 Response: {result1['response'][:200]}...")
    else:
        print(f"❌ Error: {result1['error']}")
    
    # Method 2: Direct HTTP calls
    print("\n🌐 Method 2: Direct HTTP Calls")
    result2 = hijacker.method_2_direct_http(test_prompt)
    if result2["success"]:
        print(f"✅ Success! Model used: {result2['model_used']}")
        print(f"📊 Usage: {result2['usage']}")
        print(f"💬 Response: {result2['response'][:200]}...")
    else:
        print(f"❌ Error: {result2['error']}")
    
    # Get available models
    print("\n📋 Available Models:")
    models_result = hijacker.get_available_models()
    if models_result["success"]:
        claude_models = [m for m in models_result["models"]["data"] if "claude" in m["id"]]
        print(f"✅ Found {len(claude_models)} Claude models:")
        for model in claude_models[:5]:  # Show first 5
            print(f"   - {model['id']}")
    else:
        print(f"❌ Error getting models: {models_result['error']}")
    
    # Get usage stats
    print("\n📈 Usage Statistics:")
    stats_result = hijacker.get_usage_stats()
    if stats_result["success"]:
        print("✅ Usage stats retrieved successfully")
        print(f"📊 Stats: {json.dumps(stats_result['stats'], indent=2)[:300]}...")
    else:
        print(f"❌ Error getting stats: {stats_result['error']}")
    
    print("\n" + "=" * 70)
    print("🎉 Demo completed! Your Claude API calls are now being routed to local models.")
    print("💡 All requests are tracked in your PostgreSQL database via LiteLLM.")


if __name__ == "__main__":
    main()
