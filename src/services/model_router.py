"""
Advanced Model Routing Service for LiteLLM Integration
Implements intelligent routing logic based on request characteristics, model capabilities, and performance metrics
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict

import httpx

# Initialize logger
logger = logging.getLogger(__name__)


class ModelCapability(str, Enum):
    """Model capability types"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    VISION = "vision"
    EMBEDDING = "embedding"
    REASONING = "reasoning"
    FAST_RESPONSE = "fast_response"
    PRIVACY = "privacy"
    COST_EFFECTIVE = "cost_effective"


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class RouteStrategy(str, Enum):
    """Routing strategies"""
    CAPABILITY_BASED = "capability_based"
    PERFORMANCE_BASED = "performance_based"
    COST_BASED = "cost_based"
    LOAD_BALANCED = "load_balanced"
    FALLBACK_CHAIN = "fallback_chain"


@dataclass
class ModelMetrics:
    """Model performance metrics"""
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    cost_per_token: float = 0.0
    current_load: int = 0
    last_updated: datetime = None
    total_requests: int = 0
    failed_requests: int = 0


@dataclass
class RoutingDecision:
    """Routing decision with metadata"""
    selected_model: str
    strategy_used: RouteStrategy
    confidence: float
    fallback_models: List[str]
    reasoning: str
    estimated_cost: float
    estimated_time: float


class HTTPException(Exception):
    """Simple HTTP exception for model router"""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class ModelRouter:
    """Advanced model routing service with intelligent decision making"""
    
    def __init__(self, litellm_base_url: str = "http://localhost:4000", api_key: str = None):
        self.litellm_base_url = litellm_base_url.rstrip('/')
        self.api_key = api_key
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self.model_capabilities: Dict[str, List[ModelCapability]] = {}
        self.model_groups: Dict[str, List[str]] = {}
        self.routing_rules: List[Dict[str, Any]] = []
        self.fallback_chains: Dict[str, List[str]] = {}
        
        # Initialize default configurations
        self._initialize_model_capabilities()
        self._initialize_model_groups()
        self._initialize_routing_rules()
        self._initialize_fallback_chains()
    
    def _initialize_model_capabilities(self):
        """Initialize model capability mappings"""
        self.model_capabilities = {
            # Premium models - high capability across all tasks
            "gpt-4": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.VISION
            ],
            "claude-3-opus": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.REASONING
            ],
            "azure-gpt-4": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.REASONING,
                ModelCapability.VISION
            ],
            
            # Standard models - balanced capabilities
            "gpt-4-turbo": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.FAST_RESPONSE,
                ModelCapability.VISION
            ],
            "claude-3-sonnet": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.CODE_GENERATION,
                ModelCapability.FAST_RESPONSE
            ],
            "gpt-3.5-turbo": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FAST_RESPONSE,
                ModelCapability.COST_EFFECTIVE
            ],
            "command-r-plus": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FAST_RESPONSE
            ],
            
            # Fast models - optimized for speed
            "claude-3-haiku": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FAST_RESPONSE,
                ModelCapability.COST_EFFECTIVE
            ],
            "command-r": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FAST_RESPONSE,
                ModelCapability.COST_EFFECTIVE
            ],
            "gemini-pro": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.FAST_RESPONSE,
                ModelCapability.VISION
            ],
            
            # Vision models
            "gpt-4-vision": [
                ModelCapability.VISION,
                ModelCapability.TEXT_GENERATION
            ],
            "gemini-pro-vision": [
                ModelCapability.VISION,
                ModelCapability.TEXT_GENERATION
            ],
            
            # Local models - privacy focused
            "llama3.2-1b": [
                ModelCapability.TEXT_GENERATION,
                ModelCapability.PRIVACY,
                ModelCapability.COST_EFFECTIVE
            ],
            
            # Embedding models
            "text-embedding-3-large": [ModelCapability.EMBEDDING],
            "text-embedding-3-small": [ModelCapability.EMBEDDING, ModelCapability.COST_EFFECTIVE],
            "embed-english-v3": [ModelCapability.EMBEDDING, ModelCapability.COST_EFFECTIVE]
        }
    
    def _initialize_model_groups(self):
        """Initialize model group mappings from LiteLLM config"""
        self.model_groups = {
            "premium": ["gpt-4", "claude-3-opus", "azure-gpt-4"],
            "standard": ["gpt-4-turbo", "claude-3-sonnet", "gpt-3.5-turbo", "command-r-plus"],
            "fast": ["claude-3-haiku", "gpt-3.5-turbo", "command-r", "gemini-pro"],
            "vision": ["gpt-4-vision", "gpt-4-turbo", "claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "gemini-pro-vision"],
            "local": ["llama3.2-1b"],
            "code": ["gpt-4", "claude-3-opus"],
            "embeddings": ["text-embedding-3-large", "text-embedding-3-small", "embed-english-v3"],
            "budget": ["gpt-3.5-turbo", "claude-3-haiku", "command-r", "gemini-pro"]
        }
    
    def _initialize_routing_rules(self):
        """Initialize intelligent routing rules"""
        self.routing_rules = [
            # Privacy-sensitive requests
            {
                "condition": {"privacy_required": True},
                "action": {"prefer_models": ["llama3.2-1b"], "strategy": RouteStrategy.CAPABILITY_BASED},
                "priority": 10
            },
            
            # Vision/multimodal requests
            {
                "condition": {"has_images": True},
                "action": {"require_capability": ModelCapability.VISION, "strategy": RouteStrategy.CAPABILITY_BASED},
                "priority": 9
            },
            
            # Code generation requests
            {
                "condition": {"task_type": "code"},
                "action": {"prefer_models": ["gpt-4", "claude-3-opus"], "strategy": RouteStrategy.CAPABILITY_BASED},
                "priority": 8
            },
            
            # Embedding requests
            {
                "condition": {"task_type": "embedding"},
                "action": {"require_capability": ModelCapability.EMBEDDING, "strategy": RouteStrategy.COST_BASED},
                "priority": 8
            },
            
            # Fast response requirements
            {
                "condition": {"max_response_time": 5.0},
                "action": {"require_capability": ModelCapability.FAST_RESPONSE, "strategy": RouteStrategy.PERFORMANCE_BASED},
                "priority": 7
            },
            
            # Cost-sensitive requests
            {
                "condition": {"budget_priority": True},
                "action": {"require_capability": ModelCapability.COST_EFFECTIVE, "strategy": RouteStrategy.COST_BASED},
                "priority": 6
            },
            
            # Complex reasoning tasks
            {
                "condition": {"complexity": TaskComplexity.EXPERT},
                "action": {"prefer_models": ["gpt-4", "claude-3-opus"], "strategy": RouteStrategy.CAPABILITY_BASED},
                "priority": 5
            },
            
            # High load scenarios
            {
                "condition": {"load_balancing": True},
                "action": {"strategy": RouteStrategy.LOAD_BALANCED},
                "priority": 4
            },
            
            # Default fallback
            {
                "condition": {},
                "action": {"strategy": RouteStrategy.FALLBACK_CHAIN},
                "priority": 1
            }
        ]
    
    def _initialize_fallback_chains(self):
        """Initialize fallback chains for each model"""
        self.fallback_chains = {
            # Premium model fallbacks
            "gpt-4": ["gpt-4-turbo", "claude-3-opus", "azure-gpt-4"],
            "claude-3-opus": ["gpt-4", "claude-3-sonnet", "gpt-4-turbo"],
            "azure-gpt-4": ["gpt-4", "gpt-4-turbo", "claude-3-opus"],
            
            # Standard model fallbacks
            "gpt-4-turbo": ["gpt-4", "claude-3-sonnet", "claude-3-opus"],
            "claude-3-sonnet": ["claude-3-haiku", "gpt-3.5-turbo", "gpt-4-turbo"],
            "command-r-plus": ["command-r", "claude-3-sonnet", "gpt-3.5-turbo"],
            
            # Fast model fallbacks
            "claude-3-haiku": ["gpt-3.5-turbo", "command-r", "gemini-pro"],
            "gpt-3.5-turbo": ["claude-3-haiku", "command-r", "gemini-pro"],
            "command-r": ["gpt-3.5-turbo", "claude-3-haiku", "gemini-pro"],
            "gemini-pro": ["gpt-3.5-turbo", "claude-3-haiku", "command-r"],
            
            # Vision model fallbacks
            "gpt-4-vision": ["gpt-4-turbo", "claude-3-opus", "claude-3-sonnet"],
            "gemini-pro-vision": ["gpt-4-vision", "gpt-4-turbo", "claude-3-opus"],
            
            # Embedding model fallbacks
            "text-embedding-3-large": ["text-embedding-3-small", "embed-english-v3"],
            "text-embedding-3-small": ["embed-english-v3", "text-embedding-3-large"],
            "embed-english-v3": ["text-embedding-3-small", "text-embedding-3-large"],
            
            # Local model fallbacks (to external when local fails)
            "llama3.2-1b": ["gpt-3.5-turbo", "claude-3-haiku"]
        }
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from LiteLLM"""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.litellm_base_url}/v1/models",
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
                
        except Exception as e:
            logger.error(f"Failed to get available models: {e}")
            return []
    
    async def update_model_metrics(self, model: str, response_time: float, success: bool, cost: float = 0.0):
        """Update performance metrics for a model"""
        if model not in self.model_metrics:
            self.model_metrics[model] = ModelMetrics(last_updated=datetime.utcnow())
        
        metrics = self.model_metrics[model]
        metrics.total_requests += 1
        
        if success:
            # Update average response time with exponential moving average
            alpha = 0.1  # Smoothing factor
            if metrics.avg_response_time == 0:
                metrics.avg_response_time = response_time
            else:
                metrics.avg_response_time = (alpha * response_time) + ((1 - alpha) * metrics.avg_response_time)
        else:
            metrics.failed_requests += 1
        
        # Update success rate
        metrics.success_rate = (metrics.total_requests - metrics.failed_requests) / metrics.total_requests
        
        # Update cost (simple average for now)
        if cost > 0:
            if metrics.cost_per_token == 0:
                metrics.cost_per_token = cost
            else:
                metrics.cost_per_token = (metrics.cost_per_token + cost) / 2
        
        metrics.last_updated = datetime.utcnow()
    
    def _analyze_request_characteristics(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request to determine characteristics and requirements"""
        characteristics = {}
        
        # Extract message content for analysis
        messages = request_data.get("messages", [])
        content = ""
        has_images = False
        
        for message in messages:
            if isinstance(message.get("content"), str):
                content += message["content"] + " "
            elif isinstance(message.get("content"), list):
                for item in message["content"]:
                    if item.get("type") == "text":
                        content += item.get("text", "") + " "
                    elif item.get("type") == "image_url":
                        has_images = True
        
        # Analyze content characteristics
        content_lower = content.lower()
        
        # Detect task types
        if any(keyword in content_lower for keyword in ["code", "function", "class", "import", "def ", "var ", "const "]):
            characteristics["task_type"] = "code"
        elif has_images:
            characteristics["task_type"] = "vision"
        elif "embed" in content_lower or "embedding" in content_lower:
            characteristics["task_type"] = "embedding"
        else:
            characteristics["task_type"] = "text"
        
        # Detect complexity
        word_count = len(content.split())
        if word_count > 500:
            characteristics["complexity"] = TaskComplexity.EXPERT
        elif word_count > 200:
            characteristics["complexity"] = TaskComplexity.COMPLEX
        elif word_count > 50:
            characteristics["complexity"] = TaskComplexity.MODERATE
        else:
            characteristics["complexity"] = TaskComplexity.SIMPLE
        
        # Detect special requirements
        characteristics["has_images"] = has_images
        characteristics["privacy_required"] = any(keyword in content_lower for keyword in ["private", "confidential", "sensitive", "personal"])
        characteristics["budget_priority"] = "budget" in request_data.get("metadata", {})
        characteristics["max_response_time"] = request_data.get("max_response_time", 60.0)
        characteristics["load_balancing"] = request_data.get("load_balancing", False)
        
        return characteristics
    
    def _find_matching_rule(self, characteristics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the highest priority matching routing rule"""
        matching_rules = []
        
        for rule in self.routing_rules:
            condition = rule["condition"]
            matches = True
            
            for key, value in condition.items():
                if key not in characteristics or characteristics[key] != value:
                    matches = False
                    break
            
            if matches:
                matching_rules.append(rule)
        
        # Return highest priority rule
        if matching_rules:
            return max(matching_rules, key=lambda r: r["priority"])
        
        return None
    
    def _filter_models_by_capability(self, models: List[str], required_capability: ModelCapability) -> List[str]:
        """Filter models by required capability"""
        return [
            model for model in models
            if model in self.model_capabilities and required_capability in self.model_capabilities[model]
        ]
    
    def _rank_models_by_performance(self, models: List[str]) -> List[str]:
        """Rank models by performance metrics"""
        def performance_score(model: str) -> float:
            if model not in self.model_metrics:
                return 0.5  # Default score for unknown models
            
            metrics = self.model_metrics[model]
            # Combine success rate and response time (lower is better for time)
            time_score = max(0, 1 - (metrics.avg_response_time / 60.0))  # Normalize to 60s max
            return (metrics.success_rate * 0.7) + (time_score * 0.3)
        
        return sorted(models, key=performance_score, reverse=True)
    
    def _rank_models_by_cost(self, models: List[str]) -> List[str]:
        """Rank models by cost efficiency"""
        def cost_score(model: str) -> float:
            if model not in self.model_metrics:
                # Default cost ranking based on known model tiers
                if model in self.model_groups.get("budget", []):
                    return 0.9
                elif model in self.model_groups.get("fast", []):
                    return 0.7
                elif model in self.model_groups.get("standard", []):
                    return 0.5
                elif model in self.model_groups.get("premium", []):
                    return 0.3
                else:
                    return 0.5
            
            metrics = self.model_metrics[model]
            # Lower cost per token is better
            if metrics.cost_per_token == 0:
                return 0.5
            return max(0, 1 - metrics.cost_per_token)
        
        return sorted(models, key=cost_score, reverse=True)
    
    def _balance_load(self, models: List[str]) -> List[str]:
        """Balance load across available models"""
        def load_score(model: str) -> float:
            if model not in self.model_metrics:
                return 1.0  # Prefer unknown models (likely less loaded)
            
            metrics = self.model_metrics[model]
            # Prefer models with lower current load
            return max(0, 1 - (metrics.current_load / 100.0))  # Normalize to 100 max load
        
        return sorted(models, key=load_score, reverse=True)
    
    async def route_request(self, request_data: Dict[str, Any], available_models: Optional[List[str]] = None) -> RoutingDecision:
        """Main routing logic - determine the best model for a request"""
        try:
            # Get available models if not provided
            if available_models is None:
                available_models = await self.get_available_models()
            
            if not available_models:
                raise HTTPException(503, "No models available")
            
            # Analyze request characteristics
            characteristics = self._analyze_request_characteristics(request_data)
            
            # Find matching routing rule
            matching_rule = self._find_matching_rule(characteristics)
            if not matching_rule:
                # Fallback to default rule
                matching_rule = {"action": {"strategy": RouteStrategy.FALLBACK_CHAIN}}
            
            action = matching_rule["action"]
            strategy = action["strategy"]
            
            # Start with all available models
            candidate_models = available_models.copy()
            
            # Apply capability filtering
            if "require_capability" in action:
                candidate_models = self._filter_models_by_capability(
                    candidate_models, action["require_capability"]
                )
            
            # Apply preferred models
            if "prefer_models" in action:
                preferred = [m for m in action["prefer_models"] if m in candidate_models]
                if preferred:
                    candidate_models = preferred + [m for m in candidate_models if m not in preferred]
            
            # Apply strategy-specific ranking
            if strategy == RouteStrategy.PERFORMANCE_BASED:
                candidate_models = self._rank_models_by_performance(candidate_models)
            elif strategy == RouteStrategy.COST_BASED:
                candidate_models = self._rank_models_by_cost(candidate_models)
            elif strategy == RouteStrategy.LOAD_BALANCED:
                candidate_models = self._balance_load(candidate_models)
            elif strategy == RouteStrategy.FALLBACK_CHAIN:
                # Use predefined fallback chains
                requested_model = request_data.get("model", "gpt-3.5-turbo")
                if requested_model in self.fallback_chains:
                    fallback_chain = self.fallback_chains[requested_model]
                    candidate_models = [m for m in fallback_chain if m in available_models]
                    if requested_model in available_models:
                        candidate_models.insert(0, requested_model)
            
            if not candidate_models:
                raise HTTPException(400, "No suitable models found for request requirements")
            
            # Select the top model
            selected_model = candidate_models[0]
            fallback_models = candidate_models[1:5]  # Top 4 fallbacks
            
            # Calculate confidence based on model metrics
            confidence = 0.8  # Default confidence
            if selected_model in self.model_metrics:
                metrics = self.model_metrics[selected_model]
                confidence = metrics.success_rate * 0.7 + 0.3  # Boost base confidence
            
            # Estimate cost and time
            estimated_cost = 0.01  # Default estimate
            estimated_time = 5.0   # Default estimate
            
            if selected_model in self.model_metrics:
                metrics = self.model_metrics[selected_model]
                estimated_time = max(1.0, metrics.avg_response_time)
                estimated_cost = metrics.cost_per_token * len(str(request_data).split())
            
            # Generate reasoning
            reasoning = f"Selected {selected_model} using {strategy.value} strategy"
            if "require_capability" in action:
                reasoning += f" (requires {action['require_capability'].value})"
            
            return RoutingDecision(
                selected_model=selected_model,
                strategy_used=strategy,
                confidence=confidence,
                fallback_models=fallback_models,
                reasoning=reasoning,
                estimated_cost=estimated_cost,
                estimated_time=estimated_time
            )
            
        except Exception as e:
            logger.error(f"Routing decision failed: {e}")
            # Emergency fallback
            fallback_model = "gpt-3.5-turbo" if "gpt-3.5-turbo" in (available_models or []) else (available_models[0] if available_models else "gpt-3.5-turbo")
            
            return RoutingDecision(
                selected_model=fallback_model,
                strategy_used=RouteStrategy.FALLBACK_CHAIN,
                confidence=0.5,
                fallback_models=[],
                reasoning=f"Emergency fallback due to routing error: {str(e)}",
                estimated_cost=0.01,
                estimated_time=10.0
            )
    
    async def execute_with_fallback(self, request_data: Dict[str, Any], routing_decision: RoutingDecision) -> Dict[str, Any]:
        """Execute request with automatic fallback on failure"""
        models_to_try = [routing_decision.selected_model] + routing_decision.fallback_models
        last_error = None
        
        for model in models_to_try:
            try:
                start_time = time.time()
                
                # Update request with selected model
                request_data["model"] = model
                
                # Make request to LiteLLM
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"
                
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(
                        f"{self.litellm_base_url}/v1/chat/completions",
                        json=request_data,
                        headers=headers
                    )
                    
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        # Success - update metrics
                        result = response.json()
                        
                        # Calculate cost if usage info is available
                        cost = 0.0
                        if "usage" in result:
                            usage = result["usage"]
                            # Rough cost estimation (would need actual pricing data)
                            cost = (usage.get("total_tokens", 0) * 0.00001)
                        
                        await self.update_model_metrics(model, response_time, True, cost)
                        
                        # Add routing metadata to response
                        result["routing_metadata"] = {
                            "selected_model": model,
                            "strategy": routing_decision.strategy_used.value,
                            "confidence": routing_decision.confidence,
                            "response_time": response_time,
                            "fallback_used": model != routing_decision.selected_model
                        }
                        
                        return result
                    else:
                        # HTTP error - try next model
                        await self.update_model_metrics(model, response_time, False)
                        last_error = f"HTTP {response.status_code}: {response.text}"
                        logger.warning(f"Model {model} failed with {response.status_code}, trying fallback")
                        continue
                        
            except Exception as e:
                # Request error - try next model
                response_time = time.time() - start_time
                await self.update_model_metrics(model, response_time, False)
                last_error = str(e)
                logger.warning(f"Model {model} failed with error: {e}, trying fallback")
                continue
        
        # All models failed
        raise HTTPException(500, f"All models failed. Last error: {last_error}")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing and model performance statistics"""
        stats = {
            "total_models": len(self.model_metrics),
            "model_metrics": {},
            "model_groups": self.model_groups,
            "routing_rules_count": len(self.routing_rules),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        for model, metrics in self.model_metrics.items():
            stats["model_metrics"][model] = {
                "avg_response_time": round(metrics.avg_response_time, 2),
                "success_rate": round(metrics.success_rate, 3),
                "total_requests": metrics.total_requests,
                "failed_requests": metrics.failed_requests,
                "cost_per_token": metrics.cost_per_token,
                "current_load": metrics.current_load,
                "last_updated": metrics.last_updated.isoformat() if metrics.last_updated else None
            }
        
        return stats


# Global router instance
model_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get the global model router instance"""
    global model_router
    if model_router is None:
        api_key = "sk-change-me-to-random-string"  # This should come from config
        model_router = ModelRouter(api_key=api_key)
    return model_router
