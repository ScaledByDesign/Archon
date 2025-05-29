"""
Langfuse client integration for LLM observability
Provides tracing and monitoring capabilities for LLM interactions
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from contextlib import contextmanager
from datetime import datetime
from uuid import uuid4

from langfuse import Langfuse
from langfuse.decorators import observe
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LangfuseConfig(BaseModel):
    """Configuration for Langfuse client"""
    public_key: str = Field(..., description="Langfuse public API key")
    secret_key: str = Field(..., description="Langfuse secret API key") 
    host: str = Field(..., description="Langfuse API host URL")
    release: Optional[str] = Field(None, description="Application release version")
    debug: bool = Field(False, description="Enable debug mode")
    flush_at: int = Field(10, description="Flush queue when this many items")
    flush_interval: int = Field(30, description="Flush queue every N seconds")


class LangfuseTracer:
    """
    Langfuse tracing client for LLM observability
    Provides methods for tracing LLM interactions, user sessions, and API calls
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure one client instance"""
        if cls._instance is None:
            cls._instance = super(LangfuseTracer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config: Optional[LangfuseConfig] = None):
        """Initialize Langfuse client with configuration"""
        if self._initialized:
            return
            
        if config is None:
            # Load from environment variables
            config = LangfuseConfig(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
                host=os.getenv("LANGFUSE_HOST", "https://langfuse.localhost"),
                release=os.getenv("APPLICATION_VERSION", "1.0.0"),
                debug=os.getenv("LANGFUSE_DEBUG", "false").lower() == "true",
                flush_at=int(os.getenv("LANGFUSE_FLUSH_AT", "10")),
                flush_interval=int(os.getenv("LANGFUSE_FLUSH_INTERVAL", "30"))
            )
        
        try:
            self.client = Langfuse(
                public_key=config.public_key,
                secret_key=config.secret_key,
                host=config.host,
                release=config.release,
                debug=config.debug,
                flush_at=config.flush_at,
                flush_interval=config.flush_interval
            )
            logger.info(f"Langfuse client initialized: {config.host}")
            self._initialized = True
            self._enabled = True
        except Exception as e:
            logger.error(f"Langfuse initialization error: {e}")
            self._initialized = True
            self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        """Check if Langfuse tracing is enabled"""
        return self._enabled
    
    def create_trace(
        self, 
        name: str, 
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ):
        """Create a new trace for tracking a user session or request flow"""
        if not self._enabled:
            logger.debug("Langfuse tracing disabled, skipping create_trace")
            return None
            
        try:
            trace = self.client.trace(
                name=name,
                user_id=user_id,
                metadata=metadata or {},
                tags=tags or []
            )
            logger.debug(f"Created Langfuse trace: {trace.id}")
            return trace
        except Exception as e:
            logger.error(f"Error creating Langfuse trace: {e}")
            return None
    
    def trace_llm(
        self,
        name: str,
        trace_id: Optional[str] = None,
        model: str = "",
        input: Union[str, Dict, List] = "",
        output: Union[str, Dict, List, None] = None,
        metadata: Optional[Dict[str, Any]] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
    ):
        """
        Trace an LLM interaction with detailed metrics
        Captures model, input/output, token usage, and timing information
        """
        if not self._enabled:
            logger.debug("Langfuse tracing disabled, skipping trace_llm")
            return None
        
        try:
            trace = self.client.trace(id=trace_id) if trace_id else self.client.trace(
                name=f"llm-{str(uuid4())[:8]}",
                user_id=user_id,
                tags=tags or [],
            )
            
            observation = trace.generation(
                name=name,
                model=model,
                prompt=input,
                completion=output,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                metadata=metadata or {},
                start_time=start_time,
                end_time=end_time,
            )
            
            logger.debug(f"Traced LLM generation: {observation.id}")
            return observation
        except Exception as e:
            logger.error(f"Error tracing LLM generation: {e}")
            return None

    @contextmanager
    def trace_span(
        self, 
        name: str, 
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ):
        """Context manager for tracing execution spans with timing"""
        if not self._enabled:
            logger.debug("Langfuse tracing disabled, skipping trace_span")
            try:
                yield None
            except Exception as e:
                logger.error(f"Error in traced span: {e}")
                raise
            return
            
        span = None
        error = None
        
        try:
            trace = self.client.trace(id=trace_id) if trace_id else None
            
            if trace:
                span = trace.span(
                    name=name, 
                    metadata=metadata or {},
                    tags=tags or []
                )
            else:
                # Create a new trace if none exists
                trace = self.client.trace(
                    name=f"span-trace-{str(uuid4())[:8]}", 
                    tags=tags or []
                )
                span = trace.span(
                    name=name, 
                    metadata=metadata or {},
                    tags=tags or []
                )
                
            yield span
        except Exception as e:
            error = e
            logger.error(f"Error in traced span: {e}")
            raise
        finally:
            if span:
                if error:
                    span.end(
                        status="error",
                        metadata={"error": str(error), "error_type": type(error).__name__}
                    )
                else:
                    span.end(status="success")
    
    def score_trace(
        self,
        trace_id: str,
        name: str,
        value: Union[float, int, bool],
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Add a score to an existing trace for quality metrics"""
        if not self._enabled:
            logger.debug("Langfuse tracing disabled, skipping score_trace")
            return None
            
        try:
            trace = self.client.trace(id=trace_id)
            score = trace.score(
                name=name,
                value=value,
                comment=comment,
                metadata=metadata or {}
            )
            logger.debug(f"Added score to trace: {score.id}")
            return score
        except Exception as e:
            logger.error(f"Error scoring trace: {e}")
            return None


# Initialize a global Langfuse tracer instance
langfuse_tracer = LangfuseTracer()

# Decorator for tracing functions with Langfuse
def trace_function(name=None, metadata=None, tags=None):
    """Decorator to trace function execution with Langfuse"""
    def decorator(func):
        # Only apply if tracing is enabled
        if not langfuse_tracer.is_enabled:
            return func
            
        # Apply Langfuse observe decorator
        return observe(
            name_fn=lambda *args, **kwargs: name or func.__name__,
            tags=tags or [],
            metadata=metadata or {},
        )(func)
    return decorator
