# LiteLLM with LLM Studio Docker Networking Configuration

## Executive Summary

This document provides comprehensive guidance for configuring LiteLLM in Docker containers to access LLM Studio (LM Studio) instances running on host networks. The research addresses the common "No deployments available" error and Docker networking challenges when LiteLLM containers need to communicate with host-based LLM inference services.

## Problem Analysis

### Current Environment
- **LiteLLM**: Running in Docker container on `zoi-network`
- **LLM Studio Instances**: 
  - RTX 5070 Ti: `192.168.8.135:1234`
  - RTX 3090: `192.168.8.241:1234`
- **Issue**: Container gets "No deployments available" errors despite direct host connections working perfectly

### Root Causes Identified

1. **Docker Network Isolation**: Containers on custom networks cannot directly access host network services
2. **Router Health Check Failures**: LiteLLM router cooldowns triggered by connectivity issues
3. **SSL/TLS Verification**: Default SSL verification may interfere with local endpoints
4. **Container-to-Host Communication**: Docker containers need special configuration to reach host services

## LLM Studio (LM Studio) Integration

### OpenAI API Compatibility
LM Studio provides OpenAI-compatible endpoints:
- **Base URL**: `http://localhost:1234/v1` (default)
- **Endpoints**: `/v1/models`, `/v1/chat/completions`, `/v1/embeddings`
- **Authentication**: No API key required (use placeholder like "lm-studio")
- **Model Format**: Uses loaded model names directly

### Supported Parameters
- `model`, `temperature`, `max_tokens`, `top_p`, `top_k`
- `messages`, `stream`, `stop`, `presence_penalty`, `frequency_penalty`
- `logit_bias`, `repeat_penalty`, `seed`

## Docker Networking Solutions

### Solution 1: Host Network Mode (Recommended)

**Pros:**
- Direct access to host network stack
- No network isolation issues
- Simplest configuration
- Native performance

**Cons:**
- Reduced container isolation
- Port conflicts possible
- Security considerations

**Implementation:**

```yaml
# docker-compose.yml
version: '3.8'
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    network_mode: host  # Use host networking
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    environment:
      - LITELLM_MASTER_KEY=sk-1234
    command: ["--config", "/app/config.yaml", "--detailed_debug"]
```

```bash
# Docker run command
docker run \
  --network host \
  -v $(pwd)/litellm_config.yaml:/app/config.yaml \
  -e LITELLM_MASTER_KEY=sk-1234 \
  ghcr.io/berriai/litellm:main-latest \
  --config /app/config.yaml --detailed_debug
```

### Solution 2: Extra Hosts Configuration

**Pros:**
- Maintains container isolation
- Flexible hostname mapping
- Works with custom networks

**Cons:**
- Requires IP address management
- More complex configuration

**Implementation:**

```yaml
# docker-compose.yml
version: '3.8'
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    networks:
      - zoi-network
    extra_hosts:
      - "llm-studio-5070ti:192.168.8.135"
      - "llm-studio-3090:192.168.8.241"
      - "host.docker.internal:host-gateway"  # For Docker Desktop
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    environment:
      - LITELLM_MASTER_KEY=sk-1234
    command: ["--config", "/app/config.yaml", "--detailed_debug"]
```

### Solution 3: Custom Bridge Network with Host Gateway

**Pros:**
- Modern Docker approach
- Automatic host gateway resolution
- Works across platforms

**Cons:**
- Requires Docker 20.10+
- Platform-specific behavior

**Implementation:**

```yaml
# docker-compose.yml
version: '3.8'
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    networks:
      - zoi-network
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    environment:
      - LITELLM_MASTER_KEY=sk-1234
    command: ["--config", "/app/config.yaml", "--detailed_debug"]
```

## LiteLLM Configuration

### Complete config.yaml Example

```yaml
model_list:
  # RTX 5070 Ti Instance
  - model_name: llama-5070ti
    litellm_params:
      model: openai/llama2-7b-chat  # Use openai/ prefix for compatibility
      api_base: http://192.168.8.135:1234/v1  # Direct IP (host mode)
      # api_base: http://llm-studio-5070ti:1234/v1  # With extra_hosts
      api_key: "lm-studio"  # Placeholder
    model_info:
      health_check_timeout: 30  # Increase timeout for local models
      
  # RTX 3090 Instance  
  - model_name: llama-3090
    litellm_params:
      model: openai/llama2-13b-chat
      api_base: http://192.168.8.241:1234/v1  # Direct IP (host mode)
      # api_base: http://llm-studio-3090:1234/v1  # With extra_hosts
      api_key: "lm-studio"
    model_info:
      health_check_timeout: 30
      
  # Load balanced group
  - model_name: llama-balanced
    litellm_params:
      model: openai/llama2-chat
      api_base: http://192.168.8.135:1234/v1
      api_key: "lm-studio"
  - model_name: llama-balanced
    litellm_params:
      model: openai/llama2-chat  
      api_base: http://192.168.8.241:1234/v1
      api_key: "lm-studio"

# Router settings to prevent "No deployments available" errors
router_settings:
  routing_strategy: simple-shuffle  # or least-busy
  model_group_alias: {"llama": "llama-balanced"}
  allowed_fails: 5  # Increase threshold
  cooldown_time: 60  # Seconds to wait after failures
  disable_cooldowns: false  # Keep cooldowns for failure isolation
  
# General settings
litellm_settings:
  ssl_verify: false  # Disable SSL verification for local endpoints
  request_timeout: 120  # Increase timeout for local inference
  background_health_checks: true  # Enable background health monitoring
  health_check_interval: 300  # Check every 5 minutes
  
general_settings:
  master_key: sk-1234
  database_url: null  # Disable database for simplicity
```

### Health Check Configuration

```yaml
# Enhanced health check settings
litellm_settings:
  background_health_checks: true
  health_check_interval: 300  # 5 minutes
  health_check_timeout: 60   # Per-model timeout
  
# Per-model health check overrides
model_list:
  - model_name: llama-5070ti
    litellm_params:
      model: openai/llama2-7b-chat
      api_base: http://192.168.8.135:1234/v1
      api_key: "lm-studio"
    model_info:
      health_check_timeout: 30  # Override global timeout
      mode: "embedding"  # For embedding models
```

## Troubleshooting "No Deployments Available" Error

### Router Cooldown Issues

The most common cause is router cooldowns triggered by failed health checks:

```yaml
router_settings:
  # Disable cooldowns temporarily for debugging
  disable_cooldowns: true
  
  # Or adjust cooldown parameters
  allowed_fails: 10  # Allow more failures before cooldown
  cooldown_time: 30  # Reduce cooldown duration
  
  # Enable detailed health check responses
  health_check_details: true
```

### Health Check Debugging

Test health checks manually:

```bash
# Check LiteLLM health
curl -H "Authorization: Bearer sk-1234" http://localhost:4000/health

# Check LM Studio directly
curl http://192.168.8.135:1234/v1/models
curl http://192.168.8.241:1234/v1/models

# Test from container
docker exec -it litellm-container curl http://192.168.8.135:1234/v1/models
```

### SSL/TLS Issues

Disable SSL verification for local endpoints:

```yaml
litellm_settings:
  ssl_verify: false
  ssl_cert_file: null
  ssl_check_hostname: false
```

## Best Practices and Recommendations

### Production Recommendations

1. **Use Host Network Mode**: Simplest and most reliable for local deployment
2. **Implement Health Checks**: Configure appropriate timeouts for inference latency
3. **Monitor Router State**: Use `/health` endpoint to track deployment availability
4. **Configure Cooldowns**: Balance between failure isolation and availability
5. **SSL Configuration**: Disable SSL verification for trusted local networks

### Development Recommendations

1. **Start Simple**: Use host network mode for initial testing
2. **Enable Debug Logging**: Use `--detailed_debug` flag
3. **Test Connectivity**: Verify direct endpoint access before configuring LiteLLM
4. **Monitor Logs**: Watch for connection timeouts and SSL errors

### Security Considerations

1. **Network Isolation**: Host mode reduces container isolation
2. **API Keys**: Use environment variables even for local deployments  
3. **SSL/TLS**: Only disable in trusted local environments
4. **Firewall Rules**: Configure host firewall for container access

## Implementation Steps

### Step 1: Verify LM Studio Configuration

```bash
# Test LM Studio endpoints directly
curl http://192.168.8.135:1234/v1/models
curl http://192.168.8.241:1234/v1/models

# Verify model loading
curl http://192.168.8.135:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "llama2-7b-chat", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}'
```

### Step 2: Update Docker Compose

Choose networking strategy and update `docker-compose.yml`:

```yaml
# Option A: Host networking (recommended)
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    network_mode: host
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    command: ["--config", "/app/config.yaml", "--detailed_debug", "--port", "8080"]

# Option B: Extra hosts
services:
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    networks:
      - zoi-network
    extra_hosts:
      - "llm-studio-5070ti:192.168.8.135"
      - "llm-studio-3090:192.168.8.241"
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    ports:
      - "8080:4000"
    command: ["--config", "/app/config.yaml", "--detailed_debug"]
```

### Step 3: Configure LiteLLM

Create `litellm_config.yaml` with appropriate networking configuration and test:

```bash
# Restart services
docker-compose down
docker-compose up -d litellm

# Test LiteLLM health
curl -H "Authorization: Bearer sk-1234" http://localhost:8080/health

# Test model routing
curl -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  http://localhost:8080/v1/chat/completions \
  -d '{"model": "llama-5070ti", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Step 4: Monitor and Debug

```bash
# Monitor LiteLLM logs
docker-compose logs -f litellm

# Check deployment availability
curl -H "Authorization: Bearer sk-1234" http://localhost:8080/health

# List available models
curl -H "Authorization: Bearer sk-1234" http://localhost:8080/v1/models
```

## Common Issues and Solutions

### Issue: Connection Refused

**Symptom**: `Connection refused to 192.168.8.x:1234`
**Solution**: Use host networking mode or verify extra_hosts configuration

### Issue: SSL Verification Failed

**Symptom**: `SSL certificate verification failed`
**Solution**: Set `ssl_verify: false` in litellm_settings

### Issue: Health Check Timeouts

**Symptom**: Health checks timing out, models going into cooldown
**Solution**: Increase `health_check_timeout` and `request_timeout`

### Issue: Models Not Loading

**Symptom**: `/v1/models` returns empty list
**Solution**: Verify LM Studio has models loaded and accessible

## Monitoring and Observability

### Health Check Monitoring

```bash
# Continuous health monitoring
watch -n 30 'curl -s -H "Authorization: Bearer sk-1234" http://localhost:8080/health | jq'

# Check specific model health
curl -H "Authorization: Bearer sk-1234" \
  "http://localhost:8080/health?model=llama-5070ti"
```

### Log Analysis

```bash
# Filter for networking errors
docker-compose logs litellm 2>&1 | grep -E "(Connection|SSL|timeout|deployment)"

# Monitor health check failures
docker-compose logs litellm 2>&1 | grep -E "(health_check|cooldown)"
```

## Performance Optimization

### Load Balancing Configuration

```yaml
router_settings:
  routing_strategy: "least-busy"  # Route to least busy instance
  model_group_alias: {"llama": "llama-balanced"}
  num_retries: 2
  retry_delay: 1
  timeout: 120
```

### Caching Configuration

```yaml
# Optional Redis caching for multi-container deployments
cache:
  type: "redis"
  host: "localhost"
  port: 6379
  password: null
```

## Conclusion

The recommended approach for resolving Docker networking issues with LiteLLM and LLM Studio is to use **host network mode** for local deployments. This provides the most reliable connectivity while maintaining acceptable security for local development environments. For production deployments requiring container isolation, use the extra_hosts configuration with proper IP address management and health check tuning.

The "No deployments available" error is typically caused by router cooldowns triggered by network connectivity issues, which can be resolved through proper Docker networking configuration and health check parameter tuning.