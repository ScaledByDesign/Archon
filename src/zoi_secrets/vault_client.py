"""
HashiCorp Vault Client for Secure Secret Management
Provides secure access to secrets stored in Vault for the RAG system
"""

import os
import logging
import hvac
from typing import Dict, Any, Optional
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Configuration for Vault client"""
    url: str = "http://localhost:8200"
    token: Optional[str] = None
    role_id: Optional[str] = None
    secret_id: Optional[str] = None
    timeout: int = 30
    verify_ssl: bool = False
    mount_point: str = "secret"
    
    @classmethod
    def from_env(cls) -> 'VaultConfig':
        """Create configuration from environment variables"""
        return cls(
            url=os.getenv('VAULT_ADDR', 'http://localhost:8200'),
            token=os.getenv('VAULT_TOKEN') or os.getenv('VAULT_ROOT_TOKEN'),
            role_id=os.getenv('VAULT_ROLE_ID'),
            secret_id=os.getenv('VAULT_SECRET_ID'),
            timeout=int(os.getenv('VAULT_TIMEOUT', '30')),
            verify_ssl=os.getenv('VAULT_VERIFY_SSL', 'false').lower() == 'true',
            mount_point=os.getenv('VAULT_MOUNT_POINT', 'secret')
        )


class VaultClient:
    """
    HashiCorp Vault client for secure secret management
    Supports both token-based and AppRole authentication
    """
    
    def __init__(self, config: Optional[VaultConfig] = None):
        self.config = config or VaultConfig.from_env()
        self.client = None
        self._authenticated = False
        self._connect()
    
    def _connect(self):
        """Establish connection to Vault"""
        try:
            self.client = hvac.Client(
                url=self.config.url,
                verify=self.config.verify_ssl,
                timeout=self.config.timeout
            )
            
            # Authenticate using available method
            if self.config.token:
                self._authenticate_with_token()
            elif self.config.role_id and self.config.secret_id:
                self._authenticate_with_approle()
            else:
                raise ValueError("No valid authentication method available")
                
            logger.info(f"Successfully connected to Vault at {self.config.url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Vault: {e}")
            raise
    
    def _authenticate_with_token(self):
        """Authenticate using root/service token"""
        self.client.token = self.config.token
        
        if not self.client.is_authenticated():
            raise ValueError("Invalid Vault token")
        
        self._authenticated = True
        logger.info("Successfully authenticated with Vault using token")
    
    def _authenticate_with_approle(self):
        """Authenticate using AppRole method"""
        try:
            auth_response = self.client.auth.approle.login(
                role_id=self.config.role_id,
                secret_id=self.config.secret_id
            )
            
            self.client.token = auth_response['auth']['client_token']
            self._authenticated = True
            logger.info("Successfully authenticated with Vault using AppRole")
            
        except Exception as e:
            logger.error(f"AppRole authentication failed: {e}")
            raise
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self._authenticated and self.client.is_authenticated()
    
    def get_secret(self, path: str, key: Optional[str] = None) -> Any:
        """
        Retrieve a secret from Vault
        
        Args:
            path: Secret path (e.g., 'app/database')
            key: Specific key within the secret (optional)
            
        Returns:
            Secret value or dictionary of all secret keys
        """
        if not self.is_authenticated():
            raise ValueError("Vault client not authenticated")
        
        try:
            full_path = f"{self.config.mount_point}/data/{path}"
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            
            secret_data = response['data']['data']
            
            if key:
                if key not in secret_data:
                    raise KeyError(f"Key '{key}' not found in secret '{path}'")
                return secret_data[key]
            
            return secret_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{path}': {e}")
            raise
    
    def put_secret(self, path: str, secret: Dict[str, Any]) -> bool:
        """
        Store a secret in Vault
        
        Args:
            path: Secret path (e.g., 'app/database')
            secret: Dictionary of key-value pairs to store
            
        Returns:
            True if successful
        """
        if not self.is_authenticated():
            raise ValueError("Vault client not authenticated")
        
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret
            )
            
            logger.info(f"Successfully stored secret at '{path}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret '{path}': {e}")
            raise
    
    def delete_secret(self, path: str) -> bool:
        """
        Delete a secret from Vault
        
        Args:
            path: Secret path to delete
            
        Returns:
            True if successful
        """
        if not self.is_authenticated():
            raise ValueError("Vault client not authenticated")
        
        try:
            self.client.secrets.kv.v2.delete_latest_version_of_secret(path=path)
            logger.info(f"Successfully deleted secret at '{path}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret '{path}': {e}")
            raise
    
    def list_secrets(self, path: str = "") -> list:
        """
        List secrets at a given path
        
        Args:
            path: Path to list (empty for root)
            
        Returns:
            List of secret names/paths
        """
        if not self.is_authenticated():
            raise ValueError("Vault client not authenticated")
        
        try:
            full_path = f"{self.config.mount_point}/metadata/{path}" if path else f"{self.config.mount_point}/metadata"
            response = self.client.secrets.kv.v2.list_secrets(path=path)
            return response.get('data', {}).get('keys', [])
            
        except Exception as e:
            logger.warning(f"Failed to list secrets at '{path}': {e}")
            return []
    
    def get_database_credentials(self) -> Dict[str, str]:
        """Get database connection credentials"""
        return self.get_secret('app/database')
    
    def get_redis_credentials(self) -> Dict[str, str]:
        """Get Redis connection credentials"""
        return self.get_secret('app/redis')
    
    def get_rabbitmq_credentials(self) -> Dict[str, str]:
        """Get RabbitMQ connection credentials"""
        return self.get_secret('app/rabbitmq')
    
    def get_qdrant_config(self) -> Dict[str, str]:
        """Get Qdrant configuration"""
        return self.get_secret('app/qdrant')
    
    def get_mongodb_credentials(self) -> Dict[str, str]:
        """Get MongoDB connection credentials"""
        return self.get_secret('app/mongodb')
    
    def get_llm_credentials(self) -> Dict[str, str]:
        """Get LLM API credentials"""
        return self.get_secret('app/llm')
    
    def get_authentik_config(self) -> Dict[str, str]:
        """Get Authentik configuration"""
        return self.get_secret('app/authentik')
    
    def get_jwt_config(self) -> Dict[str, str]:
        """Get JWT configuration"""
        return self.get_secret('app/jwt')
    
    def get_environment_config(self, env: str = "development") -> Dict[str, str]:
        """Get environment-specific configuration"""
        return self.get_secret(f'env/{env}')


@lru_cache(maxsize=1)
def get_vault_client() -> VaultClient:
    """Get a cached Vault client instance"""
    return VaultClient()


class SecretManager:
    """
    High-level secret management interface
    Provides convenient methods for accessing common secrets
    """
    
    def __init__(self, vault_client: Optional[VaultClient] = None):
        self.vault = vault_client or get_vault_client()
    
    def get_database_url(self) -> str:
        """Get formatted database URL"""
        creds = self.vault.get_database_credentials()
        return f"postgresql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    
    def get_redis_url(self) -> str:
        """Get formatted Redis URL"""
        creds = self.vault.get_redis_credentials()
        password_part = f":{creds['password']}@" if creds.get('password') else '@'
        return f"redis://{password_part}{creds['host']}:{creds['port']}"
    
    def get_mongodb_urls(self) -> Dict[str, str]:
        """Get formatted MongoDB URLs"""
        creds = self.vault.get_mongodb_credentials()
        auth_part = ""
        if creds.get('username') and creds.get('password'):
            auth_part = f"{creds['username']}:{creds['password']}@"
        
        return {
            'episodic': creds['episodic_url'].replace('mongodb://', f'mongodb://{auth_part}'),
            'procedural': creds['procedural_url'].replace('mongodb://', f'mongodb://{auth_part}')
        }
    
    def get_rabbitmq_url(self) -> str:
        """Get formatted RabbitMQ URL"""
        creds = self.vault.get_rabbitmq_credentials()
        vhost = creds.get('vhost', '/')
        return f"amqp://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}{vhost}"
    
    def get_mongodb_credentials(self) -> Dict[str, str]:
        """Get MongoDB credentials"""
        return self.vault.get_mongodb_credentials()
    
    def get_qdrant_credentials(self) -> Dict[str, str]:
        """Get Qdrant credentials"""
        return self.vault.get_qdrant_config()
    
    def get_jwt_config(self) -> Dict[str, str]:
        """Get JWT configuration"""
        return self.vault.get_jwt_config()
    
    def get_llm_credentials(self) -> Dict[str, str]:
        """Get LLM credentials"""
        return self.vault.get_llm_credentials()
    
    def get_secret(self, path: str, key: Optional[str] = None) -> Any:
        """Get a generic secret from Vault"""
        return self.vault.get_secret(path, key)
    
    def refresh_secrets(self):
        """Refresh all cached secrets"""
        get_vault_client.cache_clear()
        self.vault = get_vault_client()


# Global instance for easy access (lazy initialization)
_secret_manager = None

def get_secret_manager(vault_client=None):
    """Get or create the global SecretManager instance."""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager(vault_client)
    return _secret_manager
