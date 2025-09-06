# LiteLLM + Dual RTX GPU Setup Guide

## 🎯 Overview

This guide documents the successful configuration of LiteLLM with dual RTX GPUs for the Zoi AI infrastructure. This setup provides high-performance AI inference with intelligent model routing.

## 🖥️ Hardware Configuration

### RTX 5070 Ti (ioz.zoi.local:1234)
- **Purpose**: Fast coding and development tasks
- **Model**: Qwen/Qwen3-14B
- **Optimized for**: Speed and quick responses
- **LiteLLM Model**: `zoi-coder`
- **Alias**: `gpt-3.5-turbo`

### RTX 3090 (astra.zoi.local:1234)
- **Purpose**: Complex reasoning and embeddings
- **Chat Model**: Qwen/Qwen3-Coder-30B
- **Embedding Model**: text-embedding-nomic-embed-text-v1.5
- **Optimized for**: Maximum performance and capability
- **LiteLLM Models**: `zoi-planner`, `zoi-embed`
- **Alias**: `gpt-4`

## 🔧 Critical Configuration Details

### Docker Networking Solution
**Problem**: LiteLLM container cannot reach host-based LLM Studio instances due to Docker network isolation.

**Solution**: Host network mode for LiteLLM container
```yaml
litellm:
  image: ghcr.io/berriai/litellm:main-stable
  container_name: litellm
  network_mode: host  # CRITICAL: Enables direct host network access
```

### Database Connection Updates
When using host networking, update connection strings:
```yaml
environment:
  - DATABASE_URL=postgresql://postgres:litellm_password123@localhost:7063/litellm
  - REDIS_HOST=localhost
  - REDIS_PORT=7064
```

### LiteLLM Configuration (config_simple.yaml)
```yaml
# Use IP addresses instead of hostnames for reliability
model_list:
  - model_name: zoi-coder
    litellm_params:
      custom_llm_provider: openai
      model: qwen/qwen3-14b
      api_base: http://192.168.8.135:1234/v1  # Direct IP
      api_key: sk-no-key-required
      
  - model_name: zoi-planner
    litellm_params:
      custom_llm_provider: openai
      model: qwen/qwen3-coder-30b
      api_base: http://192.168.8.241:1234/v1  # Direct IP
      api_key: sk-no-key-required

# Enhanced settings for local inference
litellm_settings:
  set_verbose: true
  drop_params: true
  ssl_verify: false  # Disable SSL for local endpoints
  request_timeout: 120  # Increase timeout for local inference
  
router_settings:
  routing_strategy: simple
  num_retries: 2
  timeout: 120
  allowed_fails: 5  # Higher threshold for local inference
```

## 🚀 Quick Validation Commands

### Test Direct GPU Connectivity
```bash
# RTX 5070 Ti Direct Test
curl -X POST http://192.168.8.135:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen3-14b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'

# RTX 3090 Direct Test
curl -X POST http://192.168.8.241:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen3-coder-30b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'
```

### Test LiteLLM Routing
```bash
# Test RTX 5070 Ti via LiteLLM
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{"model": "zoi-coder", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 20}'

# Test RTX 3090 via LiteLLM
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{"model": "zoi-planner", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 20}'

# Test Embeddings
curl -X POST http://localhost:7010/v1/embeddings \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{"model": "zoi-embed", "input": "test text"}'
```

### Check Service Health
```bash
# LiteLLM Health
curl http://localhost:7010/health

# Available Models
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/v1/models

# Startup Logs
docker logs litellm --tail 30
```

## 🐛 Common Issues & Solutions

### "No deployments available" Error
**Cause**: LiteLLM can't reach the LLM Studio endpoints
**Solution**: 
1. Verify host network mode is enabled
2. Check IP addresses are correct
3. Test direct connectivity to endpoints
4. Restart LiteLLM container

### Health Check Failures
**Cause**: SSL verification or timeout issues
**Solution**:
```yaml
litellm_settings:
  ssl_verify: false
  request_timeout: 120
```

### Container DNS Issues
**Cause**: Hostnames not resolving in Docker
**Solution**: Use direct IP addresses instead of hostnames

### Database Connection Failures
**Cause**: Database connection strings still using container names
**Solution**: Update to localhost with correct ports when using host networking

## 🔄 Restart Sequence

When making configuration changes:
```bash
# 1. Stop services
docker-compose down litellm elysia

# 2. Rebuild with new config
docker-compose up -d --build litellm

# 3. Wait for startup (check logs)
docker logs litellm --tail 15

# 4. Start dependent services
docker-compose up -d elysia

# 5. Validate functionality
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/v1/models
```

## 📊 Performance Optimization

### Model Selection Strategy
- **Fast tasks**: Use `zoi-coder` (RTX 5070 Ti)
- **Complex reasoning**: Use `zoi-planner` (RTX 3090)
- **Vector operations**: Use `zoi-embed` (RTX 3090)
- **OpenAI compatibility**: Use `gpt-3.5-turbo` or `gpt-4` aliases

### Load Balancing
- RTX 5070 Ti optimized for speed and throughput
- RTX 3090 optimized for quality and complex tasks
- Automatic failover between models if needed

## 🔐 Security Considerations

### API Keys
- Master key: `sk-wqn0xwq_vha4MVM2yzw`
- LLM Studio endpoints: `sk-no-key-required`

### Network Security
- Host networking reduces container isolation
- Only enable for trusted local networks
- Consider firewall rules for production

## 📁 Key Files

### Configuration Files
- `D:\zoi\config\litellm\config_simple.yaml` - Main LiteLLM config
- `D:\zoi\apps\core\docker-compose.yml` - Service definitions

### Backup Location
- `D:\zoi\config\litellm\backups\` - Configuration backups

### Research Documentation
- `D:\zoi\docs\research\litellm-llmstudio-networking.md` - Technical research
- `D:\zoi\docs\research\litellm-implementation-plan.md` - Implementation plan
- `D:\zoi\docs\research\implementation-validation.md` - Validation results

## ✅ Success Indicators

When everything is working correctly:
1. ✅ LiteLLM shows 5 models in `/v1/models` endpoint
2. ✅ Both RTX GPUs respond via LiteLLM routing
3. ✅ Elysia can analyze Weaviate collections
4. ✅ No "No deployments available" errors
5. ✅ Health checks pass consistently

## 🎉 Final Notes

This configuration provides:
- **Dual GPU utilization**: Both RTX cards working simultaneously  
- **Intelligent routing**: Fast vs. powerful model selection
- **OpenAI compatibility**: Drop-in replacement for OpenAI API
- **High reliability**: Host networking eliminates connectivity issues
- **Performance optimization**: Hardware-matched workload distribution

The key breakthrough was using host network mode to overcome Docker's network isolation while maintaining service integration through localhost connections.