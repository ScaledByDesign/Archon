#!/usr/bin/env python3
"""
Test script to verify LiteLLM model health and functionality
"""
import requests
import json
import time
import sys
from typing import Dict, Any

def test_model_direct(model_name: str, ollama_model: str, model_type: str = 'chat') -> Dict[str, Any]:
    """Test a model directly through Ollama API"""
    print(f"Testing {model_name} ({ollama_model}) directly via Ollama...")
    
    try:
        if model_type == 'embedding':
            response = requests.post(
                'http://ollama:11434/v1/embeddings',
                json={'model': ollama_model, 'input': 'test'},
                timeout=60
            )
        else:
            response = requests.post(
                'http://ollama:11434/v1/chat/completions',
                json={
                    'model': ollama_model,
                    'messages': [{'role': 'user', 'content': 'Hello, respond with just "OK"'}],
                    'max_tokens': 5
                },
                timeout=120
            )
        
        if response.status_code == 200:
            return {'status': 'healthy', 'response_time': response.elapsed.total_seconds()}
        else:
            return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}: {response.text[:200]}'}
            
    except requests.exceptions.Timeout:
        return {'status': 'unhealthy', 'error': 'Request timeout'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

def test_litellm_health() -> Dict[str, Any]:
    """Test LiteLLM general health"""
    print("Testing LiteLLM general health...")
    
    try:
        # Try without auth first
        response = requests.get('http://localhost:4000/health', timeout=30)
        if response.status_code == 200:
            return {'status': 'healthy', 'data': response.json()}
        elif response.status_code == 401:
            return {'status': 'auth_required', 'message': 'Authentication required but service is running'}
        else:
            return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}

def main():
    """Main test function"""
    print("=" * 60)
    print("LiteLLM Model Health Check")
    print("=" * 60)
    
    # Test models to check
    models_to_test = [
        ('zoi-embed', 'mxbai-embed-large', 'embedding'),
        ('zoi-helper', 'qwen2.5-coder:7b-instruct', 'chat'),
        ('zoi-rag-helper', 'qwen2.5-coder:7b-instruct', 'chat'),
        ('zoi-rag-thinker', 'qwen2.5:7b', 'chat')
    ]
    
    # Test LiteLLM health
    litellm_health = test_litellm_health()
    print(f"LiteLLM Health: {litellm_health['status']}")
    if 'error' in litellm_health:
        print(f"  Error: {litellm_health['error']}")
    elif 'message' in litellm_health:
        print(f"  Message: {litellm_health['message']}")
    print()
    
    # Test each model
    results = {}
    for model_name, ollama_model, model_type in models_to_test:
        result = test_model_direct(model_name, ollama_model, model_type)
        results[model_name] = result
        
        print(f"  Status: {result['status']}")
        if result['status'] == 'healthy':
            print(f"  Response Time: {result['response_time']:.2f}s")
        else:
            print(f"  Error: {result['error']}")
        print()
        
        # Wait between tests to avoid resource contention
        if model_name != models_to_test[-1][0]:
            print("  Waiting 10 seconds before next test...")
            time.sleep(10)
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    healthy_count = sum(1 for r in results.values() if r['status'] == 'healthy')
    total_count = len(results)
    
    print(f"Models tested: {total_count}")
    print(f"Healthy models: {healthy_count}")
    print(f"Unhealthy models: {total_count - healthy_count}")
    print()
    
    for model_name, result in results.items():
        status_icon = "✅" if result['status'] == 'healthy' else "❌"
        print(f"{status_icon} {model_name}: {result['status']}")
    
    print("=" * 60)
    
    # Exit with appropriate code
    if healthy_count == total_count:
        print("All models are healthy! 🎉")
        sys.exit(0)
    else:
        print(f"{total_count - healthy_count} models need attention.")
        sys.exit(1)

if __name__ == "__main__":
    main()
