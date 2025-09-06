#!/usr/bin/env python3
"""
Centralized LiteLLM configuration for all Python services
Import this module to get consistent LiteLLM settings
"""

import os
from typing import Dict, Any

# LiteLLM Configuration
LITELLM_CONFIG = {
    "base_url": os.getenv("LITELLM_BASE_URL", "http://localhost:7010/v1"),
    "api_key": os.getenv("LITELLM_API_KEY", "sk-wqn0xwq_vha4MVM2yzw"),
    "models": {
        "primary": os.getenv("PRIMARY_MODEL", "zoi-coder"),
        "advanced": os.getenv("ADVANCED_MODEL", "zoi-planner"),
        "fallback": os.getenv("FALLBACK_MODEL", "gpt-4")
    },
    "timeout": 30,
    "max_tokens": 500,
    "temperature": 0.7
}

# Direct LLM Studio Configuration (if needed)
LLM_STUDIO_CONFIG = {
    "rtx_5070": {
        "url": "http://192.168.8.135:1234/v1",
        "model": "qwen/qwen3-14b",
        "description": "Fast inference on RTX 5070 Ti"
    },
    "rtx_3090": {
        "url": "http://192.168.8.241:1234/v1", 
        "model": "qwen/qwen3-coder-30b",
        "description": "Advanced reasoning on RTX 3090"
    }
}

def get_litellm_client():
    """
    Get a configured LiteLLM client
    Usage:
        from litellm_config import get_litellm_client
        client = get_litellm_client()
        response = client.post("/chat/completions", ...)
    """
    import requests
    
    class LiteLLMClient:
        def __init__(self, config: Dict[str, Any]):
            self.base_url = config["base_url"]
            self.headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            }
            self.config = config
        
        def chat_completion(self, messages, model=None, **kwargs):
            """Make a chat completion request"""
            if model is None:
                model = self.config["models"]["primary"]
            
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config["max_tokens"]),
                "temperature": kwargs.get("temperature", self.config["temperature"])
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=self.config["timeout"]
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                # Fallback to advanced model if primary fails
                if model == self.config["models"]["primary"]:
                    data["model"] = self.config["models"]["advanced"]
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=data,
                        timeout=self.config["timeout"]
                    )
                    if response.status_code == 200:
                        return response.json()
                
                raise Exception(f"LiteLLM request failed: {response.status_code} - {response.text}")
        
        def list_models(self):
            """List available models"""
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
    
    return LiteLLMClient(LITELLM_CONFIG)

# Example usage
if __name__ == "__main__":
    client = get_litellm_client()
    
    # List models
    models = client.list_models()
    if models:
        print("Available models:")
        for model in models["data"]:
            print(f"  - {model['id']}")
    
    # Test chat completion
    response = client.chat_completion([
        {"role": "user", "content": "Say 'Hello from unified LiteLLM config!'"}
    ])
    
    if response:
        print("\nTest response:")
        print(response["choices"][0]["message"]["content"])