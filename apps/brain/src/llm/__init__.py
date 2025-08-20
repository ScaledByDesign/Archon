"""
LLM Integration Package for Production RAG System

This package provides clients and utilities for interacting with various
Large Language Models through the LiteLLM proxy.
"""

from .litellm_client import (
    LiteLLMClient,
    ChatMessage,
    ChatRequest,
    EmbeddingRequest,
    LiteLLMResponse,
    ModelInfo,
    ModelTier,
    RequestType,
    quick_chat,
    quick_embedding
)

__all__ = [
    "LiteLLMClient",
    "ChatMessage", 
    "ChatRequest",
    "EmbeddingRequest",
    "LiteLLMResponse",
    "ModelInfo",
    "ModelTier",
    "RequestType",
    "quick_chat",
    "quick_embedding"
]
