# Langflow + LiteLLM Configuration Guide

## 🎯 Overview
Your Langflow instance at http://localhost:7070 is now configured to use your local LiteLLM instance for all AI model interactions. This provides:

- **Cost Savings**: All API calls route to your local GPU models
- **Privacy**: No data leaves your infrastructure  
- **Performance**: Direct access to your RTX 5070 Ti
- **Compatibility**: Full OpenAI API compatibility

## 🔧 Configuration Settings

### OpenAI Component Configuration
When adding OpenAI components in Langflow, use these settings:

```
Base URL: http://litellm:4000/v1
API Key: sk-wqn0xwq_vha4MVM2yzw
```

### Available Models

#### Claude Models (Hijacked to Local)
- **claude-3-5-sonnet-20241022** → `ollama/qwen2.5:7b`
  - Best for: Complex reasoning, analysis, strategic thinking
  - Temperature: 0.2 (balanced creativity)
  - Max Tokens: 8192

- **claude-3-sonnet-20240229** → `ollama/qwen2.5-coder:7b-instruct`  
  - Best for: Code generation, technical documentation
  - Temperature: 0.15 (precise responses)
  - Max Tokens: 6144

- **claude-3-opus-20240229** → `openai/Qwen/Qwen3-0.6B` (via vLLM)
  - Best for: Fast responses, quick tasks
  - Temperature: 0.25 (creative responses)
  - Max Tokens: 8192

- **claude-3-haiku-20240307** → `ollama/qwen2.5-coder:7b-instruct`
  - Best for: Quick coding tasks, simple queries
  - Temperature: 0.1 (precise, fast)
  - Max Tokens: 4096

#### GPT Models (Hijacked to Local)
- **gpt-3.5-turbo** → `openai/Qwen/Qwen3-0.6B` (via vLLM)
  - Best for: Fast development tasks, code snippets
  - Temperature: 0.1 (precise code generation)
  - Max Tokens: 4096

- **gpt-4** → `ollama/qwen2.5:7b`
  - Best for: Complex problem solving, architecture
  - Temperature: 0.15 (balanced precision/creativity)
  - Max Tokens: 6144

#### OpenAI GPT OSS Models (New!)
- **gpt-oss** → `ollama/gpt-oss` (OpenAI's open-source GPT model)
  - Best for: General-purpose tasks, balanced performance
  - Temperature: 0.2 (moderate creativity)
  - Max Tokens: 8192
  - Size: 13GB model with excellent capabilities

- **gpt-oss-creative** → `ollama/gpt-oss`
  - Best for: Creative writing, brainstorming, artistic tasks
  - Temperature: 0.7 (high creativity)
  - Max Tokens: 8192

- **gpt-oss-precise** → `ollama/gpt-oss`
  - Best for: Technical documentation, factual responses
  - Temperature: 0.1 (very precise)
  - Max Tokens: 6144

- **gpt-4-oss** → `ollama/gpt-oss`
  - Best for: GPT-4 replacement with better local performance
  - Temperature: 0.15 (GPT-4 compatible)
  - Max Tokens: 8192

- **gpt-4o-mini-oss** → `ollama/gpt-oss`
  - Best for: Quick tasks, mini-style responses
  - Temperature: 0.1 (fast and precise)
  - Max Tokens: 4096

## 🚀 Quick Start Workflows

### 1. Simple Chat Flow
1. Add **OpenAI** component
2. Set Base URL: `http://litellm:4000/v1`
3. Set API Key: `sk-zoi-master-key-2024-secure`
4. Choose model: `claude-3-5-sonnet-20241022`
5. Add **Chat Input** and **Chat Output** components
6. Connect: Chat Input → OpenAI → Chat Output

### 2. Code Generation Flow
1. Add **OpenAI** component
2. Configure with LiteLLM settings (above)
3. Choose model: `claude-3-sonnet-20240229` (coding specialist)
4. Add **Text Input** for requirements
5. Add **Text Output** for generated code
6. Connect: Text Input → OpenAI → Text Output

### 3. Multi-Model Comparison Flow
1. Add multiple **OpenAI** components
2. Configure each with different models:
   - Component 1: `claude-3-5-sonnet-20241022` (reasoning)
   - Component 2: `claude-3-sonnet-20240229` (coding)
   - Component 3: `gpt-4` (alternative perspective)
3. Use same input for all models
4. Compare outputs

## 📊 Monitoring & Tracking

All requests through Langflow are automatically tracked in your PostgreSQL database:

### View Usage Statistics
```sql
-- Connect to database
docker exec -it litellm-postgres psql -U postgres -d litellm

-- View recent requests
SELECT model, user_id, total_tokens, cost, created_at 
FROM request_logs 
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

### Cost Analysis
```sql
-- Cost by model
SELECT model, COUNT(*) as requests, SUM(cost) as total_cost
FROM request_logs 
GROUP BY model 
ORDER BY total_cost DESC;
```

## 🔍 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure LiteLLM is running: `docker ps | grep litellm`
   - Check health: `curl http://localhost:7010/health`

2. **Authentication Error**
   - Verify API key: `sk-zoi-master-key-2024-secure`
   - Check LiteLLM logs: `docker logs litellm`

3. **Model Not Found**
   - List available models: `curl -H "Authorization: Bearer sk-zoi-master-key-2024-secure" http://localhost:7010/v1/models`
   - Ensure Ollama models are loaded: `docker exec ollama ollama list`

4. **Slow Responses**
   - Check GPU usage: `nvidia-smi`
   - Monitor container resources: `docker stats`

### Test Connection
```bash
# Test from host
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-zoi-master-key-2024-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

## 🎯 Best Practices

1. **Model Selection**
   - Use `claude-3-5-sonnet-20241022` for complex reasoning
   - Use `claude-3-sonnet-20240229` for code generation
   - Use `claude-3-opus-20240229` for fast responses
   - Use `gpt-3.5-turbo` for quick development tasks

2. **Performance Optimization**
   - Set appropriate `max_tokens` limits
   - Use lower `temperature` for deterministic outputs
   - Monitor GPU memory usage

3. **Cost Management**
   - All costs are simulated (no real charges)
   - Use cost tracking for resource planning
   - Monitor token usage patterns

## 🎉 Success!

Your Langflow is now fully integrated with your local LiteLLM infrastructure:

- ✅ **Privacy**: All processing stays local
- ✅ **Cost**: No external API charges
- ✅ **Performance**: Direct GPU access
- ✅ **Compatibility**: Full OpenAI API support
- ✅ **Tracking**: Complete usage analytics
- ✅ **Flexibility**: Multiple model options

Start building your AI workflows at: http://localhost:7070
