# LiteLLM Integration Guide

## Overview

This guide covers the comprehensive LiteLLM integration for the Production RAG System, including the Python client, configuration, and usage patterns.

## Architecture

The LiteLLM integration consists of several key components:

1. **LiteLLM Proxy Service**: Unified interface for multiple LLM providers
2. **Python Client**: Comprehensive client with advanced features
3. **Configuration Files**: Router and model configuration
4. **Integration Layer**: FastAPI service integration

## Components

### LiteLLM Client (`src/llm/litellm_client.py`)

A comprehensive Python client that provides:

- **Multi-Provider Support**: OpenAI, Anthropic, Google, Cohere, Azure, Ollama
- **Model Selection**: Intelligent routing based on request type and performance tier
- **Cost Tracking**: Real-time cost monitoring and billing
- **Performance Metrics**: Latency, error rates, and usage statistics
- **Error Handling**: Robust error handling with fallbacks
- **Caching**: Response caching for improved performance
- **Streaming**: Support for streaming responses

### Key Classes

#### `LiteLLMClient`
Main client class for interacting with the LiteLLM proxy.

```python
from llm.litellm_client import LiteLLMClient

async with LiteLLMClient(base_url="http://zoi.local:4000") as client:
    response = await client.chat_completion(request)
```

#### `ChatRequest` and `ChatMessage`
Structured request objects for chat completions.

```python
from llm.litellm_client import ChatRequest, ChatMessage, ModelTier, RequestType

request = ChatRequest(
    messages=[ChatMessage(role="user", content="Hello!")],
    model_tier=ModelTier.STANDARD,
    request_type=RequestType.CHAT,
    temperature=0.7
)
```

#### `EmbeddingRequest`
Request object for embedding generation.

```python
from llm.litellm_client import EmbeddingRequest

request = EmbeddingRequest(
    input="Text to embed",
    model="text-embedding-3-large"
)
```

## Model Selection

The client provides intelligent model selection based on:

### Model Tiers
- **PREMIUM**: High-quality models (GPT-4, Claude-3 Opus)
- **STANDARD**: Balanced performance (GPT-4 Turbo, Claude-3 Sonnet)
- **FAST**: Quick responses (Claude-3 Haiku, GPT-3.5 Turbo)
- **LOCAL**: Local models (Mistral, Llama)
- **BUDGET**: Cost-effective options

### Request Types
- **CODE**: Code generation and programming tasks
- **CREATIVE**: Creative writing and content generation
- **ANALYSIS**: Data analysis and reasoning tasks
- **CHAT**: General conversation
- **VISION**: Image understanding tasks
- **EMBEDDING**: Text embedding generation

### Example Model Selection

```python
# Automatic selection based on tier and type
request = ChatRequest(
    messages=[ChatMessage(role="user", content="Write a Python function")],
    model_tier=ModelTier.PREMIUM,
    request_type=RequestType.CODE
)

# Manual model specification
request = ChatRequest(
    messages=[ChatMessage(role="user", content="Hello")],
    model="gpt-4"
)
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# LiteLLM Configuration
LITELLM_BASE_URL=http://zoi.local:4000
LITELLM_API_KEY=sk-1234

# Provider API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
COHERE_API_KEY=your_cohere_key
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_VERSION=2023-12-01-preview
```

### LiteLLM Configuration (`config/litellm/config.yaml`)

The configuration file defines:
- Available models and providers
- Routing strategies
- Load balancing rules
- Fallback mechanisms
- Rate limiting
- Cost controls

### Router Configuration (`config/litellm/router.yaml`)

Advanced routing configuration for:
- Request-based routing
- User tier routing
- Load balancing strategies
- Cost optimization

## Usage Examples

### Basic Chat

```python
from llm.litellm_client import quick_chat, ModelTier

response = await quick_chat(
    "Explain machine learning in simple terms",
    model_tier=ModelTier.STANDARD
)
print(response)
```

### Advanced Chat with Context

```python
from llm.litellm_client import LiteLLMClient, ChatRequest, ChatMessage

async with LiteLLMClient() as client:
    request = ChatRequest(
        messages=[
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="What is a RAG system?")
        ],
        model_tier=ModelTier.PREMIUM,
        temperature=0.7,
        max_tokens=500
    )
    
    response = await client.chat_completion(request)
    print(response.choices[0]["message"]["content"])
```

### Embedding Generation

```python
from llm.litellm_client import quick_embedding

embedding = await quick_embedding("Text to embed")
print(f"Embedding length: {len(embedding)}")
```

### Streaming Responses

```python
request = ChatRequest(
    messages=[ChatMessage(role="user", content="Tell me a story")],
    stream=True
)

async for chunk in await client.chat_completion(request):
    if chunk.get("choices") and chunk["choices"][0].get("delta", {}).get("content"):
        print(chunk["choices"][0]["delta"]["content"], end="")
```

### Cost Tracking

```python
async with LiteLLMClient(enable_cost_tracking=True) as client:
    # Make requests...
    
    metrics = client.get_metrics()
    print(f"Total cost: ${metrics['total_cost']:.6f}")
    print(f"Average latency: {metrics['average_latency']:.3f}s")
    print(f"Error rate: {metrics['error_rate']:.2%}")
```

## RAG System Integration

### Complete RAG Workflow

```python
async def rag_query(user_query: str, context: str):
    async with LiteLLMClient() as client:
        # Generate query embedding for retrieval
        query_embedding = await quick_embedding(user_query, client=client)
        
        # Use context to generate response
        request = ChatRequest(
            messages=[
                ChatMessage(
                    role="system",
                    content="Use the provided context to answer questions accurately."
                ),
                ChatMessage(
                    role="user",
                    content=f"Context: {context}\n\nQuestion: {user_query}"
                )
            ],
            model_tier=ModelTier.STANDARD,
            request_type=RequestType.ANALYSIS,
            temperature=0.3
        )
        
        response = await client.chat_completion(request)
        return response.choices[0]["message"]["content"]
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from llm.litellm_client import LiteLLMClient

app = FastAPI()

async def get_llm_client():
    async with LiteLLMClient() as client:
        yield client

@app.post("/chat")
async def chat_endpoint(
    message: str,
    client: LiteLLMClient = Depends(get_llm_client)
):
    response = await quick_chat(message, client=client)
    return {"response": response}
```

## Testing

### Running Tests

```bash
# Test LiteLLM client functionality
python scripts/test-litellm-client.py

# Test with custom URL
python scripts/test-litellm-client.py --url http://zoi.local:4000

# Run usage examples
python examples/litellm_usage.py
```

### Test Coverage

The test suite covers:
- Client initialization
- Health checks
- Model availability
- Chat completions
- Embedding generation
- Cost tracking
- Error handling
- Performance metrics

## Performance Optimization

### Caching

Enable response caching for improved performance:

```python
client = LiteLLMClient(enable_caching=True)
```

### Connection Pooling

The client uses aiohttp for efficient connection management:

```python
client = LiteLLMClient(
    timeout=600,
    max_retries=3
)
```

### Model Selection Optimization

Use appropriate model tiers for different tasks:

- **Fast models** for simple queries
- **Standard models** for balanced performance
- **Premium models** for complex reasoning
- **Local models** for privacy-sensitive tasks

## Monitoring and Alerting

### Metrics Collection

The client automatically tracks:
- Request count and latency
- Error rates and types
- Cost per request and total spend
- Model usage patterns

### Health Checks

```python
health = await client.health_check()
if health["status"] != "healthy":
    # Handle unhealthy state
    pass
```

### Cost Monitoring

```python
metrics = client.get_metrics()
if metrics["total_cost"] > COST_THRESHOLD:
    # Alert on high costs
    pass
```

## Security Considerations

### API Key Management

- Store API keys in environment variables
- Use HashiCorp Vault for production secrets
- Rotate keys regularly
- Monitor for unauthorized usage

### Rate Limiting

Configure rate limits in the LiteLLM configuration:

```yaml
litellm_settings:
  max_requests_per_minute: 100
  max_tokens_per_minute: 10000
```

### Input Validation

Always validate and sanitize user inputs:

```python
from bleach import clean

def sanitize_input(text: str) -> str:
    return clean(text, strip=True)
```

## Troubleshooting

### Common Issues

1. **Connection Errors**: Check LiteLLM proxy status and network connectivity
2. **Authentication Failures**: Verify API keys and permissions
3. **Model Not Available**: Check model configuration and provider status
4. **High Latency**: Monitor network conditions and model load
5. **Cost Overruns**: Implement proper rate limiting and monitoring

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("llm.litellm_client").setLevel(logging.DEBUG)
```

### Health Checks

Regular health checks help identify issues:

```bash
curl http://zoi.local:4000/health
```

## Best Practices

1. **Use Appropriate Models**: Select models based on task requirements
2. **Implement Fallbacks**: Always have backup models configured
3. **Monitor Costs**: Track spending and set alerts
4. **Cache Responses**: Use caching for repeated queries
5. **Handle Errors Gracefully**: Implement proper error handling
6. **Validate Inputs**: Sanitize and validate all user inputs
7. **Use Context Windows Efficiently**: Optimize prompt length
8. **Implement Rate Limiting**: Prevent abuse and control costs

## Future Enhancements

Planned improvements include:
- Advanced caching strategies
- Model performance benchmarking
- Automatic model selection optimization
- Enhanced cost prediction
- Multi-region deployment support
- Custom model fine-tuning integration

## Support

For issues and questions:
- Check the test suite output for diagnostic information
- Review LiteLLM proxy logs
- Monitor application metrics and health checks
- Consult the LiteLLM documentation for provider-specific issues
