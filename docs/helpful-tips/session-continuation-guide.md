# Session Continuation Guide for Future Claude Code Sessions

## 🎯 Quick Context Recovery

When starting a new session with Claude Code, use this guide to quickly get back up to speed on the Zoi AI infrastructure.

### Current System State ✅
- **LiteLLM**: Running in host network mode, routing to dual RTX GPUs
- **RTX 5070 Ti**: Fast coding model (zoi-coder, gpt-3.5-turbo) at 192.168.8.135:1234
- **RTX 3090**: Advanced reasoning (zoi-planner, gpt-4) + embeddings at 192.168.8.241:1234  
- **Weaviate**: Vector database with Elysia integration at localhost:7080
- **Elysia**: Agentic analysis platform at localhost:7085

### Key Breakthrough
**Problem Solved**: LiteLLM "No deployments available" error was caused by Docker network isolation preventing access to host-based LLM Studio instances.

**Solution Applied**: Host network mode for LiteLLM container with IP-based endpoint configuration.

## 🚀 Immediate Validation Commands

Start any new session with these commands to verify system health:

```bash
# 1. Check service status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Test LiteLLM routing to both GPUs
curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{"model": "zoi-coder", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'

curl -X POST http://localhost:7010/v1/chat/completions \
  -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" \
  -H "Content-Type: application/json" \
  -d '{"model": "zoi-planner", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'

# 3. Check available models
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/v1/models

# 4. Verify Weaviate collections
curl http://localhost:7080/v1/meta

# 5. Test Elysia health
curl http://localhost:7085/api/health
```

**Expected Results**: All commands should return success responses without "No deployments available" errors.

## 📁 Critical File Locations

### Configuration Files
```
D:\zoi\config\litellm\config_simple.yaml      # Main LiteLLM configuration
D:\zoi\apps\core\docker-compose.yml           # Service definitions
D:\zoi\SESSION_CONTEXT.md                     # Previous session context
```

### Backup & Research
```
D:\zoi\config\litellm\backups\                # Configuration backups
D:\zoi\docs\research\                         # Technical research documents  
D:\zoi\docs\helpful-tips\                     # This documentation
```

### Key Research Documents
```
D:\zoi\docs\research\litellm-llmstudio-networking.md       # Problem analysis
D:\zoi\docs\research\litellm-implementation-plan.md        # Solution plan
D:\zoi\docs\research\implementation-validation.md          # Validation results
```

## 🔑 Essential Information

### API Access
- **LiteLLM Master Key**: `sk-wqn0xwq_vha4MVM2yzw`
- **LiteLLM Endpoint**: `http://localhost:7010/v1`
- **LLM Studio Endpoints**: No authentication required (`sk-no-key-required`)

### Model Mappings
```
zoi-coder      → RTX 5070 Ti (192.168.8.135:1234) → qwen/qwen3-14b
zoi-planner    → RTX 3090 (192.168.8.241:1234)    → qwen/qwen3-coder-30b  
zoi-embed      → RTX 3090 (192.168.8.241:1234)    → text-embedding-nomic-embed-text-v1.5
gpt-3.5-turbo  → Alias to zoi-coder
gpt-4          → Alias to zoi-planner
```

### Network Configuration
- **LiteLLM**: Host network mode (network_mode: host)
- **Database**: localhost:7063 (PostgreSQL)
- **Redis**: localhost:7064
- **Direct GPU Access**: IP addresses instead of hostnames

## 🔧 Common Session Tasks

### Adding New Models
1. Update `config_simple.yaml` with new model definition
2. Restart LiteLLM: `docker-compose restart litellm`
3. Test new model: `curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/v1/models`

### Troubleshooting Workflow
1. Check service logs: `docker logs <service_name> --tail 20`
2. Test direct GPU connectivity (see validation commands above)
3. Verify configuration hasn't changed
4. Restart specific service if needed
5. Full system restart as last resort

### Performance Monitoring
```bash
# GPU utilization
nvidia-smi

# Container resources  
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Network latency to GPUs
ping 192.168.8.135  # RTX 5070 Ti
ping 192.168.8.241  # RTX 3090
```

## 📊 Success Criteria

A healthy system shows:
- ✅ 5 models available in LiteLLM (`/v1/models`)
- ✅ Both RTX GPUs responding via LiteLLM routing  
- ✅ Weaviate collections accessible
- ✅ Elysia can analyze data without errors
- ✅ No "No deployments available" messages
- ✅ Response times < 5 seconds for simple queries

## 🚨 Red Flags (Immediate Attention Needed)

- ❌ "No deployments available" errors → Check host networking and IP connectivity
- ❌ Empty model list → LiteLLM configuration issue, check config file
- ❌ Connection refused → Service not running or wrong port/IP
- ❌ Authentication errors → Missing or wrong API key
- ❌ Timeout errors → Check GPU availability and load

## 💡 Pro Tips for Future Sessions

### Before Making Changes
1. Always check current system state first
2. Create timestamped backup: `mkdir backups/$(date +%Y%m%d_%H%M%S)`
3. Document what you're trying to achieve
4. Test changes incrementally

### When Investigating Issues  
1. Start with the simplest test (health endpoints)
2. Work from outside-in (host → LiteLLM → GPUs)
3. Check logs chronologically (oldest errors first)
4. Compare current config to known working backup

### Communication Tips
- Always mention specific error messages
- Include relevant logs and command outputs
- Reference this documentation when describing the setup
- Note any recent changes or experiments

## 🔄 Quick Recovery Commands

If system is not working:
```bash
# Quick restart
docker-compose restart litellm elysia

# Full service restart
docker-compose down && docker-compose up -d

# Emergency reset (nuclear option)
docker-compose down --remove-orphans
docker system prune -f  
docker-compose up -d --build
```

## 📈 Optimization Opportunities

Future improvements to consider:
- Load balancing between GPUs
- Automatic model routing based on request complexity
- Performance monitoring and alerting
- Backup automation
- Health check automation
- Cost tracking and optimization

## 🎉 Success Stories

This setup successfully resolved:
1. **LiteLLM routing failures** → Host network mode solution
2. **Docker network isolation** → IP-based endpoint configuration  
3. **"No deployments available" errors** → Configuration simplification
4. **Dual GPU utilization** → Intelligent model mapping
5. **Elysia integration** → Weaviate collections working

The system now provides reliable access to both RTX GPUs through a unified LiteLLM API, supporting the full Zoi AI ecosystem.