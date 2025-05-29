# LiteLLM Provider Configuration Guide

## Overview

This document describes the comprehensive LiteLLM provider configuration for the Production RAG System, optimized for M4 Mac Mini deployment with Docker containers.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │────│   LiteLLM Proxy  │────│  External APIs  │
│   (Port 8000)   │    │   (Port 4000)    │    │  (OpenAI, etc.) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────────────────┐
                       │   Ollama Local   │
                       │   (Port 11434)   │
                       └──────────────────┘
```

## Provider Configuration

### Supported Providers

1. **OpenAI** - GPT models (gpt-4, gpt-4-turbo, gpt-3.5-turbo)
2. **Anthropic** - Claude models (claude-3-opus, claude-3-sonnet, claude-3-haiku)
3. **Google** - Gemini models (gemini-pro, gemini-pro-vision)
4. **Cohere** - Command models (command-r, command-r-plus)
5. **Azure OpenAI** - Azure-hosted GPT models
6. **Ollama** - Local models (llama3.2:1b)

### Model Groups

#### Premium Models (Quality-Optimized)
- **Purpose**: Complex reasoning, analysis, creative tasks
- **Models**: `gpt-4`, `claude-3-opus`, `azure-gpt-4`
- **Cost**: High
- **Speed**: Slower
- **Use Cases**: Research, complex analysis, high-quality content generation

#### Standard Models (Balanced)
- **Purpose**: General-purpose tasks with good quality/speed balance
- **Models**: `gpt-4-turbo`, `claude-3-sonnet`, `gpt-3.5-turbo`, `command-r-plus`
- **Cost**: Medium
- **Speed**: Medium
- **Use Cases**: General chat, document processing, moderate complexity tasks

#### Fast Models (Speed-Optimized)
- **Purpose**: Quick responses, simple tasks
- **Models**: `claude-3-haiku`, `gpt-3.5-turbo`, `command-r`, `gemini-pro`
- **Cost**: Low-Medium
- **Speed**: Fast
- **Use Cases**: Quick queries, simple Q&A, real-time applications

#### Vision Models (Multimodal)
- **Purpose**: Image analysis, visual understanding
- **Models**: `gpt-4-vision`, `gpt-4-turbo`, `claude-3-opus`, `gemini-pro-vision`
- **Cost**: High
- **Speed**: Slower
- **Use Cases**: Image analysis, document OCR, visual Q&A

#### Local Models (Privacy-Optimized)
- **Purpose**: Privacy-sensitive tasks, offline processing
- **Models**: `llama3.2-1b`
- **Cost**: Free (compute only)
- **Speed**: Very Slow on M4 CPU (20-60s)
- **Use Cases**: Sensitive data processing, offline scenarios

#### Code Models (Programming-Optimized)
- **Purpose**: Code generation, debugging, technical tasks
- **Models**: `gpt-4`, `claude-3-opus`
- **Cost**: High
- **Speed**: Medium
- **Use Cases**: Code generation, debugging, technical documentation

#### Budget Models (Cost-Optimized)
- **Purpose**: Cost-sensitive applications
- **Models**: `gpt-3.5-turbo`, `claude-3-haiku`, `command-r`, `gemini-pro`
- **Cost**: Low
- **Speed**: Fast-Medium
- **Use Cases**: High-volume applications, development/testing

## Routing Strategy

### Usage-Based Routing
- **Primary Strategy**: `usage-based-routing`
- **Fallback**: `simple-shuffle` (when Redis unavailable)
- **Benefits**: 
  - Distributes load based on actual usage
  - Prevents rate limit violations
  - Optimizes costs

### Fallback Chains

#### Intelligent Fallbacks
Each model has carefully designed fallback chains:

```yaml
Premium → Standard → Fast
gpt-4 → gpt-4-turbo → claude-3-opus → azure-gpt-4

Quality Preservation:
claude-3-opus → gpt-4 → claude-3-sonnet → gpt-4-turbo

Cost Optimization:
claude-3-haiku → gpt-3.5-turbo → command-r → gemini-pro

Local → External:
llama3.2-1b → gpt-3.5-turbo → claude-3-haiku
```

## Performance Optimization

### M4 Mac Mini Specific Settings

#### Timeouts
- **Request Timeout**: 900 seconds (15 minutes)
- **Health Check Interval**: 180 seconds (3 minutes)
- **Model Fallback Timeout**: 60 seconds

#### Local Model Performance
- **Expected Response Time**: 20-60 seconds
- **Concurrent Requests**: Limited to 1 (OLLAMA_NUM_PARALLEL=1)
- **Memory Management**: Optimized for Apple Silicon

#### Retry Configuration
- **Number of Retries**: 3
- **Retry Delay**: 2 seconds (exponential backoff)
- **Max Retry Delay**: 30 seconds

## Rate Limiting

### Production Settings
- **Requests Per Minute (RPM)**: 1,000
- **Tokens Per Minute (TPM)**: 150,000
- **Per-User Tracking**: Enabled
- **Budget Management**: Enabled

### Cost Tracking
- **Per-Model Costs**: Tracked
- **Per-API-Key Costs**: Tracked
- **Per-User Costs**: Tracked
- **Budget Alerts**: Configured

## Security Configuration

### Authentication
- **Master Key**: `LITELLM_MASTER_KEY` (Bearer token)
- **UI Access**: Admin-only with password protection
- **CORS**: Configured for web integration

### Headers
- **X-LiteLLM-Version**: Version identification
- **X-RAG-System**: System identification
- **X-Provider-Routing**: Routing status
- **X-Platform**: M4-Mac-Mini identification
- **X-Environment**: Docker environment

## Monitoring & Observability

### Metrics
- **Prometheus Metrics**: Enabled (port 4001)
- **Health Checks**: Automated with 3-minute intervals
- **Verbose Logging**: Enabled for debugging
- **Cost Tracking**: Real-time monitoring

### Health Monitoring
```bash
# Check LiteLLM health
curl -H "Authorization: Bearer sk-change-me-to-random-string" \
     http://localhost:4000/health

# Check available models
curl -H "Authorization: Bearer sk-change-me-to-random-string" \
     http://localhost:4000/v1/models

# Check Prometheus metrics
curl http://localhost:4001/metrics
```

## Environment Variables

### Required Variables
```bash
# Core LiteLLM
LITELLM_MASTER_KEY=sk-change-me-to-random-string
LITELLM_UI_PASSWORD=change-me-litellm-ui-password

# External Providers (optional)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GOOGLE_API_KEY=your-google-api-key-here
COHERE_API_KEY=your-cohere-api-key-here

# Azure OpenAI (optional)
AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Redis (for usage-based routing)
REDIS_PASSWORD=change-me-redis-pass
```

## Usage Examples

### Basic Chat Completion
```bash
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-change-me-to-random-string" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### Using Model Groups
```bash
# Use fast models for quick responses
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-change-me-to-random-string" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "fast",
    "messages": [{"role": "user", "content": "Quick question"}]
  }'

# Use local models for privacy
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-change-me-to-random-string" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local",
    "messages": [{"role": "user", "content": "Private query"}]
  }'
```

### Embedding Generation
```bash
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-change-me-to-random-string" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-3-small",
    "input": "Text to embed"
  }'
```

## Troubleshooting

### Common Issues

#### Local Model Timeouts
- **Symptom**: Requests timeout after 60+ seconds
- **Cause**: CPU-intensive processing on M4 Mac Mini
- **Solution**: Increase timeout or use external models for time-sensitive tasks

#### Provider Authentication Errors
- **Symptom**: 401 errors for external providers
- **Cause**: Missing or invalid API keys
- **Solution**: Set proper API keys in `.env` file

#### Health Check Failures
- **Symptom**: Models showing as unhealthy
- **Cause**: Non-existent models in configuration
- **Solution**: Remove references to unavailable models

### Debugging Commands
```bash
# Check Docker container logs
docker logs zoi-litellm-1

# Check Ollama models
curl http://localhost:11434/api/tags

# Test specific model
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-change-me-to-random-string" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2-1b", "messages": [{"role": "user", "content": "test"}], "max_tokens": 5}'
```

## Performance Benchmarks (M4 Mac Mini)

### Response Times
- **External APIs**: 1-5 seconds
- **Local Models**: 20-60 seconds
- **Health Checks**: 5-10 seconds
- **Model Listing**: <1 second

### Resource Usage
- **Memory**: ~2GB for LiteLLM + Ollama
- **CPU**: High during local model inference
- **Network**: Minimal for external API calls

## Best Practices

1. **Use Model Groups**: Leverage predefined groups for consistent routing
2. **Monitor Costs**: Enable cost tracking for all providers
3. **Set Timeouts**: Configure appropriate timeouts for your use case
4. **Use Fallbacks**: Always configure fallback chains
5. **Local for Privacy**: Use local models for sensitive data
6. **External for Speed**: Use external APIs for time-sensitive tasks
7. **Cache Results**: Enable caching for repeated queries
8. **Monitor Health**: Set up automated health monitoring

## Configuration Files

- **Main Config**: `/config/litellm/config.yaml`
- **Environment**: `/.env`
- **Docker Compose**: `/docker-compose.yml`
- **Documentation**: `/docs/litellm-provider-configuration.md`
