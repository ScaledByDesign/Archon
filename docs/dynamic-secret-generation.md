# Dynamic Secret Generation Implementation

## Overview

This document describes the comprehensive dynamic secret generation and rotation system implemented using HashiCorp Vault. The system provides automated credential management for MongoDB, PostgreSQL, and API keys with built-in rotation, monitoring, and alerting capabilities.

## Architecture

### Components

1. **Vault Secret Engines**
   - Database secret engine for MongoDB and PostgreSQL
   - KV secret engine for API keys and rotation metadata
   - Transit secret engine for encryption (if needed)

2. **Automation Scripts**
   - `setup-dynamic-secrets-curl.sh` - Initial configuration
   - `rotate-secrets-curl.sh` - Manual rotation execution
   - `rotate-secrets-with-logging.sh` - Automated rotation with logging
   - `monitor-rotation-health.sh` - Health monitoring and alerting
   - `setup-rotation-cron.sh` - Cron job configuration

3. **Monitoring and Logging**
   - Centralized logging in `/logs/rotation/`
   - Health checks for Vault and rotation status
   - Automated log cleanup and retention

## Configuration

### Environment Variables

Required environment variables in `.env`:

```bash
# Vault Configuration
VAULT_ADDR=http://localhost:8200
VAULT_ROOT_TOKEN=vault-root-token-change-me-in-production

# Database Connections
MONGO_EPISODIC_HOST=mongo-episodic
MONGO_EPISODIC_PORT=27017
MONGO_PROCEDURAL_HOST=mongo-procedural
MONGO_PROCEDURAL_PORT=27017

POSTGRES_HOST=authentik-db
POSTGRES_PORT=5432
POSTGRES_DB=authentik
POSTGRES_USER=authentik
POSTGRES_PASSWORD=authentik-password-change-me
```

### Vault Policies

The system uses the existing `app-policy.hcl` which provides:

```hcl
# Database secret access
path "database/creds/*" {
  capabilities = ["read"]
}

# API key access
path "secret/data/api-keys/*" {
  capabilities = ["read"]
}

# Rotation status monitoring
path "secret/data/rotation/*" {
  capabilities = ["read"]
}
```

## Secret Engines Configuration

### Database Secret Engine

**MongoDB Configuration:**
- **Episodic Database**: `database/config/mongodb-episodic`
- **Procedural Database**: `database/config/mongodb-procedural`
- **Connection String**: `mongodb://{{username}}:{{password}}@mongo-episodic:27017/episodic`

**PostgreSQL Configuration:**
- **Authentik Database**: `database/config/postgresql-authentik`
- **Connection String**: `postgresql://{{username}}:{{password}}@authentik-db:5432/authentik`

### Role Definitions

**MongoDB Roles:**
```json
{
  "db": "episodic",
  "roles": [
    {
      "role": "readWrite",
      "db": "episodic"
    }
  ]
}
```

**PostgreSQL Roles:**
```sql
CREATE ROLE "{{name}}" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "{{name}}";
```

## Rotation Schedules

### Automated Cron Jobs

1. **Daily Rotation Check** - Every day at 2:00 AM
   ```cron
   0 2 * * * /Users/nova/Sites/zoi/scripts/rotate-secrets-with-logging.sh
   ```

2. **Weekly Verification** - Every Sunday at 3:00 AM
   ```cron
   0 3 * * 0 /Users/nova/Sites/zoi/scripts/rotate-secrets-with-logging.sh
   ```

3. **Monthly Audit** - First day of month at 4:00 AM
   ```cron
   0 4 1 * * /Users/nova/Sites/zoi/scripts/rotate-secrets-with-logging.sh
   ```

### Manual Rotation

Execute immediate rotation:
```bash
./scripts/rotate-secrets-curl.sh
```

Execute rotation with logging:
```bash
./scripts/rotate-secrets-with-logging.sh
```

## Monitoring and Alerting

### Health Monitoring

Run health checks:
```bash
./scripts/monitor-rotation-health.sh
```

**Monitored Components:**
- Vault server health and seal status
- Recent rotation log analysis
- Rotation status in Vault
- Database connectivity (via secret generation tests)

### Log Management

**Log Location:** `/logs/rotation/rotation_YYYYMMDD_HHMMSS.log`

**Log Cleanup:**
```bash
# Clean logs older than 30 days (default)
./scripts/cleanup-rotation-logs.sh

# Clean logs older than 7 days
./scripts/cleanup-rotation-logs.sh 7
```

### Alerting Integration

The monitoring script returns appropriate exit codes for integration with alerting systems:
- `0` - All checks passed
- `1` - One or more checks failed

## API Integration

### Generating Dynamic Credentials

**MongoDB Episodic:**
```bash
curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
  "$VAULT_ADDR/v1/database/creds/mongodb-episodic-role"
```

**MongoDB Procedural:**
```bash
curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
  "$VAULT_ADDR/v1/database/creds/mongodb-procedural-role"
```

**PostgreSQL:**
```bash
curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
  "$VAULT_ADDR/v1/database/creds/postgresql-authentik-role"
```

### Response Format

```json
{
  "request_id": "uuid",
  "lease_id": "database/creds/mongodb-episodic-role/uuid",
  "renewable": true,
  "lease_duration": 3600,
  "data": {
    "password": "generated-password",
    "username": "v-root-mongodb-episodic-role-uuid"
  }
}
```

## Application Integration

### FastAPI Integration Example

```python
import requests
import os

class VaultSecretManager:
    def __init__(self):
        self.vault_addr = os.getenv('VAULT_ADDR')
        self.vault_token = os.getenv('VAULT_TOKEN')
        
    def get_database_credentials(self, database_type):
        """Get dynamic database credentials from Vault"""
        headers = {'X-Vault-Token': self.vault_token}
        
        role_mapping = {
            'mongodb_episodic': 'database/creds/mongodb-episodic-role',
            'mongodb_procedural': 'database/creds/mongodb-procedural-role',
            'postgresql': 'database/creds/postgresql-authentik-role'
        }
        
        path = role_mapping.get(database_type)
        if not path:
            raise ValueError(f"Unknown database type: {database_type}")
            
        response = requests.get(
            f"{self.vault_addr}/v1/{path}",
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        return {
            'username': data['data']['username'],
            'password': data['data']['password'],
            'lease_id': data['lease_id'],
            'lease_duration': data['lease_duration']
        }
    
    def revoke_lease(self, lease_id):
        """Revoke a specific lease"""
        headers = {'X-Vault-Token': self.vault_token}
        data = {'lease_id': lease_id}
        
        response = requests.post(
            f"{self.vault_addr}/v1/sys/leases/revoke",
            headers=headers,
            json=data
        )
        response.raise_for_status()

# Usage example
vault_manager = VaultSecretManager()
creds = vault_manager.get_database_credentials('mongodb_episodic')

# Use credentials for database connection
connection_string = f"mongodb://{creds['username']}:{creds['password']}@mongo-episodic:27017/episodic"
```

## Security Considerations

### Access Control

1. **Principle of Least Privilege**
   - Applications only receive credentials for required databases
   - Short-lived credentials (1 hour default TTL)
   - Role-based access control via Vault policies

2. **Network Security**
   - Vault communication over isolated Docker networks
   - TLS encryption for production deployments
   - Token-based authentication with limited scope

3. **Credential Lifecycle**
   - Automatic credential expiration
   - Immediate revocation capability
   - Audit logging of all credential access

### Rotation Security

1. **Zero-Downtime Rotation**
   - Overlapping credential validity periods
   - Graceful credential transition
   - Application-level credential refresh

2. **Failure Handling**
   - Automatic retry mechanisms
   - Fallback to previous credentials
   - Alert generation on rotation failures

## Troubleshooting

### Common Issues

1. **Database Connection Failures**
   ```bash
   # Check database connectivity from Vault
   docker exec vault-container vault write database/config/test \
     plugin_name=mongodb-database-plugin \
     connection_url="mongodb://admin:password@mongo:27017/admin" \
     allowed_roles="test-role"
   ```

2. **Token Expiration**
   ```bash
   # Check token validity
   curl -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/auth/token/lookup-self"
   ```

3. **Rotation Failures**
   ```bash
   # Check rotation logs
   tail -f /Users/nova/Sites/zoi/logs/rotation/rotation_*.log
   
   # Manual rotation test
   ./scripts/rotate-secrets-curl.sh
   ```

### Log Analysis

**Successful Rotation Indicators:**
- "✓ MongoDB episodic credentials rotated"
- "✓ PostgreSQL credentials rotated"
- "Rotation Complete"

**Failure Indicators:**
- "error creating database object"
- "failed to verify connection"
- "rotation failed with exit code"

## Performance Considerations

### Credential Caching

- **TTL Management**: Balance security vs. performance
- **Connection Pooling**: Reuse connections within credential lifetime
- **Batch Operations**: Minimize credential generation requests

### Monitoring Metrics

- Credential generation rate
- Rotation success/failure rates
- Database connection latencies
- Vault API response times

## Backup and Recovery

### Vault Data Backup

```bash
# Backup Vault data
vault operator raft snapshot save backup.snap

# Restore from backup
vault operator raft snapshot restore backup.snap
```

### Configuration Backup

- Store all configuration scripts in version control
- Document environment variable requirements
- Maintain deployment runbooks

## Future Enhancements

1. **Advanced Monitoring**
   - Prometheus metrics integration
   - Grafana dashboards
   - PagerDuty alerting

2. **Multi-Environment Support**
   - Environment-specific rotation schedules
   - Staged credential rollouts
   - Cross-environment secret sharing

3. **Enhanced Security**
   - Hardware Security Module (HSM) integration
   - Multi-factor authentication for admin operations
   - Advanced audit logging and SIEM integration

## Conclusion

The dynamic secret generation system provides a robust, secure, and automated approach to credential management. With proper monitoring, rotation, and security controls, it significantly reduces the risk of credential compromise while maintaining operational efficiency.

For support or questions, refer to the HashiCorp Vault documentation or contact the platform engineering team.
