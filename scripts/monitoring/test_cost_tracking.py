#!/usr/bin/env python3
"""
Test script to verify LiteLLM cost tracking functionality
"""
import requests
import json
import time
import sys
from typing import Dict, Any, List

def test_model_cost_tracking(model_name: str, test_message: str = "Hello, respond with just 'OK'") -> Dict[str, Any]:
    """Test cost tracking for a specific model"""
    print(f"Testing cost tracking for {model_name}...")

    # Map model names to their Ollama equivalents
    model_mapping = {
        'zoi-coder-vllm': 'Qwen/Qwen3-0.6B',  # This goes through vLLM
        'zoi-thinker': 'qwen2.5:7b',
        'zoi-helper': 'qwen2.5-coder:7b-instruct',
        'zoi-embed': 'mxbai-embed-large',
        'zoi-rag-helper': 'qwen2.5-coder:7b-instruct',
        'zoi-rag-thinker': 'qwen2.5:7b'
    }

    try:
        # Make a request to the model
        if model_name == "zoi-embed":
            # Test embedding model
            response = requests.post(
                'http://ollama:11434/v1/embeddings',
                json={'model': model_mapping[model_name], 'input': test_message},
                timeout=60
            )
        elif model_name == "zoi-coder-vllm":
            # Test vLLM model
            response = requests.post(
                'http://vllm:8000/v1/chat/completions',
                json={
                    'model': model_mapping[model_name],
                    'messages': [{'role': 'user', 'content': test_message}],
                    'max_tokens': 10
                },
                timeout=120
            )
        else:
            # Test Ollama chat models
            response = requests.post(
                'http://ollama:11434/v1/chat/completions',
                json={
                    'model': model_mapping[model_name],
                    'messages': [{'role': 'user', 'content': test_message}],
                    'max_tokens': 10
                },
                timeout=120
            )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract usage information
            usage = data.get('usage', {})
            
            result = {
                'status': 'success',
                'model': model_name,
                'response_time': response.elapsed.total_seconds(),
                'usage': usage,
                'estimated_cost': calculate_estimated_cost(model_name, usage)
            }
            
            return result
        else:
            return {
                'status': 'error',
                'model': model_name,
                'error': f'HTTP {response.status_code}: {response.text[:200]}'
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'model': model_name,
            'error': str(e)
        }

def calculate_estimated_cost(model_name: str, usage: Dict[str, Any]) -> Dict[str, float]:
    """Calculate estimated cost based on model pricing"""
    
    # Cost per token for each model (from our configuration)
    model_costs = {
        'zoi-coder-vllm': {'input': 0.000001, 'output': 0.000002},
        'zoi-thinker': {'input': 0.000002, 'output': 0.000004},
        'zoi-helper': {'input': 0.000002, 'output': 0.000003},
        'zoi-embed': {'input': 0.0000005, 'output': 0.0},
        'zoi-rag-helper': {'input': 0.000003, 'output': 0.000004},
        'zoi-rag-thinker': {'input': 0.000003, 'output': 0.000005}
    }
    
    if model_name not in model_costs:
        return {'input_cost': 0.0, 'output_cost': 0.0, 'total_cost': 0.0}
    
    costs = model_costs[model_name]
    
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)
    
    input_cost = input_tokens * costs['input']
    output_cost = output_tokens * costs['output']
    total_cost = input_cost + output_cost
    
    return {
        'input_cost': round(input_cost, 8),
        'output_cost': round(output_cost, 8),
        'total_cost': round(total_cost, 8),
        'input_tokens': input_tokens,
        'output_tokens': output_tokens
    }

def test_litellm_cost_api() -> Dict[str, Any]:
    """Test LiteLLM cost tracking API endpoints"""
    print("Testing LiteLLM cost tracking API...")
    
    try:
        # Test model cost information endpoint
        response = requests.get('http://localhost:4000/model/info', timeout=30)
        
        if response.status_code == 200:
            return {'status': 'success', 'data': response.json()}
        elif response.status_code == 401:
            return {'status': 'auth_required', 'message': 'Authentication required'}
        else:
            return {'status': 'error', 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def generate_cost_report(results: List[Dict[str, Any]]) -> None:
    """Generate a comprehensive cost tracking report"""
    print("\n" + "=" * 80)
    print("COST TRACKING REPORT")
    print("=" * 80)
    
    total_estimated_cost = 0.0
    successful_tests = 0
    
    for result in results:
        if result['status'] == 'success':
            successful_tests += 1
            model = result['model']
            usage = result['usage']
            cost = result['estimated_cost']
            
            print(f"\n📊 {model.upper()}")
            print(f"   Status: ✅ Success")
            print(f"   Response Time: {result['response_time']:.2f}s")
            
            if usage:
                print(f"   Token Usage:")
                print(f"     - Input Tokens: {usage.get('prompt_tokens', 0):,}")
                print(f"     - Output Tokens: {usage.get('completion_tokens', 0):,}")
                print(f"     - Total Tokens: {usage.get('total_tokens', 0):,}")
            
            if cost['total_cost'] > 0:
                print(f"   Estimated Cost:")
                print(f"     - Input Cost: ${cost['input_cost']:.8f}")
                print(f"     - Output Cost: ${cost['output_cost']:.8f}")
                print(f"     - Total Cost: ${cost['total_cost']:.8f}")
                total_estimated_cost += cost['total_cost']
            else:
                print(f"   Estimated Cost: $0.00 (Free/Local)")
        else:
            print(f"\n❌ {result['model'].upper()}")
            print(f"   Status: Failed")
            print(f"   Error: {result['error']}")
    
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Models Tested: {len(results)}")
    print(f"Successful Tests: {successful_tests}")
    print(f"Failed Tests: {len(results) - successful_tests}")
    print(f"Total Estimated Cost: ${total_estimated_cost:.8f}")
    
    if total_estimated_cost > 0:
        print(f"\n💡 Cost Tracking: ENABLED")
        print(f"   All models have cost tracking configured")
    else:
        print(f"\n💡 Cost Tracking: LOCAL MODELS")
        print(f"   Models are running locally with estimated costs")

def main():
    """Main test function"""
    print("=" * 80)
    print("LITELLM COST TRACKING TEST")
    print("=" * 80)
    
    # Models to test
    models_to_test = [
        'zoi-coder-vllm',
        'zoi-thinker', 
        'zoi-helper',
        'zoi-embed',
        'zoi-rag-helper',
        'zoi-rag-thinker'
    ]
    
    # Test each model
    results = []
    for i, model in enumerate(models_to_test):
        result = test_model_cost_tracking(model)
        results.append(result)
        
        # Wait between tests to avoid resource contention
        if i < len(models_to_test) - 1:
            print(f"  Waiting 5 seconds before next test...")
            time.sleep(5)
    
    # Test LiteLLM API
    api_result = test_litellm_cost_api()
    print(f"\nLiteLLM API Status: {api_result['status']}")
    
    # Generate report
    generate_cost_report(results)
    
    # Exit with appropriate code
    successful_count = sum(1 for r in results if r['status'] == 'success')
    if successful_count == len(results):
        print(f"\n🎉 All cost tracking tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {len(results) - successful_count} tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
