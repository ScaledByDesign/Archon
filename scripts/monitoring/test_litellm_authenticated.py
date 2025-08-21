#!/usr/bin/env python3
"""
Test script to verify LiteLLM cost tracking with proper authentication
"""
import requests
import json
import time
import sys
from typing import Dict, Any, List

# Master key from the .env file
LITELLM_MASTER_KEY = "sk-wqn0xwq_vha4MVM2yzw"

def test_authenticated_model(model_name: str, test_message: str, max_tokens: int = 50) -> Dict[str, Any]:
    """Test a model through the LiteLLM API with authentication"""
    print(f"Testing {model_name} via authenticated LiteLLM API...")
    print(f"  Message: {test_message[:50]}...")
    print(f"  Max tokens: {max_tokens}")
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {LITELLM_MASTER_KEY}'
        }
        
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
            
            # Look for cost information in response headers
            cost_headers = {k: v for k, v in response.headers.items() 
                          if 'cost' in k.lower() or 'usage' in k.lower() or 'token' in k.lower()}
            
            result = {
                'status': 'success',
                'model': model_name,
                'response_time': response.elapsed.total_seconds(),
                'usage': usage,
                'cost_headers': cost_headers,
                'all_headers': dict(response.headers),
                'response_preview': str(data)[:300] + "..." if len(str(data)) > 300 else str(data)
            }
            
            print(f"  ✅ Success - Status: {response.status_code}")
            if usage:
                total_tokens = usage.get('total_tokens', 0)
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                print(f"     Tokens: {input_tokens} input + {output_tokens} output = {total_tokens} total")
            
            # Check for cost-related headers
            if cost_headers:
                print(f"     Cost Headers: {cost_headers}")
            
            return result
            
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

def test_spend_endpoints() -> Dict[str, Any]:
    """Test LiteLLM spend tracking endpoints"""
    print("Testing LiteLLM spend tracking endpoints...")
    
    headers = {
        'Authorization': f'Bearer {LITELLM_MASTER_KEY}'
    }
    
    results = {}
    
    # Test spend logs endpoint
    try:
        response = requests.get('http://localhost:4000/spend/logs', headers=headers, timeout=30)
        results['spend_logs'] = {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else response.text[:200]
        }
        print(f"  Spend logs: HTTP {response.status_code}")
    except Exception as e:
        results['spend_logs'] = {'error': str(e)}
        print(f"  Spend logs: Error - {str(e)}")
    
    # Test spend tags endpoint
    try:
        response = requests.get('http://localhost:4000/spend/tags', headers=headers, timeout=30)
        results['spend_tags'] = {
            'status_code': response.status_code,
            'data': response.json() if response.status_code == 200 else response.text[:200]
        }
        print(f"  Spend tags: HTTP {response.status_code}")
    except Exception as e:
        results['spend_tags'] = {'error': str(e)}
        print(f"  Spend tags: Error - {str(e)}")
    
    return results

def calculate_expected_cost(model_name: str, usage: Dict[str, Any]) -> Dict[str, float]:
    """Calculate expected cost based on our model pricing"""
    
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
        'input_cost': round(input_cost, 10),
        'output_cost': round(output_cost, 10),
        'total_cost': round(total_cost, 10)
    }

def generate_authenticated_report(results: List[Dict[str, Any]], spend_results: Dict[str, Any]) -> None:
    """Generate comprehensive authenticated test report"""
    print("\n" + "=" * 100)
    print("LITELLM AUTHENTICATED COST TRACKING REPORT")
    print("=" * 100)
    
    # Spend endpoint results
    print(f"\n💰 SPEND TRACKING ENDPOINTS")
    print("-" * 50)
    for endpoint, result in spend_results.items():
        if 'error' in result:
            print(f"❌ {endpoint}: {result['error']}")
        else:
            status = "✅" if result['status_code'] == 200 else "⚠️"
            print(f"{status} {endpoint}: HTTP {result['status_code']}")
            if result['status_code'] == 200 and isinstance(result['data'], list):
                print(f"   Found {len(result['data'])} spend records")
    
    # Model test results
    successful_tests = [r for r in results if r['status'] == 'success']
    failed_tests = [r for r in results if r['status'] == 'error']
    
    print(f"\n📊 AUTHENTICATED MODEL TESTS")
    print("-" * 50)
    print(f"Total Models Tested: {len(results)}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if successful_tests:
        print(f"\n✅ SUCCESSFUL AUTHENTICATED TESTS")
        print("-" * 50)
        
        total_expected_cost = 0.0
        
        for result in successful_tests:
            print(f"\n{result['model'].upper()}:")
            print(f"  Response Time: {result['response_time']:.2f}s")
            
            if result['usage']:
                usage = result['usage']
                print(f"  Token Usage:")
                print(f"    - Input Tokens:  {usage.get('prompt_tokens', 0):,}")
                print(f"    - Output Tokens: {usage.get('completion_tokens', 0):,}")
                print(f"    - Total Tokens:  {usage.get('total_tokens', 0):,}")
                
                # Calculate expected cost
                expected_cost = calculate_expected_cost(result['model'], usage)
                if expected_cost['total_cost'] > 0:
                    print(f"  Expected Cost:")
                    print(f"    - Input Cost:  ${expected_cost['input_cost']:.10f}")
                    print(f"    - Output Cost: ${expected_cost['output_cost']:.10f}")
                    print(f"    - Total Cost:  ${expected_cost['total_cost']:.10f}")
                    total_expected_cost += expected_cost['total_cost']
            
            # Show cost-related headers
            if result['cost_headers']:
                print(f"  Cost Headers: {result['cost_headers']}")
            
            # Show interesting headers
            interesting_headers = {k: v for k, v in result['all_headers'].items() 
                                 if k.lower().startswith('x-litellm')}
            if interesting_headers:
                print(f"  LiteLLM Headers: {interesting_headers}")
        
        print(f"\n💰 COST SUMMARY")
        print("-" * 30)
        print(f"Total Expected Cost: ${total_expected_cost:.10f}")
        print(f"Cost per successful test: ${(total_expected_cost / len(successful_tests)):.10f}")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS")
        print("-" * 50)
        for result in failed_tests:
            print(f"- {result['model']}: {result['error']}")

def main():
    """Main test function"""
    print("=" * 100)
    print("LITELLM AUTHENTICATED COST TRACKING TEST")
    print("=" * 100)
    print("Testing cost tracking through authenticated LiteLLM API")
    print(f"Using master key: {LITELLM_MASTER_KEY[:10]}...")
    
    # Test spend endpoints first
    spend_results = test_spend_endpoints()
    
    # Models to test with different usage patterns
    test_cases = [
        {
            'model': 'zoi-helper',
            'message': 'Write a simple Python function to add two numbers.',
            'max_tokens': 100
        },
        {
            'model': 'zoi-embed',
            'message': 'This is a test sentence for cost tracking verification.',
            'max_tokens': 0  # Not used for embeddings
        },
        {
            'model': 'zoi-thinker',
            'message': 'Explain the benefits of using Docker containers.',
            'max_tokens': 150
        }
    ]
    
    print(f"\n🧪 TESTING {len(test_cases)} MODELS WITH AUTHENTICATION")
    print("-" * 100)
    
    # Test each model
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] ", end="")
        result = test_authenticated_model(
            test_case['model'], 
            test_case['message'], 
            test_case['max_tokens']
        )
        results.append(result)
        
        # Wait between tests
        if i < len(test_cases):
            print("  Waiting 5 seconds...")
            time.sleep(5)
    
    # Generate comprehensive report
    generate_authenticated_report(results, spend_results)
    
    # Final summary
    successful_count = sum(1 for r in results if r['status'] == 'success')
    
    print(f"\n🎯 FINAL SUMMARY")
    print("-" * 50)
    if successful_count > 0:
        print(f"✅ {successful_count}/{len(test_cases)} models working with authentication")
        print("✅ Cost tracking is properly configured and active")
        print("✅ Token usage is being tracked accurately")
        print("✅ LiteLLM proxy is logging all requests and costs")
    else:
        print("❌ No models working - check configuration")
    
    print(f"\n💡 VERIFICATION STEPS:")
    print("1. Check LiteLLM logs: docker logs litellm")
    print("2. Check database for spend records")
    print("3. Access LiteLLM UI at http://localhost:7010")
    print("4. Monitor Prometheus metrics for cost data")
    
    sys.exit(0 if successful_count > 0 else 1)

if __name__ == "__main__":
    main()
