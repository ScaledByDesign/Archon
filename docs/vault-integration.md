# HashiCorp Vault Integration

This document describes the secure secret management integration using HashiCorp Vault for the Production RAG System.

## Overview

The system uses HashiCorp Vault to securely store and manage sensitive credentials, API keys, and configuration secrets. This replaces hardcoded secrets with a centralized, secure secret management solution.

## Architecture

### Components

1. **Vault Server**: HashiCorp Vault 1.15 running in Docker container
2. **Python Client**: Custom `VaultClient` class for seamless integration
3. **Secret Manager**: High-level interface for application secret access
4. **AppRole Authentication**: Service-to-service authentication method

### Deployment

```yaml
# Docker service configuration
vault:
  image: hashicorp/vault:1.15
  ports:
    - "8200:8200"
  environment:
    - VAULT_DEV_ROOT_TOKEN_ID=${VAULT_ROOT_TOKEN}
    - VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200
  volumes:
    - vault_data:/vault/data
    - vault_logs:/vault/logs
    - ./config/vault:/vault/config:ro
```

## Configuration

### Environment Variables

```bash
# Vault connection
VAULT_ADDR=http://localhost:8200
VAULT_ROOT_TOKEN=vault-root-token-change-me-in-production

# AppRole credentials (generated during initialization)
VAULT_ROLE_ID=11cb1642-d078-cd21-4d0f-0085555f0873
VAULT_SECRET_ID=1606a2d9-7c6d-97ac-0f0a-c66ec7794adc
```

### Policies

#### Application Policy (`app-policy.hcl`)
```hcl
# Read-only access to application secrets
path "secret/data/app/*" {
  capabilities = ["read", "list"]
}

path "secret/data/env/development" {
  capabilities = ["read"]
}

path "secret/metadata/app/*" {
  capabilities = ["list"]
}
```

#### Admin Policy (`admin-policy.hcl`)
```hcl
# Full access to all secrets and management
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}
```

## Secret Organization

### Application Secrets

| Path | Description | Keys |
|------|-------------|------|
| `secret/app/database` | PostgreSQL credentials | host, port, username, password, database |
| `secret/app/redis` | Redis credentials | host, port, password |
| `secret/app/rabbitmq` | RabbitMQ credentials | host, port, username, password, vhost |
| `secret/app/mongodb` | MongoDB credentials | episodic_url, procedural_url, username, password |
| `secret/app/qdrant` | Qdrant configuration | url, api_key, timeout |
| `secret/app/llm` | LLM API keys | openai_api_key, anthropic_api_key, litellm_master_key |
| `secret/app/authentik` | Authentik configuration | secret_key, bootstrap_password, bootstrap_token |
| `secret/app/jwt` | JWT configuration | secret_key, algorithm, expiration |

### Environment Secrets

| Path | Description | Keys |
|------|-------------|------|
| `secret/env/development` | Development config | debug, log_level, environment |
| `secret/env/production` | Production config | debug, log_level, environment |

## Python Integration

### Basic Usage

```python
from src.secrets.vault_client import VaultClient, SecretManager

# Initialize client
vault = VaultClient()

# Get individual secret
db_password = vault.get_secret('app/database', 'password')

# Get all database credentials
db_config = vault.get_database_credentials()

# Use high-level SecretManager
secrets = SecretManager()
database_url = secrets.get_database_url()
redis_url = secrets.get_redis_url()
```

### Advanced Usage

```python
# Custom configuration
from src.secrets.vault_client import VaultConfig, VaultClient

config = VaultConfig(
    url='https://vault.example.com:8200',
    role_id='your-role-id',
    secret_id='your-secret-id',
    verify_ssl=True
)

vault = VaultClient(config)

# Store new secrets
vault.put_secret('app/new-service', {
    'api_key': 'secret-key',
    'endpoint': 'https://api.example.com'
})
```

## Authentication

### AppRole Method

The system uses AppRole authentication for service-to-service access:

1. **Role ID**: Static identifier for the application role
2. **Secret ID**: Dynamic credential that can be rotated
3. **Token**: Short-lived access token obtained from Role ID + Secret ID

### Token Lifecycle

- **Token TTL**: 1 hour (configurable)
- **Token Max TTL**: 4 hours (configurable)
- **Secret ID**: Can be rotated regularly for enhanced security

## Operations

### Initialization

```bash
# Run the initialization script
./scripts/init-vault.sh
```

This script:
1. Creates and applies security policies
2. Enables AppRole authentication
3. Creates application role
4. Generates initial Role ID and Secret ID
5. Enables KV v2 secrets engine
6. Creates initial secret structure

### Secret Management

#### Retrieving Secrets

```bash
# Using Vault CLI (in Docker container)
docker exec -e VAULT_TOKEN="vault-root-token" zoi-vault-1 vault kv get secret/app/database

# Using HTTP API
curl -H "X-Vault-Token: vault-root-token" http://localhost:8200/v1/secret/data/app/database
```

#### Updating Secrets

```bash
# Update database password
docker exec -e VAULT_TOKEN="vault-root-token" zoi-vault-1 vault kv put secret/app/database password="new-secure-password"
```

### Secret Rotation

#### Automated Rotation

```python
from src.secrets.vault_client import get_vault_client

vault = get_vault_client()

# Generate new Secret ID
new_secret = vault.client.write(
    'auth/approle/role/rag-app/secret-id',
    force=True
)
print(f"New Secret ID: {new_secret['data']['secret_id']}")
```

#### Manual Rotation

```bash
# Generate new Secret ID
docker exec -e VAULT_TOKEN="vault-root-token" zoi-vault-1 vault write -force auth/approle/role/rag-app/secret-id
```

## Security Best Practices

### Access Control

1. **Principle of Least Privilege**: Each service gets only required permissions
2. **Role-Based Access**: Use AppRole for service authentication
3. **Token Expiration**: Short-lived tokens reduce exposure risk
4. **Secret Rotation**: Regular rotation of Secret IDs and sensitive data

### Network Security

1. **TLS Encryption**: Use HTTPS in production environments
2. **Network Isolation**: Vault should be on secure network segments
3. **Firewall Rules**: Restrict access to Vault ports

### Storage Security

1. **Encrypted Storage**: Vault data is encrypted at rest
2. **Backup Encryption**: Backup files should be encrypted
3. **Access Logging**: Enable audit logging for all operations

## Monitoring and Alerts

### Health Checks

```bash
# Check Vault status
curl http://localhost:8200/v1/sys/health

# Check authentication
curl -H "X-Vault-Token: vault-root-token" http://localhost:8200/v1/auth/token/lookup-self
```

### Metrics

- **Token Usage**: Monitor token creation and expiration
- **Secret Access**: Track secret read/write operations
- **Authentication Failures**: Alert on failed authentication attempts
- **Policy Violations**: Monitor unauthorized access attempts

## Troubleshooting

### Common Issues

#### Connection Problems

```python
# Check Vault connectivity
import requests
response = requests.get('http://localhost:8200/v1/sys/health')
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

#### Authentication Issues

```bash
# Verify token
curl -H "X-Vault-Token: your-token" http://localhost:8200/v1/auth/token/lookup-self

# Check AppRole configuration
docker exec zoi-vault-1 vault read auth/approle/role/rag-app
```

#### Permission Errors

```bash
# Check applied policies
docker exec zoi-vault-1 vault token lookup -format=json

# Test policy permissions
docker exec zoi-vault-1 vault policy read app-policy
```

### Debugging

Enable debug logging in the Vault client:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from src.secrets.vault_client import VaultClient
vault = VaultClient()
```

## Backup and Recovery

### Data Backup

Vault data is stored in Docker volumes:
- **vault_data**: Contains encrypted secret data
- **vault_logs**: Contains audit and operational logs

### Recovery Procedures

1. **Container Recovery**: Restart Vault container with existing volumes
2. **Data Migration**: Export/import secrets using Vault CLI
3. **Disaster Recovery**: Restore from encrypted backups

## Production Deployment

### Security Hardening

1. **Change Default Tokens**: Replace development tokens with secure ones
2. **Enable TLS**: Configure SSL certificates for production
3. **Audit Logging**: Enable comprehensive audit logging
4. **Backup Strategy**: Implement automated backup procedures
5. **Monitoring**: Set up alerting and monitoring systems

### Configuration Updates

```bash
# Production environment variables
VAULT_ADDR=https://vault.yourdomain.com:8200
VAULT_VERIFY_SSL=true
VAULT_ROOT_TOKEN=production-secure-token
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from src.secrets.vault_client import SecretManager

app = FastAPI()

def get_secret_manager():
    return SecretManager()

@app.get("/health")
async def health_check(secrets: SecretManager = Depends(get_secret_manager)):
    # Secrets are automatically retrieved from Vault
    db_url = secrets.get_database_url()
    # Use db_url to connect to database
    return {"status": "healthy"}
```

### Database Connection

```python
import asyncpg
from src.secrets.vault_client import SecretManager

async def create_db_pool():
    secrets = SecretManager()
    db_url = secrets.get_database_url()
    
    return await asyncpg.create_pool(
        dsn=db_url,
        min_size=5,
        max_size=20
    )
```

This integration provides a secure, scalable foundation for secret management across the entire RAG system.
