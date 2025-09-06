# LiteLLM Docker Networking Implementation Plan

## Executive Summary

This document provides a detailed step-by-step implementation plan to fix the LiteLLM routing issues where the container cannot reach external LLM Studio instances due to Docker network isolation. The plan implements the host networking solution identified as the most reliable approach in the research document.

## 1. Situation Assessment

### Current Configuration Analysis

**Docker Compose Setup:**
- LiteLLM container running on isolated `zoi-network`
- Configuration file: `D:\zoi\config\litellm\config_simple.yaml`
- Target endpoints:
  - RTX 5070 Ti: `192.168.8.135:1234` (qwen/qwen3-14b model)
  - RTX 3090: `192.168.8.241:1234` (qwen/qwen3-coder-30b model)
- Elysia service depends on LiteLLM for model access

**Current Issues:**
- Container isolation prevents access to host network LLM Studio instances
- "No deployments available" errors due to failed health checks
- Router cooldowns triggered by network connectivity failures

### Root Cause Confirmation

**Primary Cause:** Docker network isolation - containers on `zoi-network` cannot directly access host network services at `192.168.8.x:1234`

**Secondary Issues:**
- Health check timeouts due to network unreachability
- Router failures causing deployment unavailability
- Missing SSL/TLS configuration for local endpoints

### Risk Assessment

**High Risk:**
- Service disruption during implementation
- Elysia service dependency failure
- Potential data loss if health checks fail during transition

**Medium Risk:**
- Port conflicts with host networking mode
- Security implications of reduced container isolation
- Performance impact during switchover

**Low Risk:**
- Configuration rollback complexity
- Database connectivity issues (LiteLLM uses PostgreSQL via container network)

## 2. Solution Selection

### Chosen Approach: Host Network Mode with Hybrid Configuration

**Primary Solution:** Host networking for LiteLLM container to access external LLM Studio instances

**Justification:**
1. **Reliability:** Direct access to host network stack eliminates connectivity issues
2. **Simplicity:** Minimal configuration changes required
3. **Performance:** Native network performance without Docker proxy overhead
4. **Compatibility:** Works seamlessly with existing LLM Studio setup

### Alternative Approaches Considered

**Option A: Extra Hosts Configuration**
- **Pros:** Maintains container isolation
- **Cons:** Complex IP management, potential DNS issues
- **Rejected:** Higher complexity with marginal security benefit for local deployment

**Option B: Custom Bridge Network with Gateway**
- **Pros:** Modern Docker approach
- **Cons:** Platform-specific behavior, requires Docker 20.10+
- **Rejected:** Compatibility concerns and added complexity

### Trade-offs Analysis

**Security Trade-off:**
- **Lost:** Container network isolation
- **Gained:** Simplified network access and reduced attack surface on network stack

**Operational Trade-off:**
- **Lost:** Port isolation (potential conflicts)
- **Gained:** Direct debugging capabilities and simplified troubleshooting

**Performance Trade-off:**
- **Lost:** Minimal Docker network overhead
- **Gained:** Native network performance for AI model requests

## 3. Implementation Steps

### Phase 1: Backup and Preparation (5 minutes)

#### Step 1.1: Create Configuration Backup
```bash
# Navigate to core directory
cd D:\zoi\apps\core

# Create backup directory with timestamp
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp docker-compose.yml backups/$(date +%Y%m%d_%H%M%S)/
cp ../../config/litellm/config_simple.yaml backups/$(date +%Y%m%d_%H%M%S)/
```

#### Step 1.2: Verify Current Service Status
```bash
# Check current service status
docker-compose ps

# Test current LiteLLM health (expected to fail)
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/health || echo "Expected failure - current networking issue"

# Verify external LLM Studio endpoints are accessible from host
curl http://192.168.8.135:1234/v1/models
curl http://192.168.8.241:1234/v1/models
```

#### Step 1.3: Document Current Port Allocation
```bash
# Check for potential port conflicts
netstat -an | findstr ":4000"
netstat -an | findstr ":7010"
```

### Phase 2: LiteLLM Configuration Update (10 minutes)

#### Step 2.1: Update LiteLLM Configuration
**File:** `D:\zoi\config\litellm\config_simple.yaml`

**Changes Required:**
1. Add SSL verification disable
2. Increase health check timeouts
3. Configure router settings for better error handling

```yaml
# ============================================
# Zoi Simple LiteLLM Configuration (KISS)
# RTX 5070 Ti (ioz.zoi) + RTX 3090 (astra.zoi)
# Host Network Mode Configuration
# ============================================

# Basic settings only
general_settings:
  master_key: sk-wqn0xwq_vha4MVM2yzw
  default_model: zoi-coder
  telemetry: false
  json_logs: true

# Enhanced LiteLLM settings for host networking
litellm_settings:
  set_verbose: true
  drop_params: true
  ssl_verify: false  # Disable SSL verification for local endpoints
  request_timeout: 120  # Increase timeout for local inference
  background_health_checks: true  # Enable background health monitoring
  health_check_interval: 300  # Check every 5 minutes

# Core models only - no complexity
model_list:
  # RTX 5070 Ti - Fast coding model
  - model_name: zoi-coder
    litellm_params:
      custom_llm_provider: openai
      model: qwen/qwen3-14b
      api_base: http://192.168.8.135:1234/v1
      api_key: sk-no-key-required
    model_info:
      health_check_timeout: 30  # Increase timeout for local models

  # RTX 3090 - Advanced reasoning model  
  - model_name: zoi-planner
    litellm_params:
      custom_llm_provider: openai
      model: qwen/qwen3-coder-30b
      api_base: http://192.168.8.241:1234/v1
      api_key: sk-no-key-required
    model_info:
      health_check_timeout: 30

  # RTX 3090 - Embeddings model
  - model_name: zoi-embed
    litellm_params:
      custom_llm_provider: openai
      model: text-embedding-nomic-embed-text-v1.5
      api_base: http://192.168.8.241:1234/v1
      api_key: sk-no-key-required
    model_info:
      health_check_timeout: 30

  # Essential aliases only
  - model_name: gpt-3.5-turbo
    litellm_params:
      custom_llm_provider: openai
      model: qwen/qwen3-14b
      api_base: http://192.168.8.135:1234/v1
      api_key: sk-no-key-required

  - model_name: gpt-4
    litellm_params:
      custom_llm_provider: openai
      model: qwen/qwen3-coder-30b
      api_base: http://192.168.8.241:1234/v1
      api_key: sk-no-key-required

# Enhanced router settings to prevent "No deployments available" errors
router_settings:
  routing_strategy: simple
  default_model: zoi-coder
  num_retries: 2
  timeout: 120
  allowed_fails: 5  # Increase threshold
  cooldown_time: 60  # Seconds to wait after failures
  disable_cooldowns: false  # Keep cooldowns for failure isolation
```

### Phase 3: Docker Compose Update (5 minutes)

#### Step 3.1: Update LiteLLM Service Configuration
**File:** `D:\zoi\apps\core\docker-compose.yml`

**Changes Required:**
1. Change LiteLLM service to use host networking
2. Update port mapping
3. Add SSL environment variables
4. Update health check for host networking

**Original LiteLLM Service (lines 117-158):**
```yaml
  # 🚪 LiteLLM Router
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    container_name: litellm
    ports:
      - "${LITELLM_PORT:-7010}:4000"
    volumes:
      - ../../config/litellm/config_simple.yaml:/app/config.yaml:ro
      - ../../config/litellm/auto_router_config.json:/app/auto_router_config.json:ro
    environment:
      - LITELLM_CONFIG=/app/config.yaml
      - DATABASE_URL=postgresql://postgres:litellm_password123@postgres:5432/litellm
      - POSTGRES_PRISMA_URL=postgresql://postgres:litellm_password123@postgres:5432/litellm
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
      - LITELLM_SALT_KEY=${LITELLM_SALT_KEY}
      - STORE_MODEL_IN_DB=True
      - PORT=4000
      - LITELLM_LOG=INFO
    command: ["--config", "/app/config.yaml"]
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks: [zoi-network]
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "wget --quiet --tries=1 --timeout=5 -O /dev/null http://localhost:4000/health/readiness || exit 1"
        ]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.litellm.rule=Host(`litellm.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.litellm.entrypoints=web"
      - "traefik.http.services.litellm.loadbalancer.server.port=4000"
```

**Updated LiteLLM Service:**
```yaml
  # 🚪 LiteLLM Router (Host Network Mode for LLM Studio Access)
  litellm:
    image: ghcr.io/berriai/litellm:main-stable
    container_name: litellm
    network_mode: host  # Enable host networking for external LLM Studio access
    volumes:
      - ../../config/litellm/config_simple.yaml:/app/config.yaml:ro
      - ../../config/litellm/auto_router_config.json:/app/auto_router_config.json:ro
    environment:
      - LITELLM_CONFIG=/app/config.yaml
      # Update database URLs to use localhost instead of service names
      - DATABASE_URL=postgresql://postgres:litellm_password123@localhost:7063/litellm
      - POSTGRES_PRISMA_URL=postgresql://postgres:litellm_password123@localhost:7063/litellm
      - REDIS_HOST=localhost
      - REDIS_PORT=7064
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
      - LITELLM_SALT_KEY=${LITELLM_SALT_KEY}
      - STORE_MODEL_IN_DB=True
      - PORT=${LITELLM_PORT:-7010}  # Use environment port directly
      - LITELLM_LOG=INFO
      # SSL Configuration for local endpoints
      - SSL_VERIFY=false
      - REQUESTS_CA_BUNDLE=""
    command: ["--config", "/app/config.yaml", "--port", "${LITELLM_PORT:-7010}"]
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    # Remove networks directive for host mode
    healthcheck:
      test:
        [
          "CMD-SHELL",
          "wget --quiet --tries=1 --timeout=10 -O /dev/null http://localhost:${LITELLM_PORT:-7010}/health/readiness || exit 1"
        ]
      interval: 60s  # Increase interval for stability
      timeout: 15s   # Increase timeout
      retries: 5
      start_period: 45s  # Longer start period for host networking
    # Update Traefik labels for host networking
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.litellm.rule=Host(`litellm.${DOMAIN:-zoi.local}`)"
      - "traefik.http.routers.litellm.entrypoints=web"
      - "traefik.http.services.litellm.loadbalancer.server.port=${LITELLM_PORT:-7010}"
```

#### Step 3.2: Update Elysia Service Dependencies
**Changes Required:** Update Elysia environment variables to use localhost instead of container networking

**Original Elysia LiteLLM Configuration (lines 409-410):**
```yaml
      - MODEL_API_BASE=http://litellm:4000/v1
      - OPENAI_API_BASE=http://litellm:4000/v1
```

**Updated Elysia LiteLLM Configuration:**
```yaml
      - MODEL_API_BASE=http://localhost:7010/v1
      - OPENAI_API_BASE=http://localhost:7010/v1
```

### Phase 4: Service Deployment (10 minutes)

#### Step 4.1: Stop Affected Services
```bash
# Stop services that depend on LiteLLM
docker-compose stop elysia
docker-compose stop litellm

# Verify services are stopped
docker-compose ps | grep -E "(litellm|elysia)"
```

#### Step 4.2: Deploy Updated Configuration
```bash
# Pull latest LiteLLM image (if needed)
docker-compose pull litellm

# Start LiteLLM with new configuration
docker-compose up -d litellm

# Wait for LiteLLM to initialize (60 seconds)
echo "Waiting for LiteLLM initialization..."
sleep 60

# Check LiteLLM logs for startup issues
docker-compose logs litellm | tail -20
```

#### Step 4.3: Verify LiteLLM Functionality
```bash
# Test LiteLLM health endpoint
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/health

# Test model availability
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/v1/models

# Test specific model endpoint
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
     -H "Content-Type: application/json" \
     -d '{"model": "zoi-coder", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 50}' \
     http://localhost:7010/v1/chat/completions
```

#### Step 4.4: Start Dependent Services
```bash
# Start Elysia service
docker-compose up -d elysia

# Wait for Elysia initialization
sleep 30

# Verify all services are running
docker-compose ps
```

### Phase 5: Validation and Testing (15 minutes)

#### Step 5.1: Comprehensive Health Checks
```bash
# Test all critical endpoints
echo "Testing LiteLLM health..."
curl -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/health | jq .

echo "Testing available models..."
curl -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/v1/models | jq .

echo "Testing zoi-coder model..."
curl -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
     -H "Content-Type: application/json" \
     -d '{"model": "zoi-coder", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}' \
     http://localhost:7010/v1/chat/completions | jq .

echo "Testing zoi-planner model..."
curl -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
     -H "Content-Type: application/json" \
     -d '{"model": "zoi-planner", "messages": [{"role": "user", "content": "Say hello"}], "max_tokens": 10}' \
     http://localhost:7010/v1/chat/completions | jq .
```

#### Step 5.2: Test Elysia Integration
```bash
# Test Elysia health endpoint
curl -f http://localhost:7085/api/health

# Check Elysia logs for LiteLLM connectivity
docker-compose logs elysia | grep -i "litellm\|model\|api" | tail -10
```

#### Step 5.3: Performance Verification
```bash
# Monitor response times
time curl -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
          -H "Content-Type: application/json" \
          -d '{"model": "zoi-coder", "messages": [{"role": "user", "content": "Count to 5"}], "max_tokens": 50}' \
          http://localhost:7010/v1/chat/completions > /dev/null

# Check for any deployment cooldowns
curl -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/health | jq '.deployments'
```

## 4. Rollback Strategy

### Immediate Rollback Procedure (5 minutes)

If issues occur during implementation, execute the following rollback steps:

#### Step 4.1: Stop Services
```bash
docker-compose stop litellm elysia
```

#### Step 4.2: Restore Original Configuration
```bash
# Restore docker-compose.yml
cp backups/$(ls backups/ | tail -1)/docker-compose.yml ./

# Restore LiteLLM configuration
cp backups/$(ls backups/ | tail -1)/config_simple.yaml ../../config/litellm/
```

#### Step 4.3: Restart with Original Configuration
```bash
# Restart services with original configuration
docker-compose up -d litellm
sleep 60
docker-compose up -d elysia

# Verify rollback success
docker-compose ps
```

### Backup Procedures

**Automated Backup Script:**
```bash
#!/bin/bash
# save as: backup_config.sh
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp docker-compose.yml $BACKUP_DIR/
cp ../../config/litellm/config_simple.yaml $BACKUP_DIR/
echo "Backup created at: $BACKUP_DIR"
```

### Recovery Steps

**Complete System Recovery:**
1. Stop all services: `docker-compose down`
2. Remove containers: `docker-compose rm -f litellm elysia`
3. Restore configurations from backup
4. Rebuild and restart: `docker-compose up -d --build`

## 5. Validation Criteria

### Success Metrics

**Primary Success Criteria:**
- LiteLLM health endpoint returns 200 status
- All configured models (zoi-coder, zoi-planner, zoi-embed) are available
- Model inference requests complete successfully within 30 seconds
- No "No deployments available" errors in logs

**Performance Benchmarks:**
- Model response time < 30 seconds for simple queries
- Health check response time < 5 seconds
- Zero deployment cooldowns in router status

### Test Procedures

#### Functional Testing
```bash
# Test suite for validation
#!/bin/bash

echo "=== LiteLLM Host Network Validation Suite ==="

# 1. Health Check Test
echo "1. Testing health endpoint..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/health)
if [ "$HEALTH" = "200" ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed (HTTP $HEALTH)"
    exit 1
fi

# 2. Model Availability Test
echo "2. Testing model availability..."
MODELS=$(curl -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/v1/models | jq -r '.data[].id' | wc -l)
if [ "$MODELS" -ge "3" ]; then
    echo "✅ Models available: $MODELS"
else
    echo "❌ Insufficient models available: $MODELS"
    exit 1
fi

# 3. Model Inference Test
echo "3. Testing model inference..."
INFERENCE=$(curl -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
                 -H "Content-Type: application/json" \
                 -d '{"model": "zoi-coder", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}' \
                 http://localhost:7010/v1/chat/completions | jq -r '.choices[0].message.content')
if [ ! -z "$INFERENCE" ]; then
    echo "✅ Inference test passed: $INFERENCE"
else
    echo "❌ Inference test failed"
    exit 1
fi

# 4. Deployment Status Test
echo "4. Testing deployment status..."
COOLDOWNS=$(curl -s -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/health | jq '.deployments | length')
if [ "$COOLDOWNS" -gt "0" ]; then
    echo "✅ Active deployments: $COOLDOWNS"
else
    echo "❌ No active deployments"
    exit 1
fi

echo "✅ All validation tests passed!"
```

#### Integration Testing
```bash
# Elysia integration test
echo "Testing Elysia -> LiteLLM integration..."
ELYSIA_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:7085/api/health)
if [ "$ELYSIA_HEALTH" = "200" ]; then
    echo "✅ Elysia integration healthy"
else
    echo "⚠️  Elysia integration may have issues (HTTP $ELYSIA_HEALTH)"
fi
```

## 6. Dependencies and Considerations

### Impact on Other Services

#### Elysia Service Changes
**Required Updates:**
- Environment variable changes for LiteLLM API base URL
- Port references updated from container networking to localhost
- Health check dependencies may require adjustment

**Testing Required:**
- Elysia can successfully make requests to LiteLLM
- Model access through Elysia API endpoints
- Weaviate integration remains functional

#### Database Connectivity
**PostgreSQL Connection Changes:**
- LiteLLM must access PostgreSQL via host networking (localhost:7063)
- Connection pooling may be affected
- Health check timing may need adjustment

**Redis Connection Changes:**
- Redis access via localhost:7064 instead of container name
- Cache functionality verification required
- Session persistence testing needed

### Security Considerations

#### Network Security
**Reduced Isolation:**
- LiteLLM container now has direct host network access
- All host network services become accessible to container
- Firewall rules should be reviewed for additional restrictions

**Mitigation Strategies:**
- Host-based firewall rules to limit container access
- Network monitoring for unexpected connections
- Regular security audit of exposed services

#### API Security
**Authentication:**
- LiteLLM master key remains the primary authentication mechanism
- API key validation continues through standard OAuth flow
- Rate limiting and access controls remain in effect

### Performance Implications

#### Network Performance
**Expected Improvements:**
- Direct network access eliminates Docker proxy overhead
- Reduced latency for LLM inference requests
- Native network stack performance

**Potential Issues:**
- Host network port conflicts
- Shared network resources with host processes
- Network debugging complexity increased

#### Resource Management
**Memory Impact:**
- No additional memory overhead from host networking
- Container memory limits remain in effect
- Host network stack resources shared

**CPU Impact:**
- Reduced CPU overhead from network translation
- Direct hardware access for network operations
- Potential contention with host network processes

### Monitoring and Observability

#### Log Management
**LiteLLM Logs:**
- Container logs available via `docker-compose logs litellm`
- Host network activities logged separately
- Integration with existing log aggregation systems

**Health Monitoring:**
- Enhanced health check endpoints for network status
- Router deployment status monitoring
- Integration with existing monitoring stack (if available)

#### Alerting Considerations
**Key Metrics to Monitor:**
- LiteLLM health endpoint status
- Model response times
- Deployment availability status
- Connection failure rates to external LLM Studio instances

**Alert Thresholds:**
- Health check failures > 2 consecutive
- Model response time > 60 seconds
- Deployment cooldown activation
- Network connectivity loss to external endpoints

### Future Considerations

#### Scalability Impact
**Single Container Limitation:**
- Host networking prevents horizontal scaling of LiteLLM
- Load balancing must be handled at application level
- Consider service mesh solutions for production scale

**Migration Path:**
- Document path to production-ready networking solution
- Consider external load balancer for multiple LiteLLM instances
- Evaluate service mesh integration options

#### Maintenance Procedures
**Regular Health Checks:**
- Weekly validation of external LLM Studio connectivity
- Monthly review of network security configurations
- Quarterly assessment of performance metrics

**Update Procedures:**
- LiteLLM container updates require service restart
- External LLM Studio updates may require configuration changes
- Network configuration changes require full service restart

---

## Implementation Timeline

**Total Estimated Time:** 45 minutes

- **Phase 1 (Backup):** 5 minutes
- **Phase 2 (Configuration):** 10 minutes
- **Phase 3 (Docker Compose):** 5 minutes
- **Phase 4 (Deployment):** 10 minutes
- **Phase 5 (Validation):** 15 minutes

**Prerequisites:**
- Administrative access to Docker host
- Network connectivity to external LLM Studio instances
- Backup storage available for configuration files
- Testing tools available (curl, jq)

**Next Steps After Implementation:**
1. Monitor system performance for 24 hours
2. Document any additional configuration optimizations
3. Update monitoring dashboards to include new metrics
4. Plan for production-grade networking solution if needed

This implementation plan provides a comprehensive approach to resolving the LiteLLM networking issues while maintaining system reliability and providing clear rollback procedures.