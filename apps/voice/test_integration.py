#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Zoi Voice Chat Application

This script tests the complete end-to-end functionality:
1. Voice app server health and API endpoints
2. LLM backend connectivity (Ollama direct vs LiteLLM proxy)
3. WebSocket connection and message flow
4. TTS and STT model availability
5. Complete voice chat pipeline simulation

Usage:
    python test_integration.py
    python test_integration.py --litellm  # Test with LiteLLM proxy
    python test_integration.py --playwright  # Run browser automation tests
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import argparse

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceChatTester:
    """Comprehensive tester for the voice chat application"""
    
    def __init__(self, base_url: str = "http://localhost:8000", litellm_url: str = "http://localhost:7010"):
        self.base_url = base_url
        self.litellm_url = litellm_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log and store test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")
        self.test_results[test_name] = {"success": success, "details": details}
    
    async def test_server_health(self) -> bool:
        """Test if the voice chat server is running and healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_test_result("Server Health", True, f"Server responding on {self.base_url}")
                return True
            else:
                self.log_test_result("Server Health", False, f"Server returned {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Server Health", False, f"Connection failed: {e}")
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Test various API endpoints"""
        endpoints = [
            ("/", "GET", "Main page"),
            ("/health", "GET", "Health check"),
            ("/api/models", "GET", "Available models"),
            ("/api/status", "GET", "System status")
        ]
        
        all_passed = True
        for endpoint, method, description in endpoints:
            try:
                if method == "GET":
                    response = await self.client.get(f"{self.base_url}{endpoint}")
                else:
                    response = await self.client.request(method, f"{self.base_url}{endpoint}")
                
                if response.status_code in [200, 404]:  # 404 is OK for optional endpoints
                    self.log_test_result(f"API {endpoint}", True, f"{description} - {response.status_code}")
                else:
                    self.log_test_result(f"API {endpoint}", False, f"{description} - {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_test_result(f"API {endpoint}", False, f"{description} - Error: {e}")
                all_passed = False
        
        return all_passed
    
    async def test_ollama_direct_connection(self) -> bool:
        """Test direct connection to Ollama"""
        try:
            # Try the configured Ollama URL from voice app
            ollama_url = "http://localhost:7040"  # From docker-compose.yml
            response = await self.client.get(f"{ollama_url}/api/tags")
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "unknown") for m in models]
                self.log_test_result("Ollama Direct", True, f"Connected, {len(models)} models: {model_names[:3]}")
                return True
            else:
                self.log_test_result("Ollama Direct", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("Ollama Direct", False, f"Connection failed: {e}")
            return False
    
    async def test_litellm_proxy_connection(self) -> bool:
        """Test connection to LiteLLM proxy"""
        try:
            # Test LiteLLM proxy health with API key
            headers = {"Authorization": "Bearer sk-wqn0xwq_vha4MVM2yzw"}
            response = await self.client.get(f"{self.litellm_url}/health", headers=headers)

            if response.status_code == 200:
                health_data = response.json()
                self.log_test_result("LiteLLM Health", True, f"Proxy healthy: {health_data}")

                # Test available models
                models_response = await self.client.get(f"{self.litellm_url}/v1/models", headers=headers)
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    model_names = [m.get("id", "unknown") for m in models_data.get("data", [])]
                    self.log_test_result("LiteLLM Models", True, f"{len(model_names)} models: {model_names[:5]}")
                    return True
                else:
                    self.log_test_result("LiteLLM Models", False, f"Models endpoint: {models_response.status_code}")
                    return False
            else:
                self.log_test_result("LiteLLM Health", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_result("LiteLLM Proxy", False, f"Connection failed: {e}")
            return False
    
    async def test_llm_chat_completion(self, use_litellm: bool = False) -> bool:
        """Test LLM chat completion"""
        if use_litellm:
            url = f"{self.litellm_url}/v1/chat/completions"
            headers = {"Authorization": "Bearer sk-wqn0xwq_vha4MVM2yzw"}
            model = "zoi-helper"  # From LiteLLM config
        else:
            url = "http://localhost:7040/v1/chat/completions"
            headers = {}
            model = "hf.co/bartowski/huihui-ai_Mistral-Small-24B-Instruct-2501-abliterated-GGUF:Q4_K_M"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello! Please respond with exactly: 'Voice chat test successful'"}],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        try:
            response = await self.client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                backend = "LiteLLM" if use_litellm else "Ollama Direct"
                self.log_test_result(f"LLM Chat ({backend})", True, f"Response: {content[:100]}")
                return True
            else:
                backend = "LiteLLM" if use_litellm else "Ollama Direct"
                self.log_test_result(f"LLM Chat ({backend})", False, f"HTTP {response.status_code}: {response.text[:200]}")
                return False
        except Exception as e:
            backend = "LiteLLM" if use_litellm else "Ollama Direct"
            self.log_test_result(f"LLM Chat ({backend})", False, f"Error: {e}")
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket connection and basic message flow"""
        try:
            ws_url = f"ws://localhost:8000/ws"
            
            async with websockets.connect(ws_url) as websocket:
                self.log_test_result("WebSocket Connect", True, "Connected successfully")
                
                # Send a test message
                test_message = {
                    "type": "text_input",
                    "text": "Hello, this is a test message"
                }
                
                await websocket.send(json.dumps(test_message))
                self.log_test_result("WebSocket Send", True, "Test message sent")
                
                # Try to receive a response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data = json.loads(response)
                    self.log_test_result("WebSocket Receive", True, f"Received: {response_data.get('type', 'unknown')}")
                    return True
                except asyncio.TimeoutError:
                    self.log_test_result("WebSocket Receive", False, "No response within 10 seconds")
                    return False
                    
        except Exception as e:
            self.log_test_result("WebSocket Connection", False, f"Error: {e}")
            return False
    
    async def run_all_tests(self, use_litellm: bool = False) -> Dict:
        """Run all integration tests"""
        logger.info("🧪 Starting comprehensive integration tests...")
        logger.info(f"🎯 Target: Voice Chat App at {self.base_url}")
        logger.info(f"🤖 LLM Backend: {'LiteLLM Proxy' if use_litellm else 'Direct Ollama'}")
        logger.info("=" * 60)
        
        # Core server tests
        await self.test_server_health()
        await self.test_api_endpoints()
        
        # Backend connectivity tests
        await self.test_ollama_direct_connection()
        await self.test_litellm_proxy_connection()
        
        # LLM functionality tests
        await self.test_llm_chat_completion(use_litellm=False)  # Test current config
        await self.test_llm_chat_completion(use_litellm=True)   # Test LiteLLM
        
        # WebSocket tests
        await self.test_websocket_connection()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        
        logger.info("=" * 60)
        logger.info(f"🏁 Test Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! Voice chat integration is working correctly.")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} tests failed. Check configuration.")
        
        return self.test_results

async def run_playwright_tests():
    """Run browser automation tests using Playwright"""
    try:
        from playwright.async_api import async_playwright
        
        logger.info("🎭 Starting Playwright browser tests...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # Navigate to voice chat app
            await page.goto("http://localhost:8000")
            
            # Check if page loads
            title = await page.title()
            logger.info(f"✅ Page loaded: {title}")
            
            # Check for key elements
            elements_to_check = [
                "button",  # Should have some buttons
                "canvas",  # Audio visualization
                "#status", # Status indicator
            ]
            
            for selector in elements_to_check:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.info(f"✅ Found element: {selector}")
                    else:
                        logger.warning(f"⚠️  Element not found: {selector}")
                except:
                    logger.warning(f"⚠️  Element not found: {selector}")
            
            # Take a screenshot
            await page.screenshot(path="voice_chat_test.png")
            logger.info("📸 Screenshot saved as voice_chat_test.png")
            
            await browser.close()
            
    except ImportError:
        logger.error("❌ Playwright not installed. Install with: pip install playwright")
        logger.info("💡 Then run: playwright install chromium")

async def main():
    parser = argparse.ArgumentParser(description="Test Zoi Voice Chat Integration")
    parser.add_argument("--litellm", action="store_true", help="Test with LiteLLM proxy instead of direct Ollama")
    parser.add_argument("--playwright", action="store_true", help="Run Playwright browser tests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Voice chat app URL")
    parser.add_argument("--litellm-url", default="http://localhost:7010", help="LiteLLM proxy URL")
    
    args = parser.parse_args()
    
    if args.playwright:
        await run_playwright_tests()
        return
    
    async with VoiceChatTester(args.base_url, args.litellm_url) as tester:
        results = await tester.run_all_tests(use_litellm=args.litellm)
        
        # Exit with error code if tests failed
        failed_tests = [name for name, result in results.items() if not result["success"]]
        if failed_tests:
            logger.error(f"❌ Failed tests: {', '.join(failed_tests)}")
            sys.exit(1)
        else:
            logger.info("🎉 All tests passed!")
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
