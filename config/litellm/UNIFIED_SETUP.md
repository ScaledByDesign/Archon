# Unified LiteLLM Configuration

## Overview
All services in the Zoi ecosystem now use the same LiteLLM configuration to ensure consistency and simplicity.

## Configuration Files

### 1. `config_simple.yaml`
The main LiteLLM configuration with three models:
- **zoi-coder**: Fast inference on RTX 5070 Ti (14B model)
- **zoi-planner**: Advanced reasoning on RTX 3090 (30B model)
- **gpt-4**: Alias for zoi-planner for compatibility

### 2. `service_config.env`
Environment variables for all services:
```bash
LITELLM_BASE_URL=http://localhost:7010/v1
LITELLM_API_KEY=sk-wqn0xwq_vha4MVM2yzw
PRIMARY_MODEL=zoi-coder
ADVANCED_MODEL=zoi-planner
```

### 3. `docker-compose.override.yml`
Ensures all Docker services use consistent LiteLLM settings.

### 4. `litellm_config.py`
Python module for easy integration in Python services.

## Service Integration

### For Docker Services
Add these environment variables:
```yaml
environment:
  - LITELLM_BASE_URL=http://host.docker.internal:7010/v1
  - LITELLM_API_KEY=sk-wqn0xwq_vha4MVM2yzw
  - PRIMARY_MODEL=zoi-coder
  - ADVANCED_MODEL=zoi-planner
```

### For Python Services
```python
from litellm_config import get_litellm_client

client = get_litellm_client()
response = client.chat_completion([
    {"role": "user", "content": "Your prompt here"}
])
```

### For JavaScript/TypeScript Services
```javascript
const LITELLM_CONFIG = {
  baseUrl: process.env.LITELLM_BASE_URL || "http://localhost:7010/v1",
  apiKey: process.env.LITELLM_API_KEY || "sk-wqn0xwq_vha4MVM2yzw",
  models: {
    primary: "zoi-coder",
    advanced: "zoi-planner"
  }
};
```

## Available Models

| Model Name | Hardware | Base Model | Use Case |
|------------|----------|------------|----------|
| zoi-coder | RTX 5070 Ti | Qwen3-14B | Fast responses, coding tasks |
| zoi-planner | RTX 3090 | Qwen3-Coder-30B | Complex reasoning, planning |
| gpt-4 | RTX 3090 | Qwen3-Coder-30B | Compatibility alias |

## Testing the Configuration

### Quick Test
```bash
# Test with curl
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zoi-coder",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### Python Test
```bash
python litellm_config.py
```

## Troubleshooting

### If models return 429 errors:
1. Restart LiteLLM: `docker-compose restart litellm`
2. Check config: `cat config_simple.yaml`
3. Verify endpoints are accessible

### If auto_router_config.json error:
```bash
rm -rf auto_router_config.json
echo '{}' > auto_router_config.json
```

## Services Using This Configuration

- **LiteLLM**: The proxy server itself
- **Elysia**: Agentic platform for Weaviate
- **Langflow**: Visual AI workflow builder
- **Unified-RAG**: Cross-collection knowledge access
- **Future Services**: Any new AI/ML services

## Key Benefits

1. **Simplicity**: One configuration for all services
2. **Consistency**: Same models and endpoints everywhere
3. **Reliability**: Simplified config reduces errors
4. **Maintainability**: Easy to update in one place

## Contact
For issues or questions, check the logs:
```bash
docker logs litellm
```