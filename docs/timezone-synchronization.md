# Docker Timezone Synchronization

## Overview

This document outlines the timezone synchronization implementation for the Production RAG System to ensure all Docker containers use the same timezone (America/Chicago) and prevent JWT validation issues and maintain consistent application behavior.

## Problem Statement

JWT tokens and other time-sensitive operations can fail when containers have different timezone settings, leading to:
- JWT validation errors due to timestamp mismatches
- Inconsistent logging timestamps across services
- Authentication flow failures
- Scheduling and cron job inconsistencies

## Solution Implementation

### Timezone Configuration Strategy

All Docker services have been configured with:

1. **Environment Variable**: `TZ=America/Chicago`
2. **Volume Mount**: `/etc/localtime:/etc/localtime:ro`

This dual approach ensures:
- Applications respect the TZ environment variable
- System-level operations use the host's timezone
- Consistent time across all containers

### Services Updated

The following services have been configured with timezone synchronization:

#### Authentication Services
- `postgres` - PostgreSQL database for Authentik
- `authentik-redis` - Redis cache for Authentik
- `authentik-server` - Main Authentik authentication server
- `authentik-worker` - Authentik background worker

#### Core Infrastructure
- `traefik` - Reverse proxy and load balancer
- `vault` - HashiCorp Vault for secret management

#### Data Services
- `redis` - Main Redis cache
- `redis-insight` - Redis management interface
- `rabbitmq` - Message queue service
- `mongo-episodic` - MongoDB for episodic data
- `mongo-procedural` - MongoDB for procedural data
- `qdrant` - Vector database

#### Application Services
- `fastapi-1`, `fastapi-2`, `fastapi-3` - API backend services
- `worker` - Background task workers (2 replicas)
- `litellm` - LLM proxy service
- `ollama` - Local LLM service

#### User Interface
- `open-webui` - Chat interface
- `n8n` - Workflow automation

#### Monitoring & Backup
- `aim` - ML experiment tracking
- `healthchecks` - Health monitoring
- `backrest` - Backup service

## Configuration Examples

### Standard Service Configuration
```yaml
service-name:
  image: service:latest
  environment:
    - TZ=America/Chicago
    # other environment variables
  volumes:
    - /etc/localtime:/etc/localtime:ro
    # other volumes
```

### Service with Existing Environment Section
```yaml
service-name:
  image: service:latest
  environment:
    - EXISTING_VAR=value
    - TZ=America/Chicago
  volumes:
    - /etc/localtime:/etc/localtime:ro
```

### Service with Environment Object
```yaml
service-name:
  image: service:latest
  environment:
    TZ: America/Chicago
    EXISTING_VAR: value
  volumes:
    - /etc/localtime:/etc/localtime:ro
```

## Verification

### Automated Verification Script

Use the provided verification script to check timezone configuration:

```bash
./scripts/verify-timezone-sync.sh
```

This script will:
- Check all running containers for proper timezone configuration
- Verify TZ environment variable is set to America/Chicago
- Confirm date output shows CST/CDT timezone
- Report any misconfigurations

### Manual Verification

Check individual containers:

```bash
# Check environment variable
docker exec <container-name> echo $TZ

# Check date output
docker exec <container-name> date

# Check timezone file (if available)
docker exec <container-name> cat /etc/timezone
```

Expected outputs:
- `TZ` should be `America/Chicago`
- `date` should show CST or CDT
- Time should be consistent across all containers

## Benefits

### Security Benefits
- **JWT Validation**: Consistent timestamps prevent token validation failures
- **Session Management**: Proper session timeout handling
- **Audit Logging**: Synchronized timestamps for security analysis

### Operational Benefits
- **Consistent Logging**: All log entries use the same timezone
- **Scheduling**: Cron jobs and scheduled tasks work correctly
- **Monitoring**: Accurate time-based metrics and alerts
- **Debugging**: Easier correlation of events across services

### Development Benefits
- **Local Development**: Matches production timezone behavior
- **Testing**: Consistent time-based test results
- **Debugging**: Easier to trace issues across services

## Troubleshooting

### Common Issues

1. **Container Not Respecting TZ Variable**
   - Some images may not support TZ environment variable
   - Solution: Use volume mount for /etc/localtime

2. **Permission Issues with /etc/localtime**
   - Mount as read-only to prevent permission errors
   - Ensure host system has proper timezone configuration

3. **Application-Specific Timezone Settings**
   - Some applications may have internal timezone configuration
   - Check application documentation for timezone settings

### Validation Commands

```bash
# Check all running containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check specific service timezone
docker-compose exec <service-name> date

# Verify timezone in logs
docker-compose logs <service-name> | head -5
```

## Maintenance

### Adding New Services

When adding new services to the Docker Compose file:

1. Add `TZ=America/Chicago` to environment variables
2. Add `/etc/localtime:/etc/localtime:ro` to volumes
3. Run verification script to confirm configuration
4. Update this documentation if needed

### Changing Timezone

To change to a different timezone:

1. Update all `TZ` environment variables in docker-compose.yml
2. Update the verification script with new expected timezone
3. Restart all services: `docker-compose down && docker-compose up -d`
4. Run verification script to confirm changes

## Related Documentation

- [JWT Authentication](./jwt-authentication.md)
- [Docker Network Isolation](./network-isolation.md)
- [Service Health Monitoring](./health-monitoring.md)
- [Backup and Recovery](./backup-recovery.md)

## Security Considerations

- Timezone synchronization is critical for JWT token validation
- Consistent timestamps are essential for audit trails
- Time-based security policies depend on accurate time synchronization
- Session timeouts and token expiration rely on consistent time

## Testing

### Integration Tests

The timezone synchronization should be tested as part of:
- JWT authentication flows
- Session management tests
- Scheduled task execution
- Log aggregation and analysis
- Backup scheduling validation

### Monitoring

Monitor for timezone-related issues:
- JWT validation failures
- Session timeout inconsistencies
- Scheduled job failures
- Log timestamp anomalies
