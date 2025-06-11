"""
LiteLLM Client for Production RAG System

This module provides a comprehensive client for interacting with the LiteLLM proxy,
supporting multiple providers, model routing, and advanced features like cost tracking,
caching, and error handling.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

import aiohttp
import openai
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ModelTier(str, Enum):
    """Model performance and cost tiers"""
    PREMIUM = "premium"
    STANDARD = "standard"
    FAST = "fast"
    LOCAL = "local"
    BUDGET = "budget"


class RequestType(str, Enum):
    """Types of requests for model routing"""
    CODE = "code"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    CHAT = "chat"
    VISION = "vision"
    EMBEDDING = "embedding"


@dataclass
class ModelInfo:
    """Information about a model"""
    name: str
    provider: str
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_streaming: bool = True
    max_tokens: int = 4096
    input_cost_per_token: float = 0.0
    output_cost_per_token: float = 0.0


class ChatMessage(BaseModel):
    """Chat message structure"""
    role: str = Field(..., description="Message role: system, user, assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name for the message")


class ChatRequest(BaseModel):
    """Chat completion request"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    model_tier: Optional[ModelTier] = None
    request_type: Optional[RequestType] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, str]]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingRequest(BaseModel):
    """Embedding request"""
    input: Union[str, List[str]]
    model: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LiteLLMResponse(BaseModel):
    """Standard response from LiteLLM"""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, Any]] = None
    cost: Optional[float] = None
    provider: Optional[str] = None


class LiteLLMClient:
    """
    Comprehensive client for LiteLLM proxy with advanced features
    """
    
    def __init__(
        self,
        base_url: str = "http://zoi.local:4000",
        api_key: Optional[str] = None,
        timeout: int = 600,
        max_retries: int = 3,
        enable_caching: bool = True,
        enable_cost_tracking: bool = True
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.enable_caching = enable_caching
        self.enable_cost_tracking = enable_cost_tracking
        
        # Initialize OpenAI client for LiteLLM proxy
        self.client = AsyncOpenAI(
            base_url=f"{self.base_url}/v1",
            api_key=api_key or "sk-1234",  # LiteLLM default
            timeout=timeout
        )
        
        # Cache for model information and responses
        self._model_cache: Dict[str, ModelInfo] = {}
        self._response_cache: Dict[str, Any] = {}
        
        # Cost tracking
        self._total_cost = 0.0
        self._request_costs: List[Dict[str, Any]] = []
        
        # Performance metrics
        self._request_count = 0
        self._total_latency = 0.0
        self._error_count = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def close(self):
        """Close the client and cleanup resources"""
        await self.client.close()
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models from LiteLLM proxy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v1/models",
                    headers=self._get_headers(),
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = []
                        for model_data in data.get("data", []):
                            model_info = ModelInfo(
                                name=model_data["id"],
                                provider=model_data.get("owned_by", "unknown"),
                                supports_vision=model_data.get("supports_vision", False),
                                supports_function_calling=model_data.get("supports_function_calling", False),
                                max_tokens=model_data.get("max_tokens", 4096)
                            )
                            models.append(model_info)
                            self._model_cache[model_info.name] = model_info
                        return models
                    else:
                        logger.error(f"Failed to get models: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _select_model(
        self,
        model: Optional[str] = None,
        model_tier: Optional[ModelTier] = None,
        request_type: Optional[RequestType] = None,
        requires_vision: bool = False,
        requires_function_calling: bool = False
    ) -> str:
        """
        Select the best model based on requirements and preferences
        """
        if model:
            return model
        
        # Model selection based on tier and type
        if model_tier == ModelTier.PREMIUM:
            candidates = ["gpt-4", "claude-3-opus", "azure-gpt-4"]
        elif model_tier == ModelTier.STANDARD:
            candidates = ["gpt-4-turbo", "claude-3-sonnet", "gpt-3.5-turbo", "command-r-plus"]
        elif model_tier == ModelTier.FAST:
            candidates = ["claude-3-haiku", "gpt-3.5-turbo", "command-r", "gemini-pro"]
        elif model_tier == ModelTier.LOCAL:
            candidates = ["mistral-7b", "llama2-7b", "llama3-8b"]
        elif model_tier == ModelTier.BUDGET:
            candidates = ["gpt-3.5-turbo", "claude-3-haiku", "command-r", "gemini-pro"]
        else:
            # Default selection based on request type
            if request_type == RequestType.CODE:
                candidates = ["codellama-7b", "gpt-4", "claude-3-opus"]
            elif request_type == RequestType.CREATIVE:
                candidates = ["claude-3-opus", "gpt-4", "claude-3-sonnet"]
            elif request_type == RequestType.ANALYSIS:
                candidates = ["gpt-4", "claude-3-opus", "gpt-4-turbo"]
            elif request_type == RequestType.CHAT:
                candidates = ["gpt-3.5-turbo", "claude-3-haiku", "command-r"]
            elif request_type == RequestType.VISION:
                candidates = ["gpt-4-vision", "claude-3-opus", "claude-3-sonnet"]
            elif request_type == RequestType.EMBEDDING:
                candidates = ["text-embedding-3-large", "text-embedding-3-small"]
            else:
                candidates = ["gpt-3.5-turbo", "claude-3-haiku"]
        
        # Filter based on requirements
        if requires_vision:
            vision_models = ["gpt-4-vision", "gpt-4-turbo", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "gemini-pro-vision"]
            candidates = [m for m in candidates if m in vision_models]
        
        if requires_function_calling:
            function_models = ["gpt-4", "gpt-4-turbo", "gpt-4-vision", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
            candidates = [m for m in candidates if m in function_models]
        
        # Return first available candidate
        return candidates[0] if candidates else "gpt-3.5-turbo"
    
    async def chat_completion(
        self,
        request: ChatRequest
    ) -> LiteLLMResponse:
        """
        Create a chat completion
        """
        start_time = time.time()
        
        try:
            # Select model
            model = self._select_model(
                model=request.model,
                model_tier=request.model_tier,
                request_type=request.request_type,
                requires_vision=any("image" in str(msg.content) for msg in request.messages),
                requires_function_calling=bool(request.functions)
            )
            
            # Prepare request
            messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": request.temperature,
                "stream": request.stream
            }
            
            if request.max_tokens:
                kwargs["max_tokens"] = request.max_tokens
            
            if request.functions:
                kwargs["functions"] = request.functions
                if request.function_call:
                    kwargs["function_call"] = request.function_call
            
            # Add metadata
            if request.user_id:
                kwargs["user"] = request.user_id
            
            # Make request
            if request.stream:
                return await self._stream_chat_completion(**kwargs)
            else:
                response = await self.client.chat.completions.create(**kwargs)
                
                # Track metrics
                latency = time.time() - start_time
                self._update_metrics(latency, success=True)
                
                # Track cost if enabled
                cost = 0.0
                if self.enable_cost_tracking and hasattr(response, 'usage'):
                    cost = self._calculate_cost(model, response.usage)
                    self._track_cost(cost, model, request.user_id)
                
                return LiteLLMResponse(
                    id=response.id,
                    object=response.object,
                    created=response.created,
                    model=response.model,
                    choices=[choice.model_dump() for choice in response.choices],
                    usage=response.usage.model_dump() if response.usage else None,
                    cost=cost,
                    provider=self._get_provider_from_model(model)
                )
                
        except Exception as e:
            self._update_metrics(time.time() - start_time, success=False)
            logger.error(f"Chat completion error: {e}")
            raise
    
    async def _stream_chat_completion(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle streaming chat completion"""
        try:
            stream = await self.client.chat.completions.create(**kwargs)
            async for chunk in stream:
                yield chunk.model_dump()
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise
    
    async def create_embedding(
        self,
        request: EmbeddingRequest
    ) -> Dict[str, Any]:
        """
        Create embeddings
        """
        start_time = time.time()
        
        try:
            # Select embedding model
            model = self._select_model(
                model=request.model,
                request_type=RequestType.EMBEDDING
            )
            
            # Make request
            response = await self.client.embeddings.create(
                model=model,
                input=request.input,
                user=request.user_id
            )
            
            # Track metrics
            latency = time.time() - start_time
            self._update_metrics(latency, success=True)
            
            # Track cost if enabled
            cost = 0.0
            if self.enable_cost_tracking and hasattr(response, 'usage'):
                cost = self._calculate_cost(model, response.usage)
                self._track_cost(cost, model, request.user_id)
            
            return {
                "object": response.object,
                "data": [item.model_dump() for item in response.data],
                "model": response.model,
                "usage": response.usage.model_dump() if response.usage else None,
                "cost": cost,
                "provider": self._get_provider_from_model(model)
            }
            
        except Exception as e:
            self._update_metrics(time.time() - start_time, success=False)
            logger.error(f"Embedding error: {e}")
            raise
    
    def _calculate_cost(self, model: str, usage: Dict[str, Any]) -> float:
        """Calculate request cost based on usage"""
        if model not in self._model_cache:
            return 0.0
        
        model_info = self._model_cache[model]
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        cost = (
            input_tokens * model_info.input_cost_per_token +
            output_tokens * model_info.output_cost_per_token
        )
        
        return cost
    
    def _track_cost(self, cost: float, model: str, user_id: Optional[str] = None):
        """Track cost for monitoring and billing"""
        self._total_cost += cost
        self._request_costs.append({
            "timestamp": time.time(),
            "cost": cost,
            "model": model,
            "user_id": user_id
        })
        
        # Keep only recent costs (last 1000 requests)
        if len(self._request_costs) > 1000:
            self._request_costs = self._request_costs[-1000:]
    
    def _get_provider_from_model(self, model: str) -> str:
        """Get provider name from model"""
        if model.startswith("gpt-") or model.startswith("text-embedding"):
            return "openai"
        elif model.startswith("claude-"):
            return "anthropic"
        elif model.startswith("gemini-"):
            return "google"
        elif model.startswith("command-"):
            return "cohere"
        elif model in ["mistral-7b", "llama2-7b", "llama3-8b", "codellama-7b", "nomic-embed"]:
            return "ollama"
        elif model.startswith("azure-"):
            return "azure"
        else:
            return "unknown"
    
    def _update_metrics(self, latency: float, success: bool):
        """Update performance metrics"""
        self._request_count += 1
        self._total_latency += latency
        if not success:
            self._error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance and cost metrics"""
        avg_latency = self._total_latency / max(self._request_count, 1)
        error_rate = self._error_count / max(self._request_count, 1)
        
        return {
            "total_requests": self._request_count,
            "total_cost": self._total_cost,
            "average_latency": avg_latency,
            "error_rate": error_rate,
            "recent_costs": self._request_costs[-10:] if self._request_costs else []
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check LiteLLM proxy health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"status": "healthy", "details": data}
                    else:
                        return {"status": "unhealthy", "status_code": response.status}
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Convenience functions for common use cases
async def quick_chat(
    message: str,
    model_tier: ModelTier = ModelTier.STANDARD,
    temperature: float = 0.7,
    client: Optional[LiteLLMClient] = None
) -> str:
    """Quick chat completion"""
    if client is None:
        client = LiteLLMClient()
    
    request = ChatRequest(
        messages=[ChatMessage(role="user", content=message)],
        model_tier=model_tier,
        temperature=temperature
    )
    
    response = await client.chat_completion(request)
    return response.choices[0]["message"]["content"]


async def quick_embedding(
    text: str,
    client: Optional[LiteLLMClient] = None
) -> List[float]:
    """Quick embedding generation"""
    if client is None:
        client = LiteLLMClient()
    
    request = EmbeddingRequest(input=text)
    response = await client.create_embedding(request)
    return response["data"][0]["embedding"]


# Example usage
if __name__ == "__main__":
    async def main():
        async with LiteLLMClient() as client:
            # Get available models
            models = await client.get_available_models()
            print(f"Available models: {[m.name for m in models]}")
            
            # Quick chat
            response = await quick_chat("Hello, how are you?", client=client)
            print(f"Response: {response}")
            
            # Get metrics
            metrics = client.get_metrics()
            print(f"Metrics: {metrics}")
    
    asyncio.run(main())
