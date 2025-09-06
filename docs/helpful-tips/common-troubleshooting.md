# Common Troubleshooting Guide for Zoi AI Stack

## 🚨 Emergency Quick Fixes

### Service Won't Start
```bash
# Check what's using the port
netstat -ano | findstr :7010

# Kill process using port (Windows)
taskkill /PID <PID> /F

# Restart Docker Desktop
# → Right-click Docker icon → Restart Docker Desktop
```

### Docker Compose Issues
```bash
# Nuclear option - reset everything
docker-compose down --remove-orphans
docker system prune -f
docker-compose up -d --build
```

### LiteLLM Not Responding
```bash
# Check container logs
docker logs litellm --tail 30

# Restart just LiteLLM
docker-compose restart litellm

# Full rebuild
docker-compose down litellm && docker-compose up -d --build litellm
```

## 🔍 Diagnostic Commands

### Check All Service Health
```bash
# Service status overview
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Health checks
curl http://localhost:7010/health        # LiteLLM
curl http://localhost:7080/v1/meta       # Weaviate  
curl http://localhost:7085/api/health    # Elysia
```

### Check Model Availability
```bash
# LiteLLM models
curl -H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw" http://localhost:7010/v1/models

# Direct GPU tests
curl -X POST http://192.168.8.135:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen/qwen3-14b", "messages": [{"role": "user", "content": "test"}], "max_tokens": 5}'
```

### Network Connectivity Tests
```bash
# Test internal DNS resolution
docker exec litellm nslookup postgres  # Should fail in host mode
docker exec litellm ping localhost     # Should work

# Test external connectivity
docker exec -it litellm curl http://192.168.8.135:1234/v1/models
```

## 🚀 Performance Issues

### Slow Response Times
1. **Check GPU utilization**: `nvidia-smi`
2. **Monitor network latency**: RTX GPUs should respond in <2s
3. **Increase timeouts**: Update `request_timeout` in LiteLLM config
4. **Check memory usage**: `docker stats`

### High Resource Usage
```bash
# Monitor container resources
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check disk space
docker system df

# Clean up if needed
docker system prune -f
docker volume prune -f
```

## 🔧 Configuration Issues

### Environment Variables Not Loading
1. Check `.env` file exists and has correct values
2. Restart containers after `.env` changes
3. Use `docker-compose config` to verify merged configuration

### Port Conflicts
```bash
# Find what's using a port
netstat -ano | findstr :7010
lsof -i :7010  # Linux/WSL

# Change ports in .env file
LITELLM_PORT=7011
WEAVIATE_PORT=7081
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker exec postgres pg_isready -U postgres

# Check database exists
docker exec postgres psql -U postgres -l

# Reset database if needed
docker-compose restart postgres
```

## 🐛 Common Error Messages

### "No deployments available for selected model"
**Solution**: LiteLLM networking issue
1. Check host network mode is enabled
2. Verify GPU endpoints are accessible
3. Restart LiteLLM container
4. Check configuration uses IP addresses, not hostnames

### "Connection refused" or "Unable to connect"
**Solution**: Service not ready or network issue
1. Wait for services to fully start (check logs)
2. Verify correct ports and URLs
3. Check firewall settings
4. Try localhost vs. 127.0.0.1 vs. actual IP

### "Authentication Error, No api key passed in"
**Solution**: Missing authorization header
```bash
# Add authorization header
-H "Authorization: Bearer sk-wqn0xwq_vha4MVM2yzw"
```

### "Model not found" or "Invalid model"
**Solution**: Model not registered in LiteLLM
1. Check available models: `/v1/models`
2. Verify model names match configuration
3. Restart LiteLLM if model list is empty

## 🔄 Recovery Procedures

### Complete System Reset
```bash
# 1. Stop everything
docker-compose down --remove-orphans

# 2. Clean up
docker system prune -f
docker volume prune -f

# 3. Rebuild from scratch  
docker-compose up -d --build

# 4. Wait for services (2-5 minutes)
# 5. Test functionality
```

### Config Rollback
```bash
# Restore from backup
cp D:\zoi\config\litellm\backups\20250905_202934\config_simple.yaml D:\zoi\config\litellm\config_simple.yaml
cp D:\zoi\config\litellm\backups\20250905_202934\docker-compose.yml D:\zoi\apps\core\docker-compose.yml

# Restart services
docker-compose down && docker-compose up -d
```

### Individual Service Recovery
```bash
# LiteLLM only
docker-compose restart litellm
docker logs litellm --tail 20

# Weaviate only  
docker-compose restart weaviate
docker logs weaviate --tail 20

# Elysia only
docker-compose restart elysia
docker logs elysia --tail 20
```

## 📱 Monitoring & Maintenance

### Regular Health Checks
```bash
# Create a health check script
#!/bin/bash
echo "=== Zoi Stack Health Check ==="
curl -s http://localhost:7010/health && echo "✅ LiteLLM OK" || echo "❌ LiteLLM DOWN"
curl -s http://localhost:7080/v1/meta && echo "✅ Weaviate OK" || echo "❌ Weaviate DOWN"  
curl -s http://localhost:7085/api/health && echo "✅ Elysia OK" || echo "❌ Elysia DOWN"
```

### Log Management
```bash
# Rotate logs to prevent disk fill
docker logs litellm --tail 100 > litellm_recent.log
docker logs weaviate --tail 100 > weaviate_recent.log
docker logs elysia --tail 100 > elysia_recent.log

# Clean old logs
docker container prune -f
```

### Backup Procedures
```bash
# Backup critical configs
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp D:\zoi\config\litellm\config_simple.yaml backups/$(date +%Y%m%d_%H%M%S)/
cp D:\zoi\apps\core\docker-compose.yml backups/$(date +%Y%m%d_%H%M%S)/
```

## 🆘 When All Else Fails

### Nuclear Options
1. **Full Docker Reset**: Restart Docker Desktop
2. **System Reboot**: Windows restart
3. **Clean Installation**: Remove all containers and rebuild
4. **Check Hardware**: GPU drivers, network connectivity

### Getting Help
- Check recent changes to configs
- Review Docker logs for error patterns  
- Test individual components in isolation
- Document exact error messages and steps to reproduce
- Check this guide for similar issues

### Prevention
- Always backup configs before changes
- Test changes incrementally
- Monitor resource usage regularly
- Keep detailed logs of what works
- Document any custom configurations

---

💡 **Pro Tip**: Most issues are resolved by:
1. Checking the logs
2. Restarting the specific service
3. Verifying network connectivity
4. Ensuring correct configuration