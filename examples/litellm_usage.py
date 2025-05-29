#!/usr/bin/env python3
"""
LiteLLM Client Usage Examples

This file demonstrates how to use the LiteLLM client for various tasks
in the Production RAG System.
"""

import asyncio
import sys
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


async def example_basic_chat():
    """Example: Basic chat completion"""
    print("🗣️  Basic Chat Example")
    print("-" * 30)
    
    async with LiteLLMClient() as client:
        # Simple chat
        response = await quick_chat(
            "Explain what a RAG system is in one sentence.",
            model_tier=ModelTier.STANDARD
        )
        print(f"Response: {response}")
        print()


async def example_model_selection():
    """Example: Different model selection strategies"""
    print("🎯 Model Selection Examples")
    print("-" * 30)
    
    async with LiteLLMClient() as client:
        # Code generation task
        code_request = ChatRequest(
            messages=[
                ChatMessage(role="system", content="You are a helpful coding assistant."),
                ChatMessage(role="user", content="Write a Python function to calculate fibonacci numbers.")
            ],
            model_tier=ModelTier.PREMIUM,
            request_type=RequestType.CODE,
            temperature=0.1
        )
        
        response = await client.chat_completion(code_request)
        print(f"Code Generation (Model: {response.model}):")
        print(response.choices[0]["message"]["content"][:200] + "...")
        print()
        
        # Creative writing task
        creative_request = ChatRequest(
            messages=[
                ChatMessage(role="user", content="Write a creative story about AI in 50 words.")
            ],
            model_tier=ModelTier.STANDARD,
            request_type=RequestType.CREATIVE,
            temperature=0.8
        )
        
        response = await client.chat_completion(creative_request)
        print(f"Creative Writing (Model: {response.model}):")
        print(response.choices[0]["message"]["content"])
        print()


async def example_embeddings():
    """Example: Generate embeddings for text"""
    print("🔢 Embedding Generation Example")
    print("-" * 30)
    
    async with LiteLLMClient() as client:
        texts = [
            "Machine learning is a subset of artificial intelligence.",
            "RAG systems combine retrieval and generation for better AI responses.",
            "Vector databases store high-dimensional embeddings efficiently."
        ]
        
        for i, text in enumerate(texts, 1):
            embedding = await quick_embedding(text, client=client)
            print(f"Text {i}: {text}")
            print(f"Embedding length: {len(embedding)}")
            print(f"First 5 values: {embedding[:5]}")
            print()


async def example_streaming_chat():
    """Example: Streaming chat completion"""
    print("🌊 Streaming Chat Example")
    print("-" * 30)
    
    async with LiteLLMClient() as client:
        request = ChatRequest(
            messages=[
                ChatMessage(role="user", content="Tell me a short story about a robot learning to paint, stream the response.")
            ],
            model_tier=ModelTier.STANDARD,
            temperature=0.7,
            stream=True
        )
        
        print("Streaming response:")
        async for chunk in await client.chat_completion(request):
            if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
                content = chunk["choices"][0]["delta"]["content"]
                print(content, end="", flush=True)
        print("\n")


async def example_cost_tracking():
    """Example: Cost tracking and metrics"""
    print("💰 Cost Tracking Example")
    print("-" * 30)
    
    async with LiteLLMClient(enable_cost_tracking=True) as client:
        # Make several requests
        tasks = [
            "What is machine learning?",
            "Explain neural networks briefly.",
            "What are transformers in AI?",
            "Define natural language processing."
        ]
        
        for task in tasks:
            await quick_chat(task, model_tier=ModelTier.FAST, client=client)
        
        # Get metrics
        metrics = client.get_metrics()
        print(f"Total requests: {metrics['total_requests']}")
        print(f"Total cost: ${metrics['total_cost']:.6f}")
        print(f"Average latency: {metrics['average_latency']:.3f}s")
        print(f"Error rate: {metrics['error_rate']:.2%}")
        print()


async def example_rag_workflow():
    """Example: Complete RAG workflow simulation"""
    print("🔍 RAG Workflow Example")
    print("-" * 30)
    
    async with LiteLLMClient() as client:
        # 1. User query
        user_query = "How do neural networks learn?"
        print(f"User Query: {user_query}")
        
        # 2. Generate embedding for similarity search
        query_embedding = await quick_embedding(user_query, client=client)
        print(f"Query embedding generated (length: {len(query_embedding)})")
        
        # 3. Simulate retrieved context (normally from vector DB)
        retrieved_context = """
        Neural networks learn through a process called backpropagation. During training,
        the network makes predictions, compares them to the correct answers, and adjusts
        its weights to minimize errors. This process involves forward propagation to
        compute outputs and backward propagation to update weights using gradient descent.
        """
        
        # 4. Generate response using retrieved context
        rag_request = ChatRequest(
            messages=[
                ChatMessage(
                    role="system",
                    content="You are a helpful AI assistant. Use the provided context to answer questions accurately."
                ),
                ChatMessage(
                    role="user",
                    content=f"Context: {retrieved_context.strip()}\n\nQuestion: {user_query}"
                )
            ],
            model_tier=ModelTier.STANDARD,
            request_type=RequestType.ANALYSIS,
            temperature=0.3
        )
        
        response = await client.chat_completion(rag_request)
        print(f"RAG Response: {response.choices[0]['message']['content']}")
        print()


async def example_error_handling():
    """Example: Error handling and fallbacks"""
    print("⚠️  Error Handling Example")
    print("-" * 30)
    
    async with LiteLLMClient() as client:
        try:
            # Try with an invalid model
            request = ChatRequest(
                messages=[ChatMessage(role="user", content="Test message")],
                model="invalid-model-12345"
            )
            await client.chat_completion(request)
        except Exception as e:
            print(f"Caught expected error: {type(e).__name__}: {str(e)[:100]}...")
        
        # Demonstrate fallback to working model
        try:
            fallback_response = await quick_chat(
                "This should work with model selection.",
                model_tier=ModelTier.FAST
            )
            print(f"Fallback successful: {fallback_response[:50]}...")
        except Exception as e:
            print(f"Fallback failed: {e}")
        print()


async def main():
    """Run all examples"""
    print("🚀 LiteLLM Client Usage Examples")
    print("=" * 50)
    print()
    
    examples = [
        example_basic_chat,
        example_model_selection,
        example_embeddings,
        # example_streaming_chat,  # Uncomment if streaming is supported
        example_cost_tracking,
        example_rag_workflow,
        example_error_handling
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example failed: {e}")
            print()
    
    print("✅ Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
