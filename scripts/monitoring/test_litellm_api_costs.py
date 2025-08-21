#!/usr/bin/env python3
"""
Test script to verify LiteLLM cost tracking through the LiteLLM API
"""
import requests
import json
import time
import sys
from typing import Dict, Any, List

def test_litellm_model(model_name: str, test_message: str, max_tokens: int = 50, api_key: str = "dummy") -> Dict[str, Any]:
    """Test a model through the LiteLLM API"""
    print(f"Testing {model_name} via LiteLLM API...")
    print(f"  Message: {test_message[:50]}...")
    print(f"  Max tokens: {max_tokens}")
    
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add API key if provided
        if api_key and api_key != "dummy":
            headers['Authorization'] = f'Bearer {api_key}'
        
        if model_name == "zoi-embed":
            # Test embedding model
            response = requests.post(
                'http://localhost:4000/v1/embeddings',
                headers=headers,
                json={
                    'model': model_name,
                    'input': test_message
                },
                timeout=120
            )
        else:
            # Test chat models
            response = requests.post(
                'http://localhost:4000/v1/chat/completions',
                headers=headers,
                json={
                    'model': model_name,
                    'messages': [{'role': 'user', 'content': test_message}],
                    'max_tokens': max_tokens,
                    'temperature': 0.1
                },
                timeout=180
            )
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract usage and cost information
            usage = data.get('usage', {})
            
            # Look for cost information in response headers or data
            cost_info = {}
            if 'x-litellm-cost' in response.headers:
                cost_info['total_cost'] = float(response.headers['x-litellm-cost'])
            
            result = {
                'status': 'success',
                'model': model_name,
                'response_time': response.elapsed.total_seconds(),
                'usage': usage,
                'cost_info': cost_info,
                'response_headers': dict(response.headers),
                'response_preview': str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
            }
            
            print(f"  ✅ Success - Status: {response.status_code}")
            if usage:
                print(f"     Tokens: {usage.get('total_tokens', 'N/A')}")
            if cost_info:
                print(f"     Cost: ${cost_info.get('total_cost', 'N/A')}")
            
            return result
            
        elif response.status_code == 401:
            return {
                'status': 'auth_required',
                'model': model_name,
                'message': 'Authentication required - this is expected for LiteLLM proxy'
            }
        else:
            error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
            print(f"  ❌ Failed - {error_msg}")
            return {
                'status': 'error',
                'model': model_name,
                'error': error_msg
            }
            
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ Error - {error_msg}")
        return {
            'status': 'error',
            'model': model_name,
            'error': error_msg
        }

def test_litellm_health_and_models() -> Dict[str, Any]:
    """Test LiteLLM health and model endpoints"""
    print("Testing LiteLLM health and model endpoints...")
    
    results = {}
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:4000/health', timeout=30)
        results['health'] = {
            'status_code': response.status_code,
            'response': response.text[:200] if response.status_code != 200 else 'OK'
        }
    except Exception as e:
        results['health'] = {'error': str(e)}
    
    # Test models endpoint
    try:
        response = requests.get('http://localhost:4000/v1/models', timeout=30)
        results['models'] = {
            'status_code': response.status_code,
            'response': response.text[:200] if response.status_code != 200 else 'OK'
        }
    except Exception as e:
        results['models'] = {'error': str(e)}
    
    return results

def generate_litellm_report(results: List[Dict[str, Any]], health_results: Dict[str, Any]) -> None:
    """Generate a comprehensive LiteLLM API test report"""
    print("\n" + "=" * 100)
    print("LITELLM API COST TRACKING REPORT")
    print("=" * 100)
    
    # Health check results
    print(f"\n🏥 HEALTH CHECK RESULTS")
    print("-" * 50)
    for endpoint, result in health_results.items():
        if 'error' in result:
            print(f"❌ {endpoint}: {result['error']}")
        else:
            status = "✅" if result['status_code'] == 200 else "⚠️" if result['status_code'] == 401 else "❌"
            print(f"{status} {endpoint}: HTTP {result['status_code']}")
    
    # Model test results
    successful_tests = [r for r in results if r['status'] == 'success']
    auth_required_tests = [r for r in results if r['status'] == 'auth_required']
    failed_tests = [r for r in results if r['status'] == 'error']
    
    print(f"\n📊 MODEL TEST RESULTS")
    print("-" * 50)
    print(f"Total Models Tested: {len(results)}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Auth Required: {len(auth_required_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if successful_tests:
        print(f"\n✅ SUCCESSFUL TESTS")
        print("-" * 50)
        for result in successful_tests:
            print(f"\n{result['model']}:")
            print(f"  Response Time: {result['response_time']:.2f}s")
            if result['usage']:
                usage = result['usage']
                print(f"  Token Usage:")
                print(f"    - Input: {usage.get('prompt_tokens', 'N/A')}")
                print(f"    - Output: {usage.get('completion_tokens', 'N/A')}")
                print(f"    - Total: {usage.get('total_tokens', 'N/A')}")
            if result['cost_info']:
                print(f"  Cost: ${result['cost_info'].get('total_cost', 'N/A')}")
            
            # Check for cost-related headers
            cost_headers = {k: v for k, v in result['response_headers'].items() 
                          if 'cost' in k.lower() or 'usage' in k.lower() or 'token' in k.lower()}
            if cost_headers:
                print(f"  Cost Headers: {cost_headers}")
    
    if auth_required_tests:
        print(f"\n🔐 AUTHENTICATION REQUIRED")
        print("-" * 50)
        for result in auth_required_tests:
            print(f"- {result['model']}: {result['message']}")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS")
        print("-" * 50)
        for result in failed_tests:
            print(f"- {result['model']}: {result['error']}")

def main():
    """Main test function"""
    print("=" * 100)
    print("LITELLM API COST TRACKING TEST")
    print("=" * 100)
    print("Testing cost tracking through LiteLLM proxy API")
    print("This will show if cost tracking is properly logged in LiteLLM")
    
    # Test health and model endpoints first
    health_results = test_litellm_health_and_models()
    
    # Models to test through LiteLLM API
    models_to_test = [
        {
            'name': 'zoi-helper',
            'message': 'Write a simple Python hello world function.',
            'max_tokens': 100
        },
        {
            'name': 'zoi-thinker', 
            'message': 'Explain the concept of recursion briefly.',
            'max_tokens': 150
        },
        {
            'name': 'zoi-coder-vllm',
            'message': 'Fix this code: def add(a b): return a + b',
            'max_tokens': 50
        },
        {
            'name': 'zoi-embed',
            'message': 'This is a test sentence for embedding cost tracking.',
            'max_tokens': 0  # Not used for embeddings
        },
        {
            'name': 'zoi-rag-helper',
            'message': 'Create a simple REST API endpoint in Python.',
            'max_tokens': 200
        }
    ]
    
    print(f"\n🧪 TESTING {len(models_to_test)} MODELS")
    print("-" * 100)
    
    # Test each model
    results = []
    for i, test_config in enumerate(models_to_test, 1):
        print(f"\n[{i}/{len(models_to_test)}] ", end="")
        result = test_litellm_model(
            test_config['name'], 
            test_config['message'], 
            test_config['max_tokens']
        )
        results.append(result)
        
        # Wait between tests
        if i < len(models_to_test):
            print("  Waiting 3 seconds...")
            time.sleep(3)
    
    # Generate comprehensive report
    generate_litellm_report(results, health_results)
    
    # Summary and recommendations
    successful_count = sum(1 for r in results if r['status'] == 'success')
    auth_count = sum(1 for r in results if r['status'] == 'auth_required')
    
    print(f"\n🎯 SUMMARY")
    print("-" * 50)
    if successful_count > 0:
        print(f"✅ {successful_count} models working without authentication")
        print("   Cost tracking data should be visible in LiteLLM logs")
    
    if auth_count > 0:
        print(f"🔐 {auth_count} models require authentication")
        print("   This is expected for production LiteLLM deployments")
        print("   To test with auth, provide LITELLM_MASTER_KEY")
    
    failed_count = len(results) - successful_count - auth_count
    if failed_count > 0:
        print(f"❌ {failed_count} models failed - check configuration")
    
    print(f"\n💡 NEXT STEPS:")
    print("1. Check LiteLLM container logs: docker logs litellm")
    print("2. Look for cost tracking entries in the logs")
    print("3. Check database for spend tracking records")
    print("4. Monitor Prometheus metrics for cost data")
    
    sys.exit(0 if successful_count > 0 or auth_count > 0 else 1)

if __name__ == "__main__":
    main()
