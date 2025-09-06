#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the new LLM Studio endpoints configuration
Tests both direct endpoints and LiteLLM proxy routing
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime

# Configuration
LLM_STUDIO_ENDPOINTS = {
    "ioz.zoi.local": {
        "url": "http://ioz.zoi.local:1234/v1",
        "models": ["qwen-14b"],
        "description": "RTX 5070 Ti - Fast coding model"
    },
    "astra.zoi.local": {
        "url": "http://astra.zoi.local:1234/v1",
        "models": ["qwen-30b", "nomic-embed-text"],
        "description": "RTX 5090 - Advanced reasoning and embeddings"
    }
}

LITELLM_ENDPOINT = "http://localhost:7010/v1"
LITELLM_KEY = "sk-wqn0xwq_vha4MVM2yzw"

# Model aliases to test
MODEL_ALIASES = {
    "zoi-coder": "Should route to ioz.zoi (Qwen 14B)",
    "zoi-planner": "Should route to astra.zoi (Qwen 30B)",
    "zoi-embed": "Should route to astra.zoi (embeddings)",
    "gpt-3.5-turbo": "Should route to zoi-coder",
    "gpt-4": "Should route to zoi-planner",
    "claude-3-haiku-20240307": "Should route to zoi-coder",
    "claude-3-opus-20240229": "Should route to zoi-planner"
}

def test_direct_endpoint(endpoint_name: str, endpoint_info: Dict[str, Any]) -> Dict[str, Any]:
    """Test a direct LLM Studio endpoint"""
    print(f"\n🔍 Testing {endpoint_name}")
    print(f"   URL: {endpoint_info['url']}")
    print(f"   Description: {endpoint_info['description']}")
    
    results = {
        "endpoint": endpoint_name,
        "url": endpoint_info["url"],
        "tests": []
    }
    
    # Test 1: Check endpoint health
    try:
        response = requests.get(f"{endpoint_info['url']}/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            print(f"   ✅ Endpoint is responding")
            print(f"   📋 Available models: {len(models.get('data', []))}")
            results["tests"].append({
                "test": "health_check",
                "status": "success",
                "models_count": len(models.get('data', []))
            })
        else:
            print(f"   ❌ Health check failed: HTTP {response.status_code}")
            results["tests"].append({
                "test": "health_check",
                "status": "failed",
                "error": f"HTTP {response.status_code}"
            })
    except Exception as e:
        print(f"   ❌ Connection error: {str(e)}")
        results["tests"].append({
            "test": "health_check",
            "status": "error",
            "error": str(e)
        })
        return results
    
    # Test 2: Test chat completion
    if "qwen" in endpoint_info["models"][0].lower():
        try:
            print(f"   🧪 Testing chat completion with {endpoint_info['models'][0]}")
            response = requests.post(
                f"{endpoint_info['url']}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": endpoint_info["models"][0],
                    "messages": [
                        {"role": "user", "content": "Reply with 'OK' and nothing else"}
                    ],
                    "max_tokens": 10,
                    "temperature": 0.1
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                print(f"   ✅ Chat completion successful")
                print(f"   📝 Response: {content[:50]}")
                results["tests"].append({
                    "test": "chat_completion",
                    "status": "success",
                    "response": content[:50]
                })
            else:
                print(f"   ❌ Chat completion failed: HTTP {response.status_code}")
                results["tests"].append({
                    "test": "chat_completion",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                })
        except Exception as e:
            print(f"   ❌ Chat error: {str(e)}")
            results["tests"].append({
                "test": "chat_completion",
                "status": "error",
                "error": str(e)
            })
    
    # Test 3: Test embeddings (only for astra.zoi)
    if "embed" in " ".join(endpoint_info["models"]).lower():
        try:
            print(f"   🧪 Testing embeddings with {endpoint_info['models'][-1]}")
            response = requests.post(
                f"{endpoint_info['url']}/embeddings",
                headers={"Content-Type": "application/json"},
                json={
                    "model": endpoint_info["models"][-1],
                    "input": "Test embedding generation"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                embedding_dim = len(data["data"][0]["embedding"])
                print(f"   ✅ Embedding generation successful")
                print(f"   📊 Embedding dimension: {embedding_dim}")
                results["tests"].append({
                    "test": "embedding",
                    "status": "success",
                    "dimension": embedding_dim
                })
            else:
                print(f"   ❌ Embedding failed: HTTP {response.status_code}")
                results["tests"].append({
                    "test": "embedding",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                })
        except Exception as e:
            print(f"   ❌ Embedding error: {str(e)}")
            results["tests"].append({
                "test": "embedding",
                "status": "error",
                "error": str(e)
            })
    
    return results

def test_litellm_proxy() -> Dict[str, Any]:
    """Test LiteLLM proxy with various model aliases"""
    print("\n🎯 Testing LiteLLM Proxy")
    print(f"   URL: {LITELLM_ENDPOINT}")
    
    results = {
        "endpoint": "litellm_proxy",
        "url": LITELLM_ENDPOINT,
        "tests": []
    }
    
    # Test proxy health
    try:
        response = requests.get(f"{LITELLM_ENDPOINT.replace('/v1', '')}/health", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ LiteLLM proxy is healthy")
            results["tests"].append({
                "test": "proxy_health",
                "status": "success"
            })
        else:
            print(f"   ⚠️  LiteLLM health check returned: {response.status_code}")
            results["tests"].append({
                "test": "proxy_health",
                "status": "warning",
                "code": response.status_code
            })
    except Exception as e:
        print(f"   ❌ LiteLLM health check error: {str(e)}")
        results["tests"].append({
            "test": "proxy_health",
            "status": "error",
            "error": str(e)
        })
    
    # Test model aliases
    for alias, description in MODEL_ALIASES.items():
        print(f"\n   🔄 Testing alias: {alias}")
        print(f"      Expected: {description}")
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {LITELLM_KEY}"
            }
            
            if "embed" in alias:
                # Test embedding model
                response = requests.post(
                    f"{LITELLM_ENDPOINT}/embeddings",
                    headers=headers,
                    json={
                        "model": alias,
                        "input": "Test embedding through proxy"
                    },
                    timeout=30
                )
            else:
                # Test chat model
                response = requests.post(
                    f"{LITELLM_ENDPOINT}/chat/completions",
                    headers=headers,
                    json={
                        "model": alias,
                        "messages": [
                            {"role": "user", "content": "Say 'Proxy working' and nothing else"}
                        ],
                        "max_tokens": 10,
                        "temperature": 0.1
                    },
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                if "embed" in alias:
                    print(f"      ✅ Embedding successful, dimension: {len(data['data'][0]['embedding'])}")
                else:
                    content = data["choices"][0]["message"]["content"]
                    print(f"      ✅ Response: {content[:30]}")
                
                results["tests"].append({
                    "test": f"alias_{alias}",
                    "status": "success",
                    "model_used": data.get("model", "unknown")
                })
            else:
                print(f"      ❌ Failed: HTTP {response.status_code}")
                error_msg = response.text[:100] if response.text else "No error message"
                print(f"      Error: {error_msg}")
                results["tests"].append({
                    "test": f"alias_{alias}",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                })
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            results["tests"].append({
                "test": f"alias_{alias}",
                "status": "error",
                "error": str(e)
            })
        
        # Small delay between tests
        time.sleep(1)
    
    return results

def test_performance() -> Dict[str, Any]:
    """Test response times and performance"""
    print("\n⚡ Performance Testing")
    
    results = {
        "test": "performance",
        "measurements": []
    }
    
    test_prompts = [
        {"prompt": "Hi", "tokens": 5, "complexity": "minimal"},
        {"prompt": "Write a Python hello world", "tokens": 50, "complexity": "simple"},
        {"prompt": "Explain quantum computing in simple terms", "tokens": 200, "complexity": "complex"}
    ]
    
    for model in ["zoi-coder", "zoi-planner"]:
        print(f"\n   📊 Testing {model} performance")
        
        for test in test_prompts:
            start_time = time.time()
            
            try:
                response = requests.post(
                    f"{LITELLM_ENDPOINT}/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {LITELLM_KEY}"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": test["prompt"]}],
                        "max_tokens": test["tokens"],
                        "temperature": 0.1,
                        "stream": False
                    },
                    timeout=60
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    tokens_used = data["usage"]["total_tokens"]
                    
                    print(f"      {test['complexity']:8} | Time: {response_time:.2f}s | Tokens: {tokens_used}")
                    
                    results["measurements"].append({
                        "model": model,
                        "complexity": test["complexity"],
                        "response_time": round(response_time, 2),
                        "tokens": tokens_used,
                        "status": "success"
                    })
                else:
                    print(f"      {test['complexity']:8} | Failed: HTTP {response.status_code}")
                    results["measurements"].append({
                        "model": model,
                        "complexity": test["complexity"],
                        "status": "failed",
                        "error": response.status_code
                    })
                    
            except Exception as e:
                print(f"      {test['complexity']:8} | Error: {str(e)[:50]}")
                results["measurements"].append({
                    "model": model,
                    "complexity": test["complexity"],
                    "status": "error",
                    "error": str(e)[:50]
                })
            
            time.sleep(1)
    
    return results

def generate_report(all_results: List[Dict[str, Any]]) -> None:
    """Generate comprehensive test report"""
    print("\n" + "=" * 80)
    print("LLM STUDIO ENDPOINTS TEST REPORT")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Direct endpoint results
    print("\n📡 DIRECT ENDPOINT TESTS")
    print("-" * 40)
    
    for result in all_results:
        if "endpoint" in result and result["endpoint"] in ["ioz.zoi", "astra.zoi"]:
            print(f"\n{result['endpoint']}:")
            success_count = sum(1 for t in result["tests"] if t["status"] == "success")
            total_count = len(result["tests"])
            print(f"  Status: {success_count}/{total_count} tests passed")
            
            for test in result["tests"]:
                status_icon = "✅" if test["status"] == "success" else "❌"
                print(f"  {status_icon} {test['test']}")
    
    # LiteLLM proxy results
    print("\n🔄 LITELLM PROXY TESTS")
    print("-" * 40)
    
    proxy_results = next((r for r in all_results if r.get("endpoint") == "litellm_proxy"), None)
    if proxy_results:
        success_count = sum(1 for t in proxy_results["tests"] if t["status"] == "success")
        total_count = len(proxy_results["tests"])
        print(f"Status: {success_count}/{total_count} tests passed")
        
        # Group by test type
        health_tests = [t for t in proxy_results["tests"] if "health" in t["test"]]
        alias_tests = [t for t in proxy_results["tests"] if "alias" in t["test"]]
        
        if health_tests:
            print("\nHealth Checks:")
            for test in health_tests:
                status_icon = "✅" if test["status"] == "success" else "⚠️" if test["status"] == "warning" else "❌"
                print(f"  {status_icon} {test['test']}")
        
        if alias_tests:
            print("\nModel Aliases:")
            for test in alias_tests:
                alias_name = test["test"].replace("alias_", "")
                status_icon = "✅" if test["status"] == "success" else "❌"
                model_used = test.get("model_used", "unknown")
                print(f"  {status_icon} {alias_name:20} → {model_used}")
    
    # Performance results
    print("\n⚡ PERFORMANCE METRICS")
    print("-" * 40)
    
    perf_results = next((r for r in all_results if r.get("test") == "performance"), None)
    if perf_results and perf_results["measurements"]:
        # Group by model
        models = {}
        for m in perf_results["measurements"]:
            if m["status"] == "success":
                model = m["model"]
                if model not in models:
                    models[model] = []
                models[model].append(m["response_time"])
        
        for model, times in models.items():
            avg_time = sum(times) / len(times)
            print(f"\n{model}:")
            print(f"  Average response time: {avg_time:.2f}s")
            print(f"  Min/Max: {min(times):.2f}s / {max(times):.2f}s")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_tests = sum(len(r.get("tests", [])) for r in all_results if "tests" in r)
    total_success = sum(
        sum(1 for t in r.get("tests", []) if t.get("status") == "success")
        for r in all_results if "tests" in r
    )
    
    success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests Run: {total_tests}")
    print(f"Successful Tests: {total_success}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n✅ LLM Studio endpoints are working excellently!")
    elif success_rate >= 70:
        print("\n⚠️  Most endpoints working, some issues detected")
    else:
        print("\n❌ Multiple failures detected, investigation needed")

def main():
    """Main test execution"""
    print("🚀 Starting LLM Studio Endpoints Test Suite")
    print("=" * 80)
    
    all_results = []
    
    # Test direct endpoints
    print("\n📡 TESTING DIRECT ENDPOINTS")
    print("-" * 40)
    
    for endpoint_name, endpoint_info in LLM_STUDIO_ENDPOINTS.items():
        result = test_direct_endpoint(endpoint_name, endpoint_info)
        all_results.append(result)
        time.sleep(2)
    
    # Test LiteLLM proxy
    print("\n🔄 TESTING LITELLM PROXY")
    print("-" * 40)
    
    proxy_result = test_litellm_proxy()
    all_results.append(proxy_result)
    
    # Test performance
    print("\n⚡ TESTING PERFORMANCE")
    print("-" * 40)
    
    perf_result = test_performance()
    all_results.append(perf_result)
    
    # Generate report
    generate_report(all_results)
    
    # Calculate exit code
    total_tests = sum(len(r.get("tests", [])) for r in all_results if "tests" in r)
    total_success = sum(
        sum(1 for t in r.get("tests", []) if t.get("status") == "success")
        for r in all_results if "tests" in r
    )
    
    success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
    
    sys.exit(0 if success_rate >= 70 else 1)

if __name__ == "__main__":
    main()