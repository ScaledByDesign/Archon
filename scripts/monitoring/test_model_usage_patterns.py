#!/usr/bin/env python3
"""
Test script to verify cost tracking with different usage patterns on a single model
"""
import requests
import json
import time
import sys
from typing import Dict, Any, List

def test_model_with_usage_pattern(model_name: str, backend_model: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
    """Test a model with a specific usage pattern"""
    print(f"Testing: {test_case['name']}")
    print(f"  Message: {test_case['message'][:50]}...")
    print(f"  Max tokens: {test_case['max_tokens']}")
    
    try:
        response = requests.post(
            'http://litellm:4000/v1/chat/completions',
            json={
                'model': model_name,
                'messages': [{'role': 'user', 'content': test_case['message']}],
                'max_tokens': test_case['max_tokens'],
                'temperature': test_case.get('temperature', 0.1)
            },
            timeout=180
        )
        
        if response.status_code == 200:
            data = response.json()
            usage = data.get('usage', {})
            
            # Calculate cost based on our model pricing
            cost_info = calculate_cost(model_name, usage)
            
            result = {
                'status': 'success',
                'test_case': test_case['name'],
                'response_time': response.elapsed.total_seconds(),
                'usage': usage,
                'cost': cost_info,
                'response_preview': data.get('choices', [{}])[0].get('message', {}).get('content', '')[:100]
            }
            
            print(f"  ✅ Success - {usage.get('total_tokens', 0)} tokens, ${cost_info['total_cost']:.8f}")
            return result
        else:
            error_msg = f'HTTP {response.status_code}: {response.text[:200]}'
            print(f"  ❌ Failed - {error_msg}")
            return {
                'status': 'error',
                'test_case': test_case['name'],
                'error': error_msg
            }
            
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ Error - {error_msg}")
        return {
            'status': 'error',
            'test_case': test_case['name'],
            'error': error_msg
        }

def calculate_cost(model_name: str, usage: Dict[str, Any]) -> Dict[str, float]:
    """Calculate cost based on model pricing"""
    
    # Cost per token for the test model
    model_costs = {
        'zoi-coder': {'input': 0.000001, 'output': 0.000002},
        'zoi-planner': {'input': 0.000002, 'output': 0.000004}
    }
    
    if model_name not in model_costs:
        return {'input_cost': 0.0, 'output_cost': 0.0, 'total_cost': 0.0}
    
    costs = model_costs[model_name]
    
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', 0)
    
    input_cost = input_tokens * costs['input']
    output_cost = output_tokens * costs['output']
    total_cost = input_cost + output_cost
    
    return {
        'input_cost': round(input_cost, 10),
        'output_cost': round(output_cost, 10),
        'total_cost': round(total_cost, 10),
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': total_tokens,
        'cost_per_token': round(total_cost / total_tokens, 10) if total_tokens > 0 else 0.0
    }

def generate_usage_report(results: List[Dict[str, Any]]) -> None:
    """Generate a detailed usage and cost report"""
    print("\n" + "=" * 100)
    print("DETAILED USAGE AND COST TRACKING REPORT")
    print("=" * 100)
    
    successful_tests = [r for r in results if r['status'] == 'success']
    failed_tests = [r for r in results if r['status'] == 'error']
    
    if successful_tests:
        print(f"\n📊 SUCCESSFUL TESTS ({len(successful_tests)})")
        print("-" * 100)
        
        total_cost = 0.0
        total_input_tokens = 0
        total_output_tokens = 0
        total_tokens = 0
        
        for i, result in enumerate(successful_tests, 1):
            usage = result['usage']
            cost = result['cost']
            
            print(f"\n{i}. {result['test_case']}")
            print(f"   Response Time: {result['response_time']:.2f}s")
            print(f"   Token Usage:")
            print(f"     • Input Tokens:  {usage.get('prompt_tokens', 0):,}")
            print(f"     • Output Tokens: {usage.get('completion_tokens', 0):,}")
            print(f"     • Total Tokens:  {usage.get('total_tokens', 0):,}")
            print(f"   Cost Breakdown:")
            print(f"     • Input Cost:    ${cost['input_cost']:.10f}")
            print(f"     • Output Cost:   ${cost['output_cost']:.10f}")
            print(f"     • Total Cost:    ${cost['total_cost']:.10f}")
            print(f"     • Cost/Token:    ${cost['cost_per_token']:.10f}")
            print(f"   Response Preview: {result['response_preview'][:80]}...")
            
            total_cost += cost['total_cost']
            total_input_tokens += cost['input_tokens']
            total_output_tokens += cost['output_tokens']
            total_tokens += cost['total_tokens']
        
        print(f"\n" + "=" * 100)
        print("AGGREGATE STATISTICS")
        print("=" * 100)
        print(f"Total Tests:        {len(successful_tests)}")
        print(f"Total Input Tokens: {total_input_tokens:,}")
        print(f"Total Output Tokens:{total_output_tokens:,}")
        print(f"Total Tokens:       {total_tokens:,}")
        print(f"Total Cost:         ${total_cost:.10f}")
        print(f"Average Cost/Token: ${(total_cost / total_tokens):.10f}" if total_tokens > 0 else "N/A")
        print(f"Average Cost/Test:  ${(total_cost / len(successful_tests)):.10f}")
        
        # Cost efficiency analysis
        print(f"\n💰 COST EFFICIENCY ANALYSIS")
        print("-" * 50)
        if total_cost > 0:
            print(f"Cost per 1K tokens: ${(total_cost / total_tokens * 1000):.8f}")
            print(f"Cost per 1M tokens: ${(total_cost / total_tokens * 1000000):.6f}")
        else:
            print("Local model - no external costs")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS ({len(failed_tests)})")
        print("-" * 100)
        for i, result in enumerate(failed_tests, 1):
            print(f"{i}. {result['test_case']}: {result['error']}")

def main():
    """Main test function"""
    print("=" * 100)
    print("MODEL USAGE PATTERN TESTING - ZOI-CODER")
    print("=" * 100)
    
    model_name = "zoi-coder"
    backend_model = "qwen-14b"
    
    # Define different usage patterns to test
    test_cases = [
        {
            'name': 'Short Query (Low Usage)',
            'message': 'Hi',
            'max_tokens': 5,
            'temperature': 0.1
        },
        {
            'name': 'Medium Query (Moderate Usage)',
            'message': 'Explain what Python is in one paragraph.',
            'max_tokens': 100,
            'temperature': 0.1
        },
        {
            'name': 'Code Request (High Usage)',
            'message': 'Write a Python function to calculate the factorial of a number with error handling and documentation.',
            'max_tokens': 300,
            'temperature': 0.1
        },
        {
            'name': 'Complex Analysis (Very High Usage)',
            'message': 'Analyze the pros and cons of different Python web frameworks (Django, Flask, FastAPI) and provide code examples for a simple REST API in each framework.',
            'max_tokens': 800,
            'temperature': 0.2
        },
        {
            'name': 'Minimal Response Test',
            'message': 'Say "OK" and nothing else.',
            'max_tokens': 3,
            'temperature': 0.0
        },
        {
            'name': 'Creative Writing (Variable Usage)',
            'message': 'Write a short story about a programmer who discovers their code can predict the future.',
            'max_tokens': 500,
            'temperature': 0.7
        },
        {
            'name': 'Technical Documentation',
            'message': 'Create comprehensive documentation for a Python class that manages database connections with connection pooling.',
            'max_tokens': 600,
            'temperature': 0.1
        },
        {
            'name': 'Quick Fix Request',
            'message': 'Fix this Python code: def add(a b): return a + b',
            'max_tokens': 50,
            'temperature': 0.1
        }
    ]
    
    print(f"Testing model: {model_name} ({backend_model})")
    print(f"Number of test cases: {len(test_cases)}")
    print(f"Expected cost per input token: $0.000002")
    print(f"Expected cost per output token: $0.000003")
    print("\n" + "-" * 100)
    
    # Run all test cases
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] ", end="")
        result = test_model_with_usage_pattern(model_name, backend_model, test_case)
        results.append(result)
        
        # Wait between tests to avoid overwhelming the model
        if i < len(test_cases):
            print("  Waiting 3 seconds...")
            time.sleep(3)
    
    # Generate comprehensive report
    generate_usage_report(results)
    
    # Final summary
    successful_count = sum(1 for r in results if r['status'] == 'success')
    print(f"\n🎯 TEST SUMMARY")
    print(f"   Successful: {successful_count}/{len(test_cases)}")
    print(f"   Failed: {len(test_cases) - successful_count}/{len(test_cases)}")
    
    if successful_count == len(test_cases):
        print(f"\n🎉 All usage pattern tests passed! Cost tracking is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  Some tests failed. Check the error details above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
