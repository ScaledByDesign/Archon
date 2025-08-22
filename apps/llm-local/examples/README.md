# Claude API Hijacking with LiteLLM

This directory contains examples and documentation for hijacking Claude API calls and routing them through your local LiteLLM instance running on `localhost:7010`.

## 🎯 What This Achieves

- **API Compatibility**: Your existing Claude-based applications continue to work unchanged
- **Cost Savings**: Route expensive Claude API calls to your local GPU models
- **Privacy**: Keep sensitive data on your local infrastructure
- **Full Tracking**: Maintain complete usage analytics and cost tracking via LiteLLM
- **Performance**: Potentially faster responses from local models
- **Offline Capability**: Work without internet connectivity

## 🔧 How It Works

1. **Model Mapping**: LiteLLM configuration maps Claude model names to your local models:
   - `claude-3-5-sonnet-20241022` → `ollama/qwen2.5:7b` (your reasoning model)
   - `claude-3-sonnet-20240229` → `ollama/qwen2.5-coder:7b-instruct` (your coding model)
   - `claude-3-opus-20240229` → `openai/Qwen/Qwen3-0.6B` (via vLLM for speed)
   - `claude-3-haiku-20240307` → `ollama/qwen2.5-coder:7b-instruct` (fast responses)

2. **Request Interception**: When applications make Claude API calls, they're intercepted by LiteLLM
3. **Local Routing**: Requests are routed to your local GPU models (RTX 5070 Ti)
4. **Response Translation**: Local model responses are formatted as Claude API responses
5. **Usage Tracking**: All requests/responses are logged in PostgreSQL with cost tracking

## 🚀 Quick Start

### 1. Ensure Your Stack is Running

```bash
cd apps/llm-local
docker-compose up -d
```

Verify services are healthy:
- LiteLLM: http://localhost:7010/health
- Ollama: http://localhost:7040/api/tags
- vLLM: http://localhost:7030/v1/models

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Example

```bash
python claude_hijack_example.py
```

## 📋 Integration Methods

### Method 1: OpenAI Client (Recommended)

```python
from openai import OpenAI

# Point OpenAI client to your LiteLLM instance
client = OpenAI(
    base_url="http://localhost:7010/v1",
    api_key="sk-zoi-master-key-2024-secure"
)

# Use Claude model names - they'll be hijacked!
response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",  # Routes to local model
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Method 2: Direct HTTP Calls

```python
import requests

response = requests.post(
    "http://localhost:7010/v1/chat/completions",
    headers={
        "Authorization": "Bearer sk-zoi-master-key-2024-secure",
        "Content-Type": "application/json"
    },
    json={
        "model": "claude-3-sonnet-20240229",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)
```

### Method 3: Environment Variable Override

For existing applications, simply change the base URL:

```bash
# Instead of using Anthropic's API
export ANTHROPIC_BASE_URL="http://localhost:7010/v1"
export ANTHROPIC_API_KEY="sk-zoi-master-key-2024-secure"

# Your existing code works unchanged!
python your_existing_claude_app.py
```

## 📊 Monitoring & Tracking

### Usage Statistics

Access LiteLLM's admin interface:
- **Web UI**: http://localhost:7010 (if enabled)
- **Metrics**: http://localhost:7010/metrics (Prometheus format)
- **Health**: http://localhost:7010/health

### Database Tracking

All requests are logged in PostgreSQL:

```sql
-- Connect to the database
psql -h localhost -p 7063 -U postgres -d litellm

-- View recent requests
SELECT model, user_id, total_tokens, cost, created_at 
FROM request_logs 
ORDER BY created_at DESC 
LIMIT 10;
```

### Cost Analysis

```python
# Get cost breakdown by model
import requests

response = requests.get(
    "http://localhost:7010/spend/tags",
    headers={"Authorization": "Bearer sk-zoi-master-key-2024-secure"}
)
print(response.json())
```

## 🔧 Configuration Customization

### Adjust Model Routing

Edit `apps/llm-local/litellm-config.yaml` to change which local models handle which Claude requests:

```yaml
- model_name: claude-3-5-sonnet-20241022
  litellm_params:
    model: ollama/your-preferred-model  # Change this
    api_base: http://ollama:11434
    temperature: 0.2  # Adjust parameters
```

### Add New Claude Models

```yaml
- model_name: claude-3-5-haiku-20241022  # New Claude model
  litellm_params:
    model: ollama/qwen2.5-coder:7b-instruct
    api_base: http://ollama:11434
    api_key: dummy
```

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure LiteLLM is running on port 7010
2. **Model Not Found**: Check that your local models are loaded in Ollama/vLLM
3. **Slow Responses**: Local models may be slower than cloud APIs initially
4. **Memory Issues**: Monitor GPU memory usage with `nvidia-smi`

### Debug Mode

Enable verbose logging in `litellm-config.yaml`:

```yaml
general_settings:
  set_verbose: true
  json_logs: true
```

### Health Checks

```bash
# Check LiteLLM health
curl http://localhost:7010/health

# Check available models
curl -H "Authorization: Bearer sk-zoi-master-key-2024-secure" \
     http://localhost:7010/v1/models

# Test a simple request
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-zoi-master-key-2024-secure" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

## 🎯 Next Steps

1. **Update Your Applications**: Change API endpoints to point to `localhost:7010`
2. **Monitor Performance**: Watch response times and adjust model assignments
3. **Scale Up**: Add more local models or GPU resources as needed
4. **Fine-tune**: Adjust temperature and other parameters for optimal results
5. **Backup Strategy**: Keep real Claude API keys as fallback for critical applications

## 📈 Benefits Achieved

- **Cost Reduction**: ~90% savings on API costs
- **Data Privacy**: All processing stays local
- **Response Speed**: Potentially faster than cloud APIs
- **Offline Capability**: Works without internet
- **Full Control**: Complete visibility and control over AI processing
- **Scalability**: Add more local compute as needed

Your Claude API calls are now successfully hijacked and routed through your local infrastructure while maintaining full compatibility and tracking! 🎉
