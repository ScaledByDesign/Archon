"""
LiteLLM wrapper with Langfuse integration
Provides enhanced LLM observability with automatic tracing
"""

import os
import logging
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

import litellm
from litellm import completion, acompletion, embedding
from litellm.utils import ModelResponse

from .langfuse_client import langfuse_tracer

logger = logging.getLogger(__name__)


class TracedLiteLLM:
    """
    LiteLLM wrapper with integrated Langfuse tracing
    Automatically records all LLM interactions with detailed metrics
    """
    
    def __init__(self, trace_all: bool = True):
        """
        Initialize the traced LiteLLM wrapper
        
        Args:
            trace_all: Whether to trace all LLM calls automatically
        """
        self.trace_all = trace_all
        logger.info("Traced LiteLLM wrapper initialized")
        
        # Initialize LiteLLM with callbacks if tracing is enabled
        if self.trace_all and langfuse_tracer.is_enabled:
            # LiteLLM already configured with Langfuse in config.yaml
            logger.info("LiteLLM configured with Langfuse callback")
    
    def _extract_token_metrics(self, response: ModelResponse) -> Dict[str, int]:
        """Extract token usage metrics from LiteLLM response"""
        try:
            usage = response.usage
            return {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            }
        except (AttributeError, TypeError):
            return {
                "prompt_tokens": None,
                "completion_tokens": None,
                "total_tokens": None,
            }
    
    def completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Synchronous completion with tracing
        
        Args:
            model: LLM model to use
            messages: List of message dictionaries (role, content)
            trace_id: Optional Langfuse trace ID for linking
            **kwargs: Additional completion parameters
            
        Returns:
            LiteLLM model response
        """
        start_time = datetime.now()
        
        try:
            # Call LiteLLM
            response = completion(model=model, messages=messages, **kwargs)
            
            # Extract metrics
            end_time = datetime.now()
            token_metrics = self._extract_token_metrics(response)
            
            # Trace if langfuse is enabled
            if langfuse_tracer.is_enabled and self.trace_all:
                langfuse_tracer.trace_llm(
                    name=f"completion_{model}",
                    trace_id=trace_id,
                    model=model,
                    input=messages,
                    output=response.choices[0].message.content if response.choices else None,
                    start_time=start_time,
                    end_time=end_time,
                    prompt_tokens=token_metrics["prompt_tokens"],
                    completion_tokens=token_metrics["completion_tokens"],
                    total_tokens=token_metrics["total_tokens"],
                    metadata={
                        "model": model,
                        "temperature": kwargs.get("temperature", None),
                        "max_tokens": kwargs.get("max_tokens", None),
                        "response_ms": (end_time - start_time).total_seconds() * 1000,
                    }
                )
            
            return response
        except Exception as e:
            # Trace error if enabled
            if langfuse_tracer.is_enabled and self.trace_all:
                langfuse_tracer.trace_llm(
                    name=f"completion_error_{model}",
                    trace_id=trace_id,
                    model=model,
                    input=messages,
                    output=str(e),
                    start_time=start_time,
                    end_time=datetime.now(),
                    metadata={
                        "model": model,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    tags=["error"]
                )
            raise
    
    async def acompletion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Asynchronous completion with tracing
        
        Args:
            model: LLM model to use
            messages: List of message dictionaries (role, content)
            trace_id: Optional Langfuse trace ID for linking
            **kwargs: Additional completion parameters
            
        Returns:
            LiteLLM model response
        """
        start_time = datetime.now()
        
        try:
            # Call LiteLLM async
            response = await acompletion(model=model, messages=messages, **kwargs)
            
            # Extract metrics
            end_time = datetime.now()
            token_metrics = self._extract_token_metrics(response)
            
            # Trace if langfuse is enabled
            if langfuse_tracer.is_enabled and self.trace_all:
                langfuse_tracer.trace_llm(
                    name=f"acompletion_{model}",
                    trace_id=trace_id,
                    model=model,
                    input=messages,
                    output=response.choices[0].message.content if response.choices else None,
                    start_time=start_time,
                    end_time=end_time,
                    prompt_tokens=token_metrics["prompt_tokens"],
                    completion_tokens=token_metrics["completion_tokens"],
                    total_tokens=token_metrics["total_tokens"],
                    metadata={
                        "model": model,
                        "temperature": kwargs.get("temperature", None),
                        "max_tokens": kwargs.get("max_tokens", None),
                        "response_ms": (end_time - start_time).total_seconds() * 1000,
                    }
                )
            
            return response
        except Exception as e:
            # Trace error if enabled
            if langfuse_tracer.is_enabled and self.trace_all:
                langfuse_tracer.trace_llm(
                    name=f"acompletion_error_{model}",
                    trace_id=trace_id,
                    model=model,
                    input=messages,
                    output=str(e),
                    start_time=start_time,
                    end_time=datetime.now(),
                    metadata={
                        "model": model,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    tags=["error"]
                )
            raise
    
    def embedding(
        self,
        model: str,
        input: Union[str, List[str]],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Get embeddings with tracing
        
        Args:
            model: Embedding model to use
            input: Text input or list of inputs
            trace_id: Optional Langfuse trace ID for linking
            **kwargs: Additional embedding parameters
            
        Returns:
            Embedding response
        """
        start_time = datetime.now()
        
        try:
            # Call LiteLLM embedding
            response = embedding(model=model, input=input, **kwargs)
            
            # Trace if langfuse is enabled
            if langfuse_tracer.is_enabled and self.trace_all:
                # Try to extract token count
                token_count = None
                try:
                    token_count = response.usage.total_tokens
                except (AttributeError, TypeError):
                    pass
                
                # Record trace
                langfuse_tracer.trace_llm(
                    name=f"embedding_{model}",
                    trace_id=trace_id,
                    model=model,
                    input=input if isinstance(input, str) else str(input)[:100] + "...",
                    output="[embedding vectors]",
                    start_time=start_time,
                    end_time=datetime.now(),
                    total_tokens=token_count,
                    metadata={
                        "model": model,
                        "vector_count": len(response.data) if hasattr(response, "data") else 1,
                        "response_ms": (datetime.now() - start_time).total_seconds() * 1000,
                    }
                )
            
            return response
        except Exception as e:
            # Trace error if enabled
            if langfuse_tracer.is_enabled and self.trace_all:
                langfuse_tracer.trace_llm(
                    name=f"embedding_error_{model}",
                    trace_id=trace_id,
                    model=model,
                    input=input if isinstance(input, str) else str(input)[:100] + "...",
                    output=str(e),
                    start_time=start_time,
                    end_time=datetime.now(),
                    metadata={
                        "model": model,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    tags=["error"]
                )
            raise


# Create global instance for easy import
traced_llm = TracedLiteLLM()
