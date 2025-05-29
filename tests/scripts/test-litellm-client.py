#!/usr/bin/env python3
"""
Test script for LiteLLM Client integration

This script tests the LiteLLM client functionality including:
- Connection to LiteLLM proxy
- Model availability and selection
- Chat completions
- Embeddings
- Cost tracking and metrics
- Error handling
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm.litellm_client import (
    LiteLLMClient,
    ChatRequest,
    ChatMessage,
    EmbeddingRequest,
    ModelTier,
    RequestType,
    quick_chat,
    quick_embedding
)


class LiteLLMTester:
    """Test suite for LiteLLM client"""
    
    def __init__(self, base_url: str = "http://localhost:4000"):
        self.base_url = base_url
        self.results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": []
        }
    
    def _log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.results["tests_run"] += 1
        if success:
            self.results["tests_passed"] += 1
            print(f"✅ {test_name}: PASSED")
            if details:
                print(f"   {details}")
        else:
            self.results["tests_failed"] += 1
            self.results["failures"].append({"test": test_name, "details": details})
            print(f"❌ {test_name}: FAILED")
            if details:
                print(f"   {details}")
        print()
    
    async def test_client_initialization(self):
        """Test client initialization"""
        try:
            client = LiteLLMClient(base_url=self.base_url)
            self._log_result(
                "Client Initialization",
                True,
                f"Client initialized with base_url: {self.base_url}"
            )
            await client.close()
            return True
        except Exception as e:
            self._log_result(
                "Client Initialization",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_health_check(self):
        """Test LiteLLM proxy health check"""
        try:
            async with LiteLLMClient(base_url=self.base_url) as client:
                health = await client.health_check()
                success = health.get("status") == "healthy"
                self._log_result(
                    "Health Check",
                    success,
                    f"Status: {health.get('status')}, Details: {health.get('details', {})}"
                )
                return success
        except Exception as e:
            self._log_result(
                "Health Check",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_get_available_models(self):
        """Test getting available models"""
        try:
            async with LiteLLMClient(base_url=self.base_url) as client:
                models = await client.get_available_models()
                success = len(models) > 0
                model_names = [m.name for m in models[:5]]  # Show first 5
                self._log_result(
                    "Get Available Models",
                    success,
                    f"Found {len(models)} models. First 5: {model_names}"
                )
                return success
        except Exception as e:
            self._log_result(
                "Get Available Models",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_chat_completion_basic(self):
        """Test basic chat completion"""
        try:
            async with LiteLLMClient(base_url=self.base_url) as client:
                request = ChatRequest(
                    messages=[ChatMessage(role="user", content="Hello, respond with just 'Hi there!'")],
                    model_tier=ModelTier.FAST,
                    temperature=0.1,
                    max_tokens=10
                )
                
                response = await client.chat_completion(request)
                success = response.choices and len(response.choices) > 0
                content = response.choices[0]["message"]["content"] if success else "No content"
                
                self._log_result(
                    "Basic Chat Completion",
                    success,
                    f"Model: {response.model}, Response: {content[:50]}..."
                )
                return success
        except Exception as e:
            self._log_result(
                "Basic Chat Completion",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_chat_completion_with_model_selection(self):
        """Test chat completion with different model selection strategies"""
        try:
            async with LiteLLMClient(base_url=self.base_url) as client:
                # Test different tiers and request types
                test_cases = [
                    (ModelTier.FAST, RequestType.CHAT, "Quick response test"),
                    (ModelTier.STANDARD, RequestType.ANALYSIS, "Analyze this: 2+2=?"),
                    (ModelTier.PREMIUM, RequestType.CREATIVE, "Write a haiku about coding")
                ]
                
                all_success = True
                results = []
                
                for tier, req_type, message in test_cases:
                    try:
                        request = ChatRequest(
                            messages=[ChatMessage(role="user", content=message)],
                            model_tier=tier,
                            request_type=req_type,
                            temperature=0.3,
                            max_tokens=50
                        )
                        
                        response = await client.chat_completion(request)
                        success = response.choices and len(response.choices) > 0
                        if success:
                            results.append(f"{tier.value}/{req_type.value}: {response.model}")
                        else:
                            all_success = False
                            results.append(f"{tier.value}/{req_type.value}: FAILED")
                    except Exception as e:
                        all_success = False
                        results.append(f"{tier.value}/{req_type.value}: ERROR - {str(e)}")
                
                self._log_result(
                    "Model Selection Strategies",
                    all_success,
                    f"Results: {', '.join(results)}"
                )
                return all_success
        except Exception as e:
            self._log_result(
                "Model Selection Strategies",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_embedding_generation(self):
        """Test embedding generation"""
        try:
            async with LiteLLMClient(base_url=self.base_url) as client:
                request = EmbeddingRequest(
                    input="This is a test sentence for embedding generation.",
                    user_id="test-user"
                )
                
                response = await client.create_embedding(request)
                success = (
                    response.get("data") and 
                    len(response["data"]) > 0 and
                    "embedding" in response["data"][0]
                )
                
                embedding_length = len(response["data"][0]["embedding"]) if success else 0
                
                self._log_result(
                    "Embedding Generation",
                    success,
                    f"Model: {response.get('model')}, Embedding length: {embedding_length}"
                )
                return success
        except Exception as e:
            self._log_result(
                "Embedding Generation",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_quick_functions(self):
        """Test convenience quick functions"""
        try:
            async with LiteLLMClient(base_url=self.base_url) as client:
                # Test quick chat
                chat_response = await quick_chat(
                    "Say 'Quick chat works!'",
                    model_tier=ModelTier.FAST,
                    client=client
                )
                chat_success = "works" in chat_response.lower()
                
                # Test quick embedding
                embedding = await quick_embedding(
                    "Test embedding text",
                    client=client
                )
                embedding_success = isinstance(embedding, list) and len(embedding) > 0
                
                overall_success = chat_success and embedding_success
                
                self._log_result(
                    "Quick Functions",
                    overall_success,
                    f"Chat: {'✓' if chat_success else '✗'}, Embedding: {'✓' if embedding_success else '✗'}"
                )
                return overall_success
        except Exception as e:
            self._log_result(
                "Quick Functions",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_cost_tracking(self):
        """Test cost tracking functionality"""
        try:
            async with LiteLLMClient(base_url=self.base_url, enable_cost_tracking=True) as client:
                # Make a few requests
                for i in range(3):
                    request = ChatRequest(
                        messages=[ChatMessage(role="user", content=f"Test message {i+1}")],
                        model_tier=ModelTier.FAST,
                        max_tokens=10,
                        user_id=f"test-user-{i+1}"
                    )
                    await client.chat_completion(request)
                
                # Check metrics
                metrics = client.get_metrics()
                success = (
                    metrics["total_requests"] >= 3 and
                    metrics["total_cost"] >= 0 and
                    metrics["average_latency"] > 0
                )
                
                self._log_result(
                    "Cost Tracking",
                    success,
                    f"Requests: {metrics['total_requests']}, Cost: ${metrics['total_cost']:.6f}, Avg Latency: {metrics['average_latency']:.3f}s"
                )
                return success
        except Exception as e:
            self._log_result(
                "Cost Tracking",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_error_handling(self):
        """Test error handling with invalid requests"""
        try:
            async with LiteLLMClient(base_url=self.base_url) as client:
                # Test with invalid model
                try:
                    request = ChatRequest(
                        messages=[ChatMessage(role="user", content="Test")],
                        model="invalid-model-name-12345"
                    )
                    await client.chat_completion(request)
                    error_handled = False
                except Exception:
                    error_handled = True
                
                # Test with empty messages
                try:
                    request = ChatRequest(messages=[])
                    await client.chat_completion(request)
                    empty_handled = False
                except Exception:
                    empty_handled = True
                
                success = error_handled and empty_handled
                
                self._log_result(
                    "Error Handling",
                    success,
                    f"Invalid model: {'✓' if error_handled else '✗'}, Empty messages: {'✓' if empty_handled else '✗'}"
                )
                return success
        except Exception as e:
            self._log_result(
                "Error Handling",
                False,
                f"Unexpected error: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting LiteLLM Client Test Suite")
        print("=" * 50)
        print()
        
        # List of test methods
        tests = [
            self.test_client_initialization,
            self.test_health_check,
            self.test_get_available_models,
            self.test_chat_completion_basic,
            self.test_chat_completion_with_model_selection,
            self.test_embedding_generation,
            self.test_quick_functions,
            self.test_cost_tracking,
            self.test_error_handling
        ]
        
        # Run tests
        for test in tests:
            await test()
        
        # Print summary
        print("=" * 50)
        print("📊 Test Summary")
        print(f"Total Tests: {self.results['tests_run']}")
        print(f"Passed: {self.results['tests_passed']} ✅")
        print(f"Failed: {self.results['tests_failed']} ❌")
        print(f"Success Rate: {(self.results['tests_passed']/max(self.results['tests_run'], 1)*100):.1f}%")
        
        if self.results['failures']:
            print("\n❌ Failed Tests:")
            for failure in self.results['failures']:
                print(f"  - {failure['test']}: {failure['details']}")
        
        return self.results['tests_failed'] == 0


async def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LiteLLM Client")
    parser.add_argument(
        "--url",
        default="http://localhost:4000",
        help="LiteLLM proxy URL (default: http://localhost:4000)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Check if LiteLLM service is running
    print(f"🔍 Testing LiteLLM client with proxy at: {args.url}")
    print()
    
    tester = LiteLLMTester(base_url=args.url)
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! LiteLLM client is working correctly.")
        return 0
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
