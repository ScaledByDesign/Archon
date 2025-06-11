# Load Balancing Configuration

## Overview

The Zoi application uses **Traefik** as a reverse proxy and load balancer to distribute traffic across multiple FastAPI backend instances. This ensures high availability, fault tolerance, and optimal performance under load.

## Architecture

```
Internet → Traefik → FastAPI Instances (3x)
                  ├── fastapi-1:8000
                  ├── fastapi-2:8000
                  └── fastapi-3:8000
```

## Load Balancing Features

### 1. Multiple FastAPI Instances
- **fastapi-1**: Primary instance
- **fastapi-2**: Secondary instance  
- **fastapi-3**: Tertiary instance
- All instances run on port 8000 internally
- External access via `api.${DOMAIN:-zoi.local}`

### 2. Traefik Configuration
- **Load Balancing Algorithm**: Round-robin (default)
- **Sticky Sessions**: Enabled with secure HTTP-only cookies
- **Health Checks**: Automated health monitoring
- **SSL/TLS**: Automatic certificate management

### 3. Health Check Configuration
```yaml
healthCheck:
  path: /health
  interval: 30s
  timeout: 5s
  scheme: http
```

### 4. Sticky Sessions
```yaml
sticky:
  cookie:
    name: server
    secure: true
    httpOnly: true
```

## Service Discovery

Traefik automatically discovers services through Docker labels:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.api.rule=Host(`api.${DOMAIN:-zoi.local}`)"
  - "traefik.http.routers.api.entrypoints=websecure"
  - "traefik.http.routers.api.tls=true"
  - "traefik.http.services.api.loadbalancer.server.port=8000"
  - "traefik.http.services.api.loadbalancer.sticky.cookie=true"
```

## Scaling Operations

### Manual Scaling
```bash
# Scale FastAPI instances
docker-compose up --scale fastapi-1=3 --scale fastapi-2=2 --scale fastapi-3=2

# Or using Docker Swarm mode
docker service scale zoi_fastapi-1=5
```

### Health Monitoring
- **Endpoint**: `/health`
- **Check Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Automatic Failover**: Unhealthy instances are removed from rotation

## Performance Optimization

### 1. Connection Pooling
- FastAPI instances use async connection pools for databases
- MongoDB: Motor async driver
- Redis: aioredis with connection pooling
- PostgreSQL: asyncpg with SQLAlchemy async engine

### 2. Async Request Handling
- All endpoints use `async def` for non-blocking operations
- Concurrent request processing
- Efficient resource utilization

### 3. Caching Strategy
- Redis for session storage and caching
- Application-level caching for frequently accessed data
- CDN integration for static assets

## Monitoring and Metrics

### Traefik Dashboard
- **URL**: `traefik.${DOMAIN:-zoi.local}`
- **Metrics**: Request rates, response times, error rates
- **Service Status**: Health check results

### Health Endpoints
- **Main Health**: `/health`
- **Auth Health**: `/api/auth/health`
- **Search Health**: `/api/search/health`

## Fault Tolerance

### 1. Automatic Failover
- Unhealthy instances automatically removed from load balancer
- Traffic redistributed to healthy instances
- Automatic recovery when instances become healthy

### 2. Circuit Breaker Pattern
- Implemented in FastAPI middleware
- Prevents cascade failures
- Graceful degradation under high load

### 3. Graceful Shutdown
- Proper signal handling in FastAPI instances
- Drain connections before shutdown
- Zero-downtime deployments

## Security

### 1. SSL/TLS Termination
- Traefik handles SSL/TLS termination
- Automatic certificate management with Let's Encrypt
- HTTP to HTTPS redirection

### 2. Rate Limiting
- Implemented at Traefik level
- Per-IP rate limiting
- DDoS protection

### 3. Security Headers
- Automatic security header injection
- CORS configuration
- CSP (Content Security Policy) headers

## Deployment Strategies

### 1. Blue-Green Deployment
```bash
# Deploy new version to staging
docker-compose -f docker-compose.staging.yml up -d

# Switch traffic after validation
# Update production configuration
```

### 2. Rolling Updates
```bash
# Update instances one by one
docker-compose up -d fastapi-1
# Wait for health check
docker-compose up -d fastapi-2
# Wait for health check  
docker-compose up -d fastapi-3
```

## Troubleshooting

### Common Issues

1. **Instance Not Responding**
   - Check health endpoint: `curl http://fastapi-1:8000/health`
   - Review container logs: `docker logs fastapi-1`
   - Verify network connectivity

2. **Load Balancer Not Routing**
   - Check Traefik dashboard
   - Verify service labels in docker-compose.yml
   - Review Traefik configuration files

3. **Sticky Sessions Not Working**
   - Verify cookie configuration
   - Check HTTPS/secure cookie settings
   - Review browser developer tools

### Monitoring Commands
```bash
# Check service status
docker-compose ps

# View Traefik logs
docker logs traefik

# Check FastAPI instance health
curl -f http://zoi.local:8000/health

# Monitor resource usage
docker stats
```

## Configuration Files

- **Main Config**: `docker-compose.yml`
- **Traefik Config**: `config/traefik/traefik.yml`
- **Dynamic Config**: `config/traefik/dynamic/services.yml`
- **Middleware Config**: `config/traefik/dynamic/middleware.yml`

## Best Practices

1. **Always use health checks** for proper load balancing
2. **Monitor resource usage** and scale proactively
3. **Implement graceful shutdown** in application code
4. **Use sticky sessions** for stateful applications
5. **Regular backup** of Traefik configuration
6. **Test failover scenarios** regularly
7. **Monitor SSL certificate expiration**

## Future Enhancements

- [ ] Implement auto-scaling based on CPU/memory metrics
- [ ] Add Prometheus metrics collection
- [ ] Implement advanced routing rules
- [ ] Add geographic load balancing
- [ ] Integrate with Kubernetes for container orchestration
